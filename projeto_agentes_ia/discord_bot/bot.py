# discord_bot/bot.py - Versão com sistema de conversas isoladas e monitoramento de logs.
import discord
from discord.ext import commands
import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import hashlib
from datetime import datetime

# Adicionar o diretório pai ao path
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.append(str(project_root))

from agents.agent_manager import AgentManager

# Carregar variáveis de ambiente
load_dotenv()

class AgentEIABot(commands.Bot):
    """Bot Discord com sistema de conversas isoladas e monitoramento de logs."""

    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True

        super().__init__(
            command_prefix='!',
            intents=intents,
            description="Bot de IA com agentes ADK, LangChain e Monitoramento de Logs"
        )

        self.agent_manager = None
        self.user_agent_preferences = {}
        self.synced = False

        # Instância global do agente de monitoramento
        self.log_monitor = None

    async def setup_hook(self):
        """Configuração inicial com agente de monitoramento."""
        try:
            print("🤖 Inicializando AgentEIA Bot...")

            # Inicializar gerenciador de agentes
            self.agent_manager = AgentManager()
            print("✅ Gerenciador de agentes inicializado")

            # Inicializar agente de monitoramento de logs
            try:
                from agents.log_monitor_agent import LogMonitorAgent

                # Obter webhook do Discord para alertas
                discord_webhook = os.getenv("DISCORD_WEBHOOK_URL")

                self.log_monitor = LogMonitorAgent(
                    discord_webhook_url=discord_webhook,
                    check_interval=300  # 5 minutos
                )
                print("✅ Agente de monitoramento de logs inicializado")

                # Iniciar monitoramento automático
                asyncio.create_task(self.log_monitor.start_monitoring())
                print("🚀 Monitoramento automático de logs iniciado")

            except Exception as log_error:
                print(f"⚠️ Erro ao inicializar monitoramento de logs: {log_error}")

            # Sincronizar comandos
            await asyncio.sleep(2)
            synced = await self.tree.sync()
            print(f"✅ {len(synced)} comandos sincronizados")
            self.synced = True

        except Exception as e:
            print(f"❌ Erro na configuração: {e}")

    async def on_ready(self):
        """Evento quando o bot está pronto."""
        print(f"🚀 {self.user} está online!")
        print(f"📊 Conectado a {len(self.guilds)} servidor(es)")
        print(f"🆔 Bot ID: {self.user.id}")

        # Se não estiver em nenhum servidor, mostrar link de convite
        if len(self.guilds) == 0:
            invite_url = f"https://discord.com/api/oauth2/authorize?client_id={self.user.id}&permissions=2147483648&scope=bot%20applications.commands"
            print("\n" + "="*60)
            print("⚠️  BOT NÃO ESTÁ EM NENHUM SERVIDOR!")
            print("🔗 Use este link para adicionar o bot:")
            print(f"{invite_url}")
            print("="*60)
            return

        # Listar servidores conectados
        for guild in self.guilds:
            print(f"   ✅ {guild.name} (ID: {guild.id})")

        # Definir atividade
        try:
            activity = discord.Activity(
                type=discord.ActivityType.watching,
                name="logs e conversando com IA"
            )
            await self.change_presence(activity=activity)
            print("✅ Status definido")
        except Exception as e:
            print(f"⚠️ Erro ao definir status: {e}")

        print("🎉 Bot totalmente operacional!")
        print("💡 Use /agenteia, /log_monitor, /log_lista no Discord!")

    def generate_session_id(self, user_id: int, guild_id: int = None, channel_id: int = None) -> str:
        """Gera ID de sessão único."""
        context_parts = [str(user_id)]

        if guild_id:
            context_parts.append(str(guild_id))
        if channel_id:
            context_parts.append(str(channel_id))

        today = datetime.now().strftime("%Y-%m-%d")
        context_parts.append(today)

        context_string = "_".join(context_parts)
        session_hash = hashlib.md5(context_string.encode()).hexdigest()

        return f"discord_{session_hash}"

