#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OOREDOO Bot — Oxylabs Proxy — 2Go Free + Balance + 20DZ — by moon"""
import telebot
from telebot.async_telebot import AsyncTeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio, requests, json, os, re, uuid, base64, time, urllib.parse, threading, logging
from datetime import datetime, timedelta
from pathlib import Path
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.getLogger("urllib3").setLevel(logging.CRITICAL)

# ═══════════════ الإعدادات ═══════════════
TOKEN = "7776492585:AAGxdB_8makFSF561lHyrZTgbS4pKh8FB5o"
ADMIN_ID = 6860937572
NOTIFY_GROUP = "@ifoekdjdh"

OOREDOO_BFF = "https://apis.ooredoo.dz/api/ooredoo-bff"
OOREDOO_AUTH = "https://apis.ooredoo.dz/api/auth/realms/myooredoo/protocol/openid-connect/token"
OOREDOO_CLIENT_ID = "myooredoo-app"
OOREDOO_X_VERSION = "1.5.17"
OOREDOO_X_SIG = "5c7641dbb82cf11066df68afc91541c967640106a95192740b43d51a5ce6777a"
OOREDOO_PLATFORM = "android"
OOREDOO_PLATFORM_ORIGIN = "mobile-android"

# Oxylabs Residential (Algeria - Algiers)
PROXY_HOST = "pr.oxylabs.io:7777"
PROXY_USER = "customer-resi_4b78d26c-sessid-0211331481-sesstime-10"
PROXY_PASS = "WYb+48cZoZ+1"

def _proxy_url():
    u = urllib.parse.quote(PROXY_USER, safe='')
    p = urllib.parse.quote(PROXY_PASS, safe='')
    return f"http://{u}:{p}@{PROXY_HOST}"

INTEGRITY_1 = ("JWBTpxXcH7KY9EXYeIRp8NjQMx2dt3vF8ejjoARazyoFzOw6Cu8+wkeV+zSVHSTeI6a12SG/FU+Q/9uBrcN71Rl"
"YO4CulD2x375NKwJRAInar8DVUilHBKUfjEsoHd6EwfLCfdYzLNXJu9POfEf6tqKn3PUe0pY6qZxWLhyVAFHw8Qwb"
"52ZqdI2soCH4S3mrz+OZL+YovdGSUKlXKIkxVroAMTAg3jljLF7gvXaEsB/O3uW+tbkBMwSX2uTOwf+rh3sgOF/"
"zPhKCFgRvZmU1o87Fa96Y/+wOcK+UpfXTCBYVrvQ1wG6ryC7vHMSqgUhYJK4tbSoti0zv4av9pwxh9Iv2MgsMENj"
"yKBK/TuFZxEG3xQCKj1LTMgn2xBEeKcbsKrEW3xDRwsccGI3D7GHnbUlhdI4ujDIRQVKHaZSwhTp+32Cr4EB/Qt"
"8p/xRbdgCde9MUlM4AYIGlfyVoHSkOvTu5c0DIIy1EhowtAkbKIJl49wsYKWvpT/nXFWzeXP3R2qzaclCnIb9qih"
"hrarmwz8l8XH2T+f7AK2uSNiuWLG5Fy2mM/YLmuJPZT9Ciag/mpy7JGImKNQAcFbSAInBdKQjUKT+COzZfrXj5r"
"wil9/HDMtuzIovq8hrQGY+roTfVPheTLWmcjkVCOL8VXAHjPb22vOuqrkMioWT9CQ5O8RgW7RKHrObeKQMp8F7tS"
"jOqkxYDFkPVN1G4nkEBrTlPKK9YtPl+j7IuH9fGcDTwhCTTqP8peuBryW0L11tApvAEi7VkJyBxpVxW")
INTEGRITY_2 = ("JWBTpxXcH7KR/kzaHeUUydDWODuU4i3H4fL9gCgKzyYfyN4qLJJE8keV+zSVHSTeI6aEyC2tbSza/NGmkflQ/Ug"
"aNZSN9SKxz7tcdQckHY25n6mOaDZ9PPMQmF4sKZqDwebce/c1SNGNn6qvTULW/L348aJvy7Vii6dyPTu3OSPV9Aw"
"KwGwQKNHN61HyK3jx/fa8Os5ux9u3Q654YLZrAJ99QGEm/C9nEBPmlHC98RjovLGBnuJOGx6k7fnyrt/Ogy5fNg"
"+tBgi5HEsoXDAwutX7TOWfx4YKHpKW//TvPRQgp69e2Xqa+CvGJJ+a/WlPMPhRCSsfo0OG04mVvlkc8eXiLzV/GP"
"uJCEmcRf9Z6V+xoDyMtU7OZ3XT5BMhI/D/N68LsRn/9dIBH6X7n0WAW3tzeKZK1zENWFKrd7aLlzEdwFzO/1JTQs"
"EDom5TRie0Kd5yic4BGvS1C1BsA2wJhzyiZ2j7RUE9m8tOAkPEIs929FYIfmH8XcCQKHT0TqT0+N+wCiyfNawPlD"
"hZWcObscFZeEmKgvqiUFCoCj6xI1hvyHK0nu7fnZ/sGc6oNT/SrFjubYWjOyoYFL7gMnlYAhyjZhjuAwN1m1/wjw"
"rOx8DbFr2NW8qb3hv+CIzK1zL3LDryKjqNkTxcOp4aJnmSTa73guCEmWc7pnLkLw5O8RgW7RKHrObeeQ0l9lu4H"
"WXwlhdWRxvVMQDimhtTrGASL6sIuaxyhOkrH4HFImP70SaCoK9+euMxnzkPjg9HqPIFj+I0KSMloVxW")

