# run_log_monitor.py
import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Adicionar o diretório do projeto ao path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

async def main():
    """Executa o agente de monitoramento de logs."""
    load_dotenv()

    print("🔍 Iniciando Sistema de Monitoramento de Logs")
    print("=" * 50)

    # Verificar configurações
    discord_webhook = os.getenv("DISCORD_WEBHOOK_URL")
    google_api_key = os.getenv("GOOGLE_API_KEY")

    if not google_api_key:
        print("❌ GOOGLE_API_KEY não encontrada no .env")
        return

    if not discord_webhook:
        print("⚠️ DISCORD_WEBHOOK_URL não configurada - alertas não serão enviados")

    try:
        from agents.log_monitor_agent import LogMonitorAgent

        # Criar agente (verificação a cada 5 minutos)
        monitor = LogMonitorAgent(
            discord_webhook_url=discord_webhook,
            check_interval=300
        )

        print("🤖 Agente de monitoramento criado com sucesso!")
        print("📋 Comandos disponíveis:")
        print("  - Digite 'start' para iniciar monitoramento automático")
        print("  - Digite 'check' para verificar logs de hoje")
        print("  - Digite 'status' para ver status do sistema")
        print("  - Digite 'quit' para sair")
        print()

        # Loop interativo
        while True:
            try:
                command = input("🔧 Digite um comando: ").strip().lower()

                if command == 'quit':
                    monitor.stop_monitoring()
                    print("👋 Encerrando sistema...")
                    break

                elif command == 'start':
                    if not monitor.is_monitoring:
                        print("🚀 Iniciando monitoramento automático...")
                        asyncio.create_task(monitor.start_monitoring())
                    else:
                        print("⚠️ Monitoramento já está ativo")

                elif command == 'stop':
                    monitor.stop_monitoring()
                    print("🛑 Monitoramento interrompido")

                elif command == 'check':
                    print("🔍 Verificando logs de hoje...")
                    response = await monitor._run_async("verificar hoje")
                    print(response)

                elif command == 'status':
                    response = await monitor._run_async("status")
                    print(response)

                elif command.startswith('check '):
                    date = command.replace('check ', '').strip()
                    response = await monitor._run_async(f"verificar data {date}")
                    print(response)

                else:
                    print("❌ Comando não reconhecido. Use: start, stop, check, status, quit")

            except KeyboardInterrupt:
                monitor.stop_monitoring()
                print("\n👋 Encerrando sistema...")
                break
            except Exception as e:
                print(f"❌ Erro: {e}")

    except Exception as e:
        print(f"❌ Erro ao inicializar sistema: {e}")

if __name__ == "__main__":
    asyncio.run(main())