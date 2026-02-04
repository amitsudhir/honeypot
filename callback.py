import requests
import json
import os

GUVI_CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"

def send_guvi_callback(session_id: str, scam_detected: bool, total_messages: int, intelligence: dict, agent_notes: str = ""):
    """
    Sends the final extraction result to the evaluation endpoint.
    Should be called asynchronously.
    """
    try:
        # Construct Payload based on official docs
        payload = {
            "sessionId": session_id,
            "scamDetected": scam_detected,
            "totalMessagesExchanged": total_messages,
            "extractedIntelligence": {
                "bankAccounts": intelligence.get("bankAccounts", []),
                "upiIds": intelligence.get("upiIds", []),
                "phishingLinks": intelligence.get("phishingLinks", []),
                "phoneNumbers": intelligence.get("phoneNumbers", []),
                "suspiciousKeywords": intelligence.get("suspiciousKeywords", [])
            },
            "agentNotes": agent_notes or "Scam detected via LLM classifier."
        }
        
        print(f"[Callback] Sending data to GUVI: {json.dumps(payload)}")
        
        # Send Request (Fail safe)
        response = requests.post(GUVI_CALLBACK_URL, json=payload, timeout=5)
        
        if response.status_code == 200:
            print("[Callback] Success!")
        else:
             print(f"[Callback] Failed: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"[Callback] Error sending callback: {e}")
