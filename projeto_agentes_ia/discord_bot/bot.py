# discord_bot/bot.py - Versão com configurações robustas
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
    """Bot Discord com configurações robustas e tratamento de erros."""
    
    def __init__(self):
        # Configurar intents necessários
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            description="Bot de IA com agentes ADK e LangChain",
            help_command=None  # Desabilitar comando de ajuda padrão
        )
        
        self.agent_manager = None
        self.user_agent_preferences = {}
        self.synced = False
    
    async def setup_hook(self):
        """Configuração inicial com tratamento robusto de erros."""
        try:
            print("🤖 Inicializando AgentEIA Bot...")
            
            # Inicializar gerenciador de agentes
            self.agent_manager = AgentManager()
            print("✅ Gerenciador de agentes inicializado")
            
            # Aguardar um pouco antes de sincronizar
            await asyncio.sleep(2)
            
            # Sincronizar comandos
            print("🔄 Sincronizando comandos...")
            try:
                synced = await self.tree.sync()
                print(f"✅ {len(synced)} comandos sincronizados")
                self.synced = True
            except Exception as sync_error:
                print(f"⚠️ Erro na sincronização: {sync_error}")
                print("Tentando novamente em 5 segundos...")
                await asyncio.sleep(5)
                try:
                    synced = await self.tree.sync()
                    print(f"✅ {len(synced)} comandos sincronizados (segunda tentativa)")
                    self.synced = True
                except Exception as sync_error2:
                    print(f"❌ Falha na sincronização: {sync_error2}")
            
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
                type=discord.ActivityType.listening,
                name="/agenteia para conversar com IA"
            )
            await self.change_presence(activity=activity)
            print("✅ Status definido")
        except Exception as e:
            print(f"⚠️ Erro ao definir status: {e}")
        
        # Verificar permissões
        await self.check_permissions()
        
        print("🎉 Bot totalmente operacional!")
        print("💡 Use /agenteia no Discord para testar!")
    
    async def check_permissions(self):
        """Verifica permissões do bot nos servidores."""
        for guild in self.guilds:
            try:
                bot_member = guild.get_member(self.user.id)
                if bot_member:
                    perms = bot_member.guild_permissions
                    missing_perms = []
                    
                    required_perms = [
                        ('send_messages', 'Enviar Mensagens'),
                        ('use_slash_commands', 'Usar Comandos Slash'),
                        ('embed_links', 'Incorporar Links'),
                        ('read_message_history', 'Ler Histórico')
                    ]
                    
                    for perm_name, perm_display in required_perms:
                        if hasattr(perms, perm_name) and not getattr(perms, perm_name):
                            missing_perms.append(perm_display)
                    
                    if missing_perms:
                        print(f"⚠️ Permissões faltando em {guild.name}: {', '.join(missing_perms)}")
                    else:
                        print(f"✅ Permissões OK em {guild.name}")
                        
            except Exception as e:
                print(f"⚠️ Erro ao verificar permissões em {guild.name}: {e}")
    
    async def on_application_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        """Trata erros de comandos slash."""
        print(f"❌ Erro no comando {interaction.command.name if interaction.command else 'desconhecido'}: {error}")
        
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "❌ Ocorreu um erro ao processar o comando. Tente novamente em alguns instantes.",
                ephemeral=True
            )
    
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

