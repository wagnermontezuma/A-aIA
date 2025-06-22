# tests/test_agents.py
import pytest
from unittest.mock import Mock, patch
from agents.adk_agent import SimpleADKAgent

def test_simple_adk_agent_initialization():
    """Testa se o SimpleADKAgent é inicializado corretamente."""
    with patch('google.adk.agents.LlmAgent'), \
         patch('google.adk.sessions.InMemorySessionService'), \
         patch('google.adk.runners.Runner'):

        agent = SimpleADKAgent(instruction="Teste")
        assert agent.name == "SimpleADKAgent"
        assert agent.app_name == "projeto_agentes_ia"
        assert agent.user_id == "test_user"

def test_simple_adk_agent_run_success(mocker):
    """Testa execução bem-sucedida do agente."""
    # Mock dos componentes do ADK
    mock_session_service = mocker.patch('google.adk.sessions.InMemorySessionService')
    mock_runner = mocker.patch('google.adk.runners.Runner')
    mock_llm_agent = mocker.patch('google.adk.agents.LlmAgent')

    # Configurar mocks
    mock_session = Mock()
    mock_session_service.return_value.create_session.return_value = mock_session

    # Mock do evento de resposta
    mock_event = Mock()
    mock_event.is_final_response.return_value = True
    mock_event.content = Mock()
    mock_event.content.parts = Mock()
    mock_event.content.parts.text = "Resposta de teste"

    mock_runner.return_value.run.return_value = [mock_event]

    # Testar o agente
    agent = SimpleADKAgent(instruction="Teste")
    result = agent.run("Pergunta de teste")

    # Verificações
    assert result == "Resposta de teste"
    mock_runner.return_value.run.assert_called_once()

def test_simple_adk_agent_run_error_handling(mocker):
    """Testa tratamento de erros do agente."""
    # Mock que gera exceção
    mocker.patch('google.adk.agents.LlmAgent')
    mocker.patch('google.adk.sessions.InMemorySessionService')
    mock_runner = mocker.patch('google.adk.runners.Runner')

    mock_runner.return_value.run.side_effect = Exception("Erro de teste")

    agent = SimpleADKAgent(instruction="Teste")
    result = agent.run("Pergunta de teste")

    assert "Erro ao executar agente" in result
    assert "Erro de teste" in result