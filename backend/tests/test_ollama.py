from unittest.mock import Mock

import pytest

from backend.app.config import Settings
from backend.app.integrations import ollama as integration


@pytest.mark.parametrize("host", ["", "http://model-server:11434"])
def test_generator_uses_configured_model_and_optional_host(monkeypatch, host):
    sdk = Mock()
    generator = sdk.Client.return_value.generate if host else sdk.generate
    generator.return_value = {"response": "An answer"}
    monkeypatch.setattr(integration, "ollama", sdk)
    result = integration.generate_completion("A prompt", Settings(model_name="test-model", ollama_host=host))
    assert result == {"response": "An answer"}
    generator.assert_called_once_with(
        model="test-model", prompt="A prompt",
        system="Answer recipe questions using the supplied recipe context. Be concise and factual.",
        options={"temperature": 0, "num_predict": 256},
    )
    if host:
        sdk.Client.assert_called_once_with(host=host)
        sdk.generate.assert_not_called()
    else:
        sdk.Client.assert_not_called()


def test_missing_sdk_raises_dependency_error(monkeypatch):
    monkeypatch.setattr(integration, "ollama", None)
    with pytest.raises(RuntimeError, match="ollama is not installed"):
        integration.generate_completion("A prompt", Settings())
