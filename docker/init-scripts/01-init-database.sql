-- docker/init-scripts/01-init-database.sql
-- Habilitar extensao pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Criar schema para organizacao
CREATE SCHEMA IF NOT EXISTS agenteia;

-- Tabela para conversas
CREATE TABLE IF NOT EXISTS agenteia.conversations (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255) NOT NULL,
    agent_type VARCHAR(50) NOT NULL,
    user_message TEXT NOT NULL,
    agent_response TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}',
    CONSTRAINT conversations_user_session_idx UNIQUE (user_id, session_id, timestamp)
);

-- Tabela para documentos RAG
CREATE TABLE IF NOT EXISTS agenteia.documents (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    source VARCHAR(255) NOT NULL DEFAULT 'manual',
    metadata JSONB DEFAULT '{}',
    embedding vector(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabela para chunks de documentos
CREATE TABLE IF NOT EXISTS agenteia.document_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES agenteia.documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_document_chunk UNIQUE (document_id, chunk_index)
);

-- Tabela para sessoes de usuario
CREATE TABLE IF NOT EXISTS agenteia.user_sessions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255) NOT NULL,
    agent_type VARCHAR(50),
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}',
    CONSTRAINT unique_user_session UNIQUE (user_id, session_id)
);

-- Indices
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON agenteia.conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_session_id ON agenteia.conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_conversations_timestamp ON agenteia.conversations(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_conversations_agent_type ON agenteia.conversations(agent_type);

CREATE INDEX IF NOT EXISTS idx_documents_embedding ON agenteia.documents USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON agenteia.document_chunks USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_documents_source ON agenteia.documents(source);
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON agenteia.documents(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON agenteia.user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_last_activity ON agenteia.user_sessions(last_activity DESC);

-- Funcao para atualizar timestamp
CREATE OR REPLACE FUNCTION agenteia.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger para atualizar updated_at
CREATE TRIGGER update_documents_updated_at 
    BEFORE UPDATE ON agenteia.documents 
    FOR EACH ROW EXECUTE FUNCTION agenteia.update_updated_at_column();

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'agenteia_app') THEN
        CREATE ROLE agenteia_app WITH LOGIN PASSWORD 'app_password_2025';
    END IF;
END
$$;

GRANT USAGE ON SCHEMA agenteia TO agenteia_app;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA agenteia TO agenteia_app;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA agenteia TO agenteia_app;

INSERT INTO agenteia.conversations (user_id, session_id, agent_type, user_message, agent_response, metadata)
VALUES 
    ('demo_user', 'demo_session', 'adk', 'Olá!', 'Olá! Como posso ajudar você hoje?', '{"demo": true}'),
    ('demo_user', 'demo_session', 'adk', 'Como você está?', 'Estou funcionando perfeitamente! Obrigado por perguntar.', '{"demo": true}');

SET ivfflat.probes = 10;
