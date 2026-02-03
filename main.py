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
        raw_body = await request.body()
        
        body = {}
        try:
            body = await request.json()
        except:
            pass
        
        # Handle flexible input keys - defensive parsing
        raw_msg = None
        session_id = str(uuid.uuid4())
        
        if isinstance(body, dict):
            sub_msg = body.get("message")
            if isinstance(sub_msg, dict):
                raw_msg = sub_msg.get("text") or sub_msg.get("content") or str(sub_msg)
            elif sub_msg:
                raw_msg = sub_msg
            else:
                raw_msg = body.get("text") or body.get("input") or body.get("content") or body.get("query")
            
            session_id = body.get("session_id") or body.get("sessionId") or session_id
            
        elif isinstance(body, list):
             if len(body) > 0 and isinstance(body[0], dict):
                 raw_msg = body[0].get("message") or body[0].get("text")
        
        elif isinstance(body, str):
             raw_msg = body

        message = str(raw_msg) if raw_msg else ""
        
        if not message.strip():
             return HoneypotResponse(
                scam=False,
                confidence=0.0,
                reply=None,
                persona=None,
                extracted={"upi": None, "bank_account": None, "ifsc": None, "link": None},
                conversation_turns=0,
                session_id=session_id
            )
        
        is_scam, confidence, label = await classifier.classify(message)
        
        reply = None
        persona_name = None
        current_extracted = {
            "upi": None, "bank_account": None, "ifsc": None, "link": None
        }

        if is_scam:
            reply = await agent.generate_reply(session_id, message)
            
            new_extracted = await extractor.extract(message)
            memory_manager.update_extracted(session_id, new_extracted)
            
            current_extracted = memory_manager.get_extracted(session_id)
            
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
