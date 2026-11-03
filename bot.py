#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OOREDOO Bot — Oxylabs — 2Go Free + Balance"""
import telebot
from telebot.async_telebot import AsyncTeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio, requests, json, os, re, uuid, base64, time, urllib.parse, logging
from datetime import datetime, timedelta
from pathlib import Path
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.getLogger("urllib3").setLevel(logging.CRITICAL)

TOKEN = "7776492585:AAGxdB_8makFSF561lHyrZTgbS4pKh8FB5o"
ADMIN_ID = 6860937572
NOTIFY_GROUP = "@ifoekdjdh"

BFF = "https://apis.ooredoo.dz/api/ooredoo-bff"
AUTH = "https://apis.ooredoo.dz/api/auth/realms/myooredoo/protocol/openid-connect/token"
CID = "myooredoo-app"
XV = "1.5.17"
XSIG = "5c7641dbb82cf11066df68afc91541c967640106a95192740b43d51a5ce6777a"

PROXY_HOST = "pr.oxylabs.io:7777"
PROXY_USER = "customer-resi_4b78d26c-sessid-0211331481-sesstime-10"
PROXY_PASS = "WYb+48cZoZ+1"

def _purl():
    u = urllib.parse.quote(PROXY_USER, safe='')
    p = urllib.parse.quote(PROXY_PASS, safe='')
    return f"http://{u}:{p}@{PROXY_HOST}"

INT1 = ("JWBTpxXcH7KY9EXYeIRp8NjQMx2dt3vF8ejjoARazyoFzOw6Cu8+wkeV+zSVHSTeI6a12SG/FU+Q/9uBrcN71Rl"
"YO4CulD2x375NKwJRAInar8DVUilHBKUfjEsoHd6EwfLCfdYzLNXJu9POfEf6tqKn3PUe0pY6qZxWLhyVAFHw8Qwb"
"52ZqdI2soCH4S3mrz+OZL+YovdGSUKlXKIkxVroAMTAg3jljLF7gvXaEsB/O3uW+tbkBMwSX2uTOwf+rh3sgOF/"
"zPhKCFgRvZmU1o87Fa96Y/+wOcK+UpfXTCBYVrvQ1wG6ryC7vHMSqgUhYJK4tbSoti0zv4av9pwxh9Iv2MgsMENj"
"yKBK/TuFZxEG3xQCKj1LTMgn2xBEeKcbsKrEW3xDRwsccGI3D7GHnbUlhdI4ujDIRQVKHaZSwhTp+32Cr4EB/Qt"
"8p/xRbdgCde9MUlM4AYIGlfyVoHSkOvTu5c0DIIy1EhowtAkbKIJl49wsYKWvpT/nXFWzeXP3R2qzaclCnIb9qih"
"hrarmwz8l8XH2T+f7AK2uSNiuWLG5Fy2mM/YLmuJPZT9Ciag/mpy7JGImKNQAcFbSAInBdKQjUKT+COzZfrXj5r"
"wil9/HDMtuzIovq8hrQGY+roTfVPheTLWmcjkVCOL8VXAHjPb22vOuqrkMioWT9CQ5O8RgW7RKHrObeKQMp8F7tS"
"jOqkxYDFkPVN1G4nkEBrTlPKK9YtPl+j7IuH9fGcDTwhCTTqP8peuBryW0L11tApvAEi7VkJyBxpVxW")
INT2 = ("JWBTpxXcH7KR/kzaHeUUydDWODuU4i3H4fL9gCgKzyYfyN4qLJJE8keV+zSVHSTeI6aEyC2tbSza/NGmkflQ/Ug"
"aNZSN9SKxz7tcdQckHY25n6mOaDZ9PPMQmF4sKZqDwebce/c1SNGNn6qvTULW/L348aJvy7Vii6dyPTu3OSPV9Aw"
"KwGwQKNHN61HyK3jx/fa8Os5ux9u3Q654YLZrAJ99QGEm/C9nEBPmlHC98RjovLGBnuJOGx6k7fnyrt/Ogy5fNg"
"+tBgi5HEsoXDAwutX7TOWfx4YKHpKW//TvPRQgp69e2Xqa+CvGJJ+a/WlPMPhRCSsfo0OG04mVvlkc8eXiLzV/GP"
"uJCEmcRf9Z6V+xoDyMtU7OZ3XT5BMhI/D/N68LsRn/9dIBH6X7n0WAW3tzeKZK1zENWFKrd7aLlzEdwFzO/1JTQs"
"EDom5TRie0Kd5yic4BGvS1C1BsA2wJhzyiZ2j7RUE9m8tOAkPEIs929FYIfmH8XcCQKHT0TqT0+N+wCiyfNawPlD"
"hZWcObscFZeEmKgvqiUFCoCj6xI1hvyHK0nu7fnZ/sGc6oNT/SrFjubYWjOyoYFL7gMnlYAhyjZhjuAwN1m1/wjw"
"rOx8DbFr2NW8qb3hv+CIzK1zL3LDryKjqNkTxcOp4aJnmSTa73guCEmWc7pnLkLw5O8RgW7RKHrObeeQ0l9lu4H"
"WXwlhdWRxvVMQDimhtTrGASL6sIuaxyhOkrH4HFImP70SaCoK9+euMxnzkPjg9HqPIFj+I0KSMloVxW")

