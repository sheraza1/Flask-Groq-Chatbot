import os
from collections import OrderedDict

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain_groq import ChatGroq

load_dotenv()

MODEL_NAME = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")
MAX_SESSIONS = 200

app = Flask(__name__)
CORS(app)

_llm = None
# One conversation per browser session, oldest evicted first.
sessions = OrderedDict()


def get_llm():
    """Create the Groq client on first use so the app can start (and be tested) without a key."""
    global _llm
    if _llm is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY is not set. Add it to your .env file.")
        _llm = ChatGroq(temperature=0.7, model_name=MODEL_NAME, groq_api_key=api_key)
    return _llm


def get_conversation(session_id):
    """Return the conversation for this session, creating it if needed."""
    if session_id in sessions:
        sessions.move_to_end(session_id)
        return sessions[session_id]

    conversation = ConversationChain(
        llm=get_llm(),
        memory=ConversationBufferMemory(),
        verbose=False,
    )
    sessions[session_id] = conversation
    while len(sessions) > MAX_SESSIONS:
        sessions.popitem(last=False)
    return conversation


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/data", methods=["POST"])
def chat():
    if not request.is_json:
        return jsonify({"response": False, "message": "Request must be JSON."}), 400

    payload = request.get_json()
    user_input = (payload.get("data") or "").strip()
    session_id = payload.get("session_id") or "default"

    if not user_input:
        return jsonify({"response": False, "message": "The 'data' field is missing or empty."}), 400

    try:
        reply = get_conversation(session_id).predict(input=user_input)
    except RuntimeError as exc:
        return jsonify({"response": False, "message": str(exc)}), 500
    except Exception as exc:
        app.logger.exception("Chat request failed: %s", exc)
        return jsonify({"response": False, "message": "Something went wrong. Please try again."}), 500

    return jsonify({"response": True, "message": reply})


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
