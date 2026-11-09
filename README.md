# CV RAG

This project builds a retrieval system for CVs stored in Google Drive, with parsing, metadata extraction, chunking, embeddings, and end-to-end evaluation.

## Structure

- `cvrag/`: domain logic and pipeline
- `app/`: Streamlit UI
- `sql/`: database schema
- `evaluation/`: benchmarking data
- `secrets/`: local secrets, not committed
- `scripts/`: operational scripts

## Setup

1. Copy `.env.example` to `.env` and fill in your values.
2. Start PostgreSQL with Docker Compose.
3. Install Python dependencies from `requirements.txt`.
4. Run the ingestion and evaluation flows you add under `cvrag/`.
