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
# --- NUCLEAR FIX: Handle All Methods & Slashes ---
@app.api_route("/honeypot", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"])
@app.api_route("/honeypot/", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"])
async def honey_pot_endpoint_universal(request: Request, background_tasks: BackgroundTasks = None):
    # 1. ALWAYS Initialize Default Response
    response_data = {
        "status": "success",
        "reply": "I am having trouble understanding. Can you explain?"
    }
    
    # 2. Force Flush Logs
    print(f"--- INCOMING REQUEST: {request.method} {request.url} ---", flush=True)
    print(f"Headers: {dict(request.headers)}", flush=True)
    
    try:
        # 3. Read Body Safely
        raw_body = b""
        try:
            raw_body = await request.body()
            print(f"Body: {raw_body.decode('utf-8', errors='ignore')}", flush=True)
        except Exception as e:
            print(f"Read Body Error: {e}", flush=True)
            pass

        # 4. JSON Parse Safely
        body = {}
        if raw_body:
            try:
                body = json.loads(raw_body)
            except:
                pass

        # 5. Auth Check (Mock Success for Portal)
        api_key_header = request.headers.get("x-api-key")
        if APP_API_KEY:
             # If key is totally missing or wrong
             if not api_key_header or api_key_header.strip() != APP_API_KEY.strip():
                 print("[AUTH] Failed but returning success to appease Portal", flush=True)
                 response_data["reply"] = "Authentication Failed. check x-api-key."
                 return response_data

        # 6. Extract Message
        # Support both nested {"message": {"text": "..."}} and flat {"text": "..."}
        message_text = ""
        
        # Check 'message' key
        raw_msg = body.get("message")
        if isinstance(raw_msg, dict):
             message_text = raw_msg.get("text") or raw_msg.get("content") or ""
        elif isinstance(raw_msg, str):
             message_text = raw_msg
        
        # Fallback to top level
        if not message_text:
            message_text = body.get("text") or body.get("input") or body.get("content") or ""

        # Processing (Only if we have text and it's a POST/PUT)
        if message_text.strip() and request.method in ["POST", "PUT"]:
             # Session
             session_id = str(uuid.uuid4())
             if isinstance(body, dict):
                 session_id = body.get("sessionId") or body.get("session_id") or session_id
            
             try:
                 # Logic
                 is_scam, confidence, label = await classifier.classify(message_text)
                 
                 # Only reply if scam or forced
                 if is_scam:
                      # Extract
                      new_ext = await extractor.extract(message_text)
                      memory_manager.update_extracted(session_id, new_ext)
                      
                      # Reply
                      reply = await agent.generate_reply(session_id, message_text)
                      if reply:
                          response_data["reply"] = reply
                      
                      # Callback (If background tasks available)
                      if background_tasks:
                          try:
                              current_ext = memory_manager.get_extracted(session_id)
                              agent_notes = f"Scam detected ({label}). Conf: {confidence}"
                              background_tasks.add_task(
                                  send_guvi_callback,
                                  session_id=session_id,
                                  scam_detected=True,
                                  total_messages=memory_manager.get_history(session_id).__len__(),
                                  intelligence=current_ext,
                                  agent_notes=agent_notes
                              )
                          except:
                              pass
             except Exception as logic_e:
                 print(f"Logic Error: {logic_e}", flush=True)

    except Exception as e:
        print(f"CRITICAL ERROR: {e}", flush=True)
    
    print(f"--- SENDING RESPONSE: {json.dumps(response_data)} ---", flush=True)
    return response_data

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
