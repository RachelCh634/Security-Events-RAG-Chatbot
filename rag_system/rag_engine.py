import torch
import logging
from sentence_transformers import util
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(__file__))

from setup import client_llm, collection, embedder
from filters import parse_filters, build_where, filter_loc_with_embeds, filter_time_with_embeds

def answer_question(question, history=None, top_k=10, similarity_threshold=0.35):
    """
    Answer a question using RAG. If `history` is provided (list of [user, assistant] pairs),
    use recent user messages to form a better query embedding and include conversation context
    in the LLM prompt.
    """
    hist = history or []

    try:
        user_msgs = [h[0] for h in hist if h and len(h) > 0]
    except Exception:
        user_msgs = []

    recent_users = user_msgs[-3:] if user_msgs else []
    combined_query = " ".join(recent_users + [question]) if recent_users else question

    filters = parse_filters(question)
    where_clause = build_where(filters)
    q_emb = embedder.encode(combined_query)

    has_any_filter = bool(filters)
    requested_results = 1000 if has_any_filter else top_k * 2
    
    query_params = {
        "query_embeddings": [q_emb.tolist()],
        "n_results": requested_results,
        "include": ["documents", "metadatas", "embeddings"]
    }
    if where_clause:
        query_params["where"] = where_clause

    res = collection.query(**query_params)
    logging.getLogger(__name__).info("Chroma query requested n_results=%s where=%s", requested_results, where_clause)
    docs, metas, embeds = res["documents"][0], res["metadatas"][0], res["embeddings"][0]

    if "location" in filters:
        docs, metas, embeds = filter_loc_with_embeds(docs, metas, embeds, filters["location"])

    if "time" in filters:
        docs, metas, embeds = filter_time_with_embeds(docs, metas, embeds, filters["time"])

    if has_any_filter:
        scored = []
        q_tensor = torch.tensor(q_emb, dtype=torch.float32)
        for d, m, e in zip(docs, metas, embeds):
            sim = util.cos_sim(q_tensor, torch.tensor(e, dtype=torch.float32)).item()
            if sim >= similarity_threshold:
                scored.append((d, m, sim))

        scored = sorted(scored, key=lambda x: x[2], reverse=True)[:top_k]
        docs, metas = [x[0] for x in scored], [x[1] for x in scored]
    else:
        scored = []
        q_tensor = torch.tensor(q_emb, dtype=torch.float32)
        for d, m, e in zip(docs, metas, embeds):
            sim = util.cos_sim(q_tensor, torch.tensor(e, dtype=torch.float32)).item()
            if sim >= similarity_threshold:
                scored.append((d, m, sim))

        scored = sorted(scored, key=lambda x: x[2], reverse=True)[:top_k]
        docs, metas = [x[0] for x in scored], [x[1] for x in scored]

    context = ""
    for i, (d, m) in enumerate(zip(docs, metas), 1):
        context += (
            f"[Event {i}]\n"
            f"- {m.get('Timestamp', 'N/A')}\n"
            f"- {m.get('Location', 'N/A')}\n"
            f"- {m.get('Severity', 'N/A')} | {m.get('Category', 'N/A')}\n"
            f"- {m.get('Name', 'N/A')}\n\n"
        )

    conv_context = ""
    try:
        for u, a in hist[-6:]:
            conv_context += f"User: {u}\nAssistant: {a}\n\n"
    except Exception:
        conv_context = ""

    today = datetime.now().strftime("%d %B %Y")
    prompt = f"""
Today's date: {today}
Use ONLY the following event data:

{context}

Conversation history:
{conv_context}

Question:
{question}

Answer clearly and reference event numbers.
""".strip()

    system_msg = {
        "role": "system",
        "content": (
            "You are a helpful and friendly assistant. Reply concisely and politely in English. "
            "If the user's input is unclear, random, or not about events, respond in a friendly conversational way "
            "WITHOUT referencing events or sources. Only show events when they are relevant to the user's question. "
            "When asked about events, reference events by their numbers and include short summaries."
        )
    }

    resp = client_llm.chat.completions.create(
        model="qwen/qwen-2.5-72b-instruct",
        messages=[system_msg, {"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=1000
    )

    return resp.choices[0].message.content, metas