import requests, time, json
TOKEN = "8980273422:AAG7c84_OTsFSXnWGLzF-2nSGd8mOfrS0eA"
offset = 0
print("Listening... (send /start to @wylleneATM_bot now)")
while True:
    r = requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates", params={"offset": offset, "timeout": 30})
    data = r.json()
    if data["ok"] and data["result"]:
        for upd in data["result"]:
            offset = upd["update_id"] + 1
            print(json.dumps(upd, indent=2))
    time.sleep(0.5)
