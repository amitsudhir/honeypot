import os
from openai import AsyncOpenAI
from typing import Optional
from memory import MemoryManager
from persona import PersonaManager

class HoneypotAgent:
    def __init__(self, memory_manager: MemoryManager, persona_manager: PersonaManager):
        self.memory = memory_manager
        self.persona = persona_manager
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv("OPENAI_BASE_URL")
        self.model = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
        
        if self.base_url:
             self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        else:
             self.client = AsyncOpenAI(api_key=self.api_key)

    async def generate_reply(self, session_id: str, user_message: str) -> str:
        # 1. Add user message to memory
        self.memory.add_message(session_id, "user", user_message)

        # 2. Get Context
        history = self.memory.get_history(session_id)
        system_prompt = self.persona.get_system_prompt(session_id)

        # 3. Construct Messages for LLM
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)

        try:
            # 4. Call LLM
            # We use a slightly higher temp (0.7) to make the persona sound more natural/confused.
            response = await self.client.chat.completions.create(
                model=self.model, 
                messages=messages,
                temperature=0.7, 
                max_tokens=150
            )

            reply = response.choices[0].message.content

            # 5. Add agent reply to memory
            self.memory.add_message(session_id, "assistant", reply)
            
            return reply

        except Exception as e:
            print(f"Agent Generation Error: {e}")
            fallback = "I am sorry, I did not understand. Can you explain about the payment again?"
            self.memory.add_message(session_id, "assistant", fallback)
            return fallback
