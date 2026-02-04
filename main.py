from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security import APIKeyHeader, APIKeyQuery
from pydantic import BaseModel
from typing import Optional, Dict
import uuid
import os
from dotenv import load_dotenv

# Load env vars
load_dotenv()

APP_API_KEY = os.getenv("APP_API_KEY")
api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)

def get_api_key(api_key_header: str = Security(api_key_header)):
    if not APP_API_KEY:
        return None
    # Flexible check: strip whitespace
    if api_key_header and api_key_header.strip() == APP_API_KEY.strip():
        return api_key_header
    return None

# Import modules
from memory import MemoryManager
from persona import PersonaManager
from classifier import ScamClassifier
from extractor import IntelligenceExtractor
from agents import HoneypotAgent

app = FastAPI(title="Agentic Honey-Pot API", description="AI-powered scam detection and intelligence extraction API.")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Components
memory_manager = MemoryManager()
persona_manager = PersonaManager()
classifier = ScamClassifier()
extractor = IntelligenceExtractor()
agent = HoneypotAgent(memory_manager, persona_manager)

# Models
class HoneypotRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


from fastapi import Request

@app.get("/")
@app.head("/")
async def root():
    return {"status": "active", "service": "Honeypot API"}

@app.get("/honeypot")
async def honeypot_get():
    return {"message": "Honeypot Endpoint is Active. Send POST request with JSON body."}

from fastapi import BackgroundTasks
from callback import send_guvi_callback

@app.post("/honeypot")
@app.head("/honeypot")
async def honey_pot_endpoint(request: Request, background_tasks: BackgroundTasks, api_key: Optional[str] = Depends(get_api_key)):
    try:
        # Debug Logging
        print(f"Headers: {request.headers}")
        try:
            raw_body = await request.body()
            print(f"Raw Body: {raw_body.decode('utf-8', errors='ignore')}")
        except:
            pass

        # --- 0. Auth Check (Soft Fail) ---
        if APP_API_KEY and not api_key:
             print("Authentication Failed!")
             # Return valid JSON schema even on error, to satisfy Portal Parser
             return {
                 "status": "error", 
                 "reply": "Authentication Failed. Check x-api-key header."
             }

        body = {}
        try:
            body = await request.json()
        except:
            pass
        
        # --- Input Parsing ---
        # Format: { "sessionId": "...", "message": { "text": "...", ... }, "conversationHistory": [] }
        
        # 1. Session ID
        session_id = body.get("sessionId") or body.get("session_id") or str(uuid.uuid4())
        
        # 2. Message Text extraction
        message_text = ""
        raw_msg_obj = body.get("message")
        
        if isinstance(raw_msg_obj, dict):
            message_text = raw_msg_obj.get("text") or raw_msg_obj.get("content") or ""
        elif isinstance(raw_msg_obj, str):
            message_text = raw_msg_obj
        else:
            message_text = body.get("text") or body.get("input") or body.get("content") or ""

        # Fail-safe empty message
        if not message_text.strip():
             return {"status": "success", "reply": "Hello? I cannot hear you."}

        # --- Processing ---
        
        # Classification
        is_scam, confidence, label = await classifier.classify(message_text)
        
        # Intel Extraction
        new_extracted = await extractor.extract(message_text)
        memory_manager.update_extracted(session_id, new_extracted)
        
        # Get accumulated intel
        current_extracted = memory_manager.get_extracted(session_id)
        
        # Agent Reply (Only if scam detected)
        reply = None
        if is_scam:
            reply = await agent.generate_reply(session_id, message_text)
            history = memory_manager.get_history(session_id)
            total_turns = len(history)

            # --- Background Reporting ---
            agent_notes = f"Scam detected ({label}). Confidence: {confidence}"
            background_tasks.add_task(
                send_guvi_callback,
                session_id=session_id,
                scam_detected=True,
                total_messages=total_turns,
                intelligence=current_extracted,
                agent_notes=agent_notes
            )

        # --- Response ---
        return {
            "status": "success",
            "reply": reply
        }

    except Exception as e:
        print(f"API Error: {e}")
        return {
            "status": "error",
            "reply": "I am having trouble connecting. Please text again."
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