BASE = Path(os.path.expanduser("~")) / "ooredoo_bot"
BASE.mkdir(parents=True, exist_ok=True)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(), logging.FileHandler(str(BASE / "bot.log"), encoding='utf-8')])

http = requests.Session()
adapter = requests.adapters.HTTPAdapter(pool_connections=20, pool_maxsize=20, max_retries=1)
http.mount("https://", adapter)
http.mount("http://", adapter)

def mask(m):
    if not m or len(m) < 4: return "05********"
    return m[:2] + "********"

def now_ms(): return str(int(time.time() * 1000))
def new_iid():
    u = uuid.uuid4().hex
    return f"{u[:8]}-{u[8:12]}-11{u[12:16]}-{u[16:20]}-{u[20:32]}{now_ms()}"
def new_psig(iid):
    return base64.b64encode(json.dumps({"platform":"android","is-physical-device":True,"device-id":iid}, separators=(',',':')).encode()).decode()
def new_corr(): return uuid.uuid4().hex + now_ms()
def new_fp(): return uuid.uuid4().hex + uuid.uuid4().hex[:32]

def _do(method, url, headers, body="", proxy=None, timeout=8):
    proxies = None
    if proxy and proxy.get("host"):
        up = f"{proxy['userpass']}@" if proxy.get("userpass") else ""
        proxies = {"http": f"http://{up}{proxy['host']}", "https": f"http://{up}{proxy['host']}"}
    try:
        if method == "GET": r = http.get(url, headers=headers, proxies=proxies, timeout=timeout, verify=False)
        elif method == "HEAD": r = http.head(url, headers=headers, proxies=proxies, timeout=timeout, verify=False)
        else: r = http.post(url, headers=headers, data=body, proxies=proxies, timeout=timeout, verify=False)
        txt = r.text
        if "<!DOCTYPE" in txt or "<html" in txt: return {"ip_blocked": True, "code": r.status_code}
        try: j = r.json()
        except: j = None
        return {"code": r.status_code, "body": txt, "headers": {k.lower(): v for k, v in r.headers.items()}, "json": j}
    except Exception as e:
        logging.warning(f"[REQ] {url[-40:]} → {str(e)[:80]}")
        return None

def req(method, url, headers, body="", proxy=None, timeout=8):
    res = _do(method, url, headers, body, proxy, timeout)
    if res is None and proxy is not None:
        res = _do(method, url, headers, body, None, timeout)
    return res

def base_h(ms, fp, corr, ts, iid, psig):
    return {"User-Agent":"Dart/3.11 (dart:io)","Accept-Encoding":"gzip","x-msisdn":ms,
            "x-device-fingerprint":fp,"x-platform-origin":"mobile-android",
            "x-correlation-id":corr,"platform":"android","x-version":XV,
            "x-signature":XSIG,"x-platform-data-signature":psig,
            "x-timestamp":ts,"x-instance-id":iid}

