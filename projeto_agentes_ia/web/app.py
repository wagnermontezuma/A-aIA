# web/app.py - Versão corrigida com logger configurado
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import asyncio
import sys
import os
import logging
import traceback
from pathlib import Path

# CONFIGURAÇÃO DO LOGGER - ADICIONAR NO INÍCIO
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Adicionar o diretório pai ao path para importar os agentes
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.append(str(project_root))

from agents.agent_manager import AgentManager
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Inicializar FastAPI
app = FastAPI(
    title="Projeto Agentes IA - Interface Multi-Agente",
    description="Interface web para interação com múltiplos agentes de IA (ADK e LangChain)",
    version="2.0.0"
)

# Configurar caminhos e templates
static_dir = current_dir / "static"
templates_dir = current_dir / "templates"

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
templates = Jinja2Templates(directory=str(templates_dir))

# Inicializar o gerenciador de agentes
agent_manager = None

@app.on_event("startup")
async def startup_event():
    """Inicializa o gerenciador de agentes quando a aplicação inicia."""
    global agent_manager
    
    # Verificar se as API keys estão configuradas
    missing_keys = []
    if not os.getenv("GOOGLE_API_KEY"):
        missing_keys.append("GOOGLE_API_KEY")
    if not os.getenv("OPENAI_API_KEY"):
        missing_keys.append("OPENAI_API_KEY")
    
    if missing_keys:
        logger.warning(f"API keys não encontradas: {', '.join(missing_keys)}")
        print(f"⚠️  AVISO: As seguintes API keys não foram encontradas: {', '.join(missing_keys)}")
        print("Configure no arquivo .env para usar todos os agentes")
    
    try:
        agent_manager = AgentManager()
        logger.info("Gerenciador de agentes inicializado com sucesso")
        print("✅ Gerenciador de agentes inicializado com sucesso")
    except Exception as e:
        logger.error(f"Erro ao inicializar gerenciador de agentes: {e}")
        print(f"❌ Erro ao inicializar gerenciador de agentes: {e}")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Página principal da aplicação."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/chat")
async def chat_endpoint(
    query: str = Form(...),
    user_id: str = Form(default="web_user"),
    session_id: str = Form(default=None)
):
    """Endpoint para processar mensagens do chat com contexto de usuário."""
    global agent_manager
    
    logger.info(f"Recebida consulta: {query[:50]}... de usuário: {user_id}")
    
    if not agent_manager:
        logger.error("Agent manager não disponível")
        raise HTTPException(
            status_code=503, 
            detail="Gerenciador de agentes não está disponível."
        )
    
    if not query.strip():
        logger.error("Query vazia recebida")
        raise HTTPException(status_code=400, detail="Pergunta não pode estar vazia.")
    
    try:
        # Definir contexto do usuário
        if not session_id:
            session_id = f"web_session_{user_id}_{hash(user_id) % 10000}"
        
        logger.info(f"Definindo contexto: user_id={user_id}, session_id={session_id}")
        agent_manager.set_user_context(user_id, session_id)
        
        # Verificar se o método existe
        if hasattr(agent_manager, 'run_current_agent_with_context'):
            logger.info("Usando run_current_agent_with_context")
            response = await agent_manager.run_current_agent_with_context(
                query.strip(), user_id, session_id
            )
        else:
            logger.info("Usando run_current_agent (fallback)")
            response = await agent_manager.run_current_agent(query.strip())
        
        logger.info(f"Resposta gerada com sucesso: {len(response)} caracteres")
        
        return JSONResponse({
            "success": True,
            "query": query,
            "response": response,
            "agent": agent_manager.current_agent,
            "agent_name": agent_manager.get_current_agent().name if agent_manager.get_current_agent() else "Desconhecido",
            "user_id": user_id,
            "session_id": session_id
        })
        
    except Exception as e:
        logger.error(f"Erro no chat endpoint: {str(e)}")
        logger.error(f"Traceback completo: {traceback.format_exc()}")
        
        return JSONResponse({
            "success": False,
            "error": f"Erro ao processar consulta: {str(e)}"
        }, status_code=500)

@app.post("/switch-agent")
async def switch_agent(agent_type: str = Form(...)):
    """Endpoint para trocar o agente ativo."""
    global agent_manager
    
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Gerenciador de agentes não disponível.")
    
    success = agent_manager.set_agent(agent_type)
    
    if success:
        logger.info(f"Agente alterado para: {agent_type}")
        return JSONResponse({
            "success": True,
            "message": f"Agente alterado para {agent_type}",
            "current_agent": agent_manager.current_agent,
            "agent_info": agent_manager.get_agent_info()
        })
    else:
        logger.error(f"Falha ao alterar para agente: {agent_type}")
        return JSONResponse({
            "success": False,
            "error": f"Agente '{agent_type}' não disponível"
        }, status_code=400)

@app.post("/add-knowledge")
async def add_knowledge_endpoint(
    content: str = Form(...),
    source: str = Form(default="user"),
    user_id: str = Form(default="web_user")
):
    """Endpoint para adicionar conhecimento ao sistema RAG."""
    global agent_manager
    
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Gerenciador de agentes não disponível.")
    
    try:
        # Definir contexto do usuário
        agent_manager.set_user_context(user_id)
        
        # Adicionar conhecimento
        if hasattr(agent_manager, 'add_knowledge_to_current_agent'):
            doc_id = agent_manager.add_knowledge_to_current_agent(
                content=content.strip(),
                source=source,
                metadata={"added_via": "web_interface", "user_id": user_id}
            )
            
            logger.info(f"Conhecimento adicionado: {doc_id}")
            
            return JSONResponse({
                "success": True,
                "message": "Conhecimento adicionado com sucesso",
                "doc_id": doc_id,
                "content_preview": content[:100] + "..." if len(content) > 100 else content
            })
        else:
            return JSONResponse({
                "success": False,
                "error": "Funcionalidade de adicionar conhecimento não disponível"
            }, status_code=501)
        
    except Exception as e:
        logger.error(f"Erro ao adicionar conhecimento: {e}")
        return JSONResponse({
            "success": False,
            "error": f"Erro ao adicionar conhecimento: {str(e)}"
        }, status_code=500)

@app.get("/health")
async def health_check():
    """Endpoint para verificar a saúde da aplicação."""
    global agent_manager
    
    return {
        "status": "healthy",
        "agent_manager_available": agent_manager is not None,
        "current_agent": agent_manager.current_agent if agent_manager else None,
        "api_keys_status": {
            "google_api_key": bool(os.getenv("GOOGLE_API_KEY")),
            "openai_api_key": bool(os.getenv("OPENAI_API_KEY")),
            "tavily_api_key": bool(os.getenv("TAVILY_API_KEY"))
        }
    }

@app.get("/api/agents-info")
async def agents_info():
    """Retorna informações sobre todos os agentes disponíveis."""
    global agent_manager
    
    if not agent_manager:
        return {"available": False, "message": "Gerenciador de agentes não inicializado"}
    
    return {
        "available": True,
        **agent_manager.get_agent_info()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)