from math import ceil
import logging
import pandas as pd
from chromadb import PersistentClient
from sentence_transformers import SentenceTransformer
from utils import clean_text, parse_timestamp, hash_text
from document_builder import build_document, build_metadata

def ingest(config):
    events = pd.read_csv(config.events_csv, dtype=str)
    event_types = pd.read_csv(config.event_types_csv, dtype=str)

    if "Timestamp" in events.columns:
        events["Timestamp"] = events["Timestamp"].apply(parse_timestamp)

    for col in events.select_dtypes(include=["object"]).columns:
        if col != "Timestamp":
            events[col] = events[col].apply(clean_text)
    for col in event_types.select_dtypes(include=["object"]).columns:
        event_types[col] = event_types[col].apply(clean_text)

    events["EventTypeID"] = events["EventTypeID"].astype(str)
    event_types["EventTypeID"] = event_types["EventTypeID"].astype(str)

    merged = events.merge(event_types, on="EventTypeID", how="left", suffixes=("", "_etype"))
    for col in ["Name", "Category", "SystemCode"]:
        etype_col = col  
        if etype_col in merged.columns:
            merged[f"Event{col}"] = merged[etype_col]
        else:
            merged[f"Event{col}"] = ""

    merged["document"] = merged.apply(build_document, axis=1)
    merged["metadata"] = merged.apply(build_metadata, axis=1)
    merged["hash"] = merged["document"].apply(hash_text)

    client = PersistentClient(config.chroma_path)
    try:
        collection = client.get_collection(config.collection_name)
        logging.info("Using existing collection: %s", config.collection_name)
    except Exception:
        collection = client.create_collection(config.collection_name)
        logging.info("Created new collection: %s", config.collection_name)

    embedder = SentenceTransformer(config.embedding_model)

    ids = merged["EventID"].astype(str).tolist()
    num_batches = ceil(len(ids) / config.batch_size)
    added = updated = skipped = 0

    for i in range(num_batches):
        batch = merged.iloc[i * config.batch_size: (i + 1) * config.batch_size]
        batch_ids = batch["EventID"].astype(str).tolist()
        print(f"Processing batch {i+1}/{num_batches} ({len(batch)} events)")

        try:
            stored = collection.get(ids=batch_ids)
            stored_ids = stored.get("ids", [])
            stored_metas = stored.get("metadatas", [])
            stored_by_id = {id_: meta for id_, meta in zip(stored_ids, stored_metas)}
        except Exception:
            stored_by_id = {}

        to_add, to_update = [], []

        for _, row in batch.iterrows():
            doc_id = str(row["EventID"])
            meta = row["metadata"].copy()
            meta["hash"] = row["hash"]

            if doc_id not in stored_by_id:
                to_add.append((doc_id, row["document"], meta))
            elif stored_by_id.get(doc_id, {}).get("hash") != row["hash"]:
                to_update.append((doc_id, row["document"], meta))
            else:
                skipped += 1

        texts = [t[1] for t in to_add + to_update]
        if texts:
            embeddings = embedder.encode(texts, batch_size=32, show_progress_bar=False).tolist()
            add_embeds = embeddings[:len(to_add)]
            update_embeds = embeddings[len(to_add):]

            if to_add:
                collection.add(
                    ids=[t[0] for t in to_add],
                    documents=[t[1] for t in to_add],
                    metadatas=[t[2] for t in to_add],
                    embeddings=add_embeds
                )
                added += len(to_add)
                print(f"Added {len(to_add)} new events")

            if to_update:
                collection.update(
                    ids=[t[0] for t in to_update],
                    documents=[t[1] for t in to_update],
                    metadatas=[t[2] for t in to_update],
                    embeddings=update_embeds
                )
                updated += len(to_update)
                print(f"Updated {len(to_update)} existing events")

        if not to_add and not to_update:
            print(f"Skipped {len(batch)} unchanged events")

    print(f"Finished ingestion. Added: {added}, Updated: {updated}, Skipped: {skipped}, Total in collection: {collection.count()}")
    return {"added": added, "updated": updated, "skipped": skipped, "total": collection.count()}