# Flask Groq Chatbot

A lightweight conversational chatbot using Flask for the web layer and a Groq-hosted Llama model for the answers. Each visitor gets their own conversation, and the bot remembers what was said earlier in that conversation.

## What it includes

- A browser chat page served directly by Flask
- Per-session conversation history, built on LangChain's `ConversationChain`
- A single `/data` endpoint for chat and a `/health` endpoint for checks
- Configurable model name through `GROQ_MODEL`
- A pytest suite that runs without network access or an API key

## Setup

Requirements: Python 3.9+ and a Groq API key from https://console.groq.com/keys.

```bash
git clone https://github.com/sheraza1/Flask-Groq-Chatbot.git
cd Flask-Groq-Chatbot

python -m venv venv
source venv/bin/activate         # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env             # add your GROQ_API_KEY
python app.py
```

The app runs at http://127.0.0.1:5000.

## Environment variables

- `GROQ_API_KEY` (required): API key for Groq.
- `GROQ_MODEL` (optional): model to use. Defaults to `llama-3.1-8b-instant`.
- `FLASK_DEBUG` (optional): `1` enables debug mode.

## Endpoints

**`POST /data`** accepts JSON with the message and a session id:

```json
{ "data": "Hello!", "session_id": "browser-session-id" }
```

and returns:

```json
{ "response": true, "message": "Hi there! How can I help?" }
```

Messages sent with the same `session_id` form one conversation. The page creates a fresh id on every load. Invalid input returns a 400 with `{"response": false, "message": "..."}`, and server errors return a 500 in the same shape.

**`GET /health`** returns `{"status": "ok"}`.

## Design notes

- Conversations are stored in an ordered dictionary keyed by session id. When more than 200 sessions exist, the least recently used one is removed.
- The Groq client is created on the first request rather than at import time, which lets the app and the tests start without a key.
- Text from the user and the model is written into the page with `textContent`, so it is never interpreted as HTML.

## Running the tests

```bash
pip install -r requirements-dev.txt
pytest
```

Seven tests use LangChain's `FakeListLLM` in place of the real model. They check health, bad input, replies, memory within a session, separation between sessions, and eviction of old sessions.

## Layout

```
app.py                  backend
templates/index.html    chat page
static/main.js          client code
static/style.css        styles
tests/test_app.py       tests
requirements.txt        dependencies
requirements-dev.txt    test dependencies
```

## Known limitations

- Memory is in process only. It resets on restart and is not shared across workers.
- `ConversationChain` is deprecated upstream and should be replaced with `RunnableWithMessageHistory` when upgrading LangChain.
- No login or rate limiting, so keep it on a local or trusted network.
