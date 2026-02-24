import asyncio

import pytest
from fastapi import HTTPException

from src.api.endpoints import validate_api_key
from src.core.config import config


def test_client_api_key_is_ignored_by_default():
    assert config.ignore_client_api_key is True
    assert config.validate_client_api_key("invalid-client-key") is True


def test_validate_api_key_dependency_ignores_client_headers(monkeypatch):
    monkeypatch.setattr(config, "ignore_client_api_key", True)
    monkeypatch.setattr(config, "anthropic_api_key", "expected")

    # Should not raise, even when header key does not match
    asyncio.run(
        validate_api_key(
            x_api_key="totally-wrong",
            authorization="Bearer also-wrong",
        )
    )


def test_validate_api_key_dependency_strict_mode(monkeypatch):
    monkeypatch.setattr(config, "ignore_client_api_key", False)
    monkeypatch.setattr(config, "anthropic_api_key", "expected")

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(validate_api_key(x_api_key="wrong", authorization=None))
    assert exc_info.value.status_code == 401

    # Matching key should pass
    asyncio.run(validate_api_key(x_api_key="expected", authorization=None))