def web_h(ms, token, tok_hdrs, platform="web"):
    ts = tok_hdrs.get("tok_timestamp") or now_ms()
    iid = tok_hdrs.get("tok_instance_id") or new_iid()
    psig = tok_hdrs.get("tok_plat_sig") or new_psig(iid)
    if platform == "web":
        return {"User-Agent":"Dart/3.11 (dart:io)","Accept-Encoding":"gzip","x-msisdn":ms,
                "x-device-fingerprint":new_fp(),"x-platform-origin":"web",
                "authorization":f"Bearer {token}","x-correlation-id":new_corr(),
                "platform":"web","x-version":XV,"x-signature":XSIG,
                "x-platform-data-signature":psig,"x-timestamp":ts,"x-instance-id":iid,
                "origin":"https://my.ooredoo.dz","referer":"https://my.ooredoo.dz/","accept":"*/*"}
    else:
        h = base_h(ms, new_fp(), new_corr(), ts, iid, psig)
        h["authorization"] = f"Bearer {token}"
        h["accept"] = "*/*"
        return h

def send_otp(ms):
    iid = new_iid(); psig = new_psig(iid)
    all_proxies = [{"host": PROXY_HOST, "userpass": f"{PROXY_USER}:{PROXY_PASS}"}, None]
    for proxy in all_proxies:
        ts, corr = now_ms(), new_corr()
        h1 = base_h(ms, new_fp(), corr, ts, iid, psig)
        r1 = req("GET", f"{BFF}/users/status?msisdn={ms}", h1, proxy=proxy, timeout=8)
        if not r1 or r1.get("ip_blocked") or r1.get("code") != 200: continue
        h2 = base_h(ms, new_fp(), new_corr(), now_ms(), iid, psig)
        r2 = req("HEAD", f"{BFF}/userInfo?msisdn={ms}", h2, proxy=proxy, timeout=8)
        if not r2 or r2.get("ip_blocked") or r2.get("code") not in (200, 204): continue
        for p34 in all_proxies:
            ts = now_ms(); corr = new_corr()
            h3 = base_h(ms, new_fp(), corr, ts, iid, psig)
            h3["content-type"] = "application/json; charset=utf-8"
            h3["x-native-integrity-token"] = INT1
            h3["x-path"] = "/api/auth/realms/myooredoo/protocol/openid-connect/token"
            h3["x-method"] = "POST"
            r3 = req("POST", f"{BFF}/checkpoint/token", h3, body="{}", proxy=p34, timeout=8)
            if not r3 or r3.get("ip_blocked"): continue
            nonce = r3.get("headers", {}).get("x-nonce-id")
            chronos = r3.get("headers", {}).get("x-chronos-id")
            if not nonce or not chronos: continue
            h4 = {"User-Agent":"Dart/3.11 (dart:io)","Accept-Encoding":"gzip","x-msisdn":ms,
                  "x-device-fingerprint":new_fp(),"x-nonce-id":nonce,"x-platform-origin":"mobile-android",
                  "platform":"android","x-version":XV,"x-signature":XSIG,
                  "x-chronos-id":chronos,"x-timestamp":ts,"x-platform-info":psig,
                  "x-force-update":"true","x-instance-id":iid,"Content-Type":"application/x-www-form-urlencoded"}
            b4 = urllib.parse.urlencode({"client_id":CID,"grant_type":"password","username":ms})
            r4 = req("POST", AUTH, h4, body=b4, proxy=p34, timeout=15)
            if r4 and r4.get("code") in (401, 403):
                return {"proxy": p34}
    return None