# Instância global do bot
bot = AgentEIABot()

# Comandos existentes (agenteia, status) permanecem iguais...

@bot.tree.command(
    name="log_monitor",
    description="🔍 Controla o sistema de monitoramento de logs"
)
@discord.app_commands.describe(
    acao="Ação: start, stop, check, status",
    data="Data específica (YYYY-MM-DD) - opcional"
)
@discord.app_commands.choices(acao=[
    discord.app_commands.Choice(name="🚀 Iniciar Monitoramento", value="start"),
    discord.app_commands.Choice(name="🛑 Parar Monitoramento", value="stop"),
    discord.app_commands.Choice(name="🔍 Verificar Hoje", value="check"),
    discord.app_commands.Choice(name="📊 Status do Sistema", value="status")
])
async def log_monitor_command(
    interaction: discord.Interaction,
    acao: discord.app_commands.Choice[str],
    data: str = None
):
    """Comando para controlar o monitoramento de logs."""
    await interaction.response.defer()

    if not bot.log_monitor:
        embed = discord.Embed(
            title="❌ Monitoramento Indisponível",
            description="Sistema de monitoramento de logs não está configurado.",
            color=0xff0000
        )
        await interaction.followup.send(embed=embed)
        return

    try:
        action = acao.value

        if action == "start":
            if not bot.log_monitor.is_monitoring:
                asyncio.create_task(bot.log_monitor.start_monitoring())
                embed = discord.Embed(
                    title="🚀 Monitoramento Iniciado",
                    description="Sistema de monitoramento de logs ativado!",
                    color=0x00ff00
                )
                embed.add_field(
                    name="📋 Configurações",
                    value=f"🔗 **URL:** {bot.log_monitor.base_url}\n⏱️ **Intervalo:** {bot.log_monitor.check_interval}s\n📊 **Status:** 🟢 Ativo",
                    inline=False
                )
            else:
                embed = discord.Embed(
                    title="⚠️ Já Ativo",
                    description="O monitoramento já está em execução.",
                    color=0xffff00
                )

        elif action == "stop":
            bot.log_monitor.stop_monitoring()
            embed = discord.Embed(
                title="🛑 Monitoramento Parado",
                description="Sistema de monitoramento desativado.",
                color=0xff9900
            )

        elif action == "check":
            embed = discord.Embed(
                title="🔍 Verificando Logs",
                description="Iniciando verificação manual...",
                color=0x0099ff
            )
            await interaction.followup.send(embed=embed)

            if data:
                response = await bot.log_monitor._run_async(f"verificar data {data}")
            else:
                response = await bot.log_monitor._run_async("verificar hoje")

            result_embed = discord.Embed(
                title="📋 Resultado da Verificação",
                description=response,
                color=0x00ff00
            )
            await interaction.followup.send(embed=result_embed)
            return

        elif action == "status":
            response = await bot.log_monitor._run_async("status")
            embed = discord.Embed(
                title="📊 Status do Sistema",
                description=response,
                color=0x0099ff
            )

        await interaction.followup.send(embed=embed)

    except Exception as e:
        error_embed = discord.Embed(
            title="❌ Erro",
            description=f"Erro ao executar comando: {str(e)}",
            color=0xff0000
        )
        await interaction.followup.send(embed=error_embed)

