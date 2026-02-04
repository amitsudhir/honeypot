import requests
import time
from datetime import datetime

# Your Render URL
URL = "https://honeypot-ak8x.onrender.com/"
INTERVAL = 14 * 60  # 14 minutes (Render sleeps after 15)

def keep_alive():
    print(f"🔥 Keep-Alive script started for {URL}")
    print(f"Ping interval: 14 minutes")
    
    while True:
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            response = requests.get(URL)
            
            if response.status_code == 200:
                print(f"[{timestamp}] ✅ Ping Success! Status: {response.status_code}")
            else:
                print(f"[{timestamp}] ⚠️ Ping Returned: {response.status_code}")
                
        except Exception as e:
            print(f"[{timestamp}] ❌ Ping Failed: {e}")
        
        # Wait for 14 minutes
        time.sleep(INTERVAL)

if __name__ == "__main__":
    keep_alive()