BASE_DIR = Path(os.path.expanduser("~")) / "ooredoo_bot"
BASE_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(), logging.FileHandler(str(BASE_DIR / "bot.log"), encoding='utf-8')])

# ═══════════════ أدوات مساعدة ═══════════════
def now_ms(): return str(int(time.time() * 1000))
def new_iid():
    u = uuid.uuid4().hex
    return f"{u[:8]}-{u[8:12]}-11{u[12:16]}-{u[16:20]}-{u[20:32]}{now_ms()}"
def new_psig(iid):
    return base64.b64encode(json.dumps({"platform":"android","is-physical-device":True,"device-id":iid}, separators=(',',':')).encode()).decode()
def new_corr(): return uuid.uuid4().hex + now_ms()
def new_fp(): return uuid.uuid4().hex + uuid.uuid4().hex[:32]

def mask(m):
    if not m or len(m) < 6: return "?"
    return m[:4] + "xxxx" + m[-2:]

def base_h(ms, fp, corr, ts, iid, psig):
    return {"User-Agent":"Dart/3.11 (dart:io)","Accept-Encoding":"gzip","x-msisdn":ms,
            "x-device-fingerprint":fp,"x-platform-origin":OOREDOO_PLATFORM_ORIGIN,
            "x-correlation-id":corr,"platform":OOREDOO_PLATFORM,"x-version":OOREDOO_X_VERSION,
            "x-signature":OOREDOO_X_SIG,"x-platform-data-signature":psig,
            "x-timestamp":ts,"x-instance-id":iid}

def web_h(ms, token, tok_hdrs):
    ts = tok_hdrs.get("tok_timestamp") or now_ms()
    iid = tok_hdrs.get("tok_instance_id") or new_iid()
    psig = tok_hdrs.get("tok_plat_sig") or new_psig(iid)
    return {"User-Agent":"Dart/3.11 (dart:io)","Accept-Encoding":"gzip","x-msisdn":ms,
            "x-device-fingerprint":new_fp(),"x-platform-origin":"web",
            "authorization":f"Bearer {token}","x-correlation-id":new_corr(),
            "platform":"web","x-version":OOREDOO_X_VERSION,"x-signature":OOREDOO_X_SIG,
            "x-platform-data-signature":psig,"x-timestamp":ts,"x-instance-id":iid,
            "origin":"https://my.ooredoo.dz","referer":"https://my.ooredoo.dz/"}

