from typing import List, Dict, Optional
import time

class MemoryManager:
    # Keeps the chat history in memory. 
    # TODO: Swap this with Redis/Postgres for production persistence.
    def __init__(self, max_turns: int = 20):
        self.sessions: Dict[str, List[Dict[str, str]]] = {}
        self.session_data: Dict[str, Dict[str, str]] = {}
        self.max_turns = max_turns

    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        return self.sessions[session_id]

    def add_message(self, session_id: str, role: str, content: str):
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        
        self.sessions[session_id].append({"role": role, "content": content})
        
        # Trim if too long
        if len(self.sessions[session_id]) > self.max_turns * 2: # *2 because user+assistant pairs
             self.sessions[session_id] = self.sessions[session_id][-(self.max_turns * 2):]

    def clear_session(self, session_id: str):
        if session_id in self.sessions:
            del self.sessions[session_id]
        if session_id in self.session_data:
            del self.session_data[session_id]

    def update_extracted(self, session_id: str, data: Dict[str, list]):
        if session_id not in self.session_data:
            self.session_data[session_id] = {
                "bankAccounts": [], "upiIds": [], "phishingLinks": [], 
                "phoneNumbers": [], "suspiciousKeywords": []
            }
        
        # Merge lists and ensure uniqueness
        current = self.session_data[session_id]
        for k, v_list in data.items():
            if v_list and isinstance(v_list, list):
                # Add new items that aren't already there
                existing = set(current.get(k, []))
                for item in v_list:
                    if item not in existing:
                        current[k].append(item)
                        existing.add(item)

    def get_extracted(self, session_id: str) -> Dict[str, list]:
        return self.session_data.get(session_id, {
            "bankAccounts": [], "upiIds": [], "phishingLinks": [], 
            "phoneNumbers": [], "suspiciousKeywords": []
        })
