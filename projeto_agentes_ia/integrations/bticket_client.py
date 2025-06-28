import aiohttp
import asyncio
import json
import os
from typing import Dict, List, Optional, Any

class BTicketClient:
    """
    Cliente assíncrono para interagir com a API B-Ticket, alinhado com a documentação oficial.
    """
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Abrir sessão HTTP."""
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Fechar sessão HTTP."""
        if self.session:
            await self.session.close()
    
    async def _make_request(self, method: str, endpoint: str, data: Dict = None, params: Dict = None) -> Dict:
        """Faz requisição HTTP para a API."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        if not self.session:
            self.session = aiohttp.ClientSession(headers=self.headers)
        
        try:
            async with self.session.request(
                method=method,
                url=url,
                json=data if data else None,
                params=params if params else None,
                timeout=30
            ) as response:
                response_text = await response.text()
                try:
                    response_json = json.loads(response_text)
                except json.JSONDecodeError:
                    response_json = {"error": "Invalid JSON response", "details": response_text}
                
                response.raise_for_status() # Levanta exceção para status HTTP 4xx/5xx
                return response_json
        except aiohttp.ClientError as e:
            print(f"Erro na requisição para {url}: {e}")
            raise
        except asyncio.TimeoutError:
            print(f"Timeout na requisição para {url}")
            raise

    # ============ AUTH ============

    async def login(self, email: str, password: str) -> Dict:
        """Realiza o login de um usuário e retorna um token de autenticação."""
        data = {"email": email, "password": password}
        # Este endpoint pode precisar de um header diferente, mas vamos manter o padrão por enquanto
        return await self._make_request("POST", "/login", data=data)

    # ============ USERS ============
    
    async def list_users(self) -> Dict:
        """Retorna uma lista de todos os usuários."""
        return await self._make_request("GET", "/users")

    async def create_user(self, name: str, email: str, password: str) -> Dict:
        """Cria um novo usuário."""
        data = {"name": name, "email": email, "password": password}
        return await self._make_request("POST", "/users", data=data)

    async def get_user(self, user_id: int) -> Dict:
        """Busca um usuário específico pelo seu ID."""
        return await self._make_request("GET", f"/users/{user_id}")

    async def update_user(self, user_id: int, **kwargs) -> Dict:
        """Atualiza os dados de um usuário específico."""
        return await self._make_request("PUT", f"/users/{user_id}", data=kwargs)

    async def delete_user(self, user_id: int) -> Dict:
        """Remove um usuário específico."""
        return await self._make_request("DELETE", f"/users/{user_id}")

    # ============ TICKETS ============
    
    async def list_tickets(self) -> Dict:
        """Retorna uma lista de todos os tickets."""
        return await self._make_request("GET", "/tickets")

    async def create_ticket(self, title: str, description: str, department_id: int, priority_id: int, user_id: int) -> Dict:
        """Cria um novo ticket."""
        data = {
            "title": title,
            "description": description,
            "department_id": department_id,
            "priority_id": priority_id,
            "user_id": user_id
        }
        return await self._make_request("POST", "/tickets", data=data)

    async def get_ticket(self, ticket_id: int) -> Dict:
        """Busca um ticket específico pelo seu ID."""
        return await self._make_request("GET", f"/tickets/{ticket_id}")

    async def update_ticket(self, ticket_id: int, **kwargs) -> Dict:
        """Atualiza os dados de um ticket específico."""
        return await self._make_request("PUT", f"/tickets/{ticket_id}", data=kwargs)

    async def delete_ticket(self, ticket_id: int) -> Dict:
        """Remove um ticket específico."""
        return await self._make_request("DELETE", f"/tickets/{ticket_id}")

    # ============ DEPARTMENTS ============

    async def list_departments(self) -> Dict:
        """Retorna uma lista de todos os departamentos."""
        return await self._make_request("GET", "/departments")

    async def create_department(self, name: str) -> Dict:
        """Cria um novo departamento."""
        data = {"name": name}
        return await self._make_request("POST", "/departments", data=data)

    async def get_department(self, department_id: int) -> Dict:
        """Busca um departamento específico pelo seu ID."""
        return await self._make_request("GET", f"/departments/{department_id}")

    async def update_department(self, department_id: int, name: str) -> Dict:
        """Atualiza um departamento específico."""
        data = {"name": name}
        return await self._make_request("PUT", f"/departments/{department_id}", data=data)

    async def delete_department(self, department_id: int) -> Dict:
        """Remove um departamento específico."""
        return await self._make_request("DELETE", f"/departments/{department_id}")

    # ============ STATUS ============

    async def list_status(self) -> Dict:
        """Retorna uma lista de todos os status de ticket disponíveis."""
        return await self._make_request("GET", "/status")

    async def create_status(self, name: str) -> Dict:
        """Cria um novo tipo de status."""
        data = {"name": name}
        return await self._make_request("POST", "/status", data=data)

    async def get_status(self, status_id: int) -> Dict:
        """Busca um status específico pelo seu ID."""
        return await self._make_request("GET", f"/status/{status_id}")

    async def update_status(self, status_id: int, name: str) -> Dict:
        """Atualiza um status específico."""
        data = {"name": name}
        return await self._make_request("PUT", f"/status/{status_id}", data=data)

    async def delete_status(self, status_id: int) -> Dict:
        """Remove um status específico."""
        return await self._make_request("DELETE", f"/status/{status_id}")

    # ============ PRIORITIES ============

    async def list_priorities(self) -> Dict:
        """Retorna uma lista de todas as prioridades de ticket."""
        return await self._make_request("GET", "/priorities")

    async def create_priority(self, name: str) -> Dict:
        """Cria um novo tipo de prioridade."""
        data = {"name": name}
        return await self._make_request("POST", "/priorities", data=data)

    async def get_priority(self, priority_id: int) -> Dict:
        """Busca uma prioridade específica pelo seu ID."""
        return await self._make_request("GET", f"/priorities/{priority_id}")

    async def update_priority(self, priority_id: int, name: str) -> Dict:
        """Atualiza uma prioridade específica."""
        data = {"name": name}
        return await self._make_request("PUT", f"/priorities/{priority_id}", data=data)

    async def delete_priority(self, priority_id: int) -> Dict:
        """Remove uma prioridade específica."""
        return await self._make_request("DELETE", f"/priorities/{priority_id}")