# discord_bot/discord_bot.py
import discord
from discord.ext import commands
import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Adicionar o diretório pai ao path para importar os agentes
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from agents.agent_manager import AgentManager

# Carregar variáveis de ambiente
load_dotenv()

class AgentEIABot(commands.Bot):
    """
    Bot Discord que integra com os agentes ADK e LangChain.
    Permite conversas inteligentes com memória através de comandos slash.
    """

    def __init__(self):
        # Configurar intents necessários
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True

        super().__init__(
            command_prefix='!',
            intents=intents,
            description="Bot de IA com agentes ADK e LangChain"
        )

        # Inicializar gerenciador de agentes
        self.agent_manager = None

        # Dicionário para armazenar preferências de agente por usuário
        self.user_agent_preferences = {}

        # Dicionário para sessões de usuário
        self.user_sessions = {}

    async def setup_hook(self):
        """Configuração inicial do bot."""
        try:
            print("🤖 Inicializando AgentEIA Bot...")

            # Inicializar gerenciador de agentes
            self.agent_manager = AgentManager()
            print("✅ Gerenciador de agentes inicializado")

            # Sincronizar comandos slash
            await self.tree.sync()
            print("✅ Comandos slash sincronizados")

        except Exception as e:
            print(f"❌ Erro na configuração do bot: {e}")

    async def on_ready(self):
        """Evento chamado quando o bot está pronto."""
        print(f"🚀 {self.user} está online!")
        print(f"📊 Conectado a {len(self.guilds)} servidor(es)")

        # Definir atividade do bot
        activity = discord.Activity(
            type=discord.ActivityType.listening,
            name="/agenteia para conversar com IA"
        )
        await self.change_presence(activity=activity)

    def get_user_session_id(self, user_id: int, guild_id: int = None) -> str:
        """Gera um ID de sessão único para o usuário."""
        base_id = f"discord_{user_id}"
        if guild_id:
            base_id += f"_{guild_id}"
        return base_id

    def get_user_agent(self, user_id: int) -> str:
        """Retorna o agente preferido do usuário (padrão: adk)."""
        return self.user_agent_preferences.get(user_id, "adk")

    def set_user_agent(self, user_id: int, agent_type: str):
        """Define o agente preferido do usuário."""
        self.user_agent_preferences[user_id] = agent_type

# Instância global do bot
bot = AgentEIABot()

