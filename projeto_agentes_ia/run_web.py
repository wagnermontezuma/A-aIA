# run_web.py
import uvicorn
import os
from dotenv import load_dotenv

def main():
    """Inicia o servidor web da aplicação."""
    load_dotenv()
    
    # Verificar se a API key está configurada
    if not os.getenv("GOOGLE_API_KEY"):
        print("⚠️  AVISO: GOOGLE_API_KEY não encontrada no arquivo .env")
        print("Configure sua chave de API do Google para usar o agente.")
        print("Exemplo no arquivo .env:")
        print("GOOGLE_API_KEY=sua_chave_aqui")
        print()
    
    print("🚀 Iniciando servidor web...")
    print("📱 Interface disponível em: http://127.0.0.1:8000")
    print("📊 Documentação da API: http://127.0.0.1:8000/docs")
    print("🔧 Para parar o servidor: Ctrl+C")
    print()
    
    # Iniciar o servidor
    uvicorn.run(
        "web.app:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()