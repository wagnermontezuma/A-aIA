# example_working_adk.py
import asyncio
import os
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import google_search
from google.genai import types

async def working_adk_example():
    """
    Exemplo funcional baseado na documentação oficial do ADK.
    Este código resolve o bug de sessão usando apenas métodos assíncronos.
    """
    load_dotenv()

    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ Configure GOOGLE_API_KEY no arquivo .env")
        return

    # Configurações
    APP_NAME = "projeto_agentes_ia"
    USER_ID = "user123"
    SESSION_ID = "session_001"

    try:
        print("=== Exemplo ADK Funcional ===\n")

        # Criar o agente
        root_agent = Agent(
            name="basic_search_agent",
            model="gemini-2.0-flash-exp",
            description="Agent to answer questions using Google Search.",
            instruction="I can answer your questions by searching the internet. Just ask me anything!",
            tools=[google_search]
        )

        # Configurar serviços
        session_service = InMemorySessionService()

        # CORREÇÃO: Usar await para criar a sessão
        session = await session_service.create_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=SESSION_ID
        )

        runner = Runner(
            agent=root_agent,
            app_name=APP_NAME,
            session_service=session_service
        )

        print(f"✅ Sessão criada: {SESSION_ID}")

        # Função para chamar o agente
        async def call_agent(query):
            print(f"\n--- Pergunta: {query} ---")

            content = types.Content(
                role='user',
                parts=[types.Part(text=query)]
            )

            # CORREÇÃO: Usar run_async ao invés de run
            events_async = runner.run_async(
                user_id=USER_ID,
                session_id=SESSION_ID,
                new_message=content
            )

            final_response = ""
            async for event in events_async:
                if event.is_final_response():
                    if hasattr(event.content, 'parts') and hasattr(event.content.parts, 'text'):
                        final_response = event.content.parts.text
                        print(f"Resposta: {final_response}")
                        return final_response
                    elif hasattr(event.content, 'parts') and isinstance(event.content.parts, list):
                        for part in event.content.parts:
                            if hasattr(part, 'text'):
                                print(f"Resposta: {part.text}")
                                return part.text

            return "Não foi possível obter resposta"

        # Testar com algumas perguntas
        queries = [
            "Qual é a capital do Brasil?",
            "Quanto é 10 + 15?",
            "O que é inteligência artificial?"
        ]

        for query in queries:
            await call_agent(query)

        print("\n✅ Teste concluído com sucesso!")

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(working_adk_example())