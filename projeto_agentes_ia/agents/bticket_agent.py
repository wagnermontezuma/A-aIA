from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.adk.tools import google_search
from google.genai import types
from .base_agent import BaseAgent
import asyncio
import os
import sys
import json
import re
from pathlib import Path
from typing import Dict, Optional

# Adicionar o diretório raiz ao sys.path para importação do cliente
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.append(str(project_root))

from integrations.bticket_client import BTicketClient
from memory.memory_manager import MemoryManager

class BTicketAgent(BaseAgent):
    """
    Agente especializado em gerenciamento de tickets B-Ticket, alinhado com a documentação oficial da API.
    """
    
    def __init__(self, instruction: str = None, use_memory: bool = True):
        super().__init__(name="BTicketAgent")
        
        # Cliente B-Ticket
        self.bticket_client = BTicketClient(
            base_url=os.getenv("BTICKET_API_URL", "https://api.bticket.com/v1"),
            api_key=os.getenv("BTICKET_API_KEY")
        )
        
        # Gerenciador de memória (opcional)
        self.memory_manager = MemoryManager() if use_memory else None
        
        # Configurar o agente ADK
        self._setup_adk_agent(instruction)
        
        # Padrões de comando para B-Ticket
        self._setup_command_patterns()

    def _setup_adk_agent(self, instruction: str):
        """Configura o agente ADK com instruções e ferramentas."""
        base_instruction = """
        Você é um especialista em gerenciamento de tickets usando o sistema B-Ticket.
        
        SUAS CAPACIDADES:
        1.  Gerenciamento de Tickets (CRUD: criar, listar, ver, atualizar, deletar)
        2.  Gerenciamento de Usuários (CRUD)
        3.  Gerenciamento de Departamentos (CRUD)
        4.  Gerenciamento de Status de Tickets (CRUD)
        5.  Gerenciamento de Prioridades de Tickets (CRUD)
        
        COMANDOS DISPONÍVEIS:
        - "listar tickets" - Lista todos os tickets.
        - "ticket [ID]" - Mostra detalhes de um ticket.
        - "criar ticket [título] para [departamento] com prioridade [prioridade] e usuário [ID do usuário]" - Cria um novo ticket.
        - "deletar ticket [ID]" - Remove um ticket.
        - "listar usuários" - Lista todos os usuários.
        - "listar departamentos" - Lista todos os departamentos.
        - "listar status" - Lista todos os status.
        - "listar prioridades" - Lista todas as prioridades.
        
        Sempre que possível, use os comandos para interagir com o B-Ticket.
        Para outras perguntas, use seu conhecimento geral.
        {instruction}
        """
        
        final_instruction = base_instruction.format(
            instruction=instruction or "Ajude com eficiência no gerenciamento de tickets."
        )
        
        self.agent = Agent(
            name="bticket_agent",
            model="gemini-2.0-flash-exp",
            description="Agente especializado em gerenciamento de tickets B-Ticket",
            instruction=final_instruction,
            tools=[google_search]
        )
        
        self.app_name = "bticket_management_system"
        self.user_id = "bticket_user"
        self.session_service = InMemorySessionService()
        self.runner = Runner(
            agent=self.agent,
            app_name=self.app_name,
            session_service=self.session_service
        )

    def _setup_command_patterns(self):
        """Configura os padrões de regex para os comandos."""
        self.command_patterns = {
            'list_tickets': r'listar tickets?',
            'get_ticket': r'ticket (\d+)',
            'create_ticket': r'criar ticket (.+?) para (.+?) com prioridade (.+?) e usuário (\d+)',
            'delete_ticket': r'deletar ticket (\d+)',
            'list_users': r'listar usuários',
            'get_user': r'usuário (\d+)',
            'list_departments': r'listar departamentos',
            'list_status': r'listar status',
            'list_priorities': r'listar prioridades',
        }

    async def _parse_command(self, query: str) -> Dict:
        """Analisa a consulta do usuário para identificar um comando B-Ticket."""
        query_lower = query.lower().strip()
        
        for command, pattern in self.command_patterns.items():
            match = re.search(pattern, query_lower)
            if match:
                return {
                    'command': command,
                    'match': match,
                    'groups': match.groups() if match.groups() else []
                }
        
        return {'command': 'general', 'match': None, 'groups': []}

    async def _execute_bticket_command(self, command_info: Dict, original_query: str) -> str:
        """Executa um comando específico do B-Ticket."""
        command = command_info['command']
        groups = command_info['groups']
        
        async with self.bticket_client as client:
            try:
                if command == 'list_tickets':
                    result = await client.list_tickets()
                    return self._format_list(result, "Tickets")
                
                elif command == 'get_ticket':
                    ticket_id = int(groups[0])
                    result = await client.get_ticket(ticket_id)
                    return self._format_item(result, "Ticket")

                elif command == 'create_ticket':
                    title, department_name, priority_name, user_id = groups
                    department_id = await self._get_id_by_name(client.list_departments, department_name.strip())
                    priority_id = await self._get_id_by_name(client.list_priorities, priority_name.strip())

                    if not department_id or not priority_id:
                        return "❌ Departamento ou Prioridade não encontrados."

                    result = await client.create_ticket(title.strip(), "Descrição a ser preenchida", department_id, priority_id, int(user_id))
                    return f"✅ Ticket criado com sucesso: {result}"

                elif command == 'delete_ticket':
                    ticket_id = int(groups[0])
                    await client.delete_ticket(ticket_id)
                    return f"✅ Ticket #{ticket_id} deletado com sucesso!"

                elif command == 'list_users':
                    result = await client.list_users()
                    return self._format_list(result, "Usuários")

                elif command == 'get_user':
                    user_id = int(groups[0])
                    result = await client.get_user(user_id)
                    return self._format_item(result, "Usuário")

                elif command == 'list_departments':
                    result = await client.list_departments()
                    return self._format_list(result, "Departamentos")

                elif command == 'list_status':
                    result = await client.list_status()
                    return self._format_list(result, "Status")

                elif command == 'list_priorities':
                    result = await client.list_priorities()
                    return self._format_list(result, "Prioridades")

            except Exception as e:
                return f"❌ Erro ao executar comando B-Ticket: {e}"
        
        return "Comando não implementado."

    async def _get_id_by_name(self, list_func, name: str) -> Optional[int]:
        """Obtém o ID de um recurso pelo nome."""
        try:
            result = await list_func()
            items = result.get('data', [])
            for item in items:
                if name.lower() in item.get('name', '').lower():
                    return item.get('id')
        except Exception as e:
            print(f"Erro ao buscar ID por nome: {e}")
        return None

    def _format_list(self, result: Dict, title: str) -> str:
        """Formata uma lista de itens."""
        items = result.get('data', [])
        if not items:
            return f"Nenhum item encontrado para {title}."
        
        response = f"**Lista de {title}:**\n\n"
        for item in items:
            response += f"- ID: {item.get('id')}, Nome: {item.get('name', item.get('title', 'N/A'))}\n"
        return response

    def _format_item(self, result: Dict, title: str) -> str:
        """Formata os detalhes de um item."""
        item = result.get('data', result)
        if not item:
            return f"{title} não encontrado."

        response = f"**Detalhes de {title} #{item.get('id')}:**\n\n"
        for key, value in item.items():
            response += f"- **{key.replace('_', ' ').capitalize()}:** {value}\n"
        return response

    async def _run_async(self, query: str) -> str:
        """Método assíncrono principal do agente."""
        try:
            print(f"[{self.name}] Processando consulta B-Ticket: '{query[:50]}...'\n")
            
            command_info = await self._parse_command(query)
            
            if command_info['command'] != 'general':
                return await self._execute_bticket_command(command_info, query)
            
            session_id = f"bticket_session_{abs(hash(query)) % 10000}"
            
            session = await self.session_service.create_session(
                app_name=self.app_name,
                user_id=self.user_id,
                session_id=session_id
            )
            
            events_async = self.runner.run(session=session, request=query)
            final_response = ""
            
            async for event in events_async:
                if event.is_final_response():
                    if hasattr(event, 'content') and event.content:
                        if hasattr(event.content, 'parts'):
                            if hasattr(event.content.parts, 'text'):
                                final_response = event.content.parts.text
                            elif isinstance(event.content.parts, list):
                                for part in event.content.parts:
                                    if hasattr(part, 'text') and part.text:
                                        final_response += part.text
                    break
            
            if not final_response:
                final_response = "Não foi possível processar sua consulta sobre B-Ticket."
            
            if self.memory_manager:
                self.memory_manager.save_interaction(
                    user_id=self.user_id,
                    session_id=session_id,
                    user_input=query,
                    agent_output=final_response
                )
            
            return final_response

        except Exception as e:
            print(f"Erro fatal no agente B-Ticket: {e}")
            return f"❌ Ocorreu um erro inesperado ao processar sua solicitação: {e}"

    def run(self, query: str):
        """Método síncrono para conveniência (executa o assíncrono)."""
        return asyncio.run(self._run_async(query))