@bot.tree.command(
    name="log_lista",
    description="📋 Visualiza logs de uma data específica"
)
@discord.app_commands.describe(
    data="Data dos logs (YYYY-MM-DD). Padrão: hoje",
    linhas="Número de linhas para mostrar (máx: 50). Padrão: 20"
)
async def log_lista_command(
    interaction: discord.Interaction,
    data: str = None,
    linhas: int = 20
):
    """Comando para visualizar logs diretamente no Discord."""
    await interaction.response.defer()

    if not bot.log_monitor:
        embed = discord.Embed(
            title="❌ Monitoramento Indisponível",
            description="Sistema de monitoramento de logs não está configurado.",
            color=0xff0000
        )
        await interaction.followup.send(embed=embed)
        return

    try:
        # Usar data atual se não especificada
        if not data:
            data = datetime.now().strftime("%Y-%m-%d")

        # Validar formato da data
        try:
            datetime.strptime(data, "%Y-%m-%d")
        except ValueError:
            embed = discord.Embed(
                title="❌ Data Inválida",
                description="Use o formato YYYY-MM-DD (ex: 2025-06-21)",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed)
            return

        # Limitar número de linhas
        linhas = max(1, min(linhas, 50))

        print(f"🔍 Buscando logs de {data}...")

        # Buscar logs
        log_content = await bot.log_monitor.fetch_logs(data)

        if not log_content:
            embed = discord.Embed(
                title="📋 Logs Não Encontrados",
                description=f"Não foi possível acessar os logs de **{data}**.\n\nPossíveis causas:\n-  Data não existe\n-  Logs não foram gerados\n-  Erro de acesso ao servidor",
                color=0xffff00
            )
            embed.add_field(
                name="🔗 URL Tentada",
                value=f"{bot.log_monitor.base_url}/{data}",
                inline=False
            )
            await interaction.followup.send(embed=embed)
            return

        # Processar logs
        log_lines = log_content.split('\n')
        total_lines = len(log_lines)

        # Pegar as últimas N linhas
        recent_lines = log_lines[-linhas:] if total_lines > linhas else log_lines

        # Extrair erros
        errors = bot.log_monitor.extract_errors(log_content)

        # Criar embed principal
        embed = discord.Embed(
            title=f"📋 Logs de {data}",
            description=f"Exibindo **{len(recent_lines)}** linhas mais recentes de **{total_lines}** total",
            color=0x0099ff
        )

        # Adicionar estatísticas
        embed.add_field(
            name="📊 Estatísticas",
            value=f"🔢 **Total de linhas:** {total_lines}\n🚨 **Erros detectados:** {len(errors)}\n📅 **Data:** {data}",
            inline=True
        )

        embed.add_field(
            name="🔗 URL",
            value=f"[Ver logs completos]({bot.log_monitor.base_url}/{data})",
            inline=True
        )

        # Adicionar amostra dos logs (limitado pelo Discord)
        log_sample = '\n'.join(recent_lines)

        # Discord tem limite de 1024 caracteres por field
        if len(log_sample) > 1000:
            log_sample = log_sample[:1000] + "..."

        embed.add_field(
            name=f"📝 Últimas {len(recent_lines)} Linhas",
            value=f"```\n{log_sample}\n```",
            inline=False
        )

        await interaction.followup.send(embed=embed)

        # Se houver erros, enviar embed separado com detalhes
        if errors:
            error_embed = discord.Embed(
                title=f"🚨 Erros Detectados em {data}",
                description=f"Encontrados **{len(errors)}** erros nos logs:",
                color=0xff0000
            )

            # Mostrar até 3 erros mais recentes
            for i, error in enumerate(errors[-3:], 1):
                error_embed.add_field(
                    name=f"❌ Erro {i}",
                    value=f"**Linha {error['line_number']}:** {error['timestamp']}\n```{error['line'][:200]}```",
                    inline=False
                )

            if len(errors) > 3:
                error_embed.add_field(
                    name="ℹ️ Mais Erros",
                    value=f"... e mais {len(errors) - 3} erros. Use `/log_monitor acao:check data:{data}` para análise completa.",
                    inline=False
                )

            await interaction.followup.send(embed=error_embed)

    except Exception as e:
        error_embed = discord.Embed(
            title="❌ Erro ao Buscar Logs",
            description=f"Ocorreu um erro ao tentar buscar os logs:\n```{str(e)}```",
            color=0xff0000
        )
        await interaction.followup.send(embed=error_embed)

