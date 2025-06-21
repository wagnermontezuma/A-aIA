# test_chat_quick.py
import requests
import time

def test_chat_endpoint():
    """Testa o endpoint de chat rapidamente."""
    print("=== Teste Rápido do Endpoint de Chat ===\n")
    
    base_url = "http://127.0.0.1:8000"
    
    # Testar se o servidor está rodando
    try:
        health_response = requests.get(f"{base_url}/health", timeout=5)
        print(f"✅ Servidor respondendo: {health_response.status_code}")
        print(f"Status: {health_response.json()}")
    except Exception as e:
        print(f"❌ Servidor não está respondendo: {e}")
        return
    
    # Testar o endpoint de chat
    try:
        chat_data = {
            "query": "Olá, como você está?",
            "user_id": "test_user",
            "session_id": "test_session"
        }
        
        print(f"\n🤖 Enviando mensagem: '{chat_data['query']}'")
        
        chat_response = requests.post(
            f"{base_url}/chat", 
            data=chat_data,
            timeout=30
        )
        
        print(f"Status da resposta: {chat_response.status_code}")
        
        if chat_response.status_code == 200:
            result = chat_response.json()
            print("✅ Chat funcionando!")
            print(f"Agente usado: {result.get('agent', 'N/A')}")
            print(f"Resposta: {result.get('response', 'N/A')[:100]}...")
        else:
            print(f"❌ Erro no chat: {chat_response.status_code}")
            print(f"Resposta: {chat_response.text}")
            
    except Exception as e:
        print(f"❌ Erro ao testar chat: {e}")

if __name__ == "__main__":
    print("Aguardando 2 segundos para o servidor inicializar...")
    time.sleep(2)
    test_chat_endpoint()