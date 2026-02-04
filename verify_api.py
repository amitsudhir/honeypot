import requests
import time
import sys

BASE_URL = "https://honeypot-ak8x.onrender.com"

# Load actual key from .env for testing, or default to placeholder
from dotenv import load_dotenv
import os
load_dotenv()
APP_API_KEY = os.getenv("APP_API_KEY", "secret123")

def wait_for_server():
    print("Waiting for server...")
    for _ in range(30):
        try:
            requests.get(f"{BASE_URL}/")
            print("Server is up!")
            return True
        except requests.exceptions.ConnectionError:
            time.sleep(1)
    return False

def test_safe_message():
    print("\n[TEST] Safe Message")
    payload = {
        "message": {"text": "Hey, are we still meeting for lunch today?"},
        "sessionId": "test_safe"
    }
    headers = {"x-api-key": APP_API_KEY}
    res = requests.post(f"{BASE_URL}/honeypot", json=payload, headers=headers)
    if res.status_code != 200:
        print(f"FAILED: Status {res.status_code}")
        print(res.text)
        return
    
    data = res.json()
    print(f"Response: {data}")
    # Safe message should have NO reply (or simplified status)
    if data.get('status') == 'success' and not data.get('reply'):
        print("PASSED: Correctly identified as SAFE (No reply).")
    else:
        print("FAILED: Generated a reply for a safe message.")

def test_scam_message():
    print("\n[TEST] Scam Message")
    payload = {
        "message": {"text": "Congratulations! You have won a lottery of $1,000,000. Please send your bank details to claim it."},
        "sessionId": "test_scam"
    }
    headers = {"x-api-key": APP_API_KEY}
    res = requests.post(f"{BASE_URL}/honeypot", json=payload, headers=headers)
    if res.status_code != 200:
        print(f"FAILED: Status {res.status_code}")
        return

    data = res.json()
    print(f"Response: {data}")
    # Scam message MUST have a reply
    if data.get('status') == 'success' and data.get('reply'):
        print("PASSED: Generated reply for SCAM.")
        print(f"Agent Reply: {data['reply']}")
    else:
        print("FAILED: No reply generated for scam.")

if __name__ == "__main__":
    if not wait_for_server():
        print("Server failed to start.")
        sys.exit(1)
    
    test_safe_message()
    test_scam_message()
