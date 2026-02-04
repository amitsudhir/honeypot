# Agentic Honey-Pot API 🍯

> **Built for the India AI Impact Buildathon 2026**

This is an autonomous backend system designed to waste scammers' time. It detects scam messages, spins up a confused persona (like an elderly uncle), and keeps the scammer busy while extracting their payment details (UPI, Bank Accounts, etc.).

## 🏗️ Architecture
The system is built with **FastAPI** and uses **LLMs (Llama-3 via Groq)** for the heavy lifting.

- **Classifier**: Decides if a message is a scam or safe.
- **Agents**: The "Persona" that talks back. We have a few profiles (confused grandpa, busy shopkeeper, etc.).
- **Extractor**: Pulls out UPI IDs and links using Regex + LLM fallback.
- **Memory**: Keeps track of the conversation so the bot doesn't forget what it just said.

## 🚀 Quick Start

### 1. Setup
Clone the repo and install the requirements.
```bash
pip install -r requirements.txt
```

### 2. Config
Create a `.env` file. You can check `.env.example` for reference.
We are using **Groq** because it's fast and has a generous free tier.

```env
OPENAI_API_KEY=gsk_your_key...
OPENAI_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=llama-3.3-70b-versatile
APP_API_KEY=secret_key_for_client
```

### 3. Run it
```bash
uvicorn main:app --reload
```
API will be live at `http://127.0.0.1:8000`.


## 📝 Notes
- The "Persona" is currently stateless between server restarts because we store session data in memory (`memory.py`). For production, we should move this to Redis.
- If you change the model, make sure it supports JSON mode or the extractor might act weird.

---
*Made with ❤️ by Sudhir*
