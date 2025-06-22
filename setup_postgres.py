import asyncio
import os
import subprocess
from pathlib import Path

async def setup_postgres():
    """Script para configurar PostgreSQL com pgvector."""
    print("\U0001F417 Configurando PostgreSQL + pgvector com Docker")
    print("=" * 50)

    try:
        subprocess.run(["docker", "--version"], check=True, capture_output=True)
        print("✅ Docker encontrado")
    except subprocess.CalledProcessError:
        print("❌ Docker não encontrado. Instale o Docker primeiro.")
        return

    docker_dir = Path("docker")
    if not docker_dir.exists():
        docker_dir.mkdir()
        print("📁 Diretório docker/ criado")

    os.chdir(docker_dir)

    required_files = ["Dockerfile.postgres", "docker-compose.yml", "init-scripts/01-init-database.sql"]
    missing = [f for f in required_files if not Path(f).exists()]
    if missing:
        print(f"❌ Arquivos faltando: {missing}")
        print("Execute o prompt 30 para criar os arquivos necessários.")
        return

    print("📋 Arquivos de configuração encontrados")

    try:
        subprocess.run(["docker-compose", "down"], check=False, capture_output=True)
        print("🛑 Containers anteriores parados")
    except Exception:
        pass

    print("🔨 Construindo imagem PostgreSQL + pgvector...")
    result = subprocess.run(["docker-compose", "build"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Erro na construção: {result.stderr}")
        return
    print("✅ Imagem construída com sucesso")

    print("🚀 Iniciando containers...")
    result = subprocess.run(["docker-compose", "up", "-d"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Erro ao iniciar: {result.stderr}")
        return
    print("✅ Containers iniciados")

    print("⏳ Aguardando inicialização do PostgreSQL...")
    await asyncio.sleep(10)

    try:
        from projeto_agentes_ia.memory.postgres_memory_service import PostgresMemoryService
        service = PostgresMemoryService()
        await service.initialize()
        print("✅ Conexão PostgreSQL testada com sucesso")
        await service.close()
    except Exception as e:
        print(f"⚠️ Erro ao testar conexão: {e}")
        print("Verifique se o container está rodando: docker-compose ps")

    print("\n🎉 PostgreSQL + pgvector configurado!")
    print("📋 Próximos passos:")
    print("1. Instale dependências: pip install -r requirements.txt")
    print("2. Teste a migração: python test_postgres_migration.py")
    print("3. Acesse pgAdmin: http://localhost:8080 (admin@agenteia.com / admin123)")

if __name__ == "__main__":
    asyncio.run(setup_postgres())