def verify_otp(ms, otp, proxy):
    iid = new_iid(); psig = new_psig(iid)
    ts = now_ms(); corr = new_corr()
    h6 = base_h(ms, new_fp(), corr, ts, iid, psig)
    h6["content-type"] = "application/json; charset=utf-8"
    h6["x-native-integrity-token"] = INT2
    h6["x-path"] = "/api/auth/realms/myooredoo/protocol/openid-connect/token"
    h6["x-method"] = "POST"
    r6 = req("POST", f"{BFF}/checkpoint/token", h6, body="{}", proxy=proxy, timeout=8)
    if not r6 or r6.get("ip_blocked"): return None
    nonce2 = r6.get("headers", {}).get("x-nonce-id")
    chronos2 = r6.get("headers", {}).get("x-chronos-id")
    if not nonce2 or not chronos2: return None
    fp7 = new_fp()
    h7 = {"User-Agent":"Dart/3.11 (dart:io)","Accept-Encoding":"gzip","x-msisdn":ms,
          "x-device-fingerprint":fp7,"x-nonce-id":nonce2,"x-platform-origin":"mobile-android",
          "platform":"android","x-version":XV,"x-signature":XSIG,
          "x-chronos-id":chronos2,"x-timestamp":ts,"x-platform-info":psig,
          "x-force-update":"true","x-instance-id":iid,"Content-Type":"application/x-www-form-urlencoded"}
    b7 = urllib.parse.urlencode({"client_id":CID,"grant_type":"password","username":ms,"otp":otp})
    r7 = req("POST", AUTH, h7, body=b7, proxy=proxy, timeout=15)
    if not r7: return None
    if r7.get("code") in (401, 403): return "wrong_otp"
    if r7.get("code") == 200 and r7.get("json") and "access_token" in r7["json"]:
        j = r7["json"]
        return {"access_token": j["access_token"], "refresh_token": j.get("refresh_token",""),
                "token_proxy_host": proxy["host"] if proxy else "direct",
                "token_proxy_user": proxy["userpass"] if proxy else "",
                "tok_fingerprint": fp7, "tok_timestamp": ts, "tok_instance_id": iid,
                "tok_plat_sig": psig}
    return None

def get_proxy(account):
    if account.get("token_proxy_host") == "direct": return None
    return {"host": account.get("token_proxy_host"), "userpass": account.get("token_proxy_user")}

def purchase_2go(account):
    ms = account["msisdn"]
    tok_hdrs = {"tok_timestamp": account.get("tok_timestamp"),
                "tok_instance_id": account.get("tok_instance_id"),
                "tok_plat_sig": account.get("tok_plat_sig")}
    h = web_h(ms, account["access_token"], tok_hdrs, "web")
    h["content-type"] = "application/json; charset=utf-8"
    body = json.dumps({"bundleCode": "BTL_24H_DATA_Free_2Go"})
    proxy = get_proxy(account)
    res = req("POST", f"{BFF}/cvm/dynamic-bundle-purchase", h, body=body, proxy=proxy, timeout=20)
    if not res: return {"ok": False, "msg": "❌ خطأ اتصال"}
    code = res.get("code")
    logging.info(f"[2Go] → {code}")
    if code == 200:
        return {"ok": True, "msg": "🎉 <b>تم تفعيل 2Go Free</b>\n\n📦 2 جيجا — 24 ساعة"}
    if code == 401: return {"ok": False, "msg": "🔐 Token منتهي — سجل جديد"}
    if code in (402, 409): return {"ok": False, "msg": "⏰ مفعّل مسبقاً أو رصيد غير كافي"}
    if res.get("ip_blocked"): return {"ok": False, "msg": "🛡️ WAF حجب الطلب"}
    return {"ok": False, "msg": f"❌ فشل (code={code})"}

