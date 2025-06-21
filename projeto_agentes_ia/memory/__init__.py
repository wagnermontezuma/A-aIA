"""
Sistema de memória conversacional e RAG para agentes de IA.
Implementação seguindo as melhores práticas de desenvolvimento assistido por IA.
"""

from .memory_manager import MemoryManager, ConversationEntry
from .rag_system import RAGManager, SimpleRAGSystem

__all__ = [
    'MemoryManager',
    'ConversationEntry',
    'RAGManager',
    'SimpleRAGSystem'
]