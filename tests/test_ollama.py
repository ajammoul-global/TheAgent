# tests/test_ollama.py

import responses
from models.ollama import OllamaModel


@responses.activate
def test_ollama_generate_success():
    model = OllamaModel()

    # Mock endpoint
    responses.add(
        responses.POST,
        f"{model.get_info()['host']}/api/generate",
        json={"response": "Hello from Ollama"},
        status=200,
    )

    result = model.generate("Say hello")
    assert result == "Hello from Ollama"


@responses.activate
def test_ollama_generate_http_error():
    model = OllamaModel()

    responses.add(
        responses.POST,
        f"{model.get_info()['host']}/api/generate",
        json={"error": "bad request"},
        status=400,
    )

    try:
        model.generate("test")
    except RuntimeError:
        assert True
    else:
        assert False, "Should raise RuntimeError on HTTP error"


@responses.activate
def test_ollama_missing_response_field():
    model = OllamaModel()

    responses.add(
        responses.POST,
        f"{model.get_info()['host']}/api/generate",
        json={"not_response": "foo"},
        status=200,
    )

    try:
        model.generate("test")
    except Exception:
        assert True
    else:
        assert False, "Should raise ValueError for missing 'response'"