def do_req(method, url, headers, body="", use_proxy=True, timeout=12):
    proxies = {"http": _proxy_url(), "https": _proxy_url()} if use_proxy else None
    try:
        s = requests.Session()
        s.verify = False
        if method == "GET":
            r = s.get(url, headers=headers, proxies=proxies, timeout=timeout)
        elif method == "HEAD":
            r = s.head(url, headers=headers, proxies=proxies, timeout=timeout)
        else:
            r = s.post(url, headers=headers, data=body, proxies=proxies, timeout=timeout)
        
        if "<!DOCTYPE" in r.text or "<html" in r.text.lower():
            return {"blocked": True, "code": r.status_code}
        try: j = r.json()
        except: j = None
        return {"code": r.status_code, "json": j, "text": r.text[:500],
                "headers": {k.lower(): v for k,v in r.headers.items()}}
    except Exception as e:
        if use_proxy:
            logging.warning(f"[PROXY-FAIL] {str(e)[:80]} — fallback direct")
            return do_req(method, url, headers, body, use_proxy=False, timeout=timeout)
        return None

# ═══════════════ OTP Flow ═══════════════
def send_otp(ms):
    iid = new_iid(); psig = new_psig(iid)
    for use_proxy in [True, False]:
        # 1. Status
        ts = now_ms()
        h1 = base_h(ms, new_fp(), new_corr(), ts, iid, psig)
        r1 = do_req("GET", f"{OOREDOO_BFF}/users/status?msisdn={ms}", h1, use_proxy=use_proxy, timeout=8)
        if not r1 or r1.get("blocked") or r1.get("code") != 200:
            logging.warning(f"[OTP-status] proxy={use_proxy} code={r1.get('code') if r1 else 'None'}")
            continue
        
        # 2. userInfo
        h2 = base_h(ms, new_fp(), new_corr(), now_ms(), iid, psig)
        r2 = do_req("HEAD", f"{OOREDOO_BFF}/userInfo?msisdn={ms}", h2, use_proxy=use_proxy, timeout=8)
        if not r2 or r2.get("blocked") or r2.get("code") not in (200, 204):
            logging.warning(f"[OTP-userInfo] proxy={use_proxy} code={r2.get('code') if r2 else 'None'}")
            continue
        
        # 3. checkpoint
        ts = now_ms()
        h3 = base_h(ms, new_fp(), new_corr(), ts, iid, psig)
        h3["content-type"] = "application/json; charset=utf-8"
        h3["x-native-integrity-token"] = INTEGRITY_1
        h3["x-path"] = "/api/auth/realms/myooredoo/protocol/openid-connect/token"
        h3["x-method"] = "POST"
        r3 = do_req("POST", f"{OOREDOO_BFF}/checkpoint/token", h3, body="{}", use_proxy=use_proxy, timeout=8)
        if not r3 or r3.get("blocked"): continue
        nonce = r3.get("headers", {}).get("x-nonce-id")
        chronos = r3.get("headers", {}).get("x-chronos-id")
        if not nonce or not chronos:
            logging.warning(f"[OTP-checkpoint] no nonce/chronos")
            continue
        
        # 4. Send OTP
        h4 = {"User-Agent":"Dart/3.11 (dart:io)","Accept-Encoding":"gzip","x-msisdn":ms,
              "x-device-fingerprint":new_fp(),"x-nonce-id":nonce,"x-platform-origin":OOREDOO_PLATFORM_ORIGIN,
              "platform":OOREDOO_PLATFORM,"x-version":OOREDOO_X_VERSION,"x-signature":OOREDOO_X_SIG,
              "x-chronos-id":chronos,"x-timestamp":ts,"x-platform-info":psig,"x-force-update":"true",
              "x-instance-id":iid,"Content-Type":"application/x-www-form-urlencoded"}
        body4 = urllib.parse.urlencode({"client_id":OOREDOO_CLIENT_ID,"grant_type":"password","username":ms})
        r4 = do_req("POST", OOREDOO_AUTH, h4, body=body4, use_proxy=use_proxy, timeout=15)
        if r4 and r4.get("code") in (401, 403):
            logging.info(f"[OTP] sent OK (proxy={use_proxy})")
            return {"ok": True, "device": {"iid":iid, "psig":psig}, "use_proxy": use_proxy}
    return {"ok": False}