def check_balance(account):
    """يجرب 4 endpoints × 2 headers"""
    ms = account["msisdn"]
    tok_hdrs = {"tok_timestamp": account.get("tok_timestamp"),
                "tok_instance_id": account.get("tok_instance_id"),
                "tok_plat_sig": account.get("tok_plat_sig")}
    proxy = get_proxy(account)
    
    h_web = web_h(ms, account["access_token"], tok_hdrs, "web")
    h_mob = web_h(ms, account["access_token"], tok_hdrs, "mobile")
    
    endpoints = [
        f"{BFF}/api/v1/subscribers/main-balance/{ms}",
        f"{BFF}/subscriptions/getAccountInfo",
        f"{BFF}/api/v1/subscribers/balance",
        f"{BFF}/subscriber/balance/{ms}",
    ]
    
    def find_bal(obj, path=""):
        results = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                np = f"{path}.{k}" if path else k
                kl = k.lower()
                if any(kw in kl for kw in ["balance", "credit", "solde", "montant", "recharge"]):
                    if isinstance(v, (int, float)) and v >= 0:
                        results.append((np, v))
                    elif isinstance(v, str) and v.strip().replace('.','',1).isdigit():
                        results.append((np, float(v)))
                results.extend(find_bal(v, np))
        elif isinstance(obj, list):
            for i, v in enumerate(obj[:3]):
                results.extend(find_bal(v, f"{path}[{i}]"))
        return results
    
    debug = []
    for url in endpoints:
        for hname, h in [("web", h_web), ("mobile", h_mob)]:
            try:
                res = req("GET", url, h, proxy=proxy, timeout=15)
                code = res.get("code") if res else None
                ep_short = "/".join(url.split("/")[-2:])[:35]
                logging.info(f"[BAL] {ep_short} ({hname}) → {code}")
                
                if res and code == 200 and res.get("json"):
                    cands = find_bal(res["json"])
                    if cands:
                        path, val = cands[0]
                        return {"ok": True, "balance": val, "path": path,
                                "endpoint": f"{ep_short} ({hname})"}
                    debug.append(f"⚠️ {hname}: 200 بدون balance")
                elif res and res.get("ip_blocked"):
                    debug.append(f"🛡️ {hname}: WAF")
                else:
                    debug.append(f"❌ {hname}: {code}")
            except Exception as e:
                debug.append(f"💥 {hname}: {str(e)[:30]}")
    
    return {"ok": False, "msg": "❌ <b>تعذر الجلب</b>\n\n" + "\n".join(debug[:6])}

def sess_path(uid): return BASE / f"sess_{uid}.json"
def save_sess(uid, d):
    try: sess_path(uid).write_text(json.dumps(d, ensure_ascii=False))
    except: pass
def load_sess(uid):
    try:
        f = sess_path(uid)
        return json.loads(f.read_text()) if f.exists() else None
    except: return None
def clear_sess(uid):
    try:
        f = sess_path(uid)
        if f.exists(): f.unlink()
    except: pass

bot = AsyncTeleBot(TOKEN)
states = {}

async def notify(offer, ms):
    if not NOTIFY_GROUP: return
    try:
        txt = f"✅ <b>تفعيل</b>\n🌐 أوريدو\n🎁 {offer}\n📱 {mask(ms)}\n⏱️ {datetime.now().strftime('%H:%M')}"
        await bot.send_message(NOTIFY_GROUP, txt, parse_mode='HTML')
    except: pass

def main_kb():
    m = InlineKeyboardMarkup(row_width=1)
    m.add(InlineKeyboardButton("🎁 2Go Free", callback_data="go_2go"))
    m.add(InlineKeyboardButton("💰 الرصيد", callback_data="go_bal"))
    m.add(InlineKeyboardButton("🔄 رقم آخر", callback_data="go_out"))
    return m

def back_kb():
    m = InlineKeyboardMarkup(); m.add(InlineKeyboardButton("↩️ رجوع", callback_data="go_menu")); return m

@bot.message_handler(commands=['start'])
async def cmd_start(msg):
    uid = msg.from_user.id
    s = load_sess(uid)
    if s and s.get("access_token"):
        await bot.send_message(uid, f"📱 <b>{mask(s['msisdn'])}</b>\n\nاختر:", reply_markup=main_kb(), parse_mode='HTML')
        return
    states[uid] = {"step": "await_phone"}
    await bot.send_message(uid, "👋 <b>أوريدو بوت</b>\n\n📱 أرسل رقمك:\nمثال: <code>056232XXXX</code>", parse_mode='HTML')

