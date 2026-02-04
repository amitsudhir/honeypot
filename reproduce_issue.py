import requests
import json

BASE_URL = "http://127.0.0.1:8000"
API_KEY = "secret123"

def test_exact_failure_case():
    payload = {
        "sessionId": "1fc994e9-f4c5-47ee-8806-90aeb969928f",
        "message": {
            "sender": "scammer",
            "text": "Your bank account will be blocked today. Verify immediately.",
            "timestamp": 1769776085000
        },
        "conversationHistory": [],
        "metadata": {
            "channel": "SMS",
            "language": "English",
            "locale": "IN"
        }
    }
    
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }
    
    print(f"Sending POST to {BASE_URL}/honeypot")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        res = requests.post(f"{BASE_URL}/honeypot", json=payload, headers=headers)
        print(f"Status Code: {res.status_code}")
        print(f"Raw Response Text: {res.text}")
        
        try:
            data = res.json()
            print("Response JSON:")
            print(json.dumps(data, indent=2))
        except json.JSONDecodeError as e:
            print(f"JSON Decode Error: {e}")
            
    except Exception as e:
        print(f"Request Failed: {e}")

if __name__ == "__main__":
    test_exact_failure_case()
