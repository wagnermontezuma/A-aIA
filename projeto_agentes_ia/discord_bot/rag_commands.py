# discord_bot/rag_commands.py
import discord
from discord.ext import commands
import asyncio
import os
import sys
import tempfile
import re
from pathlib import Path
from urllib.parse import urlparse

# Adicionar o diretório pai ao path
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.append(str(project_root))

from memory.document_processor import DocumentProcessor
from memory.postgres_rag_system import PostgresRAGSystem

class RAGCommands(commands.Cog):
    """Comandos Discord para alimentação do sistema RAG."""
    
    def __init__(self, bot):
        self.bot = bot
        self.document_processor = DocumentProcessor()
        self.rag_system = None
        self.setup_rag_system()
    
    def setup_rag_system(self):
        """Configura o sistema RAG."""
        try:
            self.rag_system = PostgresRAGSystem(embedding_model="local")
            print("✅ Sistema RAG configurado para comandos Discord")
        except Exception as e:
            print(f"❌ Erro ao configurar sistema RAG: {e}")
    
    @discord.app_commands.command(
        name="rag_add_url",
        description="📚 Adiciona conteúdo de uma URL ao conhecimento dos agentes"
    )
    @discord.app_commands.describe(
        url="URL do documento ou página web",
        nome="Nome personalizado para identificar o documento (opcional)"
    )
    async def rag_add_url(self, interaction: discord.Interaction, url: str, nome: str = None):
        """Adiciona conteúdo de URL ao RAG."""
        await interaction.response.defer()
        
        try:
            # Validar URL
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                embed = discord.Embed(
                    title="❌ URL Inválida",
                    description="Por favor, forneça uma URL válida (ex: https://exemplo.com)",
                    color=0xff0000
                )
                await interaction.followup.send(embed=embed)
                return
            
            if not self.rag_system:
                embed = discord.Embed(
                    title="❌ Sistema RAG Indisponível",
                    description="O sistema RAG não está configurado.",
                    color=0xff0000
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Inicializar RAG se necessário
            if not self.rag_system._initialized:
                await self.rag_system.initialize()
            
            embed = discord.Embed(
                title="🔄 Processando URL",
                description=f"Baixando e processando conteúdo de: {url}",
                color=0x0099ff
            )
            await interaction.followup.send(embed=embed)
            
            # Processar URL
            result = await self.document_processor.process_url(url, nome)
            
            # Adicionar chunks ao RAG
            added_count = 0
            for chunk in result['chunks']:
                doc_id = await self.rag_system.add_document(
                    content=chunk,
                    source=f"url:{result['source']}",
                    metadata={
                        "type": result['type'],
                        "url": url,
                        "added_by": str(interaction.user.id),
                        "added_via": "discord_url",
                        "chunk_index": added_count,
                        "total_chunks": result['total_chunks'],
                        **result['metadata']
                    }
                )
                if doc_id:
                    added_count += 1
            
            # Resposta de sucesso
            success_embed = discord.Embed(
                title="✅ URL Adicionada ao Conhecimento",
                description=f"Conteúdo processado e adicionado com sucesso!",
                color=0x00ff00
            )
            
            success_embed.add_field(
                name="📊 Estatísticas",
                value=f"🔗 **URL:** {url}\n📝 **Tipo:** {result['type']}\n📄 **Chunks:** {added_count}\n📊 **Caracteres:** {result['metadata']['char_count']}\n📝 **Palavras:** {result['metadata']['word_count']}",
                inline=False
            )
            
            success_embed.add_field(
                name="🤖 Disponibilidade",
                value="O conhecimento já está disponível para ambos os agentes (ADK e LangChain)",
                inline=False
            )
            
            await interaction.followup.send(embed=success_embed)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Erro ao Processar URL",
                description=f"Ocorreu um erro ao processar a URL:\n```{str(e)}```",
                color=0xff0000
            )
            await interaction.followup.send(embed=error_embed)
    
    @discord.app_commands.command(
        name="rag_add_file",
        description="📎 Adiciona um arquivo anexado ao conhecimento dos agentes"
    )
    @discord.app_commands.describe(
        arquivo="Arquivo para adicionar (PDF, TXT, DOCX, HTML)",
        nome="Nome personalizado para identificar o documento (opcional)"
    )
    async def rag_add_file(self, interaction: discord.Interaction, arquivo: discord.Attachment, nome: str = None):
        """Adiciona arquivo anexado ao RAG."""
        await interaction.response.defer()
        
        try:
            if not self.rag_system:
                embed = discord.Embed(
                    title="❌ Sistema RAG Indisponível",
                    description="O sistema RAG não está configurado.",
                    color=0xff0000
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Verificar tamanho do arquivo
            max_size = 50 * 1024 * 1024  # 50MB
            if arquivo.size > max_size:
                embed = discord.Embed(
                    title="❌ Arquivo Muito Grande",
                    description=f"O arquivo deve ter no máximo 50MB. Tamanho atual: {arquivo.size / 1024 / 1024:.1f}MB",
                    color=0xff0000
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Verificar extensão
            supported_extensions = ['.pdf', '.txt', '.md', '.docx', '.html', '.htm']
            file_extension = Path(arquivo.filename).suffix.lower()
            
            if file_extension not in supported_extensions:
                embed = discord.Embed(
                    title="❌ Formato Não Suportado",
                    description=f"Formatos suportados: {', '.join(supported_extensions)}\nArquivo enviado: {file_extension}",
                    color=0xff0000
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Inicializar RAG se necessário
            if not self.rag_system._initialized:
                await self.rag_system.initialize()
            
            embed = discord.Embed(
                title="🔄 Processando Arquivo",
                description=f"Processando: {arquivo.filename} ({arquivo.size / 1024:.1f} KB)",
                color=0x0099ff
            )
            await interaction.followup.send(embed=embed)
            
            # Processar arquivo
            result = await self.document_processor.process_discord_attachment(
                arquivo.url, arquivo.filename, nome
            )
            
            # Adicionar chunks ao RAG
            added_count = 0
            for chunk in result['chunks']:
                doc_id = await self.rag_system.add_document(
                    content=chunk,
                    source=f"file:{result['source']}",
                    metadata={
                        "type": result['type'],
                        "filename": arquivo.filename,
                        "file_size": arquivo.size,
                        "added_by": str(interaction.user.id),
                        "added_via": "discord_file",
                        "chunk_index": added_count,
                        "total_chunks": result['total_chunks'],
                        **result['metadata']
                    }
                )
                if doc_id:
                    added_count += 1
            
            # Resposta de sucesso
            success_embed = discord.Embed(
                title="✅ Arquivo Adicionado ao Conhecimento",
                description=f"Arquivo processado e adicionado com sucesso!",
                color=0x00ff00
            )
            
            success_embed.add_field(
                name="📊 Estatísticas",
                value=f"📎 **Arquivo:** {arquivo.filename}\n📝 **Tipo:** {result['type']}\n📄 **Chunks:** {added_count}\n💾 **Tamanho:** {arquivo.size / 1024:.1f} KB\n📊 **Caracteres:** {result['metadata']['char_count']}\n📝 **Palavras:** {result['metadata']['word_count']}",
                inline=False
            )
            
            success_embed.add_field(
                name="🤖 Disponibilidade",
                value="O conhecimento já está disponível para ambos os agentes (ADK e LangChain)",
                inline=False
            )
            
            await interaction.followup.send(embed=success_embed)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Erro ao Processar Arquivo",
                description=f"Ocorreu um erro ao processar o arquivo:\n```{str(e)}```",
                color=0xff0000
            )
            await interaction.followup.send(embed=error_embed)
    
    @discord.app_commands.command(
        name="rag_add_text",
        description="📝 Adiciona texto direto ao conhecimento dos agentes"
    )
    @discord.app_commands.describe(
        texto="Texto para adicionar ao conhecimento",
        nome="Nome para identificar este conhecimento"
    )
    async def rag_add_text(self, interaction: discord.Interaction, texto: str, nome: str):
        """Adiciona texto direto ao RAG."""
        await interaction.response.defer()
        
        try:
            if not self.rag_system:
                embed = discord.Embed(
                    title="❌ Sistema RAG Indisponível",
                    description="O sistema RAG não está configurado.",
                    color=0xff0000
                )
                await interaction.followup.send(embed=embed)
                return
            
            if len(texto) == 0:
                embed = discord.Embed(
                    title="❌ Texto Vazio",
                    description="Por favor, forneça algum texto para adicionar.",
                    color=0xff0000
                )
                await interaction.followup.send(embed=embed)
                return
            
            if not nome:
                 embed = discord.Embed(
                    title="❌ Nome Necessário",
                    description="Por favor, forneça um nome para identificar este conhecimento.",
                    color=0xff0000
                )
                 await interaction.followup.send(embed=embed)
                 return
            
            # Inicializar RAG se necessário
            if not self.rag_system._initialized:
                await self.rag_system.initialize()
            
            embed = discord.Embed(
                title="🔄 Processando Texto",
                description=f"Processando texto com nome: {nome}",
                color=0x0099ff
            )
            await interaction.followup.send(embed=embed)
            
            # Processar texto
            result = await self.document_processor._process_text_content(texto, nome)
            
            # Adicionar chunks ao RAG
            added_count = 0
            for chunk in result['chunks']:
                doc_id = await self.rag_system.add_document(
                    content=chunk,
                    source=f"text:{result['source']}",
                    metadata={
                        "type": result['type'],
                        "added_by": str(interaction.user.id),
                        "added_via": "discord_text",
                        "chunk_index": added_count,
                        "total_chunks": result['total_chunks'],
                        **result['metadata']
                    }
                )
                if doc_id:
                    added_count += 1
            
            # Resposta de sucesso
            success_embed = discord.Embed(
                title="✅ Texto Adicionado ao Conhecimento",
                description=f"Texto processado e adicionado com sucesso!",
                color=0x00ff00
            )
            
            success_embed.add_field(
                name="📊 Estatísticas",
                value=f"📝 **Nome:** {nome}\n📄 **Chunks:** {added_count}\n📊 **Caracteres:** {result['metadata']['char_count']}\n📝 **Palavras:** {result['metadata']['word_count']}",
                inline=False
            )
            
            success_embed.add_field(
                name="Conteúdo (Início)",
                value=f"```{texto[:200] + '...' if len(texto) > 200 else texto}```",
                inline=False
            )
            
            await interaction.followup.send(embed=success_embed)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Erro ao Processar Texto",
                description=f"Ocorreu um erro:\n```{str(e)}```",
                color=0xff0000
            )
            await interaction.followup.send(embed=error_embed)
    
    @discord.app_commands.command(
        name="rag_search",
        description="🔍 Busca no conhecimento dos agentes"
    )
    @discord.app_commands.describe(
        consulta="Termo para buscar no conhecimento",
        limite="Número de resultados (máx: 10)"
    )
    async def rag_search(self, interaction: discord.Interaction, consulta: str, limite: int = 5):
        """Busca no conhecimento do RAG."""
        await interaction.response.defer()
        
        try:
            if not self.rag_system:
                embed = discord.Embed(
                    title="❌ Sistema RAG Indisponível",
                    description="O sistema RAG não está configurado.",
                    color=0xff0000
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Inicializar RAG se necessário
            if not self.rag_system._initialized:
                await self.rag_system.initialize()
            
            limite = max(1, min(limite, 10))  # Limitar entre 1 e 10
            
            # Buscar documentos
            results = await self.rag_system.search_documents(consulta, limite)
            
            if not results:
                embed = discord.Embed(
                    title="🔍 Busca no Conhecimento",
                    description=f"Nenhum resultado encontrado para: **{consulta}**",
                    color=0xffff00
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Criar embed com resultados
            embed = discord.Embed(
                title="🔍 Resultados da Busca",
                description=f"Encontrados **{len(results)}** resultados para: **{consulta}**",
                color=0x00ff00
            )
            
            for i, result in enumerate(results, 1):
                content = result['content'][:200] + "..." if len(result['content']) > 200 else result['content']
                source = result['source']
                relevance = result['relevance']
                
                embed.add_field(
                    name=f"📄 Resultado {i} (Relevância: {relevance:.2f})",
                    value=f"**Fonte:** {source}\n```{content}```",
                    inline=False
                )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Erro na Busca",
                description=f"Ocorreu um erro:\n```{str(e)}```",
                color=0xff0000
            )
            await interaction.followup.send(embed=error_embed)
    
    @discord.app_commands.command(
        name="rag_stats",
        description="📊 Mostra estatísticas do conhecimento dos agentes"
    )
    async def rag_stats(self, interaction: discord.Interaction):
        """Mostra estatísticas do RAG."""
        await interaction.response.defer()
        
        try:
            if not self.rag_system:
                embed = discord.Embed(
                    title="❌ Sistema RAG Indisponível",
                    description="O sistema RAG não está configurado.",
                    color=0xff0000
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Inicializar RAG se necessário
            if not self.rag_system._initialized:
                await self.rag_system.initialize()
            
            # Buscar estatísticas do banco
            async with self.rag_system.pool.acquire() as conn:
                # Contar documentos totais
                total_docs = await conn.fetchval("SELECT COUNT(*) FROM agenteia.documents")
                
                # Contar por fonte
                sources = await conn.fetch("""
                    SELECT source, COUNT(*) as count 
                    FROM agenteia.documents 
                    GROUP BY source 
                    ORDER BY count DESC 
                    LIMIT 10
                """)
                
                # Estatísticas gerais
                stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total_docs,
                        SUM(LENGTH(content)) as total_chars,
                        AVG(LENGTH(content)) as avg_chars,
                        MIN(created_at) as oldest,
                        MAX(created_at) as newest
                    FROM agenteia.documents
                """)
            
            embed = discord.Embed(
                title="📊 Estatísticas do Conhecimento",
                description="Informações sobre o conhecimento armazenado dos agentes",
                color=0x0099ff
            )
            
            embed.add_field(
                name="📈 Estatísticas Gerais",
                value=f"📄 **Total de documentos:** {stats['total_docs']}\n📊 **Total de caracteres:** {stats['total_chars']:,}\n📝 **Média de caracteres:** {int(stats['avg_chars']) if stats['avg_chars'] else 0}\n📅 **Mais antigo:** {stats['oldest'].strftime('%d/%m/%Y') if stats['oldest'] else 'N/A'}\n📅 **Mais recente:** {stats['newest'].strftime('%d/%m/%Y') if stats['newest'] else 'N/A'}",
                inline=False
            )
            
            if sources:
                sources_text = "\n".join([f"📁 **{source['source'][:30]}{'...' if len(source['source']) > 30 else ''}:** {source['count']}" for source in sources[:5]])
                embed.add_field(
                    name="📂 Top 5 Fontes",
                    value=sources_text,
                    inline=False
                )
            
            embed.add_field(
                name="🤖 Disponibilidade",
                value="Todo o conhecimento está disponível para ambos os agentes (ADK e LangChain)",
                inline=False
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Erro ao Obter Estatísticas",
                description=f"Ocorreu um erro:\n```{str(e)}```",
                color=0xff0000
            )
            await interaction.followup.send(embed=error_embed)

async def setup(bot):
    """Função para adicionar os comandos ao bot."""
    await bot.add_cog(RAGCommands(bot))