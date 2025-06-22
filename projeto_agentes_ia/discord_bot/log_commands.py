# discord_bot/log_commands.py
import discord
from discord.ext import commands
import asyncio
import os
import sys
from pathlib import Path

# Adicionar o diretório pai ao path
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.append(str(project_root))

from agents.log_monitor_agent import LogMonitorAgent

class LogMonitorCommands(commands.Cog):
    """Comandos Discord para controle do monitoramento de logs."""

    def __init__(self, bot):
        self.bot = bot
        self.log_monitor = None
        self.setup_monitor()

    def setup_monitor(self):
        """Configura o agente de monitoramento."""
        try:
            discord_webhook = os.getenv("DISCORD_WEBHOOK_URL")
            self.log_monitor = LogMonitorAgent(
                discord_webhook_url=discord_webhook,
                check_interval=300  # 5 minutos
            )
            print("✅ Agente de monitoramento de logs configurado")
        except Exception as e:
            print(f"❌ Erro ao configurar monitoramento: {e}")

    @discord.app_commands.command(
        name="log_monitor",
        description="Controla o sistema de monitoramento de logs"
    )
    @discord.app_commands.describe(
        acao="Ação a ser executada: start, stop, check, status",
        data="Data específica para verificar (formato: YYYY-MM-DD)"
    )
    @discord.app_commands.choices(acao=[
        discord.app_commands.Choice(name="🚀 Iniciar Monitoramento", value="start"),
        discord.app_commands.Choice(name="🛑 Parar Monitoramento", value="stop"),
        discord.app_commands.Choice(name="🔍 Verificar Hoje", value="check"),
        discord.app_commands.Choice(name="📊 Status do Sistema", value="status")
    ])
    async def log_monitor_command(
        self,
        interaction: discord.Interaction,
        acao: discord.app_commands.Choice[str],
        data: str = None
    ):
        """Comando principal para controle do monitoramento."""
        await interaction.response.defer()

        if not self.log_monitor:
            embed = discord.Embed(
                title="❌ Erro",
                description="Sistema de monitoramento não está configurado.",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed)
            return

        try:
            action = acao.value

            if action == "start":
                if not self.log_monitor.is_monitoring:
                    asyncio.create_task(self.log_monitor.start_monitoring())
                    embed = discord.Embed(
                        title="🚀 Monitoramento Iniciado",
                        description="Sistema de monitoramento de logs ativado!",
                        color=0x00ff00
                    )
                    embed.add_field(
                        name="📋 Configurações",
                        value=f"-  URL: {self.log_monitor.base_url}\n-  Intervalo: {self.log_monitor.check_interval}s\n-  Status: 🟢 Ativo",
                        inline=False
                    )
                else:
                    embed = discord.Embed(
                        title="⚠️ Já Ativo",
                        description="O monitoramento já está em execução.",
                        color=0xffff00
                    )

            elif action == "stop":
                self.log_monitor.stop_monitoring()
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
                    response = await self.log_monitor._run_async(f"verificar data {data}")
                else:
                    response = await self.log_monitor._run_async("verificar hoje")

                result_embed = discord.Embed(
                    title="📋 Resultado da Verificação",
                    description=response,
                    color=0x00ff00
                )
                await interaction.followup.send(embed=result_embed)
                return

            elif action == "status":
                response = await self.log_monitor._run_async("status")
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

async def setup(bot):
    """Função para adicionar os comandos ao bot."""
    await bot.add_cog(LogMonitorCommands(bot))