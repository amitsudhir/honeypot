# CURL Examples

## Check SAFE Message
```bash
curl -X POST "http://127.0.0.1:8000/honeypot" \
     -H "Content-Type: application/json" \
     -H "x-api-key: <YOUR_APP_API_KEY>" \
     -d '{"message": "Hello, how are you?", "session_id": "test1"}'
```

## Check SCAM Message
```bash
curl -X POST "http://127.0.0.1:8000/honeypot" \
     -H "Content-Type: application/json" \
     -H "x-api-key: <YOUR_APP_API_KEY>" \
     -d '{"message": "Urgent! You have won $5000. Send UPI to 9876543210@ybl to claim.", "session_id": "test2"}'
```

## Check Persistence (Reply to Agent)
```bash
curl -X POST "http://127.0.0.1:8000/honeypot" \
     -H "Content-Type: application/json" \
     -H "x-api-key: <YOUR_APP_API_KEY>" \
     -d '{"message": "Why are you delaying? Send money now!", "session_id": "test2"}'
```
