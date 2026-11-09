CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
    id                 BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    drive_file_id      TEXT NOT NULL UNIQUE,
    title              TEXT NOT NULL,
    source_uri         TEXT,
    mime_type          TEXT NOT NULL,
    content_hash       TEXT,
    drive_modified_at  TIMESTAMPTZ,

    status             TEXT NOT NULL DEFAULT 'pending'
                       CHECK (status IN ('pending', 'processing', 'ready', 'failed', 'unsupported')),
    error_message      TEXT,

    metadata           JSONB NOT NULL DEFAULT '{}',

    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS parsed_texts (
    id             BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    document_id    BIGINT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    parser         TEXT NOT NULL CHECK (parser IN ('pymupdf', 'llamaparse')),
    text           TEXT NOT NULL,
    page_count     INT,
    parse_seconds  REAL,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE (document_id, parser)
);

CREATE TABLE IF NOT EXISTS chunks (
    id             BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    document_id    BIGINT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    parser         TEXT NOT NULL CHECK (parser IN ('pymupdf', 'llamaparse')),
    strategy       TEXT NOT NULL CHECK (strategy IN ('recursive', 'sections', 'whole', 'parent_child')),
    chunk_index    INT NOT NULL,
    parent_id      BIGINT REFERENCES chunks(id) ON DELETE CASCADE,

    content        TEXT NOT NULL,
    metadata       JSONB NOT NULL DEFAULT '{}',
    token_count    INT,

    content_tsv    TSVECTOR GENERATED ALWAYS AS (to_tsvector('english', content)) STORED,
    embedding      VECTOR(1536),

    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE (document_id, parser, strategy, chunk_index)
);
CREATE INDEX IF NOT EXISTS chunks_embedding_idx
    ON chunks USING hnsw (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS chunks_content_tsv_idx
    ON chunks USING gin (content_tsv);

CREATE TABLE IF NOT EXISTS conversations (
    id                   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title                TEXT,
    summary              TEXT,
    summary_upto_message BIGINT,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS messages (
    id                BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    conversation_id   BIGINT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role              TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content           TEXT NOT NULL,
    standalone_query  TEXT,
    metadata          JSONB NOT NULL DEFAULT '{}',
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS message_results (
    message_id   BIGINT NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    rank         INT NOT NULL,
    document_id  BIGINT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    score        REAL,
    reason       TEXT,
    PRIMARY KEY (message_id, rank)
);