import os
import json
from openai import AsyncOpenAI
from typing import Tuple

class ScamClassifier:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv("OPENAI_BASE_URL") # Support for Groq/Local
        self.model = os.getenv("LLM_MODEL", "gpt-3.5-turbo") # Default to gpt-3.5
        
        if self.base_url:
            self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        else:
            self.client = AsyncOpenAI(api_key=self.api_key)

    async def classify(self, text: str) -> Tuple[bool, float, str]:
        """
        Classifies the text as SCAM, SUSPICIOUS, or SAFE.
        Returns (is_scam, confidence_score, label).
        """
        try:
            if not self.api_key:
                # Fail open or closed? Safe for now if no key.
                return False, 0.0, "SAFE"

            prompt = f"""
            Analyze the following message and classify it into one of these categories:
            1. SCAM (Phishing, Lottery, Urgent Money Request, Job Scam, etc.)
            2. SUSPICIOUS (Unsolicited, vague requests, strange links)
            3. SAFE (Normal conversation, greeting, relevant query)

            Return a JSON object:
            {{
                "label": "SCAM" | "SUSPICIOUS" | "SAFE",
                "confidence": 0.0 to 1.0
            }}

            Message: "{text}"
            """

            response = await self.client.chat.completions.create(
                model=self.model, 
                messages=[
                    {"role": "system", "content": "You are an expert cybersecurity AI. Output only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content
            print(f"[Classifier] Raw content: {content}") # Debug print
            
            # Sanitize content if needed (sometimes it adds ```json ... ```)
            if "```" in content:
                content = content.replace("```json", "").replace("```", "")
                
            result = json.loads(content)
            
            label = result.get("label", "SAFE").upper()
            confidence = result.get("confidence", 0.0)

            # Treat SCAM and SUSPICIOUS as honeypot activation triggers
            is_scam = label in ["SCAM", "SUSPICIOUS"]
            
            return is_scam, confidence, label

        except Exception as e:
            print(f"[Classifier] Error: {e}")
            import traceback
            traceback.print_exc()
            return False, 0.0, "SAFE"
