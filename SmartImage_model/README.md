# SmartImage Model Service

This service exposes a small Flask API for LangChain-based model calls.

## Setup

1) Create a virtual environment and install deps:

python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

2) Copy env sample and fill values:

copy .env.example .env

3) Run the service:

python app.py

## Endpoints

- GET /health
- POST /api/agent/chat
  - body: { "prompt": "..." }
  - or: { "messages": [{"role":"user","content":"..."}] }

## Env vars

- OPENAI_BASE_URL
- OPENAI_API_KEY
- REDIS_HOST
- REDIS_PORT
- REDIS_DB
- REDIS_PASSWORD
- SYSTEM_PROMPT
