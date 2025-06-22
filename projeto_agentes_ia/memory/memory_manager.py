# memory/memory_manager.py - Versão com base de dados separada por conversa
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import os
from pathlib import Path
import hashlib
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod

@dataclass
class ConversationEntry:
    """Representa uma entrada de conversa."""
    timestamp: str
    user_id: str
    session_id: str
    user_message: str
    agent_response: str
    agent_type: str
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'ConversationEntry':
        return cls(**data)

class BaseMemoryService(ABC):
    """Classe base para serviços de memória."""

    @abstractmethod
    def save_conversation(self, entry: ConversationEntry) -> None:
        pass

    @abstractmethod
    def get_conversation_history(self, user_id: str, session_id: str = None, limit: int = 10) -> List[ConversationEntry]:
        pass

    @abstractmethod
    def search_conversations(self, user_id: str, query: str, limit: int = 5) -> List[ConversationEntry]:
        pass

    @abstractmethod
    def clear_conversation(self, user_id: str, session_id: str = None) -> bool:
        pass

class IsolatedFileMemoryService(BaseMemoryService):
    """
    Implementação de memória com arquivos isolados por conversa.
    Cada combinação user_id + session_id tem seu próprio arquivo.
    """

    def __init__(self, storage_path: str = "memory_storage"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)

    def _get_conversation_file(self, user_id: str, session_id: str) -> Path:
        """Retorna o caminho do arquivo específico para uma conversa."""
        # Criar hash único para a combinação user_id + session_id
        conversation_key = f"{user_id}_{session_id}"
        safe_key = hashlib.md5(conversation_key.encode()).hexdigest()
        return self.storage_path / f"conversation_{safe_key}.json"

    def _get_user_directory(self, user_id: str) -> Path:
        """Retorna o diretório específico do usuário."""
        safe_user_id = hashlib.md5(user_id.encode()).hexdigest()
        user_dir = self.storage_path / f"user_{safe_user_id}"
        user_dir.mkdir(exist_ok=True)
        return user_dir

    def save_conversation(self, entry: ConversationEntry) -> None:
        """Salva uma entrada de conversa no arquivo específico da conversa."""
        conversation_file = self._get_conversation_file(entry.user_id, entry.session_id)

        # Carregar histórico existente desta conversa específica
        conversations = []
        if conversation_file.exists():
            try:
                with open(conversation_file, 'r', encoding='utf-8') as f:
                    conversations = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                conversations = []

        # Adicionar nova conversa
        conversations.append(entry.to_dict())

        # Manter apenas as últimas 100 interações por conversa
        if len(conversations) > 100:
            conversations = conversations[-100:]

        # Salvar de volta no arquivo específico
        try:
            with open(conversation_file, 'w', encoding='utf-8') as f:
                json.dump(conversations, f, ensure_ascii=False, indent=2)
            print(f"💾 Conversa salva: {conversation_file.name}")
        except Exception as e:
            print(f"❌ Erro ao salvar conversa: {e}")

    def get_conversation_history(self, user_id: str, session_id: str = None, limit: int = 10) -> List[ConversationEntry]:
        """Recupera o histórico de uma conversa específica."""
        if not session_id:
            return []

        conversation_file = self._get_conversation_file(user_id, session_id)

        if not conversation_file.exists():
            return []

        try:
            with open(conversation_file, 'r', encoding='utf-8') as f:
                conversations = json.load(f)

            # Retornar as mais recentes
            recent_conversations = conversations[-limit:] if conversations else []
            return [ConversationEntry.from_dict(c) for c in recent_conversations]

        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def search_conversations(self, user_id: str, query: str, limit: int = 5) -> List[ConversationEntry]:
        """Busca em todas as conversas do usuário."""
        user_dir = self._get_user_directory(user_id)
        matching_conversations = []
        query_lower = query.lower()

        # Buscar em todos os arquivos de conversa do usuário
        for conversation_file in user_dir.glob("conversation_*.json"):
            try:
                with open(conversation_file, 'r', encoding='utf-8') as f:
                    conversations = json.load(f)

                for conv in conversations:
                    user_msg = conv.get('user_message', '').lower()
                    agent_resp = conv.get('agent_response', '').lower()

                    if query_lower in user_msg or query_lower in agent_resp:
                        matching_conversations.append(ConversationEntry.from_dict(conv))

            except (json.JSONDecodeError, FileNotFoundError):
                continue

        # Retornar as mais recentes que fazem match
        return matching_conversations[-limit:] if matching_conversations else []

    def clear_conversation(self, user_id: str, session_id: str = None) -> bool:
        """Limpa uma conversa específica."""
        if not session_id:
            return False

        conversation_file = self._get_conversation_file(user_id, session_id)

        try:
            if conversation_file.exists():
                conversation_file.unlink()
                print(f"🗑️ Conversa limpa: {conversation_file.name}")
                return True
            return False
        except Exception as e:
            print(f"❌ Erro ao limpar conversa: {e}")
            return False

    def list_user_conversations(self, user_id: str) -> List[Dict]:
        """Lista todas as conversas de um usuário."""
        user_dir = self._get_user_directory(user_id)
        conversations_info = []

        for conversation_file in user_dir.glob("conversation_*.json"):
            try:
                with open(conversation_file, 'r', encoding='utf-8') as f:
                    conversations = json.load(f)

                if conversations:
                    first_msg = conversations[0] # Corrigido para pegar a primeira mensagem
                    last_msg = conversations[-1]

                    conversations_info.append({
                        "file": conversation_file.name,
                        "session_id": first_msg.get('session_id', 'unknown'),
                        "start_time": first_msg.get('timestamp', 'unknown'),
                        "last_time": last_msg.get('timestamp', 'unknown'),
                        "message_count": len(conversations)
                    })

            except (json.JSONDecodeError, FileNotFoundError):
                continue

        return sorted(conversations_info, key=lambda x: x['last_time'], reverse=True)

