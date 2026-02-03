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
        Combines Regex and LLM extraction to get structured intelligence.
        """
        # 1. Regex Extraction (Fast, precise for patterns)
        regex_data = self._extract_regex(text)

        # 2. LLM Extraction (Smart, handles context/formatting)
        llm_data = await self._extract_llm(text)

        # 3. Merge Strategies
        # We prioritize regex for strict patterns (like UPI/Links) if they match,
        # but LLM might catch things regex misses (like "my number is 99...")
        
        merged = {
            "upi": regex_data.get("upi") or llm_data.get("upi"),
            "bank_account": regex_data.get("bank_account") or llm_data.get("bank_account"),
            "ifsc": regex_data.get("ifsc") or llm_data.get("ifsc"),
            "link": regex_data.get("link") or llm_data.get("link")
        }
        return merged

    def _extract_regex(self, text: str) -> Dict[str, Optional[str]]:
        data = {
           "upi": None,
           "bank_account": None,
           "ifsc": None,
           "link": None
        }

        # UPI Pattern (e.g., example@oksbi)
        upi_pattern = r'[a-zA-Z0-9.\-_]+@[a-zA-Z]+'
        upi_match = re.search(upi_pattern, text)
        if upi_match:
            data['upi'] = upi_match.group(0)

        # Link Pattern (http/https)
        url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+'
        url_match = re.search(url_pattern, text)
        if url_match:
            data['link'] = url_match.group(0)

        # IFSC Pattern (4 letters, 0, 6 chars)
        ifsc_pattern = r'[A-Z]{4}0[A-Z0-9]{6}'
        ifsc_match = re.search(ifsc_pattern, text)
        if ifsc_match:
            data['ifsc'] = ifsc_match.group(0)

        # Bank Account (Simple 9-18 digits, careful not to match phone numbers)
        # This is hard with regex alone without context, relies mostly on LLM.
        # But we can try looking for "Account" keyword context or just long digits.
        # For now, let's rely on LLM for Bank Account to avoid false positives with phone numbers.
        
        return data

    async def _extract_llm(self, text: str) -> Dict[str, Optional[str]]:
        try:
            if not self.api_key:
                return {}
            
            prompt = """
            Extract the following scam intelligence from the message. 
            Return a JSON object with keys: "upi", "bank_account", "ifsc", "link".
            Values should be null if not found.
            Message: "{text}"
            """
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful data extractor. Output only valid JSON."},
                    {"role": "user", "content": prompt.format(text=text)}
                ],
                temperature=0,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            # Fallback or log error
            print(f"Extraction Error: {e}")
            return {"upi": None, "bank_account": None, "ifsc": None, "link": None}