@bot.tree.command(
    name="agenteia",
    description="Converse com agentes de IA (ADK ou LangChain)"
)
async def agenteia_command(
    interaction: discord.Interaction,
    modelo: str = discord.app_commands.Choice(name="adk", value="adk"),
    pergunta: str = None
):
    """
    Comando principal para interagir com os agentes de IA.

    Args:
        modelo: Escolha entre 'adk' ou 'langchain'
        pergunta: Sua pergunta para o agente
    """
    await interaction.response.defer(thinking=True)

    try:
        user_id = interaction.user.id
        guild_id = interaction.guild.id if interaction.guild else None
        session_id = bot.get_user_session_id(user_id, guild_id)

        # Definir agente preferido do usuário
        bot.set_user_agent(user_id, modelo)

        if not pergunta:
            # Se não há pergunta, mostrar informações do agente
            embed = discord.Embed(
                title="🤖 AgentEIA - Assistente de IA",
                description=f"Agente **{modelo.upper()}** selecionado!",
                color=0x00ff00
            )

            if modelo == "adk":
                embed.add_field(
                    name="🔧 Google ADK",
                    value="-  Modelo Gemini 2.0 Flash\n-  Busca na internet\n-  Memória conversacional",
                    inline=False
                )
            else:
                embed.add_field(
                    name="🧠 LangChain",
                    value="-  Modelo GPT-4o-mini\n-  Ferramentas de busca\n-  Memória avançada",
                    inline=False
                )

            embed.add_field(
                name="💡 Como usar",
                value="Use `/agenteia modelo:adk pergunta:sua pergunta aqui`",
                inline=False
            )

            await interaction.followup.send(embed=embed)
            return

        # Verificar se o agente está disponível
        if not bot.agent_manager or modelo not in bot.agent_manager.agents:
            embed = discord.Embed(
                title="❌ Agente Indisponível",
                description=f"O agente **{modelo}** não está disponível no momento.",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed)
            return

        # Configurar agente e contexto
        bot.agent_manager.set_agent(modelo)
        bot.agent_manager.set_user_context(str(user_id), session_id)

        # Processar a pergunta
        response = await bot.agent_manager.run_current_agent_with_context(
            pergunta, str(user_id), session_id
        )

        # Criar embed de resposta
        embed = discord.Embed(
            title=f"🤖 Resposta do {modelo.upper()}",
            description=response[:4000],  # Limite do Discord
            color=0x0099ff
        )

        embed.add_field(
            name="👤 Pergunta",
            value=pergunta[:1000],  # Limite para o campo
            inline=False
        )

        embed.set_footer(
            text=f"Agente: {modelo.upper()} | Usuário: {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )

        await interaction.followup.send(embed=embed)

    except Exception as e:
        error_embed = discord.Embed(
            title="❌ Erro",
            description=f"Ocorreu um erro ao processar sua solicitação: {str(e)}",
            color=0xff0000
        )
        await interaction.followup.send(embed=error_embed)

@agenteia_command.autocomplete('modelo')
async def modelo_autocomplete(
    interaction: discord.Interaction,
    current: str
) -> list[discord.app_commands.Choice[str]]:
    """Autocomplete para o parâmetro modelo."""
    choices = [
        discord.app_commands.Choice(name="🔧 Google ADK (Gemini)", value="adk"),
        discord.app_commands.Choice(name="🧠 LangChain (GPT-4)", value="langchain")
    ]

    return [choice for choice in choices if current.lower() in choice.name.lower()]

@bot.tree.command(
    name="agente_info",
    description="Mostra informações sobre os agentes disponíveis"
)
async def agente_info_command(interaction: discord.Interaction):
    """Mostra informações detalhadas sobre os agentes."""
    await interaction.response.defer()

    try:
        if not bot.agent_manager:
            await interaction.followup.send("❌ Gerenciador de agentes não disponível.")
            return

        agent_info = bot.agent_manager.get_agent_info()

        embed = discord.Embed(
            title="🤖 Agentes de IA Disponíveis",
            description="Informações sobre os agentes do AgentEIA",
            color=0x00ff00
        )

        for agent_type, info in agent_info["agents_status"].items():
            status_emoji = "✅" if info["available"] else "❌"
            embed.add_field(
                name=f"{status_emoji} {info['name']}",
                value=f"**Tipo:** {agent_type.upper()}\n**Descrição:** {info['description']}",
                inline=False
            )

        embed.add_field(
            name="📊 Status Geral",
            value=f"**Agente Atual:** {agent_info.get('current_agent', 'Nenhum').upper()}\n**Total Disponível:** {len(agent_info['available_agents'])}",
            inline=False
        )

        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(f"❌ Erro ao obter informações: {str(e)}")

@bot.tree.command(
    name="limpar_memoria",
    description="Limpa sua memória conversacional"
)
async def limpar_memoria_command(interaction: discord.Interaction):
    """Limpa a memória conversacional do usuário."""
    await interaction.response.defer()

    try:
        user_id = interaction.user.id
        guild_id = interaction.guild.id if interaction.guild else None
        session_id = bot.get_user_session_id(user_id, guild_id)

        # Limpar preferências e sessões
        if user_id in bot.user_agent_preferences:
            del bot.user_agent_preferences[user_id]

        if session_id in bot.user_sessions:
            del bot.user_sessions[session_id]

        embed = discord.Embed(
            title="🧠 Memória Limpa",
            description="Sua memória conversacional foi limpa com sucesso!",
            color=0x00ff00
        )

        embed.add_field(
            name="ℹ️ O que foi limpo",
            value="-  Histórico de conversas\n-  Preferência de agente\n-  Contexto da sessão",
            inline=False
        )

        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(f"❌ Erro ao limpar memória: {str(e)}")

@bot.tree.command(
    name="adicionar_conhecimento",
    description="Adiciona conhecimento específico ao sistema RAG"
)
async def adicionar_conhecimento_command(
    interaction: discord.Interaction,
    conteudo: str,
    fonte: str = "discord_user"
):
    """Adiciona conhecimento ao sistema RAG dos agentes."""
    await interaction.response.defer()

    try:
        if not bot.agent_manager:
            await interaction.followup.send("❌ Gerenciador de agentes não disponível.")
            return

        # Adicionar conhecimento ao agente atual
        doc_id = bot.agent_manager.add_knowledge_to_current_agent(
            content=conteudo,
            source=fonte,
            metadata={
                "added_by": str(interaction.user.id),
                "added_via": "discord",
                "guild_id": str(interaction.guild.id) if interaction.guild else None
            }
        )

        embed = discord.Embed(
            title="📚 Conhecimento Adicionado",
            description="Conhecimento adicionado com sucesso ao sistema!",
            color=0x00ff00
        )

        embed.add_field(
            name="📝 Conteúdo",
            value=conteudo[:500] + "..." if len(conteudo) > 500 else conteudo,
            inline=False
        )

        embed.add_field(
            name="🔍 Fonte",
            value=fonte,
            inline=True
        )

        if doc_id:
            embed.add_field(
                name="🆔 ID do Documento",
                value=doc_id[:8] + "...",
                inline=True
            )

        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(f"❌ Erro ao adicionar conhecimento: {str(e)}")

def run_bot():
    """Executa o bot Discord."""
    token = os.getenv("DISCORD_BOT_TOKEN")

    if not token:
        print("❌ DISCORD_BOT_TOKEN não encontrado no arquivo .env")
        print("Configure o token do seu bot Discord no arquivo .env")
        return

    try:
        bot.run(token)
    except discord.LoginFailure:
        print("❌ Token do Discord inválido. Verifique o DISCORD_BOT_TOKEN no arquivo .env")
    except Exception as e:
        print(f"❌ Erro ao executar o bot: {e}")

if __name__ == "__main__":
    run_bot()