class MemoryManager:
    """Gerenciador principal de memória com suporte a conversas isoladas."""

    def __init__(self, memory_service: BaseMemoryService = None):
        self.memory_service = memory_service or IsolatedFileMemoryService()

    def save_interaction(self, user_id: str, session_id: str, user_message: str,
                           agent_response: str, agent_type: str, metadata: Dict = None) -> None:
        """Salva uma interação na conversa específica."""
        entry = ConversationEntry(
            timestamp=datetime.now().isoformat(),
            user_id=user_id,
            session_id=session_id,
            user_message=user_message,
            agent_response=agent_response,
            agent_type=agent_type,
            metadata=metadata or {}
        )

        self.memory_service.save_conversation(entry)

    def get_context_for_agent(self, user_id: str, session_id: str = None, limit: int = 5) -> str:
        """Gera contexto de conversa específica para o agente."""
        history = self.memory_service.get_conversation_history(user_id, session_id, limit)

        if not history:
            return "Esta é uma nova conversa."

        context_parts = [f"CONTEXTO DA CONVERSA ATUAL (Sessão: {session_id}):"]
        for i, entry in enumerate(history, 1):
            context_parts.append(f"{i}. Usuário: {entry.user_message}")
            context_parts.append(f"   {entry.agent_type}: {entry.agent_response[:100]}...")
            context_parts.append("")

        return "\n".join(context_parts)

    def search_relevant_context(self, user_id: str, current_query: str, limit: int = 3) -> str:
        """Busca contexto relevante em todas as conversas do usuário."""
        relevant_conversations = self.memory_service.search_conversations(user_id, current_query, limit)

        if not relevant_conversations:
            return ""

        context_parts = ["CONVERSAS RELACIONADAS DE OUTRAS SESSÕES:"]
        for i, entry in enumerate(relevant_conversations, 1):
            context_parts.append(f"{i}. Pergunta similar: {entry.user_message}")
            context_parts.append(f"   Resposta anterior: {entry.agent_response[:150]}...")
            context_parts.append(f"   (Sessão: {entry.session_id})")
            context_parts.append("")

        return "\n".join(context_parts)

    def clear_conversation(self, user_id: str, session_id: str) -> bool:
        """Limpa uma conversa específica."""
        return self.memory_service.clear_conversation(user_id, session_id)

    def list_user_conversations(self, user_id: str) -> List[Dict]:
        """Lista todas as conversas de um usuário."""
        if hasattr(self.memory_service, 'list_user_conversations'):
            return self.memory_service.list_user_conversations(user_id)
        return []


