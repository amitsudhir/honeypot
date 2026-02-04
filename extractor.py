import re
import json
import os
from typing import Dict, Any, Optional
from openai import AsyncOpenAI

class IntelligenceExtractor:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv("OPENAI_BASE_URL")
        self.model = os.getenv("LLM_MODEL", "gpt-3.5-turbo")

        if self.base_url:
            self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        else:
            self.client = AsyncOpenAI(api_key=self.api_key)

    async def extract(self, text: str) -> Dict[str, Any]:
        """
        Combines Regex and LLM extraction to get structured intelligence lists.
        """
        # 1. Regex Extraction (Fast, precise for patterns)
        regex_data = self._extract_regex(text)

        # 2. LLM Extraction (Smart, handles context/formatting)
        llm_data = await self._extract_llm(text)

        # 3. Merge Strategies (Union of lists)
        merged = {
            "bankAccounts": list(set(regex_data.get("bankAccounts", []) + llm_data.get("bankAccounts", []))),
            "upiIds": list(set(regex_data.get("upiIds", []) + llm_data.get("upiIds", []))),
            "phishingLinks": list(set(regex_data.get("phishingLinks", []) + llm_data.get("phishingLinks", []))),
            "phoneNumbers": list(set(regex_data.get("phoneNumbers", []) + llm_data.get("phoneNumbers", []))),
            "suspiciousKeywords": list(set(llm_data.get("suspiciousKeywords", []))) # LLM only for keywords
        }
        return merged

    def _extract_regex(self, text: str) -> Dict[str, list]:
        data = {
           "bankAccounts": [],
           "upiIds": [],
           "phishingLinks": [],
           "phoneNumbers": [],
           "suspiciousKeywords": []
        }

        # UPI Pattern
        upi_pattern = r'[a-zA-Z0-9.\-_]+@[a-zA-Z]+'
        data['upiIds'] = re.findall(upi_pattern, text)

        # Link Pattern
        url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+'
        data['phishingLinks'] = re.findall(url_pattern, text)

        # Phone Pattern (Indian +91 or 10 digits)
        phone_pattern = r'(?:\+91[\-\s]?)?[6-9]\d{9}'
        data['phoneNumbers'] = re.findall(phone_pattern, text)

        # Bank Account (Simple 9-18 digits context) - Weak regex, relying more on LLM
        # But we can try catching long number strings
        bank_pattern = r'\b\d{9,18}\b'
        possible_accounts = re.findall(bank_pattern, text)
        # Filter out 10 digit numbers that look like phones
        data['bankAccounts'] = [acc for acc in possible_accounts if len(acc) != 10]
        
        return data

    async def _extract_llm(self, text: str) -> Dict[str, list]:
        try:
            if not self.api_key:
                return {}
            
            prompt = """
            Extract scam intelligence from the message. 
            Return a JSON object with keys: "bankAccounts", "upiIds", "phishingLinks", "phoneNumbers", "suspiciousKeywords".
            Values must be LISTS of strings. Return empty list [] if nothing found.
            
            "suspiciousKeywords": specific urgent/scam words used (e.g. "blocked", "verify", "expire").
            
            Message: "{text}"
            """
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful data extractor. Output only valid JSON with lists."},
                    {"role": "user", "content": prompt.format(text=text)}
                ],
                temperature=0,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            print(f"Extraction Error: {e}")
            return {"bankAccounts": [], "upiIds": [], "phishingLinks": [], "phoneNumbers": [], "suspiciousKeywords": []}
