# update_agents_postgres.py
import os
import sys
from pathlib import Path
import asyncio # Importar asyncio para create_task

def update_agent_files():
    """Atualiza os arquivos dos agentes para usar PostgreSQL."""
    print("🔄 === ATUALIZANDO AGENTES PARA POSTGRESQL ===")

    # Mapeamento de arquivos para atualizar
    updates = {
        "projeto_agentes_ia/agents/adk_agent_with_memory.py": { # Caminho corrigido
            "old": "self.memory_manager = MemoryManager()",
            "new": """# Usar PostgreSQL como padrão
        try:
            from memory.memory_manager import PostgresMemoryManager
            self.memory_manager = PostgresMemoryManager()
            asyncio.create_task(self.memory_manager.initialize())
        except ImportError:
            # Fallback para sistema de arquivos
            from memory.memory_manager import MemoryManager # Importar MemoryManager para fallback
            self.memory_manager = MemoryManager()"""
        },
        "projeto_agentes_ia/agents/langchain_agent_with_memory.py": { # Caminho corrigido
            "old": "self.memory_manager = MemoryManager()",
            "new": """# Usar PostgreSQL como padrão
        try:
            from memory.memory_manager import PostgresMemoryManager
            self.memory_manager = PostgresMemoryManager()
            asyncio.create_task(self.memory_manager.initialize())
        except ImportError:
            # Fallback para sistema de arquivos
            from memory.memory_manager import MemoryManager # Importar MemoryManager para fallback
            self.memory_manager = MemoryManager()"""
        }
    }

    for file_path, update_info in updates.items():
        if Path(file_path).exists():
            print(f"📝 Atualizando {file_path}...")

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if update_info["old"] in content:
                content = content.replace(update_info["old"], update_info["new"])

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)

                print(f"✅ {file_path} atualizado")
            else:
                print(f"⚠️ {file_path} já atualizado ou padrão não encontrado")
        else:
            print(f"❌ {file_path} não encontrado")

    print("✅ Atualização dos agentes concluída")

if __name__ == "__main__":
    update_agent_files()