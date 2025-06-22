# agents/log_monitor_agent.py
from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.adk.tools import google_search
from google.genai import types
from .base_agent import BaseAgent
import asyncio
import aiohttp
import os
import sys
import re
import json
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import List, Dict, Optional
import hashlib

# Adicionar o diretório de memória ao path
memory_path = Path(__file__).parent.parent / "memory"
sys.path.append(str(memory_path))

from memory_manager import MemoryManager
from rag_system import RAGManager

class LogMonitorAgent(BaseAgent):
    """
    Agente especializado em monitoramento de logs com integração Discord.
    Monitora logs em tempo real e envia alertas quando detecta erros.
    """

    def __init__(self, discord_webhook_url: str = None, check_interval: int = 300):
        load_dotenv()

        try:
            # Configurações do agente
            self.base_url = "https://backend.casasorveteiro.com.br/log-viewer/logs"
            self.discord_webhook_url = discord_webhook_url or os.getenv("DISCORD_WEBHOOK_URL")
            self.check_interval = check_interval  # Intervalo em segundos (padrão: 5 minutos)

            # Inicializar sistemas de memória
            self.memory_manager = MemoryManager()
            self.rag_manager = RAGManager(use_advanced=False)

            # Controle de estado
            self.last_check_time = {}  # Por data
            self.known_errors = set()  # Cache de erros já reportados
            self.is_monitoring = False

            # Padrões de erro para detectar
            self.error_patterns = [
                r'ERROR',
                r'CRITICAL',
                r'FATAL',
                r'Exception',
                r'Traceback',
                r'500\s+Internal\s+Server\s+Error',
                r'404\s+Not\s+Found',
                r'Connection\s+refused',
                r'Timeout',
                r'Failed\s+to\s+connect',
                r'Database\s+error',
                r'SQL\s+Error'
            ]

            # Instrução especializada para análise de logs
            instruction = """
            Você é um especialista em análise de logs de aplicações web e monitoramento de sistemas.

            SUAS RESPONSABILIDADES:
            1. Analisar logs de aplicações em busca de erros, exceções e problemas críticos
            2. Identificar padrões de erro e classificar sua severidade
            3. Gerar alertas claros e informativos para a equipe de desenvolvimento
            4. Sugerir possíveis causas e soluções para os problemas encontrados

            CRITÉRIOS DE ANÁLISE:
            - CRÍTICO: Erros que podem afetar a disponibilidade do sistema
            - ALTO: Exceções não tratadas, erros de banco de dados
            - MÉDIO: Warnings importantes, timeouts ocasionais
            - BAIXO: Informações de debug, avisos menores

            FORMATO DE RESPOSTA:
            - Seja claro e objetivo
            - Inclua timestamp e contexto do erro
            - Sugira ações corretivas quando possível
            - Use emojis para facilitar a identificação visual
            """

            # Criar o agente ADK
            self.agent = Agent(
                name="log_monitor_agent",
                model="gemini-2.0-flash-exp",
                description="Agente especializado em monitoramento de logs e alertas Discord",
                instruction=instruction,
                tools=[google_search]
            )

            # Configurações da aplicação
            self.app_name = "log_monitor_system"
            self.user_id = "log_monitor"

            # Inicializar serviços
            self.session_service = InMemorySessionService()
            self.runner = Runner(
                agent=self.agent,
                app_name=self.app_name,
                session_service=self.session_service
            )

            super().__init__(name="LogMonitorAgent")
            print(f"✅ {self.name} inicializado com sucesso")
            print(f"🔗 URL base: {self.base_url}")
            print(f"⏱️ Intervalo de verificação: {self.check_interval}s")

        except Exception as e:
            print(f"❌ Erro ao inicializar {self.name}: {e}")
            raise

    async def fetch_logs(self, date: str) -> Optional[str]:
        """Busca os logs de uma data específica."""
        url = f"{self.base_url}/{date}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as response:
                    if response.status == 200:
                        content = await response.text()
                        print(f"📥 Logs obtidos para {date}: {len(content)} caracteres")
                        return content
                    else:
                        print(f"⚠️ Erro HTTP {response.status} ao acessar logs de {date}")
                        return None

        except asyncio.TimeoutError:
            print(f"⏰ Timeout ao acessar logs de {date}")
            return None
        except Exception as e:
            print(f"❌ Erro ao buscar logs de {date}: {e}")
            return None

    def extract_errors(self, log_content: str) -> List[Dict]:
        """Extrai erros do conteúdo dos logs usando padrões regex."""
        errors = []
        lines = log_content.split('\n')

        for i, line in enumerate(lines):
            for pattern in self.error_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    # Capturar contexto (linha anterior e posterior)
                    context_start = max(0, i - 1)
                    context_end = min(len(lines), i + 2)
                    context = '\n'.join(lines[context_start:context_end])

                    # Extrair timestamp se possível
                    timestamp_match = re.search(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}', line)
                    timestamp = timestamp_match.group() if timestamp_match else "Timestamp não encontrado"

                    # Criar hash único para evitar duplicatas
                    error_hash = hashlib.md5(line.encode()).hexdigest()

                    if error_hash not in self.known_errors:
                        errors.append({
                            'line': line.strip(),
                            'context': context,
                            'timestamp': timestamp,
                            'pattern': pattern,
                            'hash': error_hash,
                            'line_number': i + 1
                        })
                        self.known_errors.add(error_hash)

        return errors

    async def analyze_errors_with_ai(self, errors: List[Dict], date: str) -> str:
        """Usa o agente ADK para analisar os erros encontrados."""
        if not errors:
            return "Nenhum erro detectado nos logs."

        try:
            # Preparar contexto para análise
            error_summary = f"ANÁLISE DE LOGS - {date}\n\n"
            error_summary += f"Total de erros detectados: {len(errors)}\n\n"

            for i, error in enumerate(errors[:5], 1):  # Limitar a 5 erros por análise
                error_summary += f"ERRO {i}:\n"
                error_summary += f"Timestamp: {error['timestamp']}\n"
                error_summary += f"Linha {error['line_number']}: {error['line']}\n"
                error_summary += f"Contexto:\n{error['context']}\n"
                error_summary += "-" * 50 + "\n"

            if len(errors) > 5:
                error_summary += f"\n... e mais {len(errors) - 5} erros detectados.\n"

            # Criar sessão para análise
            session_id = f"log_analysis_{date}_{datetime.now().strftime('%H%M%S')}"
            session = await self.session_service.create_session(
                app_name=self.app_name,
                user_id=self.user_id,
                session_id=session_id
            )

            # Prompt para análise
            analysis_prompt = f"""
            Analise os seguintes erros encontrados nos logs da aplicação:

            {error_summary}

            Por favor, forneça:
            1. 🚨 Classificação de severidade (CRÍTICO/ALTO/MÉDIO/BAIXO)
            2. 🔍 Análise dos erros mais importantes
            3. 💡 Possíveis causas e soluções
            4. ⚡ Ações recomendadas para a equipe

            Seja conciso mas informativo. Use emojis para facilitar a leitura.
            """

            # Executar análise
            content = types.Content(
                role='user',
                parts=[types.Part(text=analysis_prompt)]
            )

            events_async = self.runner.run_async(
                user_id=self.user_id,
                session_id=session_id,
                new_message=content
            )

            analysis_result = ""
            async for event in events_async:
                if event.is_final_response():
                    if hasattr(event, 'content') and event.content:
                        if hasattr(event.content, 'parts'):
                            if hasattr(event.content.parts, 'text'):
                                analysis_result = event.content.parts.text
                            elif isinstance(event.content.parts, list):
                                for part in event.content.parts:
                                    if hasattr(part, 'text') and part.text:
                                        analysis_result += part.text
                    break

            return analysis_result or "Não foi possível analisar os erros."

        except Exception as e:
            print(f"❌ Erro na análise de IA: {e}")
            return f"Erro na análise: {str(e)}"

    async def send_discord_alert(self, message: str, date: str, errors_count: int):
        """Envia alerta para o Discord via webhook."""
        if not self.discord_webhook_url:
            print("⚠️ Discord webhook não configurado")
            return False

        try:
            # Preparar payload do Discord
            embed = {
                "title": "🚨 Alerta de Monitoramento de Logs",
                "description": f"Erros detectados nos logs de {date}",
                "color": 0xff0000,  # Vermelho
                "fields": [
                    {
                        "name": "📅 Data",
                        "value": date,
                        "inline": True
                    },
                    {
                        "name": "🔢 Erros Detectados",
                        "value": str(errors_count),
                        "inline": True
                    },
                    {
                        "name": "🔗 URL dos Logs",
                        "value": f"{self.base_url}/{date}",
                        "inline": False
                    },
                    {
                        "name": "🤖 Análise IA",
                        "value": message[:1000] + "..." if len(message) > 1000 else message,
                        "inline": False
                    }
                ],
                "timestamp": datetime.now().isoformat(),
                "footer": {
                    "text": "Sistema de Monitoramento de Logs"
                }
            }

            payload = {
                "embeds": [embed],
                "username": "Log Monitor Bot"
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.discord_webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 204:
                        print(f"✅ Alerta enviado para Discord com sucesso")
                        return True
                    else:
                        print(f"❌ Erro ao enviar para Discord: {response.status}")
                        return False

        except Exception as e:
            print(f"❌ Erro ao enviar alerta Discord: {e}")
            return False

    async def monitor_date(self, date: str) -> bool:
        """Monitora os logs de uma data específica."""
        print(f"🔍 Monitorando logs de {date}...")

        # Buscar logs
        log_content = await self.fetch_logs(date)
        if not log_content:
            return False

        # Extrair erros
        errors = self.extract_errors(log_content)

        if errors:
            print(f"⚠️ {len(errors)} erros detectados em {date}")

            # Analisar com IA
            analysis = await self.analyze_errors_with_ai(errors, date)

            # Enviar alerta
            await self.send_discord_alert(analysis, date, len(errors))

            # Salvar na memória
            self.memory_manager.save_interaction(
                user_id=self.user_id,
                session_id=f"monitor_{date}",
                user_message=f"Monitoramento de logs {date}",
                agent_response=analysis,
                agent_type="LogMonitor",
                metadata={
                    "date": date,
                    "errors_count": len(errors),
                    "url": f"{self.base_url}/{date}"
                }
            )

            return True
        else:
            print(f"✅ Nenhum erro encontrado em {date}")
            return False

    async def start_monitoring(self):
        """Inicia o monitoramento contínuo."""
        self.is_monitoring = True
        print(f"🚀 Iniciando monitoramento de logs...")
        print(f"⏱️ Verificação a cada {self.check_interval} segundos")

        while self.is_monitoring:
            try:
                # Monitorar hoje e ontem
                today = datetime.now().strftime("%Y-%m-%d")
                yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

                for date in [today, yesterday]:
                    await self.monitor_date(date)
                    await asyncio.sleep(2)  # Pausa entre datas

                # Aguardar próxima verificação
                print(f"⏳ Próxima verificação em {self.check_interval} segundos...")
                await asyncio.sleep(self.check_interval)

            except Exception as e:
                print(f"❌ Erro no monitoramento: {e}")
                await asyncio.sleep(60)  # Aguardar 1 minuto em caso de erro

    def stop_monitoring(self):
        """Para o monitoramento."""
        self.is_monitoring = False
        print("🛑 Monitoramento interrompido")

    async def _run_async(self, query: str) -> str:
        """Método assíncrono para comandos manuais."""
        try:
            print(f"[{self.name}] Processando comando: '{query[:50]}...'")

            # Comandos disponíveis
            if "iniciar monitoramento" in query.lower():
                if not self.is_monitoring:
                    asyncio.create_task(self.start_monitoring())
                    return "🚀 Monitoramento de logs iniciado!"
                else:
                    return "⚠️ Monitoramento já está ativo."

            elif "parar monitoramento" in query.lower():
                self.stop_monitoring()
                return "🛑 Monitoramento de logs interrompido."

            elif "verificar hoje" in query.lower():
                today = datetime.now().strftime("%Y-%m-%d")
                has_errors = await self.monitor_date(today)
                return f"✅ Verificação de {today} concluída. {'Erros encontrados!' if has_errors else 'Nenhum erro detectado.'}"

            elif "verificar" in query.lower() and "data" in query.lower():
                # Extrair data do comando
                date_match = re.search(r'\d{4}-\d{2}-\d{2}', query)
                if date_match:
                    date = date_match.group()
                    has_errors = await self.monitor_date(date)
                    return f"✅ Verificação de {date} concluída. {'Erros encontrados!' if has_errors else 'Nenhum erro detectado.'}"
                else:
                    return "❌ Formato de data inválido. Use YYYY-MM-DD"

            elif "status" in query.lower():
                status = "🟢 Ativo" if self.is_monitoring else "🔴 Inativo"
                return f"📊 Status do monitoramento: {status}\n🔗 URL: {self.base_url}\n⏱️ Intervalo: {self.check_interval}s"

            else:
                return """
🤖 **Comandos disponíveis:**

-  `iniciar monitoramento` - Inicia o monitoramento automático
-  `parar monitoramento` - Para o monitoramento
-  `verificar hoje` - Verifica logs de hoje
-  `verificar data YYYY-MM-DD` - Verifica logs de data específica
-  `status` - Mostra status do sistema

📋 **Informações:**
- Monitora automaticamente logs de hoje e ontem
- Detecta erros usando padrões avançados
- Envia alertas para Discord quando encontra problemas
- Usa IA para análise inteligente dos erros
                """

        except Exception as e:
            error_msg = f"Erro ao processar comando: {str(e)}"
            print(f"[{self.name}] {error_msg}")
            return f"❌ {error_msg}"