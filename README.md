# RAG System Prototype

## Overview

This is a full-stack Retrieval-Augmented Generation (RAG) system.
It allows ingestion of raw datasets and provides a user-facing chat interface for querying the data.

* **Ingestion Pipeline:** Reads CSV/SQLite from `./data`, cleans text, generates embeddings, and stores them in ChromaDB (`./chroma_db`).
  **Note:** To ingest data, run `ingestion_pipeline\main.py`.
* **Chat UI:** A Gradio interface that retrieves relevant context from ChromaDB and generates natural language answers using an LLM.

---

## How to Run the System

1. Make sure Docker and Docker Compose are installed (optional: you can also run locally with a Python venv).
2. Clone this repository.
3. Copy `.env.example` to `.env` and fill in API keys and paths.

Run with Docker Compose (recommended):

```bash
docker-compose up --build
```

Access the services:

* **Chat UI (Gradio):** [http://127.0.0.1:7860](http://127.0.0.1:7860)

Or run locally without Docker:

```powershell
# Windows PowerShell (from repository root)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# Re-ingest data
python ingestion_pipeline\main.py
# Run the Gradio app
python app.py
```

---

## Engineering Decisions

### 1. Chunking Strategy

* Large text is split into ~500 token chunks with some overlap (~50 tokens).
* **Reason:** Ensures that the vector retrieval captures enough context for each chunk without losing continuity between segments, improving answer relevance.

### 2. Embedding Model

* Using `sentence-transformers/all-MiniLM-L6-v2`.
* **Reason:** Lightweight, fast, and produces high-quality embeddings suitable for semantic search on moderate-sized datasets.

### 3. LLM Approach

* By default, the system uses OpenRouter as the LLM gateway, with the model qwen/qwen-2.5-72b-instruct configured as the primary model.
* **Reason:** This allows flexible access to multiple high-quality models without vendor lock-in, while keeping latency and cost efficient.
* **Optional:** You can switch to OpenAI models or any other provider supported by OpenRouter by updating the environment variables or the setup.py configuration.

---

## Notes

* Data is stored persistently in `./chroma_db`.
* Raw datasets should be placed in the `./data` folder.
* The system is containerized for easy deployment; simply running `docker-compose up --build` starts everything.
* **Remember:** To ingest or re-ingest data, run `python ingestion_pipeline\main.py`.