@bot.callback_query_handler(func=lambda c: True)
async def cb(call):
    uid = call.from_user.id
    try: await bot.delete_message(call.message.chat.id, call.message.message_id)
    except: pass
    if call.data == "go_menu":
        s = load_sess(uid)
        if s: await bot.send_message(uid, f"📱 <b>{mask(s['msisdn'])}</b>\n\nاختر:", reply_markup=main_kb(), parse_mode='HTML')
        else: await cmd_start(call.message)
        return
    if call.data == "go_out":
        clear_sess(uid); states[uid] = {"step": "await_phone"}
        await bot.send_message(uid, "🔄 أرسل رقم جديد:")
        return
    s = load_sess(uid)
    if not s: await bot.send_message(uid, "⚠️ /start"); return
    if call.data == "go_2go":
        await bot.send_message(uid, "⏳ تفعيل 2Go...")
        res = await asyncio.to_thread(purchase_2go, s)
        if res["ok"]: await notify("2Go Free", s["msisdn"])
        await bot.send_message(uid, res["msg"], reply_markup=back_kb(), parse_mode='HTML')
        return
    if call.data == "go_bal":
        await bot.send_message(uid, "⏳ جلب الرصيد...")
        res = await asyncio.to_thread(check_balance, s)
        if res.get("ok"):
            txt = f"💰 <b>{res['balance']} دج</b>\n\n📱 <code>{mask(s['msisdn'])}</code>\n\n<i>📊 {res['endpoint']}</i>\n<i>🔍 {res['path']}</i>"
        else:
            txt = res.get("msg", "❌")
        await bot.send_message(uid, txt, reply_markup=back_kb(), parse_mode='HTML')
        return

@bot.message_handler(func=lambda m: True, content_types=['text'])
async def handle_text(msg):
    uid = msg.from_user.id; txt = msg.text.strip()
    state = states.get(uid, {})
    if state.get("step") == "await_phone":
        digits = re.sub(r"\D", "", txt)
        if not re.match(r"^0?[567]\d{8}$", digits):
            await bot.send_message(uid, "❌ رقم غير صحيح"); return
        if digits.startswith("0"): digits = digits[1:]
        ms = "213" + digits
        await bot.send_message(uid, "⏳ إرسال OTP...")
        otp_res = await asyncio.to_thread(send_otp, ms)
        if not otp_res:
            await bot.send_message(uid, "❌ تعذر الإرسال"); return
        states[uid] = {"step": "await_otp", "ms": ms, "proxy": otp_res.get("proxy")}
        await bot.send_message(uid, f"✅ <b>OTP مرسل</b>\n\n📱 <code>0{digits}</code>\n\n📩 أدخل الرمز (6 أرقام)", parse_mode='HTML')
        return
    if state.get("step") == "await_otp":
        if not txt.isdigit() or len(txt) != 6:
            await bot.send_message(uid, "❌ 6 أرقام"); return
        wm = await bot.send_message(uid, "⏳ تحقق...")
        res = await asyncio.to_thread(verify_otp, state["ms"], txt, state["proxy"])
        try: await bot.delete_message(uid, wm.message_id)
        except: pass
        if res == "wrong_otp":
            await bot.send_message(uid, "❌ رمز خاطئ"); return
        if not res:
            await bot.send_message(uid, "❌ فشل — /start"); return
        sess = {"msisdn": state["ms"], **res}
        save_sess(uid, sess)
        states[uid] = {"step": "menu"}
        await bot.send_message(uid, f"✅ <b>دخول ناجح</b>\n\n📱 <b>{mask(state['ms'])}</b>\n\nاختر:", reply_markup=main_kb(), parse_mode='HTML')
        return
    await cmd_start(msg)

async def main():
    print("="*55); print("🤖 Ooredoo Bot"); print("="*55)
    try:
        r = requests.get("https://ip.oxylabs.io/location",
                        proxies={"http": _purl(), "https": _purl()}, timeout=15, verify=False)
        print(f"✅ Proxy: {r.json().get('ip','?')}")
    except Exception as e:
        print(f"⚠️ Proxy: {str(e)[:60]}")
    print("✅ يعمل...\n")
    await bot.infinity_polling(skip_pending=True, timeout=30)

if __name__ == "__main__":
    try: asyncio.run(main())
    except KeyboardInterrupt: print("\n👋")
