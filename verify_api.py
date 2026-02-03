import requests
import time
import sys

BASE_URL = "http://127.0.0.1:8004"

def wait_for_server():
    print("Waiting for server...")
    for _ in range(30):
        try:
            requests.get(f"{BASE_URL}/docs")
            print("Server is up!")
            return True
        except requests.exceptions.ConnectionError:
            time.sleep(1)
    return False

def test_safe_message():
    print("\n[TEST] Safe Message")
    payload = {
        "message": "Hey, are we still meeting for lunch today?",
        "session_id": "test_safe"
    }
    headers = {"x-api-key": "my_secret_judge_key_123"}
    res = requests.post(f"{BASE_URL}/honeypot", json=payload, headers=headers)
    if res.status_code != 200:
        print(f"FAILED: Status {res.status_code}")
        print(res.text)
        return
    
    data = res.json()
    print(f"Response: {data}")
    if not data['scam']:
        print("PASSED: Correctly identified as SAFE.")
    else:
        print("FAILED: Incorrectly identified as SCAM.")

def test_scam_message():
    print("\n[TEST] Scam Message")
    payload = {
        "message": "Congratulations! You have won a lottery of $1,000,000. Please send your bank details to claim it.",
        "session_id": "test_scam"
    }
    headers = {"x-api-key": "my_secret_judge_key_123"}
    res = requests.post(f"{BASE_URL}/honeypot", json=payload, headers=headers)
    if res.status_code != 200:
        print(f"FAILED: Status {res.status_code}")
        return

    data = res.json()
    print(f"Response: {data}")
    if data['scam']:
        print("PASSED: Correctly identified as SCAM.")
        if data['reply']:
            print(f"Agent Reply: {data['reply']}")
        else:
            print("WARNING: No reply generated.")
    else:
        print("FAILED: Incorrectly identified as SAFE.")

if __name__ == "__main__":
    if not wait_for_server():
        print("Server failed to start.")
        sys.exit(1)
    
    test_safe_message()
    test_scam_message()
