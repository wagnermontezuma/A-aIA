# memory/postgres_rag_system.py
import asyncio
import asyncpg
import json
import os
import hashlib
from typing import List, Dict, Optional
from datetime import datetime
from dotenv import load_dotenv

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from .postgres_memory_service import PostgresConfig

class PostgresRAGSystem:
    """Sistema RAG usando PostgreSQL com pgvector."""

    def __init__(self, config: PostgresConfig = None, embedding_model: str = "local"):
        load_dotenv()
        self.config = config or PostgresConfig(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            database=os.getenv("POSTGRES_DB", "agenteia_db"),
            user=os.getenv("POSTGRES_USER", "agenteia_user"),
            password=os.getenv("POSTGRES_PASSWORD", "agenteia_password_2025")
        )
        self.pool: Optional[asyncpg.Pool] = None
        self._initialized = False
        self.embedding_model = embedding_model
        self.encoder = None
        if embedding_model == "local" and SENTENCE_TRANSFORMERS_AVAILABLE:
            self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
            self.embedding_dim = 384
        elif embedding_model == "openai" and OPENAI_AVAILABLE:
            openai.api_key = os.getenv("OPENAI_API_KEY")
            self.embedding_dim = 1536
        else:
            print("⚠️ Nenhum modelo de embedding disponível, usando busca textual")
            self.embedding_dim = None

    async def initialize(self):
        if self._initialized:
            return
        try:
            self.pool = await asyncpg.create_pool(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.user,
                password=self.config.password,
                min_size=2,
                max_size=10
            )
            self._initialized = True
            print(f"✅ PostgreSQL RAG inicializado: {self.embedding_model}")
        except Exception as e:
            print(f"❌ Erro ao conectar PostgreSQL RAG: {e}")
            raise

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        if not text.strip():
            return None
        try:
            if self.embedding_model == "local" and self.encoder:
                embedding = self.encoder.encode(text)
                return embedding.tolist()
            elif self.embedding_model == "openai" and OPENAI_AVAILABLE:
                response = openai.Embedding.create(input=text, model="text-embedding-ada-002")
                return response['data'][0]['embedding']
            return None
        except Exception as e:
            print(f"❌ Erro ao gerar embedding: {e}")
            return None

    async def add_document(self, content: str, source: str = "manual", metadata: Dict = None) -> str:
        if not self._initialized:
            await self.initialize()
        try:
            embedding = self.generate_embedding(content)
            doc_id = hashlib.md5(content.encode()).hexdigest()
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO agenteia.documents (content, source, metadata, embedding)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT DO NOTHING
                    """,
                    content,
                    source,
                    json.dumps(metadata or {}),
                    embedding
                )
            print(f"📚 Documento adicionado: {doc_id[:8]}...")
            return doc_id
        except Exception as e:
            print(f"❌ Erro ao adicionar documento: {e}")
            return ""

    async def search_documents(self, query: str, limit: int = 5) -> List[Dict]:
        if not self._initialized:
            await self.initialize()
        try:
            async with self.pool.acquire() as conn:
                if self.embedding_dim:
                    query_embedding = self.generate_embedding(query)
                    if query_embedding:
                        rows = await conn.fetch(
                            """
                            SELECT content, source, metadata, embedding <#> $1 as distance
                            FROM agenteia.documents
                            WHERE embedding IS NOT NULL
                            ORDER BY embedding <#> $1
                            LIMIT $2
                            """,
                            query_embedding, limit
                        )
                    else:
                        rows = []
                else:
                    rows = await conn.fetch(
                        """
                        SELECT content, source, metadata,
                               ts_rank(to_tsvector('portuguese', content), plainto_tsquery('portuguese', $1)) as rank
                        FROM agenteia.documents
                        WHERE to_tsvector('portuguese', content) @@ plainto_tsquery('portuguese', $1)
                        ORDER BY rank DESC
                        LIMIT $2
                        """,
                        query, limit
                    )
            results = []
            for row in rows:
                relevance = 1.0 - row.get('distance', 0.5) if 'distance' in row else row.get('rank', 0.5)
                results.append({
                    'content': row['content'],
                    'source': row['source'],
                    'metadata': json.loads(row['metadata']) if row['metadata'] else {},
                    'relevance': relevance
                })
            return results
        except Exception as e:
            print(f"❌ Erro na busca de documentos: {e}")
            return []

    async def get_relevant_context(self, query: str, limit: int = 3) -> str:
        documents = await self.search_documents(query, limit)
        if not documents:
            return ""
        context_parts = ["CONHECIMENTO RELEVANTE (PostgreSQL):"]
        for i, doc in enumerate(documents, 1):
            content = doc['content'][:300] + "..." if len(doc['content']) > 300 else doc['content']
            context_parts.append(f"{i}. Fonte: {doc['source']} (Relevância: {doc['relevance']:.2f})")
            context_parts.append(f"   Conteúdo: {content}")
            context_parts.append("")
        return "\n".join(context_parts)

    async def close(self):
        if self.pool:
            await self.pool.close()
            self._initialized = False
