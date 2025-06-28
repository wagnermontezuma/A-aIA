import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import sys
from pathlib import Path

# Adicionar o diretório raiz ao sys.path
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.append(str(project_root))

from agents.bticket_agent import BTicketAgent

class BTicketCommands(commands.Cog):
    """Comandos Discord para integração com B-Ticket."""
    
    def __init__(self, bot):
        self.bot = bot
        self.bticket_agent = None
        self.setup_agent()
    
    def setup_agent(self):
        """Configura o agente B-Ticket."""
        try:
            self.bticket_agent = BTicketAgent()
            print("✅ Agente B-Ticket configurado para Discord")
        except Exception as e:
            print(f"❌ Erro ao configurar agente B-Ticket: {e}")
    
    @app_commands.command(
        name="bticket",
        description="Interage com o sistema B-Ticket"
    )
    @app_commands.describe(
        comando="Comando para executar no B-Ticket",
        parametros="Parâmetros adicionais (opcional)"
    )
    @app_commands.choices(comando=[
        app_commands.Choice(name="Listar Tickets", value="listar tickets"),
        app_commands.Choice(name="Listar Usuários", value="listar usuários"),
        app_commands.Choice(name="Listar Departamentos", value="listar departamentos"),
        app_commands.Choice(name="Listar Status", value="listar status"),
        app_commands.Choice(name="Listar Prioridades", value="listar prioridades"),
    ])
    async def bticket_command(
        self,
        interaction: discord.Interaction,
        comando: app_commands.Choice[str],
        parametros: str = None
    ):
        """Comando genérico para B-Ticket."""
        await interaction.response.defer()
        
        if not self.bticket_agent:
            embed = discord.Embed(
                title="❌ B-Ticket Indisponível",
                description="O agente B-Ticket não está configurado.",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed)
            return
        
        try:
            # Construir consulta
            query = comando.value
            if parametros:
                query += f" {parametros}"
            
            # Executar comando
            response = await self.bticket_agent._run_async(query)
            
            # Criar embed de resposta
            embed = discord.Embed(
                title=f"B-Ticket - {comando.name}",
                description=response[:4000] if len(response) > 4000 else response,
                color=0x0099ff
            )
            
            await interaction.followup.send(embed=embed)
        
        except Exception as e:
            embed = discord.Embed(
                title="❌ Erro no Comando B-Ticket",
                description=f"Ocorreu um erro: {e}",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed)

    @app_commands.command(
        name="ticket",
        description="Mostra detalhes de um ticket específico"
    )
    @app_commands.describe(
        ticket_id="ID do ticket para visualizar"
    )
    async def ticket_details_command(
        self,
        interaction: discord.Interaction,
        ticket_id: int
    ):
        """Mostra detalhes de um ticket."""
        await interaction.response.defer()
        
        if not self.bticket_agent:
            embed = discord.Embed(
                title="❌ B-Ticket Indisponível",
                description="O agente B-Ticket não está configurado.",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed)
            return
        
        try:
            query = f"ticket {ticket_id}"
            response = await self.bticket_agent._run_async(query)
            
            embed = discord.Embed(
                title=f"Ticket #{ticket_id}",
                description=response,
                color=0x0099ff
            )
            
            await interaction.followup.send(embed=embed)
        
        except Exception as e:
            embed = discord.Embed(
                title=f"❌ Erro ao buscar ticket #{ticket_id}",
                description=f"Ocorreu um erro: {e}",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed)

    @app_commands.command(
        name="create_ticket",
        description="Cria um novo ticket no B-Ticket"
    )
    @app_commands.describe(
        title="Título do ticket",
        department_name="Nome do departamento",
        priority_name="Nome da prioridade (ex: Baixa, Média, Alta)",
        user_id="ID do usuário solicitante"
    )
    async def create_ticket_command(
        self,
        interaction: discord.Interaction,
        title: str,
        department_name: str,
        priority_name: str,
        user_id: int
    ):
        """Cria um novo ticket."""
        await interaction.response.defer()

        if not self.bticket_agent:
            embed = discord.Embed(
                title="❌ B-Ticket Indisponível",
                description="O agente B-Ticket não está configurado.",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed)
            return

        try:
            query = f"criar ticket {title} para {department_name} com prioridade {priority_name} e usuário {user_id}"
            response = await self.bticket_agent._run_async(query)

            embed = discord.Embed(
                title="✅ Ticket Criado",
                description=response,
                color=0x00ff00
            )
            await interaction.followup.send(embed=embed)

        except Exception as e:
            embed = discord.Embed(
                title="❌ Erro ao criar ticket",
                description=f"Ocorreu um erro: {e}",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed)

    @app_commands.command(
        name="delete_ticket",
        description="Deleta um ticket no B-Ticket"
    )
    @app_commands.describe(
        ticket_id="ID do ticket a ser deletado"
    )
    async def delete_ticket_command(
        self,
        interaction: discord.Interaction,
        ticket_id: int
    ):
        """Deleta um ticket."""
        await interaction.response.defer()

        if not self.bticket_agent:
            embed = discord.Embed(
                title="❌ B-Ticket Indisponível",
                description="O agente B-Ticket não está configurado.",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed)
            return

        try:
            query = f"deletar ticket {ticket_id}"
            response = await self.bticket_agent._run_async(query)

            embed = discord.Embed(
                title="✅ Ticket Deletado",
                description=response,
                color=0x00ff00
            )
            await interaction.followup.send(embed=embed)

        except Exception as e:
            embed = discord.Embed(
                title="❌ Erro ao deletar ticket",
                description=f"Ocorreu um erro: {e}",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(BTicketCommands(bot))