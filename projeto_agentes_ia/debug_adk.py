# debug_adk.py
import os
from dotenv import load_dotenv

def investigate_llm_agent():
    """Investiga os métodos e atributos disponíveis no LlmAgent."""
    try:
        from google.adk.agents import LlmAgent
        from google.adk.tools import google_search

        print("=== Investigação do LlmAgent ===\n")

        # Criar uma instância do LlmAgent
        agent = LlmAgent(
            model="gemini-2.0-flash-exp",
            name="debug_agent",
            description="Agente para debug",
            instruction="Você é um assistente útil.",
            tools=[google_search]
        )

        print("✅ LlmAgent criado com sucesso!")
        print(f"Tipo do objeto: {type(agent)}")
        print(f"Classe: {agent.__class__}")
        print()

        # Listar todos os métodos e atributos
        print("=== MÉTODOS E ATRIBUTOS DISPONÍVEIS ===")
        all_attributes = dir(agent)

        # Separar métodos públicos dos privados
        public_methods = [attr for attr in all_attributes if not attr.startswith('_')]
        private_methods = [attr for attr in all_attributes if attr.startswith('_') and not attr.startswith('__')]

        print("MÉTODOS PÚBLICOS:")
        for i, method in enumerate(public_methods, 1):
            attr_obj = getattr(agent, method)
            attr_type = "método" if callable(attr_obj) else "atributo"
            print(f"  {i:2d}. {method} ({attr_type})")

        print(f"\nMÉTODOS PRIVADOS: {len(private_methods)} encontrados")

        # Tentar identificar métodos que podem ser usados para executar
        print("\n=== MÉTODOS CANDIDATOS PARA EXECUÇÃO ===")
        execution_candidates = []
        for method_name in public_methods:
            method_obj = getattr(agent, method_name)
            if callable(method_obj):
                # Verificar se o nome sugere execução
                if any(keyword in method_name.lower() for keyword in
                       ['run', 'execute', 'process', 'generate', 'chat', 'send', 'ask', 'query', 'call']):
                    execution_candidates.append(method_name)

        if execution_candidates:
            print("Métodos que podem ser usados para execução:")
            for candidate in execution_candidates:
                print(f"  - {candidate}")
        else:
            print("Nenhum método óbvio de execução encontrado.")

        # Tentar obter informações sobre assinatura dos métodos
        print("\n=== ASSINATURAS DOS MÉTODOS CANDIDATOS ===")
        import inspect

        for candidate in execution_candidates[:3]:  # Limitar a 3 para não sobrecarregar
            try:
                method_obj = getattr(agent, candidate)
                signature = inspect.signature(method_obj)
                print(f"{candidate}{signature}")
            except Exception as e:
                print(f"{candidate}: Não foi possível obter assinatura - {e}")

        # Verificar se há documentação
        print(f"\n=== DOCUMENTAÇÃO DO OBJETO ===")
        if agent.__doc__:
            print("Documentação da classe:")
            print(agent.__doc__)
        else:
            print("Nenhuma documentação encontrada na classe.")

        return agent, execution_candidates

    except ImportError as e:
        print(f"❌ Erro ao importar: {e}")
        print("Verifique se o google-adk está instalado corretamente.")
        return None, []
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return None, []

def test_execution_methods(agent, candidates):
    """Testa os métodos candidatos com uma consulta simples."""
    if not agent or not candidates:
        print("Não há agente ou candidatos para testar.")
        return

    test_query = "Olá, como você está?"
    print(f"\n=== TESTANDO MÉTODOS COM A CONSULTA: '{test_query}' ===")

    for method_name in candidates:
        try:
            print(f"\n--- Testando {method_name} ---")
            method_obj = getattr(agent, method_name)

            # Tentar diferentes formas de chamar o método
            for attempt in [
                lambda: method_obj(test_query),
                lambda: method_obj(message=test_query),
                lambda: method_obj(input=test_query),
                lambda: method_obj(text=test_query)
            ]:
                try:
                    result = attempt()

                    # Processar diferentes tipos de resultado
                    if isinstance(result, dict):
                        return result.get("output", result.get("response", str(result)))
                    elif isinstance(result, str):
                        return result
                    else:
                        return str(result)

                except Exception as e:
                    continue  # Tentar próxima forma

            print(f"❌ Nenhum formato de chamada funcionou para {method_name}")

        except Exception as e:
            print(f"❌ Erro ao testar {method_name}: {e}")

if __name__ == "__main__":
    load_dotenv()

    # Verificar se a API key está configurada
    if not os.getenv("GOOGLE_API_KEY"):
        print("⚠️  GOOGLE_API_KEY não encontrada no .env")
        print("Continuando com a investigação (alguns testes podem falhar)...")

    # Investigar o LlmAgent
    agent, candidates = investigate_llm_agent()

    # Testar métodos candidatos
    if agent and candidates:
        test_execution_methods(agent, candidates)

    print("\n=== INVESTIGAÇÃO CONCLUÍDA ===")
    print("Use as informações acima para corrigir a implementação do SimpleADKAgent.")