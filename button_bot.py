import requests, json, socket, time, os, tempfile, wave, subprocess, io

# Try to import vosk for voice (optional)
try:
    import vosk
    vosk_model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vosk_model", "model")
    if os.path.exists(vosk_model_path):
        vosk_model = vosk.Model(vosk_model_path)
    else:
        vosk_model = None
except:
    vosk_model = None

TOKEN = os.environ.get("BOT_TOKEN", "8980273422:AAG7c84_OTsFSXnWGLzF-2nSGd8mOfrS0eA")
HOST = os.environ.get("SERVER_HOST", "localhost")
PORT = int(os.environ.get("SERVER_PORT", "9999"))

# ---------- Server communication ----------
def server(cmd):
    try:
        s = socket.socket(); s.settimeout(5)
        s.connect((HOST, PORT)); s.sendall(json.dumps(cmd).encode())
        r = json.loads(s.recv(4096).decode()); s.close()
        return r
    except Exception as e:
        return {"status":"error","message":str(e)}

# ---------- Telegram helpers ----------
def send(chat_id, text, markup=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    if markup: payload["reply_markup"] = json.dumps(markup)
    requests.post(url, json=payload)

def answer(cb_id):
    requests.post(f"https://api.telegram.org/bot{TOKEN}/answerCallbackQuery",
                  json={"callback_query_id": cb_id})

def send_document(chat_id, caption, file_data, filename):
    url = f"https://api.telegram.org/bot{TOKEN}/sendDocument"
    files = {'document': (filename, file_data.encode('utf-8'))}
    data = {'chat_id': chat_id, 'caption': caption}
    requests.post(url, files=files, data=data)

# ---------- Voice recognition ----------
def transcribe_ogg(file_path):
    if not vosk_model: return None
    wav_path = file_path + ".wav"
    try:
        subprocess.run(["ffmpeg","-i",file_path,"-ar","16000","-ac","1",wav_path], check=True, capture_output=True)
    except:
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_ogg(file_path)
            audio = audio.set_frame_rate(16000).set_channels(1)
            audio.export(wav_path, format="wav")
        except: return None
    if not os.path.exists(wav_path): return None
    wf = wave.open(wav_path, "rb")
    rec = vosk.KaldiRecognizer(vosk_model, wf.getframerate())
    text = ""
    while True:
        data = wf.readframes(4000)
        if len(data)==0: break
        if rec.AcceptWaveform(data):
            res = json.loads(rec.Result())
            text += res.get("text","") + " "
    res = json.loads(rec.FinalResult())
    text += res.get("text","")
    wf.close(); os.unlink(wav_path)
    return text.strip().lower()

# ---------- Keyboards ----------
def main_menu():
    return {"inline_keyboard":[
        [{"text":"💰 Balance","callback_data":"bal"},{"text":"💸 Deposit","callback_data":"dep"}],
        [{"text":"🏧 Withdraw","callback_data":"wit"},{"text":"📋 History","callback_data":"his"}],
        [{"text":"💸 Transfer","callback_data":"trf"},{"text":"🪙 Crypto","callback_data":"crypto"}],
        [{"text":"🤖 AI","callback_data":"ai"},{"text":"💳 Cardless","callback_data":"card"}],
        [{"text":"🧾 Bill Pay","callback_data":"bill"},{"text":"🎯 Goals","callback_data":"goal"}],
        [{"text":"📈 Invest","callback_data":"inv"},{"text":"💰 Loans","callback_data":"loan"}],
        [{"text":"🌍 Convert","callback_data":"conv"},{"text":"🔐 Change PIN","callback_data":"pin"}],
        [{"text":"🔐 2FA","callback_data":"2fa"},{"text":"📧 Email","callback_data":"email"}],
        [{"text":"📒 Ledger","callback_data":"ledger"},{"text":"❌ Logout","callback_data":"out"}]
    ]}

def login_btn():
    return {"inline_keyboard":[[{"text":"🔑 Login","callback_data":"login"}]]}

# ---------- State ----------
state = {}; user = {}

# ---------- Text handler ----------
def process_text(chat_id, text):
    s = state.get(chat_id); text = text.strip().lower()
    if s == "LOGIN_USER": user[chat_id] = {"username": text}; state[chat_id] = "LOGIN_PIN"; send(chat_id, "PIN:"); return
    if s == "LOGIN_PIN": user[chat_id]["pin"] = text; state[chat_id] = "LOGIN_SEC"; send(chat_id, "Security answer:"); return
    if s == "LOGIN_SEC":
        u = user[chat_id]["username"]; p = user[chat_id]["pin"]; a = text
        r = server({"cmd":"LOGIN","username":u,"pin":p,"security_answer":a})
        if r.get("status") == "ok":
            user[chat_id] = {"username":u,"logged_in":True}
            send(chat_id, f"✅ Logged in as {u}. Balance: ${r['balance']:.2f}", main_menu())
            server({"cmd":"SET_CHAT_ID","chat_id":chat_id})
        elif r.get("status") == "otp_required":
            send(r["chat_id"], f"🔐 Code: {r['otp_code']}")
            user[chat_id] = {"username":u,"temp_token":r["temp_token"]}
            state[chat_id] = "OTP"; send(chat_id, "Enter OTP:")
        else: send(chat_id, f"❌ {r.get('message','')}", login_btn())
        state.pop(chat_id, None); return
    if s == "OTP":
        u = user[chat_id]["username"]; t = user[chat_id]["temp_token"]
        r = server({"cmd":"VERIFY_OTP","username":u,"temp_token":t,"otp":text})
        if r.get("status") == "ok":
            user[chat_id] = {"username":u,"logged_in":True}
            send(chat_id, f"✅ Verified. Balance: ${r['balance']:.2f}", main_menu())
        else: send(chat_id,"❌ Invalid OTP", login_btn()); user.pop(chat_id, None)
        state.pop(chat_id, None); return
    if s in ("DEP_AMT","WDR_AMT"):
        try:
            amt = float(text); cmd = "DEPOSIT" if s == "DEP_AMT" else "WITHDRAW"
            r = server({"cmd":cmd,"amount":amt})
            if r.get("status") == "ok": send(chat_id, f"✅ New balance: ${r['new_balance']:.2f}", main_menu())
            else: send(chat_id, f"❌ {r.get('message','')}", main_menu())
        except: send(chat_id, "Invalid amount.", main_menu())
        state.pop(chat_id, None); return
    if s == "TRF_RECIP": user[chat_id]["trf_recip"] = text; state[chat_id] = "TRF_AMT"; send(chat_id, "Amount:"); return
    if s == "TRF_AMT":
        try:
            amt = float(text); target = user[chat_id]["trf_recip"]
            r = server({"cmd":"TRANSFER","recipient":target,"amount":amt})
            send(chat_id, f"{'✅' if r.get('status')=='ok' else '❌'} {r.get('message','')}", main_menu())
        except: send(chat_id, "Invalid amount.", main_menu())
        state.pop(chat_id, None); return
    if s == "AI_WAIT":
        r = server({"cmd":"AI_ASSIST","message":text})
        send(chat_id, r.get("reply","Sorry."), main_menu()); state.pop(chat_id, None); return
    if s == "CARD_AMT":
        try:
            amt = float(text); r = server({"cmd":"CARDLESS_GENERATE","amount":amt})
            if r.get("status") == "ok": send(chat_id, f"Code: {r['code']}\nAmount: ${r['amount']:.2f}\nExpires: {r['expires']}", main_menu())
            else: send(chat_id, f"❌ {r.get('message','')}", main_menu())
        except: send(chat_id, "Invalid amount.", main_menu())
        state.pop(chat_id, None); return
    if s == "BILL_BILLER": user[chat_id]["bill_biller"] = text; state[chat_id] = "BILL_AMT"; send(chat_id, "Amount:"); return
    if s == "BILL_AMT":
        try:
            amt = float(text); biller = user[chat_id]["bill_biller"]
            r = server({"cmd":"BILL_PAY","biller":biller,"amount":amt})
            if r.get("status") == "ok": send(chat_id, f"✅ Paid ${amt:.2f} to {biller}. New balance: ${r['new_balance']:.2f}", main_menu())
            else: send(chat_id, f"❌ {r.get('message','')}", main_menu())
        except: send(chat_id, "Invalid amount.", main_menu())
        state.pop(chat_id, None); return
    if s == "GOAL_NAME": user[chat_id]["goal_name"] = text; state[chat_id] = "GOAL_TARGET"; send(chat_id, "Target amount:"); return
    if s == "GOAL_TARGET":
        try:
            target = float(text); name = user[chat_id]["goal_name"]
            r = server({"cmd":"SAVINGS_GOAL_CREATE","goal_name":name,"target":target})
            send(chat_id, f"{'✅' if r.get('status')=='ok' else '❌'} {r.get('message','')}", main_menu())
        except: send(chat_id, "Invalid target.", main_menu())
        state.pop(chat_id, None); return
    if s == "INV_BUY_SYM": user[chat_id]["inv_sym"] = text.upper(); state[chat_id] = "INV_BUY_AMT"; send(chat_id, "Amount in USD:"); return
    if s == "INV_BUY_AMT":
        try:
            amt = float(text); sym = user[chat_id]["inv_sym"]
            r = server({"cmd":"INVEST_BUY","symbol":sym,"amount":amt})
            send(chat_id, f"{'✅' if r.get('status')=='ok' else '❌'} {r.get('message','')}", main_menu())
        except: send(chat_id, "Invalid amount.", main_menu())
        state.pop(chat_id, None); return
    if s == "INV_SELL_SYM": user[chat_id]["inv_sym"] = text.upper(); state[chat_id] = "INV_SELL_QTY"; send(chat_id, "Quantity:"); return
    if s == "INV_SELL_QTY":
        try:
            qty = float(text); sym = user[chat_id]["inv_sym"]
            r = server({"cmd":"INVEST_SELL","symbol":sym,"quantity":qty})
            send(chat_id, f"{'✅' if r.get('status')=='ok' else '❌'} {r.get('message','')}", main_menu())
        except: send(chat_id, "Invalid quantity.", main_menu())
        state.pop(chat_id, None); return
    if s == "LOAN_AMT": user[chat_id]["loan_amt"] = text; state[chat_id] = "LOAN_TERM"; send(chat_id, "Term (months):"); return
    if s == "LOAN_TERM":
        try:
            principal = float(user[chat_id]["loan_amt"]); term = int(text)
            r = server({"cmd":"LOAN_REQUEST","principal":principal,"term":term})
            send(chat_id, f"{'✅' if r.get('status')=='ok' else '❌'} {r.get('message','')}", main_menu())
        except: send(chat_id, "Invalid input.", main_menu())
        state.pop(chat_id, None); return
    if s == "LOAN_PAY_ID": user[chat_id]["loan_id"] = text; state[chat_id] = "LOAN_PAY_AMT"; send(chat_id, "Payment:"); return
    if s == "LOAN_PAY_AMT":
        try:
            lid = int(user[chat_id]["loan_id"]); amt = float(text)
            r = server({"cmd":"LOAN_PAY","loan_id":lid,"amount":amt})
            send(chat_id, f"{'✅' if r.get('status')=='ok' else '❌'} {r.get('message','')}", main_menu())
        except: send(chat_id, "Invalid input.", main_menu())
        state.pop(chat_id, None); return
    if s == "CONV_FROM": user[chat_id]["conv_from"] = text.upper(); state[chat_id] = "CONV_TO"; send(chat_id, "To currency:"); return
    if s == "CONV_TO": user[chat_id]["conv_to"] = text.upper(); state[chat_id] = "CONV_AMT"; send(chat_id, "Amount:"); return
    if s == "CONV_AMT":
        try:
            amt = float(text); f = user[chat_id]["conv_from"]; t = user[chat_id]["conv_to"]
            r = server({"cmd":"CURRENCY_CONVERT","from":f,"to":t,"amount":amt})
            if r.get("status") == "ok": send(chat_id, f"{amt} {f} = {r['converted']} {t}", main_menu())
            else: send(chat_id, f"❌ {r.get('message','')}", main_menu())
        except: send(chat_id, "Invalid amount.", main_menu())
        state.pop(chat_id, None); return
    if s == "PIN_OLD": user[chat_id]["old_pin"] = text; state[chat_id] = "PIN_NEW"; send(chat_id, "New 4-digit PIN:"); return
    if s == "PIN_NEW":
        old = user[chat_id].get("old_pin"); new = text
        r = server({"cmd":"CHANGE_PIN","old_pin":old,"new_pin":new})
        send(chat_id, f"{'✅' if r.get('status')=='ok' else '❌'} {r.get('message','')}", main_menu())
        state.pop(chat_id, None); return
    if s == "SET_EMAIL":
        email = text if text.lower() != "none" else ""
        r = server({"cmd":"SET_EMAIL","email":email})
        send(chat_id, f"{'✅' if r.get('status')=='ok' else '❌'} Email set.", main_menu())
        state.pop(chat_id, None); return
    # Crypto buy flow
    if s == "CRYPTO_BUY_CURRENCY":
        user[chat_id] = user.get(chat_id, {})
        user[chat_id]["crypto_currency"] = text.upper()
        state[chat_id] = "CRYPTO_BUY_USD"
        send(chat_id, "Amount in USD to spend:")
        return
    if s == "CRYPTO_BUY_USD":
        try:
            usd = float(text)
            curr = user[chat_id].get("crypto_currency","")
            r = server({"cmd":"CRYPTO_BUY","currency":curr,"amount":usd})
            send(chat_id, f"{'✅' if r.get('status')=='ok' else '❌'} {r.get('message','')}", main_menu())
        except: send(chat_id, "Invalid amount.", main_menu())
        state.pop(chat_id, None); return
    # Crypto sell flow
    if s == "CRYPTO_SELL_CURRENCY":
        user[chat_id] = user.get(chat_id, {})
        user[chat_id]["crypto_currency"] = text.upper()
        state[chat_id] = "CRYPTO_SELL_AMOUNT"
        send(chat_id, "Crypto amount to sell:")
        return
    if s == "CRYPTO_SELL_AMOUNT":
        try:
            amt = float(text)
            curr = user[chat_id].get("crypto_currency","")
            r = server({"cmd":"CRYPTO_SELL","currency":curr,"amount":amt})
            send(chat_id, f"{'✅' if r.get('status')=='ok' else '❌'} {r.get('message','')}", main_menu())
        except: send(chat_id, "Invalid amount.", main_menu())
        state.pop(chat_id, None); return
    # Crypto send flow
    if s == "CRYPTO_SEND_CURRENCY":
        user[chat_id] = user.get(chat_id, {})
        user[chat_id]["crypto_currency"] = text.upper()
        state[chat_id] = "CRYPTO_SEND_RECIPIENT"
        send(chat_id, "Recipient username:")
        return
    if s == "CRYPTO_SEND_RECIPIENT":
        user[chat_id]["crypto_recipient"] = text
        state[chat_id] = "CRYPTO_SEND_AMOUNT"
        send(chat_id, "Crypto amount to send:")
        return
    if s == "CRYPTO_SEND_AMOUNT":
        try:
            amt = float(text)
            curr = user[chat_id].get("crypto_currency","")
            target = user[chat_id].get("crypto_recipient","")
            r = server({"cmd":"CRYPTO_SEND","currency":curr,"amount":amt,"recipient":target})
            send(chat_id, f"{'✅' if r.get('status')=='ok' else '❌'} {r.get('message','')}", main_menu())
        except: send(chat_id, "Invalid amount.", main_menu())
        state.pop(chat_id, None); return
    # Registration flow
    if s == "REG_USER": user[chat_id] = {"reg_username": text}; state[chat_id] = "REG_PIN"; send(chat_id, "PIN:"); return
    if s == "REG_PIN": user[chat_id]["reg_pin"] = text; state[chat_id] = "REG_SEC_Q"; send(chat_id, "Security question:"); return
    if s == "REG_SEC_Q": user[chat_id]["reg_sec_q"] = text; state[chat_id] = "REG_SEC_A"; send(chat_id, "Answer:"); return
    if s == "REG_SEC_A":
        u = user[chat_id]["reg_username"]; p = user[chat_id]["reg_pin"]; q = user[chat_id]["reg_sec_q"]; a = text
        r = server({"cmd":"REGISTER","username":u,"pin":p,"security_q":q,"security_a":a})
        send(chat_id, f"{'✅' if r.get('status')=='ok' else '❌'} {r.get('message','')}", login_btn())
        state.pop(chat_id, None); user.pop(chat_id, None); return
    # Default
    if text == "/start":
        if user.get(chat_id, {}).get("logged_in"):
            send(chat_id, f"Welcome back, {user[chat_id]['username']}!", main_menu())
        else:
            send(chat_id, "Welcome to Wyllene ATM! Please log in.", login_btn())
    else:
        send(chat_id, "Use the buttons below.", main_menu() if user.get(chat_id, {}).get("logged_in") else login_btn())

# ---------- Callback handler ----------
def process_callback(chat_id, cb_id, data):
    answer(cb_id)
    is_logged = user.get(chat_id, {}).get("logged_in")
    if not is_logged and data not in ("login","register_start"):
        send(chat_id, "Login first.", login_btn()); return
    if data == "login": state[chat_id] = "LOGIN_USER"; send(chat_id, "Username:")
    elif data == "register_start": state[chat_id] = "REG_USER"; send(chat_id, "Choose a username:")
    elif data == "bal":
        r = server({"cmd":"BALANCE"}); send(chat_id, f"💰 Balance: ${r.get('balance',0):.2f}", main_menu())
    elif data == "dep": state[chat_id] = "DEP_AMT"; send(chat_id, "Amount to deposit:")
    elif data == "wit": state[chat_id] = "WDR_AMT"; send(chat_id, "Amount to withdraw:")
    elif data == "his":
        r = server({"cmd":"HISTORY"}); hist = r.get("history",[])
        if hist:
            lines = [f"{t['time']} {t['type']} ${t['amount']:.2f}" for t in hist[:5]]
            send(chat_id, "Last:\n"+"\n".join(lines), main_menu())
        else: send(chat_id, "No transactions.", main_menu())
    elif data == "trf": state[chat_id] = "TRF_RECIP"; send(chat_id, "Recipient:")
    elif data == "ai": state[chat_id] = "AI_WAIT"; send(chat_id, "Ask anything:")
    elif data == "card": state[chat_id] = "CARD_AMT"; send(chat_id, "Amount for code:")
    elif data == "bill": state[chat_id] = "BILL_BILLER"; send(chat_id, "Biller name:")
    elif data == "goal": state[chat_id] = "GOAL_NAME"; send(chat_id, "Goal name:")
    elif data == "inv":
        markup = {"inline_keyboard":[[{"text":"📊 Portfolio","callback_data":"inv_port"},{"text":"🟢 Buy","callback_data":"inv_buy"},{"text":"🔴 Sell","callback_data":"inv_sell"}]]}
        send(chat_id, "Invest:", markup)
    elif data == "inv_buy": state[chat_id] = "INV_BUY_SYM"; send(chat_id, "Symbol:")
    elif data == "inv_sell": state[chat_id] = "INV_SELL_SYM"; send(chat_id, "Symbol:")
    elif data == "inv_port":
        r = server({"cmd":"INVEST_PORTFOLIO"}); port = r.get("portfolio",[])
        if port:
            lines = [f"{p['symbol']}: {p['quantity']:.2f} sh @ ${p['current_price']:.2f} = ${p['value']:.2f}" for p in port]
            send(chat_id, "Portfolio:\n"+"\n".join(lines), main_menu())
        else: send(chat_id, "No holdings.", main_menu())
    elif data == "loan":
        markup = {"inline_keyboard":[[{"text":"📋 Status","callback_data":"loan_stat"},{"text":"🆕 Request","callback_data":"loan_req"},{"text":"💸 Pay","callback_data":"loan_pay"}]]}
        send(chat_id, "Loan:", markup)
    elif data == "loan_stat":
        r = server({"cmd":"LOAN_STATUS"}); loans = r.get("loans",[])
        if loans:
            lines = [f"ID:{l['loan_id']} Rem:{l['remaining']:.2f} Month:{l['monthly_payment']:.2f}" for l in loans]
            send(chat_id, "Loans:\n"+"\n".join(lines), main_menu())
        else: send(chat_id, "No active loans.", main_menu())
    elif data == "loan_req": state[chat_id] = "LOAN_AMT"; send(chat_id, "Amount:")
    elif data == "loan_pay": state[chat_id] = "LOAN_PAY_ID"; send(chat_id, "Loan ID:")
    elif data == "conv": state[chat_id] = "CONV_FROM"; send(chat_id, "From currency (USD, EUR, GBP, JPY):")
    elif data == "pin": state[chat_id] = "PIN_OLD"; send(chat_id, "Current PIN:")
    elif data == "2fa":
        r = server({"cmd":"TOGGLE_2FA","enable":True}); send(chat_id, f"{'✅' if r.get('status')=='ok' else '❌'} 2FA enabled.", main_menu())
    elif data == "email": state[chat_id] = "SET_EMAIL"; send(chat_id, "Your email (or 'none'):")
    elif data == "ledger":
        r = server({"cmd":"LEDGER"})
        if r.get("status") == "ok":
            ledger = r.get("ledger",[])
            if ledger:
                lines = [f"{t['time']} {t['type']} ${t['amount']:.2f} Bal:${t['balance']:.2f}" for t in ledger[:10]]
                send(chat_id, "📒 Recent transactions:\n"+"\n".join(lines), main_menu())
                csv_r = server({"cmd":"CSV_EXPORT"})
                if csv_r.get("status") == "ok":
                    send_document(chat_id, "Full ledger", csv_r["csv"], "ledger.csv")
            else:
                send(chat_id, "No transactions yet.", main_menu())
        else:
            send(chat_id, "Could not load ledger.", main_menu())
    elif data == "crypto":
        markup = {"inline_keyboard":[
            [{"text":"📊 Portfolio","callback_data":"crypto_portfolio"}],
            [{"text":"🟢 Buy","callback_data":"crypto_buy"}],
            [{"text":"🔴 Sell","callback_data":"crypto_sell"}],
            [{"text":"💸 Send","callback_data":"crypto_send"}]
        ]}
        send(chat_id, "Crypto options:", markup)
    elif data == "crypto_buy": state[chat_id] = "CRYPTO_BUY_CURRENCY"; send(chat_id, "Enter crypto (BTC, ETH, USDT):")
    elif data == "crypto_sell": state[chat_id] = "CRYPTO_SELL_CURRENCY"; send(chat_id, "Enter crypto (BTC, ETH, USDT):")
    elif data == "crypto_send": state[chat_id] = "CRYPTO_SEND_CURRENCY"; send(chat_id, "Enter crypto (BTC, ETH, USDT):")
    elif data == "crypto_portfolio":
        r = server({"cmd":"CRYPTO_PORTFOLIO"})
        if r.get("status") == "ok":
            port = r.get("portfolio",[])
            if port:
                lines = [f"{p['currency']}: {p['balance']:.6f} @ ${p['price_usd']:.2f} = ${p['value_usd']:.2f}" for p in port]
                total_msg = f"🪙 Portfolio:\n" + "\n".join(lines) + f"\nTotal: ${r['total_value_usd']:.2f}"
                send(chat_id, total_msg, main_menu())
            else:
                send(chat_id, "No crypto holdings.", main_menu())
        else:
            send(chat_id, "Error.", main_menu())
    elif data == "out": user.pop(chat_id, None); state.pop(chat_id, None); send(chat_id, "Logged out.", login_btn())
    else: send(chat_id, "Unknown action.", main_menu())

# ---------- Polling loop ----------
def main():
    offset = 0; print("🤖 Bot started (voice + crypto + ledger).")
    while True:
        try:
            resp = requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates", params={"offset":offset,"timeout":30})
            data = resp.json()
            if data.get("ok"):
                for upd in data["result"]:
                    offset = upd["update_id"] + 1
                    if "message" in upd:
                        msg = upd["message"]; chat = msg["chat"]["id"]
                        if "text" in msg:
                            process_text(chat, msg["text"])
                        elif "voice" in msg:
                            file_id = msg["voice"]["file_id"]
                            file_url = f"https://api.telegram.org/bot{TOKEN}/getFile?file_id={file_id}"
                            file_resp = requests.get(file_url).json()
                            if file_resp.get("ok"):
                                download_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_resp['result']['file_path']}"
                                ogg_file = tempfile.NamedTemporaryFile(delete=False, suffix=".ogg")
                                ogg_file.write(requests.get(download_url).content)
                                ogg_file.close()
                                transcript = transcribe_ogg(ogg_file.name)
                                os.unlink(ogg_file.name)
                                if transcript:
                                    send(chat, f"🗣️ Heard: {transcript}")
                                    process_text(chat, transcript)
                                else:
                                    send(chat, "Sorry, couldn't understand the voice message.")
                            else:
                                send(chat, "Failed to download voice file.")
                    elif "callback_query" in upd:
                        cb = upd["callback_query"]; process_callback(cb["message"]["chat"]["id"], cb["id"], cb["data"])
        except Exception as e: print("Poll error:", e)
        time.sleep(0.5)

if __name__ == "__main__":
    main()
