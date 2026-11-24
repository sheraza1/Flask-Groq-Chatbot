import pytest
from langchain_core.language_models.fake import FakeListLLM

import app as chat_app


@pytest.fixture(autouse=True)
def fake_llm(monkeypatch):
    """Use an offline model so the tests need no API key or network."""
    monkeypatch.setattr(chat_app, "get_llm", lambda: FakeListLLM(responses=["first reply", "second reply", "third reply"]))
    chat_app.sessions.clear()


@pytest.fixture
def client():
    chat_app.app.config["TESTING"] = True
    return chat_app.app.test_client()


def send(client, text, session_id="abc"):
    return client.post("/data", json={"data": text, "session_id": session_id})


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_rejects_non_json(client):
    response = client.post("/data", data="hello")
    assert response.status_code == 400
    assert response.get_json()["response"] is False


def test_rejects_empty_message(client):
    response = send(client, "   ")
    assert response.status_code == 400


def test_returns_model_reply(client):
    response = send(client, "hello")
    assert response.status_code == 200
    assert response.get_json() == {"response": True, "message": "first reply"}


def test_conversation_is_remembered_within_a_session(client):
    send(client, "hello")
    send(client, "and again")
    messages = chat_app.sessions["abc"].memory.chat_memory.messages
    assert len(messages) == 4


def test_sessions_do_not_share_history(client):
    send(client, "hello", session_id="one")
    send(client, "hello", session_id="two")
    assert chat_app.sessions["one"] is not chat_app.sessions["two"]
    assert len(chat_app.sessions["one"].memory.chat_memory.messages) == 2


def test_oldest_session_is_evicted(client, monkeypatch):
    monkeypatch.setattr(chat_app, "MAX_SESSIONS", 2)
    for name in ("a", "b", "c"):
        send(client, "hi", session_id=name)
    assert list(chat_app.sessions) == ["b", "c"]
