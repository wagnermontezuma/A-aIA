from typing import List, Dict, Optional
import os
from pathlib import Path
import json
from datetime import datetime
import hashlib

try:
    # Usar a nova importação para HuggingFaceEmbeddings
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain_community.vectorstores import FAISS
    from langchain_core.documents import Document
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    LANGCHAIN_AVAILABLE = True
except ImportError:
    try:
        # Fallback para a versão antiga se a nova não estiver disponível
        from langchain_community.embeddings import HuggingFaceEmbeddings
        from langchain_community.vectorstores import FAISS
        from langchain_core.documents import Document
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        LANGCHAIN_AVAILABLE = True
    except ImportError:
        LANGCHAIN_AVAILABLE = False
        print("⚠️  LangChain não disponível para RAG. Usando busca simples por texto.")

class SimpleRAGSystem:
    """Sistema RAG simples baseado em busca de texto (fallback)."""

    def __init__(self, storage_path: str = "rag_storage"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        self.documents_file = self.storage_path / "documents.json"
        self.documents = self._load_documents()

    def _load_documents(self) -> List[Dict]:
        """Carrega documentos salvos."""
        if self.documents_file.exists():
            with open(self.documents_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def _save_documents(self):
        """Salva documentos."""
        with open(self.documents_file, 'w', encoding='utf-8') as f:
            json.dump(self.documents, f, ensure_ascii=False, indent=2)

    def add_document(self, content: str, metadata: Dict = None) -> str:
        """Adiciona um documento ao sistema."""
        doc_id = hashlib.md5(content.encode()).hexdigest()

        document = {
            "id": doc_id,
            "content": content,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        }

        # Verificar se já existe
        existing_ids = [doc["id"] for doc in self.documents]
        if doc_id not in existing_ids:
            self.documents.append(document)
            self._save_documents()

        return doc_id

    def search(self, query: str, limit: int = 3) -> List[Dict]:
        """Busca documentos relevantes."""
        query_lower = query.lower()
        scored_docs = []

        for doc in self.documents:
            content_lower = doc["content"].lower()

            # Busca simples por palavras-chave
            score = 0
            for word in query_lower.split():
                if word in content_lower:
                    score += content_lower.count(word)

            # Adicionar pontuação base se a consulta estiver contida no conteúdo
            if query_lower in content_lower:
                 score += 1 # Pontuação base para correspondência exata ou parcial

            if score > 0:
                scored_docs.append((score, doc))

        # Ordenar por relevância e retornar os melhores
        scored_docs.sort(key=lambda x: x[0], reverse=True) # Ordenar pelo score
        return [doc for score, doc in scored_docs[:limit]]

class AdvancedRAGSystem:
    """Sistema RAG avançado usando LangChain e embeddings."""

    def __init__(self, storage_path: str = "rag_storage"):
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("LangChain não está disponível. Use SimpleRAGSystem.")

        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)

        # Usar embeddings locais (gratuitos)
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

        self.vectorstore_path = self.storage_path / "vectorstore"
        self.vectorstore = self._load_or_create_vectorstore()

    def _load_or_create_vectorstore(self):
        """Carrega ou cria o vectorstore."""
        if self.vectorstore_path.exists():
            try:
                return FAISS.load_local(
                    str(self.vectorstore_path),
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
            except Exception as e:
                print(f"Erro ao carregar vectorstore: {e}")
                print("Criando novo vectorstore...")

        # Criar novo vectorstore vazio
        dummy_doc = Document(page_content="Documento inicial", metadata={"type": "dummy"})
        vectorstore = FAISS.from_documents([dummy_doc], self.embeddings)
        return vectorstore

    def add_document(self, content: str, metadata: Dict = None) -> str:
        """Adiciona um documento ao sistema RAG."""
        doc_id = hashlib.md5(content.encode()).hexdigest()

        # Dividir texto em chunks menores
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )

        chunks = text_splitter.split_text(content)

        # Criar documentos
        documents = []
        for i, chunk in enumerate(chunks):
            doc_metadata = {
                "doc_id": doc_id,
                "chunk_id": f"{doc_id}_{i}",
                "timestamp": datetime.now().isoformat(),
                **(metadata or {})
            }
            documents.append(Document(page_content=chunk, metadata=doc_metadata))

        # Adicionar ao vectorstore
        if documents:
            self.vectorstore.add_documents(documents)
            self._save_vectorstore()

        return doc_id

    def search(self, query: str, limit: int = 3) -> List[Dict]:
        """Busca documentos relevantes usando similaridade semântica."""
        try:
            # Buscar documentos similares
            docs = self.vectorstore.similarity_search(query, k=limit)

            results = []
            for doc in docs:
                if doc.metadata.get("type") != "dummy":  # Pular documento dummy
                    results.append({
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "relevance": "high"  # FAISS não retorna score diretamente
                    })

            return results
        except Exception as e:
            print(f"Erro na busca: {e}")
            return []

    def _save_vectorstore(self):
        """Salva o vectorstore."""
        try:
            self.vectorstore.save_local(str(self.vectorstore_path))
        except Exception as e:
            print(f"Erro ao salvar vectorstore: {e}")

class RAGManager:
    """Gerenciador principal do sistema RAG."""

    def __init__(self, use_advanced: bool = True):
        try:
            if use_advanced and LANGCHAIN_AVAILABLE:
                self.rag_system = AdvancedRAGSystem()
                self.system_type = "Advanced"
            else:
                self.rag_system = SimpleRAGSystem()
                self.system_type = "Simple"
        except Exception as e:
            print(f"Erro ao inicializar sistema avançado: {e}")
            self.rag_system = SimpleRAGSystem()
            self.system_type = "Simple (Fallback)"

        print(f"✅ Sistema RAG inicializado: {self.system_type}")

    def add_knowledge(self, content: str, source: str = "manual", metadata: Dict = None) -> str:
        """Adiciona conhecimento ao sistema."""
        full_metadata = {
            "source": source,
            "added_at": datetime.now().isoformat(),
            **(metadata or {})
        }

        doc_id = self.rag_system.add_document(content, full_metadata)
        print(f"📚 Conhecimento adicionado: {doc_id[:8]}...")
        return doc_id

    def get_relevant_context(self, query: str, limit: int = 3) -> str:
        """Busca contexto relevante para uma consulta."""
        relevant_docs = self.rag_system.search(query, limit)

        if not relevant_docs:
            return ""

        context_parts = ["CONHECIMENTO RELEVANTE:"]
        for i, doc in enumerate(relevant_docs, 1):
            content = doc["content"][:200] + "..." if len(doc["content"]) > 200 else doc["content"]
            source = doc.get("metadata", {}).get("source", "desconhecida")
            context_parts.append(f"{i}. Fonte: {source}")
            context_parts.append(f"   Conteúdo: {content}")
            context_parts.append("")

        return "\n".join(context_parts)