class PostgresMemoryManager:
    """Gerenciador de memória usando PostgreSQL com pgvector."""

    def __init__(self, config: 'PostgresConfig' = None):
        from .postgres_memory_service import PostgresMemoryService, PostgresConfig
        from .postgres_rag_system import PostgresRAGSystem

        self.memory_service = PostgresMemoryService(config)
        self.rag_system = PostgresRAGSystem(config)
        self._initialized = False

    async def initialize(self):
        if not self._initialized:
            await self.memory_service.initialize()
            await self.rag_system.initialize()
            self._initialized = True
            print("✅ PostgresMemoryManager inicializado")

    async def save_interaction(self, user_id: str, session_id: str, user_message: str,
                               agent_response: str, agent_type: str, metadata: Dict = None) -> None:
        if not self._initialized:
            await self.initialize()

        entry = ConversationEntry(
            timestamp=datetime.now().isoformat(),
            user_id=user_id,
            session_id=session_id,
            user_message=user_message,
            agent_response=agent_response,
            agent_type=agent_type,
            metadata=metadata or {}
        )

        await self.memory_service.save_conversation(entry)

    async def get_context_for_agent(self, user_id: str, session_id: str = None, limit: int = 5) -> str:
        if not self._initialized:
            await self.initialize()

        history = await self.memory_service.get_conversation_history(user_id, session_id, limit)

        if not history:
            return "Esta é uma nova conversa."

        context_parts = [f"CONTEXTO DA CONVERSA (PostgreSQL - Sessão: {session_id}):"]
        for i, entry in enumerate(history, 1):
            context_parts.append(f"{i}. Usuário: {entry.user_message}")
            context_parts.append(f"   {entry.agent_type}: {entry.agent_response[:100]}...")
            context_parts.append("")

        return "\n".join(context_parts)

    async def search_relevant_context(self, user_id: str, current_query: str, limit: int = 3) -> str:
        if not self._initialized:
            await self.initialize()

        relevant_conversations = await self.memory_service.search_conversations(user_id, current_query, limit)

        if not relevant_conversations:
            return ""

        context_parts = ["CONVERSAS RELACIONADAS (PostgreSQL):"]
        for i, entry in enumerate(relevant_conversations, 1):
            context_parts.append(f"{i}. Pergunta similar: {entry.user_message}")
            context_parts.append(f"   Resposta anterior: {entry.agent_response[:150]}...")
            context_parts.append(f"   (Sessão: {entry.session_id})")
            context_parts.append("")

        return "\n".join(context_parts)

    async def add_knowledge(self, content: str, source: str = "manual", metadata: Dict = None) -> str:
        if not self._initialized:
            await self.initialize()
        return await self.rag_system.add_document(content, source, metadata)

    async def get_relevant_knowledge(self, query: str, limit: int = 3) -> str:
        if not self._initialized:
            await self.initialize()
        return await self.rag_system.get_relevant_context(query, limit)

    async def clear_conversation(self, user_id: str, session_id: str) -> bool:
        if not self._initialized:
            await self.initialize()
        return await self.memory_service.clear_conversation(user_id, session_id)

    async def list_user_conversations(self, user_id: str) -> List[Dict]:
        if not self._initialized:
            await self.initialize()
        return await self.memory_service.get_user_sessions(user_id)

    async def close(self):
        if self._initialized:
            await self.memory_service.close()
            await self.rag_system.close()
            self._initialized = False
