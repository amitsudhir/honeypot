from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security import APIKeyHeader, APIKeyQuery
from pydantic import BaseModel
from typing import Optional, Dict
import uuid
import os
from dotenv import load_dotenv

# Load env vars
load_dotenv()

# Setup Authentication
# TODO: Move this to a proper auth middleware later
APP_API_KEY = os.getenv("APP_API_KEY")
api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)

def get_api_key(api_key_header: str = Security(api_key_header)):
    if not APP_API_KEY:
        # If API key is not set in env, we might want to warn or fail open/closed.
        # For Hackathon security, failing open is risky, so let's enforce it if set.
        return None 
    
    if api_key_header == APP_API_KEY:
        return api_key_header
    
    raise HTTPException(status_code=403, detail="Could not validate credentials")

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
    allow_origins=["*"],  # Allow ALL origins (Hackathon Portal needs this)
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

class ExtractedData(BaseModel):
    upi: Optional[str]
    bank_account: Optional[str]
    ifsc: Optional[str]
    link: Optional[str]

class HoneypotResponse(BaseModel):
    scam: bool
    confidence: float
    reply: Optional[str]
    persona: Optional[str]
    extracted: ExtractedData
    conversation_turns: int
    session_id: str

from fastapi import Request

@app.get("/")
async def root():
    return {"status": "active", "service": "Honeypot API"}

@app.get("/honeypot")
async def honeypot_get():
    return {"message": "Honeypot Endpoint is Active. Send POST request with JSON body."}

@app.post("/honeypot")
async def honey_pot_endpoint(request: Request, api_key: str = Depends(get_api_key)):
    try:
        # DEBUGGING: Log everything
        raw_body = await request.body()
        print(f"[DEBUG] Headers: {request.headers}")
        print(f"[DEBUG] Raw Bytes: {raw_body}")
        
        body = {}
        try:
            body = await request.json()
        except:
            print("[DEBUG] JSON Decode Failed (Body might be empty or text)")
        
        # Handle flexible input keys - defensive parsing
        raw_msg = None
        session_id = str(uuid.uuid4())
        
        if isinstance(body, dict):
            # Standard dict body
            # Check for nested "message": {"text": "..."}
            sub_msg = body.get("message")
            if isinstance(sub_msg, dict):
                raw_msg = sub_msg.get("text") or sub_msg.get("content") or str(sub_msg)
            elif sub_msg:
                raw_msg = sub_msg
            else:
                # Check aliases at root level
                raw_msg = body.get("text") or body.get("input") or body.get("content") or body.get("query")
            
            # Session ID
            session_id = body.get("session_id") or body.get("sessionId") or session_id
            
        elif isinstance(body, list):
             # Weird case: Body is a list?
             print(f"[WARN] Body is a list: {body}")
             if len(body) > 0 and isinstance(body[0], dict):
                 raw_msg = body[0].get("message") or body[0].get("text")
        
        elif isinstance(body, str):
             # Body might be just a plain string
             raw_msg = body

        # Final Message Cleaning
        message = str(raw_msg) if raw_msg else ""
        
        # FAIL-SAFE: If message is empty, Return SAFE immediately (Don't call LLM)
        if not message.strip():
             print("[WARN] No message found. Returning SAFE default.")
             return HoneypotResponse(
                scam=False,
                confidence=0.0,
                reply=None,
                persona=None,
                extracted={"upi": None, "bank_account": None, "ifsc": None, "link": None},
                conversation_turns=0,
                session_id=session_id
            )
        
        # 2. Classification
        is_scam, confidence, label = await classifier.classify(message)
        
        reply = None
        persona_name = None
        current_extracted = {
            "upi": None, "bank_account": None, "ifsc": None, "link": None
        }

        # 3. Honeypot Activation
        if is_scam:
            # Generate Reply
            reply = await agent.generate_reply(session_id, message)
            
            # Extract Intelligence
            new_extracted = await extractor.extract(message)
            memory_manager.update_extracted(session_id, new_extracted)
            
            # Get Accumulated Intelligence
            current_extracted = memory_manager.get_extracted(session_id)
            
            # Get Persona Name
            persona_name = persona_manager.get_persona(session_id).name
        
        # Get turn count
        history = memory_manager.get_history(session_id)
        # Each turn is a dict, so length is number of messages. 
        # API requires "conversation_turns" -> usually round trips or just count.
        turns = len(history)

        return HoneypotResponse(
            scam=is_scam,
            confidence=confidence,
            reply=reply,
            persona=persona_name,
            extracted=current_extracted,
            conversation_turns=turns,
            session_id=session_id
        )

    except Exception as e:
        # Failsafe
        print(f"API Error: {e}")
        return HoneypotResponse(
            scam=False,
            confidence=0.0,
            reply="An internal error occurred.",
            persona=None,
            extracted={"upi": None, "bank_account": None, "ifsc": None, "link": None},
            conversation_turns=0,
            session_id=session_id or "error"
        )

# For running with python main.py mostly for debugging, usually use uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
