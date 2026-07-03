import pytest

from src.agentic_layer.config.settings import BASE_SERVERS, DEFAULT_SERVERS, get_server_config
from src.agentic_layer.exceptions import UnknownServerKeyError


def test_protected_server_registered_when_auth_enabled(monkeypatch):
    monkeypatch.setenv("FHIR_USE_AUTH", "true")
    monkeypatch.setenv("FHIR_SERVER_BASE", "https://fhir.example.com/R4")
    monkeypatch.delenv("FHIR_DEFAULT_SERVER_KEY", raising=False)

    config = get_server_config("protected")

    assert config.key == "protected"
    assert config.requires_auth is True
    assert config.base_url == "https://fhir.example.com/R4"


def test_public_server_does_not_require_auth(monkeypatch):
    monkeypatch.setenv("FHIR_USE_AUTH", "false")
    config = get_server_config("hapi")
    assert config.requires_auth is False
    assert config.auth_token is None


def test_unknown_server_key_raises(monkeypatch):
    monkeypatch.setenv("FHIR_USE_AUTH", "false")
    with pytest.raises(UnknownServerKeyError):
        get_server_config("not-a-real-server")


def test_mockhealth_server_requires_auth(monkeypatch):
    monkeypatch.delenv("MOCK_HEALTH_API_KEY", raising=False)
    monkeypatch.setenv("FHIR_USE_AUTH", "false")
    config = get_server_config("mockhealth")
    assert config.key == "mockhealth"
    assert config.requires_auth is True
    assert config.base_url == "https://api.mock.health/fhir"
    assert config.auth_token is None


def test_mockhealth_server_loads_api_key_from_env(monkeypatch):
    monkeypatch.setenv("MOCK_HEALTH_API_KEY", "sk_test_example_key")
    monkeypatch.setenv("FHIR_USE_AUTH", "false")
    config = get_server_config("mockhealth")
    assert config.auth_token == "sk_test_example_key"


def test_mockhealth_auth_headers_use_server_key(monkeypatch):
    from src.agentic_layer.config.settings import get_auth_headers

    monkeypatch.setenv("MOCK_HEALTH_API_KEY", "sk_test_example_key")
    monkeypatch.setenv("FHIR_USE_AUTH", "false")
    config = get_server_config("mockhealth")
    headers = get_auth_headers(config)
    assert headers == {"Authorization": "Bearer sk_test_example_key"}


def test_firely_public_server_config(monkeypatch):
    monkeypatch.setenv("FHIR_USE_AUTH", "false")
    config = get_server_config("firely")
    assert config.key == "firely"
    assert config.requires_auth is False
    assert config.base_url == "https://server.fire.ly/R4"


def test_notebook_demo_servers_are_registered(monkeypatch):
    """Notebook demo uses hapi, firely, mockhealth — all must be in BASE_SERVERS."""
    monkeypatch.setenv("FHIR_USE_AUTH", "false")
    demo_keys = {"hapi", "firely", "mockhealth"}
    assert demo_keys.issubset(BASE_SERVERS.keys())
    assert DEFAULT_SERVERS["mockhealth"]["requires_auth"] is True
    assert DEFAULT_SERVERS["mockhealth"]["auth_token_env"] == "MOCK_HEALTH_API_KEY"


def test_get_settings_reads_environment(monkeypatch):
    from src.agentic_layer.config.settings import get_settings

    monkeypatch.setenv("FHIR_DEFAULT_SERVER_KEY", "firely")
    monkeypatch.setenv("FHIR_USE_AUTH", "true")
    monkeypatch.setenv("FHIR_AUTH_TYPE", "oauth2")
    monkeypatch.setenv("FHIR_AUTH_TOKEN", "token-123")

    settings = get_settings()
    assert settings["default_server_key"] == "firely"
    assert settings["use_auth"] is True
    assert settings["auth_type"] == "oauth2"
    assert settings["auth_token"] == "token-123"


def test_get_auth_provider_disabled_when_use_auth_false(monkeypatch):
    from src.agentic_layer.config import settings as settings_module

    monkeypatch.setenv("FHIR_USE_AUTH", "false")
    settings_module._auth_provider_cache = None
    assert settings_module.get_auth_provider() is None


def test_get_auth_headers_uses_global_provider_when_configured(monkeypatch):
    from src.agentic_layer.config.settings import get_auth_headers, get_server_config

    monkeypatch.setenv("FHIR_USE_AUTH", "true")
    monkeypatch.setenv("FHIR_AUTH_TYPE", "bearer")
    monkeypatch.setenv("FHIR_AUTH_TOKEN", "global-token")
    monkeypatch.setenv("FHIR_SERVER_BASE", "https://fhir.example.com/R4")
    monkeypatch.delenv("FHIR_DEFAULT_SERVER_KEY", raising=False)

    from src.agentic_layer.config import settings as settings_module

    settings_module._auth_provider_cache = None
    config = get_server_config("protected")
    headers = get_auth_headers(config)
    assert headers == {"Authorization": "Bearer global-token"}
    settings_module._auth_provider_cache = None


def test_invalid_default_server_key_raises(monkeypatch):
    monkeypatch.setenv("FHIR_USE_AUTH", "false")
    monkeypatch.setenv("FHIR_DEFAULT_SERVER_KEY", "not-registered")

    with pytest.raises(UnknownServerKeyError):
        get_server_config(None)


def test_use_auth_without_server_base_skips_protected_registration(monkeypatch):
    monkeypatch.setenv("FHIR_USE_AUTH", "true")
    monkeypatch.delenv("FHIR_SERVER_BASE", raising=False)

    config = get_server_config("hapi")
    assert config.key == "hapi"
    with pytest.raises(UnknownServerKeyError):
        get_server_config("protected")


def test_unknown_default_key_maps_to_protected_when_auth_enabled(monkeypatch):
    monkeypatch.setenv("FHIR_USE_AUTH", "true")
    monkeypatch.setenv("FHIR_SERVER_BASE", "https://fhir.example.com/R4")
    monkeypatch.setenv("FHIR_DEFAULT_SERVER_KEY", "custom-unknown")
    monkeypatch.setenv("FHIR_AUTH_TOKEN", "protected-token")

    from src.agentic_layer.config import settings as settings_module

    settings_module._auth_provider_cache = None
    config = get_server_config(None)
    assert config.key == "protected"
    assert config.auth_token == "protected-token"
    settings_module._auth_provider_cache = None