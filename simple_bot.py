import requests, time, json
TOKEN = "8980273422:AAG7c84_OTsFSXnWGLzF-2nSGd8mOfrS0eA"
offset = 0
print("Simple listener running... Send a message now.")
while True:
    r = requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates", params={"offset": offset, "timeout": 30})
    data = r.json()
    if data.get("ok") and data["result"]:
        for upd in data["result"]:
            offset = upd["update_id"] + 1
            msg = upd.get("message", {})
            if "text" in msg:
                print("Got message:", msg["text"])
    time.sleep(0.5)
