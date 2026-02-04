from fastapi import FastAPI, Request, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
import uuid
import os
import json
from dotenv import load_dotenv

load_dotenv()
APP_API_KEY = os.getenv("APP_API_KEY")

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

from callback import send_guvi_callback

@app.post("/honeypot")
@app.head("/honeypot", include_in_schema=False)
async def honey_pot_endpoint(request: Request, background_tasks: BackgroundTasks):
    response_data = {
        "status": "success",
        "reply": "I did not understand that."
    }

    try:
        api_key_header = request.headers.get("x-api-key")
        
        if APP_API_KEY:
            if not api_key_header or api_key_header.strip() != APP_API_KEY.strip():
                print(f"[Auth] Invalid Key: {api_key_header}")
                response_data["reply"] = "Authentication Failed."
                return response_data

        try:
            body = await request.json()
        except:
            return response_data

        session_id = str(uuid.uuid4())
        if isinstance(body, dict):
            session_id = body.get("sessionId") or body.get("session_id") or session_id

        message_text = ""
        raw_msg = body.get("message")
        
        if isinstance(raw_msg, dict):
             message_text = raw_msg.get("text") or raw_msg.get("content") or ""
        elif isinstance(raw_msg, str):
             message_text = raw_msg
        else:
             message_text = body.get("text") or body.get("input") or ""

        if not message_text.strip():
            return response_data

        try:
            is_scam, confidence, label = await classifier.classify(message_text)
            
            if is_scam:
                new_ext = await extractor.extract(message_text)
                memory_manager.update_extracted(session_id, new_ext)
                
                reply = await agent.generate_reply(session_id, message_text)
                if reply:
                    response_data["reply"] = reply
                
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
                except Exception as cb_e:
                    print(f"Callback Error: {cb_e}")

        except Exception as logic_e:
            print(f"Logic Error: {logic_e}")
            
    except Exception as e:
        print(f"Endpoint Error: {e}")
    
    return response_data

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
