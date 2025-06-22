"""
Sistema de memória conversacional e RAG para agentes de IA.
Implementação seguindo as melhores práticas de desenvolvimento assistido por IA.
"""

from .memory_manager import MemoryManager, ConversationEntry, PostgresMemoryManager
from .rag_system import RAGManager, SimpleRAGSystem
from .postgres_memory_service import PostgresMemoryService, PostgresConfig
from .postgres_rag_system import PostgresRAGSystem

__all__ = [
    'MemoryManager',
    'ConversationEntry',
    'RAGManager',
    'SimpleRAGSystem',
    'PostgresMemoryService',
    'PostgresRAGSystem',
    'PostgresMemoryManager',
    'PostgresConfig'
]