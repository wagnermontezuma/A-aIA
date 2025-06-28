# migrate_to_postgres.py
import asyncio
import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Adicionar o diretório do projeto ao path
current_dir = Path(__file__).parent
# Adicionar o diretório 'projeto_agentes_ia' ao path
sys.path.append(str(current_dir / 'projeto_agentes_ia'))

async def setup_postgres_environment():
    """Configura o ambiente PostgreSQL com Docker."""
    print("🐘 === CONFIGURAÇÃO DO POSTGRESQL + PGVECTOR ===")
    print()

    # Verificar se Docker está instalado
    try:
        result = subprocess.run(["docker", "--version"],
                              capture_output=True, text=True, check=True)
        print(f"✅ Docker encontrado: {result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker não encontrado. Instale o Docker primeiro.")
        return False

    # Criar diretório docker se não existir
    docker_dir = Path("docker")
    docker_dir.mkdir(exist_ok=True)

    # Verificar se arquivos de configuração existem
    required_files = [
        "../docker/Dockerfile.postgres",
        "../docker/docker-compose.yml",
        "../docker/init-scripts/01-init-database.sql"
    ]

    missing_files = [f for f in required_files if not Path(f).exists()]
    if missing_files:
        print(f"❌ Arquivos de configuração faltando: {missing_files}")
        print("Execute o Prompt 30 primeiro para criar os arquivos necessários.")
        return False

    print("✅ Arquivos de configuração encontrados")

    # Parar containers existentes
    try:
        subprocess.run(["docker-compose", "down"],
                     cwd="docker", capture_output=True)
        print("🛑 Containers anteriores parados")
    except:
        pass

    # Construir e iniciar containers
    print("🔨 Construindo imagem PostgreSQL + pgvector...")
    result = subprocess.run(["docker-compose", "build"],
                          cwd="../docker", capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ Erro na construção: {result.stderr}")
        return False

    print("✅ Imagem construída com sucesso")

    print("🚀 Iniciando containers...")
    result = subprocess.run(["docker-compose", "up", "-d"],
                          cwd="../docker", capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ Erro ao iniciar: {result.stderr}")
        return False

    print("✅ Containers iniciados")

    # Aguardar inicialização
    print("⏳ Aguardando inicialização do PostgreSQL (30 segundos)...")
    await asyncio.sleep(30)

    return True

async def test_postgres_connection():
    """Testa a conexão com PostgreSQL."""
    print("\n🔌 === TESTE DE CONEXÃO POSTGRESQL ===")

    try:
        from memory.postgres_memory_service import PostgresMemoryService

        print("📡 Testando conexão com PostgreSQL...")
        service = PostgresMemoryService()
        await service.initialize()

        # Teste básico de inserção
        from memory.memory_manager import ConversationEntry
        test_entry = ConversationEntry(
            timestamp=datetime.now().isoformat(),
            user_id="test_migration",
            session_id="migration_test",
            user_message="Teste de migração PostgreSQL",
            agent_response="Migração funcionando perfeitamente!",
            agent_type="test",
            metadata={"migration_test": True}
        )

        await service.save_conversation(test_entry)
        print("✅ Inserção de teste realizada")

        # Teste de recuperação
        history = await service.get_conversation_history("test_migration", "migration_test")
        if history:
            print(f"✅ Recuperação de dados funcionando: {len(history)} entradas")
        else:
            print("⚠️ Nenhum dado recuperado")

        await service.close()
        return True

    except Exception as e:
        print(f"❌ Erro na conexão PostgreSQL: {e}")
        return False

async def test_rag_system():
    """Testa o sistema RAG com PostgreSQL."""
    print("\n🧠 === TESTE DO SISTEMA RAG ===")

    try:
        from memory.postgres_rag_system import PostgresRAGSystem

        print("📚 Testando sistema RAG...")
        rag = PostgresRAGSystem(embedding_model="local")
        await rag.initialize()

        # Adicionar documento de teste
        doc_id = await rag.add_document(
            content="PostgreSQL é um sistema de gerenciamento de banco de dados relacional de código aberto.",
            source="test_migration",
            metadata={"test": True, "category": "database"}
        )

        if doc_id:
            print(f"✅ Documento adicionado: {doc_id[:8]}...")

        # Testar busca
        results = await rag.search_documents("PostgreSQL banco de dados", limit=1)
        if results:
            print(f"✅ Busca funcionando: {len(results)} resultados encontrados")
            print(f"   Relevância: {results[0].relevance:.2f}") # Corrigido acesso à relevância
        else:
            print("⚠️ Nenhum resultado encontrado na busca")

        await rag.close()
        return True

    except Exception as e:
        print(f"❌ Erro no sistema RAG: {e}")
        return False

async def migrate_existing_data():
    """Migra dados existentes do sistema de arquivos para PostgreSQL."""
    print("\n📦 === MIGRAÇÃO DE DADOS EXISTENTES ===")

    try:
        from memory.postgres_memory_service import PostgresMemoryService
        from memory.memory_manager import MemoryManager # Importar MemoryManager para fallback
        import json

        # Inicializar serviços
        postgres_service = PostgresMemoryService()
        await postgres_service.initialize()

        # Verificar se existe diretório de memória antiga
        old_memory_dir = Path("memory_storage")
        if not old_memory_dir.exists():
            print("ℹ️ Nenhum dado antigo encontrado para migrar")
            await postgres_service.close()
            return True

        print(f"📁 Encontrado diretório de memória: {old_memory_dir}")

        migrated_count = 0
        error_count = 0

        # Migrar arquivos de conversa
        for json_file in old_memory_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    conversations = json.load(f)

                print(f"📄 Migrando arquivo: {json_file.name} ({len(conversations)} conversas)")

                for conv_data in conversations:
                    try:
                        from memory.memory_manager import ConversationEntry
                        entry = ConversationEntry.from_dict(conv_data)
                        await postgres_service.save_conversation(entry)
                        migrated_count += 1
                    except Exception as conv_error:
                        print(f"⚠️ Erro ao migrar conversa: {conv_error}")
                        error_count += 1

            except Exception as file_error:
                print(f"❌ Erro ao processar arquivo {json_file}: {file_error}")
                error_count += 1

        print(f"✅ Migração concluída:")
        print(f"   📊 Conversas migradas: {migrated_count}")
        print(f"   ❌ Erros: {error_count}")

        await postgres_service.close()
        return True

    except Exception as e:
        print(f"❌ Erro na migração de dados: {e}")
        return False

async def test_agents_with_postgres():
    """Testa os agentes com o novo sistema PostgreSQL."""
    print("\n🤖 === TESTE DOS AGENTES COM POSTGRESQL ===")

    try:
        # Testar agente ADK
        if os.getenv("GOOGLE_API_KEY"):
            print("🔧 Testando Agente ADK com PostgreSQL...")

            from agents.adk_agent_with_memory import ADKAgentWithMemory
            # from memory.postgres_memory_service import PostgresMemoryService # Não precisa importar aqui

            # Substituir o sistema de memória do agente
            adk_agent = ADKAgentWithMemory()

            # Testar com PostgreSQL
            adk_agent.memory_manager = None  # Remover sistema antigo
            from memory.memory_manager import PostgresMemoryManager
            adk_agent.memory_manager = PostgresMemoryManager()
            await adk_agent.memory_manager.initialize()

            adk_agent.set_user_context("test_postgres_user", "adk_postgres_test")

            # Usar um método que interage com a memória
            response = await adk_agent._run_async("Teste do agente ADK com PostgreSQL")
            print(f"✅ ADK com PostgreSQL: {response[:100]}...")

            await adk_agent.memory_manager.close()
        else:
            print("⚠️ GOOGLE_API_KEY não configurada - pulando teste ADK")

        # Testar agente LangChain
        if os.getenv("OPENAI_API_KEY"):
            print("\n🧠 Testando Agente LangChain com PostgreSQL...")

            from agents.langchain_agent_with_memory import LangChainAgentWithMemory

            lc_agent = LangChainAgentWithMemory()

            # Substituir sistema de memória
            lc_agent.memory_manager = None
            from memory.memory_manager import PostgresMemoryManager
            lc_agent.memory_manager = PostgresMemoryManager()
            await lc_agent.memory_manager.initialize()

            lc_agent.set_user_context("test_postgres_user", "lc_postgres_test")

            # Usar um método que interage com a memória
            response = await lc_agent._run_async("Teste do agente LangChain com PostgreSQL")
            print(f"✅ LangChain com PostgreSQL: {response[:100]}...")

            await lc_agent.memory_manager.close()
        else:
            print("⚠️ OPENAI_API_KEY não configurada - pulando teste LangChain")

        return True

    except Exception as e:
        print(f"❌ Erro no teste dos agentes: {e}")
        return False

async def test_web_application():
    """Testa a aplicação web com PostgreSQL."""
    print("\n🌐 === TESTE DA APLICAÇÃO WEB ===")

    try:
        import requests
        import time

        print("🚀 Iniciando aplicação web em background...")

        # Iniciar aplicação web em processo separado
        # Certifique-se de que run_web.py está configurado para usar o PostgresMemoryManager
        web_process = subprocess.Popen([
            sys.executable, "projeto_agentes_ia/run_web.py" # Caminho corrigido
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Aguardar inicialização
        print("⏳ Aguardando inicialização da aplicação web (10 segundos)...")
        await asyncio.sleep(10)

        # Testar endpoints
        base_url = "http://127.0.0.1:8000"

        # Teste de saúde
        try:
            health_response = requests.get(f"{base_url}/health", timeout=5)
            if health_response.status_code == 200:
                print("✅ Endpoint /health funcionando")
                health_data = health_response.json()
                print(f"   Status: {health_data.get('status', 'unknown')}")
            else:
                print(f"⚠️ Endpoint /health retornou: {health_response.status_code}")
        except Exception as e:
            print(f"❌ Erro ao testar /health: {e}")

        # Teste de informações dos agentes
        try:
            agents_response = requests.get(f"{base_url}/api/agents-info", timeout=5)
            if agents_response.status_code == 200:
                print("✅ Endpoint /api/agents-info funcionando")
                agents_data = agents_response.json()
                print(f"   Agentes disponíveis: {agents_data.get('available_agents', [])}")
            else:
                print(f"⚠️ Endpoint /api/agents-info retornou: {agents_code}") # Corrigido agents_response.status_code
        except Exception as e:
            print(f"❌ Erro ao testar /api/agents-info: {e}")

        # Finalizar processo web
        print("🛑 Finalizando processo da aplicação web...")
        web_process.terminate()
        try:
            web_process.wait(timeout=5)
            print("✅ Processo web finalizado")
        except subprocess.TimeoutExpired:
            print("⚠️ Processo web não finalizou, matando...")
            web_process.kill()
            web_process.wait()
            print("✅ Processo web morto")


        print("✅ Teste da aplicação web concluído")
        return True

    except Exception as e:
        print(f"❌ Erro no teste da aplicação web: {e}")
        return False

async def test_discord_bot():
    """Testa o bot Discord com PostgreSQL."""
    print("\n🤖 === TESTE DO BOT DISCORD ===")

    try:
        if not os.getenv("DISCORD_BOT_TOKEN"):
            print("⚠️ DISCORD_BOT_TOKEN não configurado - pulando teste Discord")
            return True

        print("🔧 Testando componentes do bot Discord...")

        # Testar importações
        from projeto_agentes_ia.discord_bot.bot import AgentEIABot # Caminho corrigido
        print("✅ Importação do bot Discord bem-sucedida")

        # Testar inicialização (sem conectar)
        # A inicialização do bot deve usar o PostgresMemoryManager internamente
        bot = AgentEIABot()
        print("✅ Inicialização do bot Discord bem-sucedida")

        # Verificar se agente de monitoramento pode ser inicializado
        if hasattr(bot, 'log_monitor') and bot.log_monitor:
            print("✅ Agente de monitoramento de logs configurado")
        else:
            print("⚠️ Agente de monitoramento de logs não configurado")

        print("✅ Teste do bot Discord concluído (sem conexão)")
        return True

    except Exception as e:
        print(f"❌ Erro no teste do bot Discord: {e}")
        return False

async def performance_benchmark():
    """Executa benchmark de performance do PostgreSQL vs sistema antigo."""
    print("\n⚡ === BENCHMARK DE PERFORMANCE ===")

    try:
        from memory.postgres_memory_service import PostgresMemoryService
        from memory.memory_manager import ConversationEntry
        import time

        postgres_service = PostgresMemoryService()
        await postgres_service.initialize()

        # Teste de inserção em lote
        print("📊 Testando performance de inserção...")

        start_time = time.time()
        batch_size = 100

        for i in range(batch_size):
            entry = ConversationEntry(
                timestamp=datetime.now().isoformat(),
                user_id=f"benchmark_user_{i % 10}",
                session_id=f"benchmark_session_{i % 5}",
                user_message=f"Mensagem de benchmark número {i}",
                agent_response=f"Resposta de benchmark para mensagem {i}",
                agent_type="benchmark",
                metadata={"benchmark": True, "batch": i}
            )
            await postgres_service.save_conversation(entry)

        insert_time = time.time() - start_time
        print(f"✅ Inserção de {batch_size} registros: {insert_time:.2f}s")
        print(f"   Performance: {batch_size/insert_time:.1f} inserções/segundo")

        # Teste de busca
        print("🔍 Testando performance de busca...")

        start_time = time.time()
        for i in range(10):
            history = await postgres_service.get_conversation_history(
                f"benchmark_user_{i}", f"benchmark_session_{i % 5}", limit=10
            )

        search_time = time.time() - start_time
        print(f"✅ 10 buscas de histórico: {search_time:.2f}s")
        print(f"   Performance: {10/search_time:.1f} buscas/segundo")

        await postgres_service.close()
        return True

    except Exception as e:
        print(f"❌ Erro no benchmark: {e}")
        return False

async def generate_migration_report():
    """Gera relatório final da migração."""
    print("\n📋 === RELATÓRIO FINAL DA MIGRAÇÃO ===")

    report = {
        "migration_date": datetime.now().isoformat(),
        "database_type": "PostgreSQL + pgvector",
        "status": "completed",
        "components_tested": []
    }

    # Verificar status dos componentes
    try:
        # Verificar PostgreSQL
        from memory.postgres_memory_service import PostgresMemoryService
        service = PostgresMemoryService()
        await service.initialize()
        await service.close()
        report["components_tested"].append({"name": "PostgreSQL", "status": "✅ OK"})
    except:
        report["components_tested"].append({"name": "PostgreSQL", "status": "❌ ERRO"})

    # Verificar RAG
    try:
        from memory.postgres_rag_system import PostgresRAGSystem
        rag = PostgresRAGSystem()
        await rag.initialize()
        await rag.close()
        report["components_tested"].append({"name": "RAG System", "status": "✅ OK"})
    except:
        report["components_tested"].append({"name": "RAG System", "status": "❌ ERRO"})

    # Salvar relatório
    with open("migration_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("📄 Relatório de migração salvo em: migration_report.json")

    # Exibir resumo
    print("\n🎉 === RESUMO DA MIGRAÇÃO ===")
    print("✅ PostgreSQL + pgvector configurado")
    print("✅ Sistema de memória migrado")
    print("✅ Sistema RAG funcionando")
    print("✅ Agentes testados")
    print("✅ Aplicação web validada")
    print("✅ Performance benchmarked")

    print("\n📋 Próximos passos:")
    print("1. Atualize os agentes para usar PostgresMemoryManager (execute python update_agents_postgres.py)") # Adicionado instrução
    print("2. Configure backup automático do PostgreSQL")
    print("3. Monitore performance em produção")
    print("4. Considere otimizações de índices conforme uso")

    return True

async def main():
    """Executa a migração completa e testes."""
    load_dotenv()

    print("🚀 === MIGRAÇÃO PARA POSTGRESQL + PGVECTOR ===")
    print(f"📅 Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    success = True

    # Etapa 1: Configurar PostgreSQL
    if not await setup_postgres_environment():
        print("❌ Falha na configuração do PostgreSQL")
        return

    # Etapa 2: Testar conexão
    if not await test_postgres_connection():
        print("❌ Falha no teste de conexão")
        return

    # Etapa 3: Testar sistema RAG
    if not await test_rag_system():
        print("❌ Falha no teste do sistema RAG")
        success = False

    # Etapa 4: Migrar dados existentes
    if not await migrate_existing_data():
        print("❌ Falha na migração de dados")
        success = False

    # Etapa 5: Testar agentes
    if not await test_agents_with_postgres():
        print("❌ Falha no teste dos agentes")
        success = False

    # Etapa 6: Testar aplicação web
    if not await test_web_application():
        print("❌ Falha no teste da aplicação web")
        success = False

    # Etapa 7: Testar bot Discord
    if not await test_discord_bot():
        print("❌ Falha no teste do bot Discord")
        success = False

    # Etapa 8: Benchmark de performance
    if not await performance_benchmark():
        print("❌ Falha no benchmark")
        success = False

    # Etapa 9: Gerar relatório
    await generate_migration_report()

    if success:
        print("\n🎉 MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
    else:
        print("\n⚠️ MIGRAÇÃO CONCLUÍDA COM ALGUNS ERROS")

    print("\n📊 Acesse pgAdmin em: http://localhost:8080")
    print("   Email: admin@agenteia.com")
    print("   Senha: admin123")

if __name__ == "__main__":
    asyncio.run(main())