def verify_otp(ms, otp, device, use_proxy):
    iid = device["iid"]; psig = device["psig"]
    ts = now_ms(); corr = new_corr()
    
    # checkpoint
    h6 = base_h(ms, new_fp(), corr, ts, iid, psig)
    h6["content-type"] = "application/json; charset=utf-8"
    h6["x-native-integrity-token"] = INTEGRITY_2
    h6["x-path"] = "/api/auth/realms/myooredoo/protocol/openid-connect/token"
    h6["x-method"] = "POST"
    r6 = do_req("POST", f"{OOREDOO_BFF}/checkpoint/token", h6, body="{}", use_proxy=use_proxy, timeout=8)
    if not r6 or r6.get("blocked"): return None
    nonce = r6.get("headers", {}).get("x-nonce-id")
    chronos = r6.get("headers", {}).get("x-chronos-id")
    if not nonce or not chronos: return None
    
    fp7 = new_fp()
    h7 = {"User-Agent":"Dart/3.11 (dart:io)","Accept-Encoding":"gzip","x-msisdn":ms,
          "x-device-fingerprint":fp7,"x-nonce-id":nonce,"x-platform-origin":OOREDOO_PLATFORM_ORIGIN,
          "platform":OOREDOO_PLATFORM,"x-version":OOREDOO_X_VERSION,"x-signature":OOREDOO_X_SIG,
          "x-chronos-id":chronos,"x-timestamp":ts,"x-platform-info":psig,"x-force-update":"true",
          "x-instance-id":iid,"Content-Type":"application/x-www-form-urlencoded"}
    body7 = urllib.parse.urlencode({"client_id":OOREDOO_CLIENT_ID,"grant_type":"password","username":ms,"otp":otp})
    r7 = do_req("POST", OOREDOO_AUTH, h7, body=body7, use_proxy=use_proxy, timeout=15)
    if not r7: return None
    if r7.get("code") in (401, 403): return "wrong_otp"
    if r7.get("code") == 200 and r7.get("json") and "access_token" in r7["json"]:
        j = r7["json"]
        return {"access_token": j["access_token"], "refresh_token": j.get("refresh_token",""),
                "tok_fingerprint": fp7, "tok_timestamp": ts, "tok_instance_id": iid,
                "tok_plat_sig": psig, "use_proxy": use_proxy, "issued_at": int(time.time())}
    return None

# ═══════════════ Purchase / Balance ═══════════════
def purchase_2go(account):
    ms = account["msisdn"]; tok_hdrs = {"tok_timestamp": account.get("tok_timestamp"),
        "tok_instance_id": account.get("tok_instance_id"), "tok_plat_sig": account.get("tok_plat_sig")}
    h = web_h(ms, account["access_token"], tok_hdrs)
    h["content-type"] = "application/json; charset=utf-8"
    h["accept"] = "*/*"
    body = json.dumps({"bundleCode": "BTL_24H_DATA_Free_2Go"})
    
    for use_proxy in [account.get("use_proxy", True), not account.get("use_proxy", True)]:
        res = do_req("POST", f"{OOREDOO_BFF}/cvm/dynamic-bundle-purchase", h, body=body, use_proxy=use_proxy, timeout=20)
        logging.info(f"[2Go] proxy={use_proxy} → {res.get('code') if res else 'None'} | {str(res.get('text',''))[:150] if res else ''}")
        if not res: continue
        if res.get("code") == 200:
            return {"ok": True, "msg": "🎉 تم تفعيل 2Go Free — 24H"}
        if res.get("code") in (401, 403):
            return {"ok": False, "msg": "⚠️ Token منتهي — سجل دخول من جديد"}
        if res.get("code") in (402, 409):
            return {"ok": False, "msg": "⏰ العرض مفعّل مسبقاً أو غير متاح"}
    return {"ok": False, "msg": "❌ فشل التفعيل — جرّب لاحقاً"}

def purchase_20dz(account):
    ms = account["msisdn"]; tok_hdrs = {"tok_timestamp": account.get("tok_timestamp"),
        "tok_instance_id": account.get("tok_instance_id"), "tok_plat_sig": account.get("tok_plat_sig")}
    h = web_h(ms, account["access_token"], tok_hdrs)
    h["content-type"] = "application/json; charset=utf-8"
    h["accept"] = "*/*"
    body = json.dumps({"bundleCode": "BTL_24H_DATA_20DZD_1Go", "validity": "day", "validityAmount": "1"})
    
    for use_proxy in [account.get("use_proxy", True), not account.get("use_proxy", True)]:
        res = do_req("POST", f"{OOREDOO_BFF}/cvm/dynamic-bundle-purchase", h, body=body, use_proxy=use_proxy, timeout=20)
        logging.info(f"[20DZ] proxy={use_proxy} → {res.get('code') if res else 'None'}")
        if not res: continue
        if res.get("code") == 200: return {"ok": True, "msg": "✅ تم تفعيل 20دج — 1Go"}
        if res.get("code") in (401, 403): return {"ok": False, "msg": "⚠️ Token منتهي"}
        if res.get("code") in (402, 409): return {"ok": False, "msg": "❌ رصيد غير كافي أو مفعّل مسبقاً"}
    return {"ok": False, "msg": "❌ فشل التفعيل"}

