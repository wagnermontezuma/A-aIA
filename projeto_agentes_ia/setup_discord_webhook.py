# setup_discord_webhook.py
import os
from dotenv import load_dotenv

def setup_webhook_instructions():
    """Mostra instruções para configurar webhook do Discord."""
    print("🔧 Configuração do Webhook do Discord")
    print("=" * 50)
    print()
    print("📋 Passos para criar o webhook:")
    print("1. Vá para o seu servidor Discord")
    print("2. Clique com botão direito no canal onde quer receber alertas")
    print("3. Selecione 'Editar Canal'")
    print("4. Vá para a aba 'Integrações'")
    print("5. Clique em 'Criar Webhook'")
    print("6. Dê um nome (ex: 'Log Monitor')")
    print("7. Copie a URL do webhook")
    print("8. Adicione no arquivo .env:")
    print("   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...")
    print()

    # Verificar se já está configurado
    load_dotenv()
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

    if webhook_url:
        print("✅ Webhook já configurado!")
        print(f"🔗 URL: {webhook_url[:50]}...")
    else:
        print("⚠️ Webhook não configurado ainda")
        print("Configure no arquivo .env para receber alertas")

if __name__ == "__main__":
    setup_webhook_instructions()