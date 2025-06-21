# check_bot_setup.py
import os
from dotenv import load_dotenv
import requests

def check_bot_setup():
    """Verifica a configuração do bot Discord."""
    load_dotenv(dotenv_path='projeto_agentes_ia/.env')
    
    print("=== Verificação da Configuração do Bot ===\n")
    
    # Verificar token
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        print("❌ DISCORD_BOT_TOKEN não encontrado")
        return
    
    print("✅ Token encontrado")
    
    # Verificar se o token é válido
    headers = {"Authorization": f"Bot {token}"}
    
    try:
        response = requests.get(
            "https://discord.com/api/v10/users/@me",
            headers=headers
        )
        
        if response.status_code == 200:
            bot_info = response.json()
            print(f"✅ Bot válido: {bot_info['username']}#{bot_info['discriminator']}")
            print(f"🆔 ID: {bot_info['id']}")
            
            # Gerar link de convite
            bot_id = bot_info['id']
            invite_url = f"https://discord.com/api/oauth2/authorize?client_id={bot_id}&permissions=2147483648&scope=bot%20applications.commands"
            
            print(f"\n🔗 LINK DE CONVITE DO BOT:")
            print(f"{invite_url}")
            print("\n📋 INSTRUÇÕES:")
            print("1. Copie o link acima")
            print("2. Cole no seu navegador")
            print("3. Selecione o servidor onde quer adicionar o bot")
            print("4. Clique em 'Autorizar'")
            print("5. Reinicie o bot após adicionar ao servidor")
            
        else:
            print(f"❌ Token inválido: {response.status_code}")
            return
            
    except Exception as e:
        print(f"❌ Erro ao verificar token: {e}")
        return
    
    # Verificar guilds
    try:
        response = requests.get(
            "https://discord.com/api/v10/users/@me/guilds",
            headers=headers
        )
        
        if response.status_code == 200:
            guilds = response.json()
            if guilds:
                print(f"\n📊 Bot já está em {len(guilds)} servidor(es):")
                for guild in guilds:
                    print(f"   ✅ {guild['name']} (ID: {guild['id']})")
            else:
                print(f"\n⚠️ Bot não está em nenhum servidor ainda!")
                print("Use o link de convite acima para adicionar a um servidor.")
        else:
            print(f"⚠️ Não foi possível listar servidores: {response.status_code}")
            
    except Exception as e:
        print(f"⚠️ Erro ao listar servidores: {e}")

if __name__ == "__main__":
    check_bot_setup()