@bot.tree.command(
    name="log_search",
    description="🔍 Busca por texto específico nos logs"
)
@discord.app_commands.describe(
    termo="Termo para buscar nos logs",
    data="Data dos logs (YYYY-MM-DD). Padrão: hoje",
    limite="Número máximo de resultados (máx: 10). Padrão: 5"
)
async def log_search_command(
    interaction: discord.Interaction,
    termo: str,
    data: str = None,
    limite: int = 5
):
    """Comando para buscar texto específico nos logs."""
    await interaction.response.defer()

    if not bot.log_monitor:
        embed = discord.Embed(
            title="❌ Monitoramento Indisponível",
            description="Sistema de monitoramento de logs não está configurado.",
            color=0xff0000
        )
        await interaction.followup.send(embed=embed)
        return

    try:
        # Usar data atual se não especificada
        if not data:
            data = datetime.now().strftime("%Y-%m-%d")

        # Validar formato da data
        try:
            datetime.strptime(data, "%Y-%m-%d")
        except ValueError:
            embed = discord.Embed(
                title="❌ Data Inválida",
                description="Use o formato YYYY-MM-DD (ex: 2025-06-21)",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed)
            return

        # Limitar resultados
        limite = max(1, min(limite, 10))

        print(f"🔍 Buscando '{termo}' nos logs de {data}...")

        # Buscar logs
        log_content = await bot.log_monitor.fetch_logs(data)

        if not log_content:
            embed = discord.Embed(
                title="📋 Logs Não Encontrados",
                description=f"Não foi possível acessar os logs de **{data}**.",
                color=0xffff00
            )
            await interaction.followup.send(embed=embed)
            return

        # Buscar termo nos logs
        log_lines = log_content.split('\n')
        matches = []

        for i, line in enumerate(log_lines, 1):
            if termo.lower() in line.lower():
                matches.append({
                    'line_number': i,
                    'content': line.strip(),
                    'context': '\n'.join(log_lines[max(0, i-2):min(len(log_lines), i+1)])
                })

                if len(matches) >= limite:
                    break

        # Criar resposta
        if not matches:
            embed = discord.Embed(
                title="🔍 Busca nos Logs",
                description=f"Nenhum resultado encontrado para **'{termo}'** em {data}",
                color=0xffff00
            )
            embed.add_field(
                name="📊 Informações",
                value=f"🔢 **Linhas analisadas:** {len(log_lines)}\n📅 **Data:** {data}",
                inline=False
            )
        else:
            embed = discord.Embed(
                title="🔍 Resultados da Busca",
                description=f"Encontrados **{len(matches)}** resultados para **'{termo}'** em {data}",
                color=0x00ff00
            )

            for i, match in enumerate(matches, 1):
                embed.add_field(
                    name=f"📍 Resultado {i} (Linha {match['line_number']})",
                    value=f"```{match['content'][:200]}```",
                    inline=False
                )

        await interaction.followup.send(embed=embed)

    except Exception as e:
        error_embed = discord.Embed(
            title="❌ Erro na Busca",
            description=f"Ocorreu um erro ao buscar nos logs:\n```{str(e)}```",
            color=0xff0000
        )
        await interaction.followup.send(embed=error_embed)

# Manter comandos existentes (agenteia, status, etc.)...

def run_bot():
    """Executa o bot Discord."""
    token = os.getenv("DISCORD_BOT_TOKEN")

    if not token:
        print("❌ DISCORD_BOT_TOKEN não encontrado no .env")
        return

    try:
        print("🚀 Iniciando bot com monitoramento de logs integrado...")
        bot.run(token)
    except discord.LoginFailure:
        print("❌ Token do Discord inválido")
    except Exception as e:
        print(f"❌ Erro ao executar o bot: {e}")