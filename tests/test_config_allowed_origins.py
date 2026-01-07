import os
from FastApi.core.config import Settings


def test_allowed_origins_star(monkeypatch):
    monkeypatch.setenv("ALLOWED_ORIGINS", "*")
    s = Settings()
    assert s.ALLOWED_ORIGINS == ["*"]


def test_allowed_origins_empty_string(monkeypatch):
    monkeypatch.setenv("ALLOWED_ORIGINS", "")
    s = Settings()
    assert s.ALLOWED_ORIGINS == ["*"]


def test_allowed_origins_csv(monkeypatch):
    monkeypatch.setenv("ALLOWED_ORIGINS", "http://a, http://b")
    s = Settings()
    assert s.ALLOWED_ORIGINS == ["http://a", "http://b"]


def test_allowed_origins_json_array(monkeypatch):
    monkeypatch.setenv("ALLOWED_ORIGINS", '["http://a", "http://b"]')
    s = Settings()
    assert s.ALLOWED_ORIGINS == ["http://a", "http://b"]


def test_allowed_origins_not_set(monkeypatch):
    monkeypatch.delenv("ALLOWED_ORIGINS", raising=False)
    s = Settings()
    assert s.ALLOWED_ORIGINS == ["*"]