def get_balance(account):
    ms = account["msisdn"]; tok_hdrs = {"tok_timestamp": account.get("tok_timestamp"),
        "tok_instance_id": account.get("tok_instance_id"), "tok_plat_sig": account.get("tok_plat_sig")}
    h = web_h(ms, account["access_token"], tok_hdrs)
    
    for use_proxy in [account.get("use_proxy", True), not account.get("use_proxy", True)]:
        res = do_req("GET", f"{OOREDOO_BFF}/subscriptions/getAccountInfo", h, use_proxy=use_proxy, timeout=15)
        if not res or res.get("blocked"): continue
        if res.get("code") == 200 and isinstance(res.get("json"), dict):
            d = res["json"]
            bal = d.get("accountBalance") or d.get("mainBalance") or "?"
            return {"ok": True, "balance": bal, "raw": d}
        if res.get("code") == 401: return {"ok": False, "msg": "🔐 Token منتهي"}
    return {"ok": False, "msg": "❌ تعذر جلب الرصيد"}

# ═══════════════ Sessions ═══════════════
def acc_path(uid): return BASE_DIR / f"acc_{uid}.json"
def acc_save(uid, d):
    try: acc_path(uid).write_text(json.dumps(d, ensure_ascii=False))
    except: pass
def acc_load(uid):
    try:
        f = acc_path(uid)
        return json.loads(f.read_text()) if f.exists() else None
    except: return None
def acc_clear(uid):
    try:
        f = acc_path(uid)
        if f.exists(): f.unlink()
    except: pass

# ═══════════════ Bot ═══════════════
bot = AsyncTeleBot(TOKEN)
steps = {}

async def notify_ok(offer, ms):
    if not NOTIFY_GROUP: return
    try:
        txt = f"✅ <b>تفعيل ناجح</b>\n🌐 أوريدو 🟠\n🎁 {offer}\n📱 {mask(ms)}\n⏱️ {datetime.now().strftime('%H:%M:%S')}"
        await bot.send_message(NOTIFY_GROUP, txt, parse_mode='HTML')
    except: pass

def main_kb(acc):
    m = InlineKeyboardMarkup(row_width=1)
    m.add(InlineKeyboardButton("🎁 2Go Free — 24H", callback_data="go_2go"))
    m.add(InlineKeyboardButton("⚡ 20دج — 1Go — 24H", callback_data="go_20dz"))
    m.add(InlineKeyboardButton("💰 عرض الرصيد", callback_data="go_bal"))
    m.add(InlineKeyboardButton("🔄 تسجيل رقم آخر", callback_data="go_logout"))
    return m

def back_kb(cb="go_menu"):
    m = InlineKeyboardMarkup(); m.add(InlineKeyboardButton("↩️ رجوع", callback_data=cb)); return m

@bot.message_handler(commands=['start'])
async def cmd_start(msg):
    uid = msg.from_user.id
    acc = acc_load(uid)
    if acc and acc.get("access_token"):
        await bot.send_message(uid, f"📱 <b>{mask(acc['msisdn'])}</b>\n\nاختر:", reply_markup=main_kb(acc), parse_mode='HTML')
        return
    steps[uid] = {"step": "await_phone"}
    await bot.send_message(uid, "👋 أرسل رقم هاتفك (05XXXXXXXX):", parse_mode='HTML')

