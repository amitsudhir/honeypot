import requests

BASE_URL = "http://127.0.0.1:8000"

def check_methods():
    print(f"Testing {BASE_URL}/")
    
    # Test GET
    try:
        res_get = requests.get(f"{BASE_URL}/")
        print(f"GET / -> {res_get.status_code}")
    except Exception as e:
        print(f"GET Failed: {e}")

    # Test HEAD
    try:
        res_head = requests.head(f"{BASE_URL}/")
        print(f"HEAD / -> {res_head.status_code}")
    except Exception as e:
        print(f"HEAD Failed: {e}")

    # Test POST on Root (Should be 405)
    try:
        res_post = requests.post(f"{BASE_URL}/", json={})
        print(f"POST / -> {res_post.status_code} (Expected 405)")
    except Exception as e:
        print(f"POST Failed: {e}")

if __name__ == "__main__":
    check_methods()
