from fastapi import FastAPI, Request, BackgroundTasks, HTTPException, Header
from pydantic import BaseModel, Field
from typing import Optional, Union, Dict, Any
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
from callback import send_guvi_callback

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

# Robust Request Model
class HoneypotRequest(BaseModel):
    message: Optional[Union[str, Dict[str, Any]]] = None
    text: Optional[str] = None
    input: Optional[str] = None
    # Support both session_id and sessionId
    session_id: Optional[str] = Field(None, alias="sessionId")
    session_id_snake: Optional[str] = Field(None, alias="session_id")

    def get_session_id(self) -> str:
        # Priority: sessionId -> session_id -> new uuid
        return self.session_id or self.session_id_snake or str(uuid.uuid4())

    def get_message_text(self) -> str:
        # Logic to extract text from various possible fields
        msg_text = ""
        if isinstance(self.message, dict):
            msg_text = self.message.get("text") or self.message.get("content") or ""
        elif isinstance(self.message, str):
            msg_text = self.message
        
        if not msg_text:
            msg_text = self.text or self.input or ""
        
        return msg_text

@app.get("/")
@app.head("/")
async def root():
    return {"status": "active", "service": "Honeypot API"}

@app.get("/honeypot")
async def honeypot_get():
    return {"message": "Honeypot Endpoint is Active. Send POST request with JSON body."}

@app.post("/honeypot")
@app.head("/honeypot", include_in_schema=False)
async def honey_pot_endpoint(
    request: HoneypotRequest, 
    background_tasks: BackgroundTasks, 
    x_api_key: Optional[str] = Header(None)
):
    response_data = {
        "status": "success",
        "reply": "I did not understand that."
    }

    # API Key Validation
    if APP_API_KEY:
        if not x_api_key or x_api_key.strip() != APP_API_KEY.strip():
            print(f"[Auth] Invalid Key: {x_api_key}")
            # Instead of returning 200 with error message, standard practice is 401 or 403,
            # but to maintain 'confusion' for a honeypot, we might reply loosely.
            # However, for the Hackathon Tester, explicit failure might be safely returned or logged.
            # We will stick to the previous behavior: return 200 but say Authentication Failed.
            response_data["reply"] = "Authentication Failed."
            return response_data

    # Extract ID and Message using the helper methods
    session_id = request.get_session_id()
    message_text = request.get_message_text()

    if not message_text.strip():
        # If no message, just return default response
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
                history_len = 0
                try:
                     history_len = len(memory_manager.get_history(session_id))
                except:
                     pass

                agent_notes = f"Scam detected ({label}). Conf: {confidence}"
                
                background_tasks.add_task(
                    send_guvi_callback,
                    session_id=session_id,
                    scam_detected=True,
                    total_messages=history_len,
                    intelligence=current_ext,
                    agent_notes=agent_notes
                )
            except Exception as cb_e:
                print(f"Callback Error: {cb_e}")

    except Exception as logic_e:
        print(f"Logic Error: {logic_e}")
        # Consider whether to expose internal errors. For a honeypot, probably not.
    
    return response_data

if __name__ == "__main__":
    import uvicorn
    # CRITICAL FIX: Use the PORT environment variable provided by Render
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
