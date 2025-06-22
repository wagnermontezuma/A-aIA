# memory/postgres_memory_service.py
import asyncio
import asyncpg
import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

from .memory_manager import ConversationEntry, BaseMemoryService

@dataclass
class PostgresConfig:
    """Configuração para conexão PostgreSQL."""
    host: str = "localhost"
    port: int = 5432
    database: str = "agenteia_db"
    user: str = "agenteia_user"
    password: str = "agenteia_password_2025"
    schema: str = "agenteia"
    max_connections: int = 10

class PostgresMemoryService(BaseMemoryService):
    """Memória usando PostgreSQL com pgvector."""

    def __init__(self, config: PostgresConfig = None):
        load_dotenv()
        self.config = config or PostgresConfig(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            database=os.getenv("POSTGRES_DB", "agenteia_db"),
            user=os.getenv("POSTGRES_USER", "agenteia_user"),
            password=os.getenv("POSTGRES_PASSWORD", "agenteia_password_2025"),
            schema=os.getenv("POSTGRES_SCHEMA", "agenteia")
        )
        self.pool: Optional[asyncpg.Pool] = None
        self._initialized = False

    async def initialize(self):
        """Inicializa o pool de conexões."""
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
                max_size=self.config.max_connections,
                command_timeout=60
            )
            async with self.pool.acquire() as conn:
                await conn.execute("SELECT 1")
            self._initialized = True
            print(f"✅ PostgreSQL pool inicializado: {self.config.host}:{self.config.port}")
        except Exception as e:
            print(f"❌ Erro ao conectar PostgreSQL: {e}")
            raise

    async def close(self):
        if self.pool:
            await self.pool.close()
            self._initialized = False

    async def save_conversation(self, entry: ConversationEntry) -> None:
        if not self._initialized:
            await self.initialize()
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO agenteia.conversations 
                    (user_id, session_id, agent_type, user_message, agent_response, metadata, timestamp)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """,
                    entry.user_id,
                    entry.session_id,
                    entry.agent_type,
                    entry.user_message,
                    entry.agent_response,
                    json.dumps(entry.metadata or {}),
                    datetime.fromisoformat(entry.timestamp)
                )
            print(f"💾 Conversa salva no PostgreSQL: {entry.user_id}/{entry.session_id}")
        except Exception as e:
            print(f"❌ Erro ao salvar conversa: {e}")
            raise

    async def get_conversation_history(self, user_id: str, session_id: str = None, limit: int = 10) -> List[ConversationEntry]:
        if not self._initialized:
            await self.initialize()
        try:
            async with self.pool.acquire() as conn:
                if session_id:
                    rows = await conn.fetch(
                        """
                        SELECT user_id, session_id, agent_type, user_message, agent_response, metadata, timestamp
                        FROM agenteia.conversations
                        WHERE user_id = $1 AND session_id = $2
                        ORDER BY timestamp DESC
                        LIMIT $3
                        """,
                        user_id, session_id, limit
                    )
                else:
                    rows = await conn.fetch(
                        """
                        SELECT user_id, session_id, agent_type, user_message, agent_response, metadata, timestamp
                        FROM agenteia.conversations
                        WHERE user_id = $1
                        ORDER BY timestamp DESC
                        LIMIT $2
                        """,
                        user_id, limit
                    )
            conversations = []
            for row in reversed(rows):
                conversations.append(
                    ConversationEntry(
                        timestamp=row['timestamp'].isoformat(),
                        user_id=row['user_id'],
                        session_id=row['session_id'],
                        user_message=row['user_message'],
                        agent_response=row['agent_response'],
                        agent_type=row['agent_type'],
                        metadata=json.loads(row['metadata']) if row['metadata'] else {}
                    )
                )
            return conversations
        except Exception as e:
            print(f"❌ Erro ao buscar historico: {e}")
            return []

    async def search_conversations(self, user_id: str, query: str, limit: int = 5) -> List[ConversationEntry]:
        if not self._initialized:
            await self.initialize()
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT user_id, session_id, agent_type, user_message, agent_response, metadata, timestamp,
                           ts_rank(to_tsvector('portuguese', user_message || ' ' || agent_response),
                                   plainto_tsquery('portuguese', $2)) as rank
                    FROM agenteia.conversations
                    WHERE user_id = $1
                      AND (to_tsvector('portuguese', user_message || ' ' || agent_response) @@ plainto_tsquery('portuguese', $2))
                    ORDER BY rank DESC, timestamp DESC
                    LIMIT $3
                    """,
                    user_id, query, limit
                )
            conversations = []
            for row in rows:
                conversations.append(
                    ConversationEntry(
                        timestamp=row['timestamp'].isoformat(),
                        user_id=row['user_id'],
                        session_id=row['session_id'],
                        user_message=row['user_message'],
                        agent_response=row['agent_response'],
                        agent_type=row['agent_type'],
                        metadata=json.loads(row['metadata']) if row['metadata'] else {}
                    )
                )
            return conversations
        except Exception as e:
            print(f"❌ Erro na busca: {e}")
            return []

    async def clear_conversation(self, user_id: str, session_id: str = None) -> bool:
        if not self._initialized:
            await self.initialize()
        try:
            async with self.pool.acquire() as conn:
                if session_id:
                    result = await conn.execute(
                        "DELETE FROM agenteia.conversations WHERE user_id = $1 AND session_id = $2",
                        user_id, session_id
                    )
                else:
                    result = await conn.execute(
                        "DELETE FROM agenteia.conversations WHERE user_id = $1",
                        user_id
                    )
            deleted_count = int(result.split()[-1])
            print(f"🗑️ {deleted_count} conversas removidas")
            return deleted_count > 0
        except Exception as e:
            print(f"❌ Erro ao limpar conversas: {e}")
            return False

    async def get_user_sessions(self, user_id: str) -> List[Dict]:
        if not self._initialized:
            await self.initialize()
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT session_id, agent_type, MIN(timestamp) as start_time, MAX(timestamp) as last_time, COUNT(*) as message_count
                    FROM agenteia.conversations
                    WHERE user_id = $1
                    GROUP BY session_id, agent_type
                    ORDER BY MAX(timestamp) DESC
                    """,
                    user_id
                )
            sessions = []
            for row in rows:
                sessions.append({
                    'session_id': row['session_id'],
                    'agent_type': row['agent_type'],
                    'start_time': row['start_time'].isoformat(),
                    'last_time': row['last_time'].isoformat(),
                    'message_count': row['message_count']
                })
            return sessions
        except Exception as e:
            print(f"❌ Erro ao listar sessões: {e}")
            return []