@bot.callback_query_handler(func=lambda c: True)
async def cb_handler(call):
    uid = call.from_user.id
    try: await bot.delete_message(call.message.chat.id, call.message.message_id)
    except: pass
    
    if call.data == "go_menu":
        acc = acc_load(uid)
        if acc: await bot.send_message(uid, f"📱 <b>{mask(acc['msisdn'])}</b>\n\nاختر:", reply_markup=main_kb(acc), parse_mode='HTML')
        else: await cmd_start(call.message)
        return
    
    if call.data == "go_logout":
        acc_clear(uid); steps[uid] = {"step": "await_phone"}
        await bot.send_message(uid, "🔄 أرسل رقم جديد:")
        return
    
    acc = acc_load(uid)
    if not acc: await bot.send_message(uid, "⚠️ سجل دخول أولاً"); return
    
    if call.data == "go_2go":
        await bot.send_message(uid, "⏳ جاري تفعيل 2Go Free...")
        res = await asyncio.to_thread(purchase_2go, acc)
        if res["ok"]: await notify_ok("2Go Free", acc["msisdn"])
        await bot.send_message(uid, res["msg"], reply_markup=back_kb(), parse_mode='HTML')
        return
    
    if call.data == "go_20dz":
        await bot.send_message(uid, "⏳ جاري تفعيل 20دج — 1Go...")
        res = await asyncio.to_thread(purchase_20dz, acc)
        if res["ok"]: await notify_ok("20دج — 1Go", acc["msisdn"])
        await bot.send_message(uid, res["msg"], reply_markup=back_kb(), parse_mode='HTML')
        return
    
    if call.data == "go_bal":
        await bot.send_message(uid, "⏳ جاري جلب الرصيد...")
        res = await asyncio.to_thread(get_balance, acc)
        if res.get("ok"):
            txt = f"💰 <b>رصيدك: {res['balance']} دج</b>\n\n📱 <code>{mask(acc['msisdn'])}</code>"
        else:
            txt = res.get("msg", "❌ فشل")
        await bot.send_message(uid, txt, reply_markup=back_kb(), parse_mode='HTML')
        return

@bot.message_handler(func=lambda m: True, content_types=['text'])
async def handle_text(msg):
    uid = msg.from_user.id
    txt = msg.text.strip()
    step = steps.get(uid, {})
    
    if step.get("step") == "await_phone":
        digits = re.sub(r"\D", "", txt)
        if not re.match(r"^0[567]\d{8}$", digits):
            await bot.send_message(uid, "❌ رقم غير صحيح، جرب 05XXXXXXXX")
            return
        ms = "213" + digits[1:]
        await bot.send_message(uid, "⏳ جاري إرسال رمز OTP...")
        res = await asyncio.to_thread(send_otp, ms)
        if not res.get("ok"):
            await bot.send_message(uid, "❌ تعذر إرسال OTP — تأكد من الرقم")
            return
        steps[uid] = {"step": "await_otp", "ms": ms, "device": res["device"], "use_proxy": res["use_proxy"]}
        await bot.send_message(uid, f"✅ <b>تم إرسال OTP</b>\n\n📱 إلى: <code>{digits}</code>\n\n📩 أدخل الرمز (6 أرقام)", parse_mode='HTML')
        return
    
    if step.get("step") == "await_otp":
        if not txt.isdigit() or len(txt) != 6:
            await bot.send_message(uid, "❌ 6 أرقام")
            return
        wm = await bot.send_message(uid, "⏳ جاري التحقق...")
        res = await asyncio.to_thread(verify_otp, step["ms"], txt, step["device"], step["use_proxy"])
        try: await bot.delete_message(uid, wm.message_id)
        except: pass
        if res == "wrong_otp":
            await bot.send_message(uid, "❌ رمز خاطئ")
            return
        if not res:
            await bot.send_message(uid, "❌ فشل التحقق")
            return
        acc = {"msisdn": step["ms"], **res}
        acc_save(uid, acc)
        steps[uid] = {"step": "menu"}
        await bot.send_message(uid, f"✅ <b>تم الدخول</b>\n\n📱 <b>{mask(step['ms'])}</b>\n\nاختر:", reply_markup=main_kb(acc), parse_mode='HTML')
        return
    
    await cmd_start(msg)

async def main():
    print("="*50); print("🤖 Ooredoo Bot — Oxylabs Proxy"); print("="*50)
    try:
        r = requests.get("https://ip.oxylabs.io/location", proxies={"http": _proxy_url(), "https": _proxy_url()}, timeout=15, verify=False)
        print(f"✅ Proxy: {r.json()}")
    except Exception as e:
        print(f"⚠️ Proxy: {str(e)[:80]}")
    print("✅ يعمل...")
    await bot.infinity_polling(skip_pending=True, timeout=30)

if __name__ == "__main__":
    try: asyncio.run(main())
    except KeyboardInterrupt: print("\n👋")
