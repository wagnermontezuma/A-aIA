# tests/test_conversational_agent.py
import pytest
from agents.conversational_adk_agent import ConversationalADKAgent

def test_conversational_agent_initialization():
    """Testa se o agente conversacional é inicializado corretamente."""
    agent = ConversationalADKAgent()
    assert agent.name == "ConversationalAgent"
    assert len(agent.conversation_history) == 0

def test_conversation_context_management(mocker):
    """Testa o gerenciamento de contexto da conversa."""
    # Mock do LlmAgent
    mock_llm_agent = mocker.patch('google.adk.agents.LlmAgent')
    mock_instance = mock_llm_agent.return_value
    mock_instance.invoke.return_value = {"output": "Resposta de teste"}

    agent = ConversationalADKAgent()

    # Primeira pergunta
    result1 = agent.run("Qual é a capital do Brasil?")
    assert len(agent.conversation_history) == 1

    # Segunda pergunta com contexto
    result2 = agent.run("E qual é a população dessa cidade?")
    assert len(agent.conversation_history) == 2

    # Verifica se o contexto foi incluído na segunda chamada
    call_args = mock_instance.invoke.call_args_list[1]
    assert "CONTEXTO DA CONVERSA ANTERIOR" in call_args

def test_conversation_reset():
    """Testa a funcionalidade de reset da conversa."""
    agent = ConversationalADKAgent()
    agent.conversation_history = [{"query": "teste", "response": "resposta"}]

    agent.reset_conversation()
    assert len(agent.conversation_history) == 0