@bot.tree.command(
    name="agenteia",
    description="🤖 Converse com agentes de IA (ADK ou LangChain)"
)
@discord.app_commands.describe(
    modelo="Escolha: adk (Google Gemini) ou langchain (GPT-4)",
    pergunta="Sua pergunta para o agente"
)
@discord.app_commands.choices(modelo=[
    discord.app_commands.Choice(name="🔧 ADK (Google Gemini)", value="adk"),
    discord.app_commands.Choice(name="🧠 LangChain (GPT-4)", value="langchain")
])
async def agenteia_command(
    interaction: discord.Interaction,
    modelo: discord.app_commands.Choice[str],
    pergunta: str
):
    """Comando principal com validação robusta."""
    await interaction.response.defer(thinking=True)
    
    try:
        modelo_value = modelo.value
        user_id = interaction.user.id
        guild_id = interaction.guild.id if interaction.guild else None
        channel_id = interaction.channel.id
        
        print(f"🔄 Comando recebido: {modelo_value} - {pergunta[:30]}...")
        
        # Verificar se o agente está disponível
        if not bot.agent_manager or modelo_value not in bot.agent_manager.agents:
            embed = discord.Embed(
                title="❌ Agente Indisponível",
                description=f"O agente **{modelo.name}** não está disponível.\n\nVerifique se as API keys estão configuradas.",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Configurar sessão
        session_id = bot.generate_session_id(user_id, guild_id, channel_id)
        bot.agent_manager.set_agent(modelo_value)
        bot.agent_manager.set_user_context(str(user_id), session_id)
        
        # Processar pergunta
        response = await bot.agent_manager.run_current_agent_with_context(
            pergunta, str(user_id), session_id
        )
        
        # Criar resposta
        embed = discord.Embed(
            title=f"🤖 {modelo.name}",
            description=response[:4000] if len(response) > 4000 else response,
            color=0x0099ff if modelo_value == "adk" else 0x00ff99
        )
        
        embed.add_field(
            name="❓ Pergunta",
            value=pergunta[:1000] if len(pergunta) > 1000 else pergunta,
            inline=False
        )
        
        embed.add_field(name="📍 Canal", value=f"#{interaction.channel.name}", inline=True)
        embed.add_field(name="🆔 Sessão", value=f"`{session_id[:12]}...`", inline=True)
        
        embed.set_footer(
            text=f"Por {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )
        
        await interaction.followup.send(embed=embed)
        print(f"✅ Resposta enviada para {interaction.user.display_name}")
        
    except Exception as e:
        print(f"❌ Erro no comando agenteia: {e}")
        error_embed = discord.Embed(
            title="❌ Erro Interno",
            description=f"Ocorreu um erro:\n```{str(e)[:1000]}```",
            color=0xff0000
        )
        await interaction.followup.send(embed=error_embed)

@bot.tree.command(
    name="status",
    description="📊 Verifica o status dos agentes"
)
async def status_command(interaction: discord.Interaction):
    """Comando de status."""
    await interaction.response.defer()
    
    try:
        if not bot.agent_manager:
            await interaction.followup.send("❌ Gerenciador não disponível.")
            return
        
        agent_info = bot.agent_manager.get_agent_info()
        
        embed = discord.Embed(
            title="📊 Status dos Agentes",
            color=0x00ff00
        )
        
        for agent_type, info in agent_info["agents_status"].items():
            status = "🟢 Online" if info["available"] else "🔴 Offline"
            embed.add_field(
                name=f"{info['name']}",
                value=f"{status}\n{info['description'][:100]}...",
                inline=True
            )
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        await interaction.followup.send(f"❌ Erro: {str(e)}")

def run_bot():
    """Executa o bot com tratamento de erros."""
    token = os.getenv("DISCORD_BOT_TOKEN")
    
    if not token:
        print("❌ DISCORD_BOT_TOKEN não encontrado no .env")
        print("Configure: DISCORD_BOT_TOKEN=seu_token")
        return
    
    print("🚀 Iniciando bot...")
    print("🔧 Para resolver 'Integração desconhecida':")
    print("   1. Verifique permissões no Discord Developer Portal")
    print("   2. Re-convide o bot se necessário")
    print("   3. Use Ctrl+R no Discord após inicialização")
    
    try:
        bot.run(token)
    except discord.LoginFailure:
        print("❌ Token inválido")
    except discord.HTTPException as e:
        print(f"❌ Erro HTTP: {e}")
    except Exception as e:
        print(f"❌ Erro: {e}")