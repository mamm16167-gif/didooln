#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v6.8.4 — 2GB Free + Server Monitor + OTP fix + JWT device-id fix"""
import telebot
from telebot.async_telebot import AsyncTeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio, sqlite3, requests, random, time, re, json, os, uuid, base64, threading, logging, urllib3, hashlib, string, signal
from datetime import datetime, timedelta, timezone as tz
from pathlib import Path
from collections import deque
import html as _html

def _auto_button_style(text):
    t = str(text)
    if "إلغاء" in t or t.strip().startswith("❌") or "🚫" in t or "حذف" in t:
        return "danger"
    if "تأكيد" in t or "اشترِ" in t or "دفع" in t or "🛒" in t:
        return "success"
    return "primary"

_orig_ikb_init = InlineKeyboardButton.__init__
_orig_ikb_to_dict = InlineKeyboardButton.to_dict

def _new_ikb_init(self, *args, style=None, **kwargs):
    _orig_ikb_init(self, *args, **kwargs)
    self.style = style

def _new_ikb_to_dict(self):
    d = _orig_ikb_to_dict(self)
    if "style" not in d:
        explicit = getattr(self, "style", None)
        d["style"] = explicit if explicit else _auto_button_style(self.text)
    return d

InlineKeyboardButton.__init__ = _new_ikb_init
InlineKeyboardButton.to_dict = _new_ikb_to_dict

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.getLogger("urllib3").setLevel(logging.CRITICAL)

# ==================== الإعدادات ====================
TOKEN = "7924355653:AAHeIAyfFwEP1L-UtIGmnwo31PXzFWZsjxE"
ADMIN_ID = 6860937572
REQUIRED_CHANNEL = "@kfodoedjtu546m"
CHANNEL_LINK = "https://t.me/kfodoedjtu546m"

DJ_CLIENT_ID = "87pIExRhxBb3_wGsA5eSEfyATloa"
DJ_CLIENT_SECRET = "uf82p68Bgisp8Yg1Uz8Pf6_v1XYa"
DJ_BASE = "https://apim.djezzy.dz/mobile-api"
DJ_HEADERS = {'User-Agent': "MobileApp/3.0.0", 'Accept': "application/json",
              'Content-Type': "application/json", 'accept-language': "fr", 'Connection': 'keep-alive'}
COOLDOWN_2GB = 604800
COOLDOWN_FREE_2GB_OO = 86400
OTP_RESEND_COOLDOWN = 60
OTP_VERIFY_MIN_WAIT = 3
OTP_VERIFY_MAX_RETRY = 3
DZ_HEADERS = DJ_HEADERS
DZ_BASE_URL = DJ_BASE
PAGE_FOLLOW_TEXT = f"📢 تابع قناتنا: {CHANNEL_LINK}"

DJ_72GB_QR_CODE = "FX8IWas7nzwBIZ0cuEal"

OO_MAINTENANCE = False
OO_MAINTENANCE_MSG = ("🛠️ <b>شبكة أوريدو في صيانة حالياً</b>\n\n"
                      "نعتذر منكم، خدمة أوريدو متوقفة مؤقتاً.\n"
                      "✅ <b>يمكنك استخدام جيزي بشكل طبيعي الآن.</b>")

OO_BFF = "https://apis.ooredoo.dz/api/ooredoo-bff"
OO_AUTH = "https://apis.ooredoo.dz/api/auth/realms/myooredoo/protocol/openid-connect/token"
OO_CLIENT = "myooredoo-app"
X_VERSION = "1.5.15"
X_VERSION_OTP = "1.5.16"
X_SIG = "5c7641dbb82cf11066df68afc91541c967640106a95192740b43d51a5ce6777a"
X_SIG_RAMADAN = "c66054ba6166fe08d1a6a702fb10b151102a6f4ef058fcf3d995ee511ff0d267"
NOTIFY_GROUP = "@ifoekdjdh"

_oo_72gb_jobs = {}
_oo_72gb_jobs_lock = threading.Lock()
OO_72GB_MAX_ATTEMPTS = 40
OO_OTP_MAX_ATTEMPTS  = 15

# ==================== Oxylabs ====================
PROXY_USERNAME = "resi_0614e541"
PROXY_PASSWORD = "GfOR31Pbb6~G"
PROXY_COUNTRY  = "dz"
PROXY_CITY     = "algiers"
PROXY_HOST     = "pr.oxylabs.io:7777"

_current_session   = ["31298419"]
_proxy_rotate_lock = threading.Lock()
_last_rotate_time  = [0.0]
ROTATE_COOLDOWN    = 3
_proxy_fail_count  = [0]
_proxy_fail_until  = [0.0]
_proxy_fail_lock   = threading.Lock()

def _build_proxy_url():
    with _proxy_rotate_lock:
        sess = _current_session[0]
    user = f"customer-{PROXY_USERNAME}-cc-{PROXY_COUNTRY}-city-{PROXY_CITY}-sessid-{sess}"
    return f"http://{user}:{PROXY_PASSWORD}@{PROXY_HOST}"

def _rotate_proxy_session(force=False):
    with _proxy_rotate_lock:
        now = time.time()
        if not force and now - _last_rotate_time[0] < ROTATE_COOLDOWN:
            return False
        _last_rotate_time[0] = now
        _current_session[0] = ''.join(random.choices(string.digits, k=8))
        new_id = _current_session[0]
    logging.warning(f"[PROXY] 🔄 Rotated → sessid-{new_id}")
    return True

def _should_use_proxy():
    with _proxy_fail_lock:
        return time.time() > _proxy_fail_until[0]

def _mark_proxy_failed():
    with _proxy_fail_lock:
        _proxy_fail_count[0] += 1
        if _proxy_fail_count[0] >= 3:
            _proxy_fail_until[0] = time.time() + 30
            _proxy_fail_count[0] = 0
    _rotate_proxy_session()

def _mark_proxy_success():
    with _proxy_fail_lock:
        _proxy_fail_count[0] = 0
        _proxy_fail_until[0] = 0.0

# ==================== OO Proxy Pool ====================
_OO_PROXY_AUTH = "1c3kqov80uaa:pl37isqkvtla7o8"
_OO_PROXY_IPS = [
    "104.207.37.238","216.26.238.222","216.26.250.168","104.207.49.9",
    "104.207.40.45","216.26.236.181","216.26.252.144","209.50.163.58",
    "216.26.252.128","65.111.7.243","65.111.15.199","209.50.166.222",
    "65.111.10.84","45.3.47.7","104.207.60.70","104.207.41.105",
    "45.3.35.230","65.111.15.119","216.26.227.234","104.207.47.45",
    "104.207.36.86","104.207.60.175","45.3.46.144","65.111.13.117",
    "209.50.187.105","45.3.34.106","104.207.37.80","216.26.248.27",
    "216.26.250.166","104.207.36.101","216.26.252.179","209.50.163.98",
    "209.50.160.221","45.3.32.243","209.50.179.206","104.207.48.5",
    "45.3.34.201","151.123.177.47","45.3.39.53","45.3.40.34",
    "65.111.7.58","151.123.176.78","216.26.237.178","216.26.236.30",
    "45.3.42.51","209.50.189.222","209.50.172.2","209.50.185.177",
    "216.26.228.216","217.181.92.216","216.26.243.226","104.207.62.88",
    "216.26.242.143","209.50.176.88","216.26.251.250","45.3.44.60",
    "104.207.38.73","45.3.54.189","216.26.233.153","45.3.34.140",
    "216.26.255.205","104.207.43.242","104.207.53.230","45.3.52.86",
    "209.50.188.83","209.50.180.63","104.207.40.181","216.26.235.150",
    "209.50.180.38","209.50.177.236","104.207.37.247","209.50.169.172",
    "209.50.181.194","216.26.226.10","104.207.36.168","209.50.167.119",
    "45.3.47.161","209.50.162.215","209.50.165.46","45.3.34.28",
    "104.207.62.160","45.3.47.99","216.26.242.93","209.50.164.48",
    "104.207.48.71","209.50.183.7","104.207.33.146","65.111.29.120",
    "65.111.14.158","104.207.52.36","104.167.19.123","217.181.92.82",
    "104.207.39.112","104.207.48.29","45.3.48.106","45.3.33.47",
    "104.207.43.50","104.207.32.150","104.207.40.85","65.111.0.243",
]
OO_PROXY_POOL = [f"{_OO_PROXY_AUTH}@{ip}:3129" for ip in _OO_PROXY_IPS]

_oo_proxy_in_use   = {}
_oo_user_to_proxy  = {}
_oo_proxy_health   = {}
_oo_proxy_lock     = threading.Lock()
OO_PROXY_HOLD_SECONDS = 180
OO_PROXY_BAN_AFTER    = 3
OO_PROXY_BAN_SECONDS  = 600

def _mask_oo_proxy(p):
    try: return p.split("@", 1)[1]
    except: return (p or "?")[:20] + "..."

def _get_oo_proxy_for_user(uid, exclude=None):
    exclude = exclude or set()
    with _oo_proxy_lock:
        now = time.time()
        existing = _oo_user_to_proxy.get(uid)
        if existing and existing not in exclude:
            info = _oo_proxy_in_use.get(existing)
            if info and (now - info["since"]) < OO_PROXY_HOLD_SECONDS:
                h = _oo_proxy_health.get(existing, {})
                if h.get("banned_until", 0) < now:
                    return existing
            _oo_proxy_in_use.pop(existing, None)
            _oo_user_to_proxy.pop(uid, None)
        used = set(_oo_proxy_in_use.keys())
        candidates = []
        for p in OO_PROXY_POOL:
            if p in used or p in exclude: continue
            h = _oo_proxy_health.get(p, {})
            if h.get("banned_until", 0) > now: continue
            candidates.append(p)
        if not candidates:
            for p in OO_PROXY_POOL:
                if p in exclude: continue
                h = _oo_proxy_health.get(p, {})
                if h.get("banned_until", 0) > now: continue
                candidates.append(p)
        if not candidates:
            candidates = [p for p in OO_PROXY_POOL if p not in exclude]
        if not candidates:
            return OO_PROXY_POOL[0]
        chosen = random.choice(candidates)
        _oo_proxy_in_use[chosen] = {"uid": uid, "since": now}
        _oo_user_to_proxy[uid] = chosen
        logging.info(f"[OO-PROXY] uid={uid} ← {_mask_oo_proxy(chosen)}")
        return chosen

def _release_oo_proxy(uid, reason="manual"):
    with _oo_proxy_lock:
        p = _oo_user_to_proxy.pop(uid, None)
        if p:
            _oo_proxy_in_use.pop(p, None)
            logging.info(f"[OO-PROXY] Released uid={uid} ({reason}) {_mask_oo_proxy(p)}")

def _mark_oo_proxy_success(uid):
    _release_oo_proxy(uid, reason="success")

def _mark_oo_proxy_fail(proxy_str, reason="conn"):
    if not proxy_str: return
    with _oo_proxy_lock:
        h = _oo_proxy_health.setdefault(proxy_str, {"fails": 0, "banned_until": 0, "last_fail": 0})
        h["fails"] += 1
        h["last_fail"] = time.time()
        if h["fails"] >= OO_PROXY_BAN_AFTER:
            h["banned_until"] = time.time() + OO_PROXY_BAN_SECONDS
            logging.warning(f"[OO-PROXY] 🚫 BANNED {_mask_oo_proxy(proxy_str)} {OO_PROXY_BAN_SECONDS}s ({reason})")
            _oo_proxy_in_use.pop(proxy_str, None)
            for u, p in list(_oo_user_to_proxy.items()):
                if p == proxy_str:
                    _oo_user_to_proxy.pop(u, None)

def _mark_oo_proxy_ok(proxy_str):
    if not proxy_str: return
    with _oo_proxy_lock:
        h = _oo_proxy_health.get(proxy_str)
        if h:
            h["fails"] = 0
            h["banned_until"] = 0

RATE_PLAN_NAMES = {
    "654": "Dima", "627": "N'YOOZ", "682": "N'YOOZ",
    "625": "La Gold", "626": "La Gold Jdida", "628": "Ooredoo POP",
    "629": "Dima+", "630": "Anazik", "631": "Anafilx",
    "632": "YOOZ", "633": "Ooredoo Pro",
}

PHONE_STICKER = "CAACAgIAAxkBAAIMG2mxR6mD0xL5WplUQ0sTGQ8aECNdAAJ3BQACP5XMCmWM0yxKQdlOOgQ"
INACTIVITY_SECONDS = 600

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

BASE_DIR = Path(os.path.expanduser("~")) / "unified_bot"
SESSIONS_DIR = BASE_DIR / "sessions"
for d in (BASE_DIR, SESSIONS_DIR):
    d.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(), logging.FileHandler(str(BASE_DIR / "bot.log"), encoding='utf-8')])

_LOG_BUFFER = deque(maxlen=500)
_LOG_LOCK = threading.Lock()

class _RingBufferHandler(logging.Handler):
    def emit(self, record):
        try:
            msg = self.format(record)
            with _LOG_LOCK: _LOG_BUFFER.append(msg)
        except: pass

_ring_handler = _RingBufferHandler()
_ring_handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s', datefmt='%H:%M:%S'))
_ring_handler.setLevel(logging.INFO)
logging.getLogger().addHandler(_ring_handler)

def get_logs(n=30, filter_kw=None):
    with _LOG_LOCK: lines = list(_LOG_BUFFER)
    if filter_kw:
        lines = [l for l in lines if filter_kw.lower() in l.lower()]
    return lines[-n:]

def format_logs_for_telegram(lines, title):
    header = f"📋 <b>{_html.escape(title)}</b>\n━━━━━━━━━━━━━━━━\n<pre>"
    footer = "</pre>"
    body_raw = "\n".join(lines) if lines else "(فارغ)"
    body = _html.escape(body_raw)
    max_body = 3800 - len(header) - len(footer)
    if len(body) > max_body:
        body = "..." + body[-max_body:]
    return header + body + footer

STEPS_FILE = BASE_DIR / "user_steps.json"
DB_PATH = str(BASE_DIR / "boykta.db")

# ==================== HTTP ====================
def _new_session(headers=None, use_proxy=True):
    s = requests.Session()
    a = requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=20, max_retries=1, pool_block=False)
    s.mount('http://', a); s.mount('https://', a); s.verify = False
    if use_proxy and _should_use_proxy():
        proxy_url = _build_proxy_url()
        s.proxies = {"http": proxy_url, "https": proxy_url}
    if headers: s.headers.update(headers)
    return s

async def safe_request(method, url, json=None, headers=None, timeout=15):
    def _sync():
        if _should_use_proxy():
            for proxy_attempt in range(2):
                try:
                    s = requests.Session(); s.verify = False
                    proxy_url = _build_proxy_url()
                    s.proxies = {"http": proxy_url, "https": proxy_url}
                    r = s.request(method, url, json=json, headers=headers, timeout=timeout)
                    try: j = r.json()
                    except: j = None
                    _mark_proxy_success()
                    return {'status': r.status_code, 'json': j, 'text': r.text[:500]}
                except Exception as e:
                    logging.warning(f"[SAFE-REQ] proxy #{proxy_attempt+1}: {str(e)[:80]}")
                    _rotate_proxy_session()
                    if proxy_attempt == 0: time.sleep(0.3)
        try:
            s = requests.Session(); s.verify = False
            r = s.request(method, url, json=json, headers=headers, timeout=timeout)
            try: j = r.json()
            except: j = None
            return {'status': r.status_code, 'json': j, 'text': r.text[:500]}
        except requests.exceptions.Timeout:
            return {'status': 0, 'json': None, 'text': 'timeout'}
        except Exception as e:
            return {'status': 0, 'json': None, 'text': str(e)[:200]}
    return await asyncio.to_thread(_sync)

def _oo_req_direct(method, url, headers, data, timeout):
    try:
        s = requests.Session(); s.verify = False
        r = s.request(method, url, headers=headers, data=data, timeout=timeout, allow_redirects=False)
        try: body = r.json()
        except: body = {"_raw": (r.text or "")[:500]}
        r.close()
        return r.status_code, dict(r.headers), body
    except Exception as e:
        return 0, {}, {"_error": str(e)[:100]}

def _oo_req_with_proxy(method, url, headers, content=b"", timeout=12, proxy_str=None):
    if not proxy_str:
        return _oo_req_direct(method, url, headers,
                              content if isinstance(content, bytes) else content.encode(), timeout)
    data = content if isinstance(content, bytes) else content.encode()
    try:
        s = requests.Session(); s.verify = False
        a = requests.adapters.HTTPAdapter(pool_connections=5, pool_maxsize=10, max_retries=0, pool_block=False)
        s.mount('http://', a); s.mount('https://', a)
        s.proxies = {"http": f"http://{proxy_str}", "https": f"http://{proxy_str}"}
        r = s.request(method, url, headers=headers, data=data, timeout=timeout, allow_redirects=False)
        head = (r.text or "")[:200].lstrip().lower()
        if head.startswith(("<!doctype", "<html")):
            r.close(); _mark_oo_proxy_fail(proxy_str, "html"); return None
        try: body = r.json()
        except: body = {"_raw": (r.text or "")[:500]}
        r.close()
        if r.status_code >= 500:
            _mark_oo_proxy_fail(proxy_str, f"http{r.status_code}"); return None
        if r.status_code == 403:
            _mark_oo_proxy_fail(proxy_str, "forbidden")
        _mark_oo_proxy_ok(proxy_str)
        return r.status_code, dict(r.headers), body
    except requests.exceptions.Timeout:
        _mark_oo_proxy_fail(proxy_str, "timeout"); return None
    except requests.exceptions.ConnectionError:
        _mark_oo_proxy_fail(proxy_str, "conn"); return None
    except Exception:
        _mark_oo_proxy_fail(proxy_str, "err"); return None

def _dz_req(method, url, headers=None, params=None, json_body=None, data=None, timeout=15):
    if _should_use_proxy():
        for proxy_attempt in range(2):
            try:
                s = _new_session(headers, use_proxy=True)
                if method == "GET": r = s.get(url, params=params, timeout=timeout)
                elif method == "POST":
                    if json_body is not None: r = s.post(url, params=params, json=json_body, timeout=timeout)
                    elif data is not None: r = s.post(url, params=params, data=data, timeout=timeout)
                    else: r = s.post(url, params=params, timeout=timeout)
                else: r = s.request(method, url, params=params, timeout=timeout)
                _mark_proxy_success()
                return r
            except Exception as e:
                logging.warning(f"[DZ-REQ] proxy #{proxy_attempt+1}: {str(e)[:80]}")
                _rotate_proxy_session()
                if proxy_attempt == 0: time.sleep(0.3)
    try:
        s = _new_session(headers, use_proxy=False)
        if method == "GET": r = s.get(url, params=params, timeout=timeout)
        elif method == "POST":
            if json_body is not None: r = s.post(url, params=params, json=json_body, timeout=timeout)
            elif data is not None: r = s.post(url, params=params, data=data, timeout=timeout)
            else: r = s.post(url, params=params, timeout=timeout)
        else: r = s.request(method, url, params=params, timeout=timeout)
        return r
    except Exception as e:
        logging.error(f"[DZ-REQ-ERR] {method} {url[:60]}: {str(e)[:100]}")
        return None

def dz_extract_msg(j):
    if not j: return ""
    if isinstance(j, dict):
        msg = j.get("message")
        if isinstance(msg, dict):
            return msg.get("ar") or msg.get("en") or msg.get("fr") or ""
        if isinstance(msg, str): return msg
    return ""

bot = AsyncTeleBot(TOKEN)
user_steps = {}
_last_otp_sent = {}
MAIN_EVENT_LOOP = None

# ==================== DB ====================
def init_db():
    conn = sqlite3.connect(DB_PATH, timeout=15, check_same_thread=False)
    c = conn.cursor()
    try: c.execute("PRAGMA journal_mode=WAL")
    except: pass
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id INTEGER PRIMARY KEY, username TEXT, join_date TEXT, 
                  is_logged_in INTEGER DEFAULT 0, last_phone TEXT)''')
    try: c.execute("ALTER TABLE users ADD COLUMN last_phone TEXT")
    except: pass
    c.execute('''CREATE TABLE IF NOT EXISTS numbers 
                 (phone TEXT PRIMARY KEY, user_id INTEGER, token TEXT,
                  last_activation_2gb REAL DEFAULT 0,
                  last_activation_3gb REAL DEFAULT 0,
                  last_activation_offers REAL DEFAULT 0, added_date TEXT)''')
    existing_nums = [r[1] for r in c.execute("PRAGMA table_info(numbers)").fetchall()]
    for col, col_type in {'user_id':'INTEGER','token':'TEXT','last_activation_2gb':'REAL DEFAULT 0',
                          'last_activation_3gb':'REAL DEFAULT 0','last_activation_offers':'REAL DEFAULT 0',
                          'added_date':'TEXT'}.items():
        if col not in existing_nums:
            try: c.execute(f"ALTER TABLE numbers ADD COLUMN {col} {col_type}")
            except: pass
    c.execute('''CREATE TABLE IF NOT EXISTS stats (id INTEGER PRIMARY KEY)''')
    if c.execute("SELECT COUNT(*) FROM stats WHERE id = 1").fetchone()[0] == 0:
        c.execute("INSERT INTO stats (id) VALUES (1)")
    all_cols = ["total_2gb","total_3gb","total_offers","oo_logins","oo_snap","oo_spins",
                "oo_balance","oo_offers_view","dz_logins","oo_soccer_enrolls","oo_20dzd_1go",
                "oo_gift_plays","oo_gift_won","oo_gifts_total","oo_free_2gb","oo_bundles","oo_72gb","dz_72gb"]
    existing = [r[1] for r in c.execute("PRAGMA table_info(stats)").fetchall()]
    for col in all_cols:
        if col not in existing:
            try: c.execute(f"ALTER TABLE stats ADD COLUMN {col} INTEGER DEFAULT 0")
            except: pass
    c.execute('''CREATE TABLE IF NOT EXISTS offer_activations
                 (phone TEXT, offer_code TEXT, activated_at REAL,
                  PRIMARY KEY (phone, offer_code))''')
    conn.commit(); conn.close()

init_db()

def db_query(q, p=(), fetch=False, fetchall=False):
    for attempt in range(3):
        try:
            conn = sqlite3.connect(DB_PATH, timeout=15, check_same_thread=False)
            c = conn.cursor()
            c.execute(q, p)
            r = None
            if fetch: r = c.fetchone()
            elif fetchall: r = c.fetchall()
            else: conn.commit()
            conn.close()
            return r
        except sqlite3.OperationalError as e:
            logging.error(f"DB try {attempt+1}: {e}")
            time.sleep(0.2 * (attempt + 1))
        except Exception as e:
            logging.error(f"DB: {e}"); return None
    return None

def inc_stat(field):
    try: db_query(f"UPDATE stats SET {field} = COALESCE({field}, 0) + 1 WHERE id = 1")
    except: pass

# ==================== 72GB helpers ====================
def dz_check_72gb_status(phone):
    row = db_query("SELECT activated_at FROM offer_activations WHERE phone=? AND offer_code='72GB'",
                   (phone,), fetch=True)
    if row and row[0]:
        elapsed = time.time() - row[0]
        if elapsed < 3 * 86400:
            return {"status": "ACTIVE", "expires_in": 3 * 86400 - elapsed}
    return {"status": "NONE"}

def dz_mark_72gb_activated(phone):
    db_query("INSERT OR REPLACE INTO offer_activations (phone, offer_code, activated_at) VALUES (?, '72GB', ?)",
             (phone, time.time()))

def _check_72gb_in_active_products(token, phone):
    h = DJ_HEADERS.copy()
    h['Authorization'] = f"Bearer {token}"
    for url in [f"{DJ_BASE}/api/v1/subscribers/active-products/{phone}",
                f"{DJ_BASE}/api/v1/subscribers/products/{phone}",
                f"{DJ_BASE}/api/v1/services/scan/status/{phone}"]:
        try:
            r = _dz_req("GET", url, headers=h, timeout=8)
            if r and r.status_code == 200:
                body = (r.text or "").lower()
                if any(kw in body for kw in ["72go", "72 gb", "72gb", "72 جيجا"]):
                    return True
        except: continue
    return False

_dz_72gb_semaphore = threading.Semaphore(4)
_dz_72gb_active_uids = set()
_dz_72gb_active_lock = threading.Lock()

def _try_acquire_72gb_slot(uid):
    with _dz_72gb_active_lock:
        if uid in _dz_72gb_active_uids: return False
        _dz_72gb_active_uids.add(uid)
    return True

def _release_72gb_slot(uid):
    with _dz_72gb_active_lock:
        _dz_72gb_active_uids.discard(uid)

def _acquire_and_activate_72gb(token, phone):
    if not _dz_72gb_semaphore.acquire(timeout=25): return "TIMEOUT"
    try: return dj_activate_72gb_scan(token, phone)
    finally: _dz_72gb_semaphore.release()

def save_steps():
    try:
        clean = {}
        for k, v in list(user_steps.items()):
            if isinstance(v, dict):
                clean[str(k)] = {kk: vv for kk, vv in v.items()
                                 if kk in ("step","phone","msisdn","display","last_activity","otp_msg_id")}
            else: clean[str(k)] = v
        STEPS_FILE.write_text(json.dumps(clean, ensure_ascii=False))
    except: pass

def load_steps_saved():
    try:
        if STEPS_FILE.exists():
            d = json.loads(STEPS_FILE.read_text())
            return {int(k): v for k, v in d.items()}
    except: pass
    return {}

# ==================== جيزي ====================
def dj_request_otp(phone):
    url = f"{DJ_BASE}/oauth2/registration"
    params = {'msisdn': phone, 'client_id': DJ_CLIENT_ID, 'scope': "smsotp"}
    payload = {"consent-agreement": [{"marketing-notifications": False}], "is-consent": True}
    for ua in ["MobileApp/3.0.7", "MobileApp/3.0.0", "okhttp/4.12.0"]:
        h = DJ_HEADERS.copy(); h['User-Agent'] = ua
        r = _dz_req("POST", url, headers=h, params=params, json_body=payload, timeout=15)
        if r is None:
            time.sleep(0.5); continue
        if r.status_code == 200: return True
        if r.status_code in (429, 400): return False
        time.sleep(0.5)
    return False

def dj_verify_otp(phone, otp):
    url = f"{DJ_BASE}/oauth2/token"
    clean = ''.join(filter(str.isdigit, otp))
    if len(clean) != 6: return None
    payload = {'otp': clean, 'mobileNumber': phone, 'scope': "djezzyAppV2",
               'client_id': DJ_CLIENT_ID, 'client_secret': DJ_CLIENT_SECRET, 'grant_type': "mobile"}
    h = DJ_HEADERS.copy(); h['Content-Type'] = "application/x-www-form-urlencoded"
    last_status = 0
    for attempt in range(OTP_VERIFY_MAX_RETRY):
        if attempt > 0: time.sleep(OTP_VERIFY_MIN_WAIT)
        r = _dz_req("POST", url, headers=h, data=payload, timeout=25)
        if r is None: continue
        last_status = r.status_code
        if r.status_code == 200:
            try: return r.json().get('access_token')
            except: return None
        if r.status_code == 429: return None
    if last_status == 401: return "EXPIRED"
    return None

def dj_check_balance(token, phone):
    h = DJ_HEADERS.copy()
    h['Authorization'] = f"Bearer {token}"
    h['User-Agent'] = "MobileApp/3.0.7"
    url = f"{DJ_BASE}/api/v1/subscribers/main-balance/{phone}"
    for attempt in range(2):
        r = _dz_req("GET", url, headers=h, timeout=15)
        if r is None: continue
        if r.status_code == 200:
            try:
                data = r.json().get("data", r.json())
                return {"status": "SUCCESS",
                        "balance": float(data.get("mainBalance", 0) or 0),
                        "due": float(data.get("due", 0) or 0)}
            except: return {"status": "FAILED", "balance": 0, "due": 0}
        if r.status_code == 401: return {"status": "EXPIRED", "balance": 0, "due": 0}
        time.sleep(1)
    return {"status": "FAILED", "balance": 0, "due": 0}

def dj_extract_price(p):
    try:
        m = re.search(r'(\d+)', str(p))
        if m: return int(m.group(1))
    except: pass
    return None

def dj_activate_2gb(token, phone):
    h = DJ_HEADERS.copy()
    h['Authorization'] = f"Bearer {token}"
    h['User-Agent'] = "MobileApp/3.0.7"
    endpoints = [f"{DJ_BASE}/api/v1/services/shake/{phone}",
                 f"{DJ_BASE}/api/v1/services/walk/activate-reward/{phone}",
                 f"{DJ_BASE}/api/v1/subscribers/activate-product/{phone}"]
    last_code = 0
    for url in endpoints:
        r = _dz_req("POST", url, headers=h, json_body={"packageCode": "GIFTWALKWIN2GO"}, timeout=20)
        if r is None: continue
        last_code = r.status_code
        if r.status_code == 401: return "EXPIRED"
        if r.status_code in (200, 201):
            body = (r.text or "").lower()
            if "already" in body: return "LIMIT"
            return "SUCCESS"
        if r.status_code == 402: return "NO_BALANCE"
        if r.status_code == 429: return "RATE_LIMIT"
        time.sleep(0.3)
    if last_code == 403: return "NOT_ALLOWED"
    return "FAILED"

def dj_activate_72gb_scan(token, phone):
    db_check = dz_check_72gb_status(phone)
    if db_check["status"] == "ACTIVE": return "LIMIT"
    h = DJ_HEADERS.copy()
    h['Authorization'] = f"Bearer {token}"
    h['User-Agent'] = "MobileApp/3.0.9"
    try:
        if _check_72gb_in_active_products(token, phone):
            dz_mark_72gb_activated(phone)
            return "LIMIT"
    except: pass
    url = f"{DJ_BASE}/api/v1/services/scan/activate-reward/{phone}"
    payload = {"qrCode": DJ_72GB_QR_CODE}
    try:
        r = _dz_req("POST", url, headers=h, json_body=payload, timeout=20)
        if r is None: return "FAILED"
        logging.info(f"[DJ-72GB] {phone} → HTTP {r.status_code} | {(r.text or '')[:250]}")
        if r.status_code == 401: return "EXPIRED"
        body = (r.text or "").lower()
        already_kw = ["already", "déjà", "deja", "مفعل", "activated",
                      "duplicate", "exist", "limit reached", "déjà activé"]
        not_eligible_kw = ["not eligible", "n'êtes pas éligible", "pas éligible",
                           "non éligible", "غير مؤهل", "not-eligible"]
        if any(kw in body for kw in already_kw):
            dz_mark_72gb_activated(phone); return "LIMIT"
        if any(kw in body for kw in not_eligible_kw):
            dz_mark_72gb_activated(phone); return "LIMIT"
        try:
            j = r.json()
            msg = j.get("message", {})
            msg_text = ""
            if isinstance(msg, dict):
                msg_text = (str(msg.get("ar","")) + " " + str(msg.get("en","")) + " " + str(msg.get("fr",""))).lower()
            elif isinstance(msg, str):
                msg_text = msg.lower()
            if msg_text and any(kw in msg_text for kw in already_kw + not_eligible_kw):
                dz_mark_72gb_activated(phone); return "LIMIT"
        except: pass
        if r.status_code in (200, 201):
            dz_mark_72gb_activated(phone); return "SUCCESS"
        if r.status_code == 400: return "NOT_ELIGIBLE"
        if r.status_code == 402: return "NO_BALANCE"
        if r.status_code == 429:
            _rotate_proxy_session(force=True); return "RATE_LIMIT"
        if r.status_code >= 500: return "SERVER_BUSY"
        return "FAILED"
    except Exception as e:
        logging.warning(f"[DJ-72GB] {phone}: {e}")
        return "FAILED"
async def dz_activate_paid_offer_async(token, phone, package_code, offer_type, offer_name, price):
    h = DZ_HEADERS.copy(); h['Authorization'] = f"Bearer {token}"
    async def _try_post(url, label):
        r = await safe_request('POST', url, json={"packageCode": package_code}, headers=h, timeout=12)
        if r['status'] == 401:
            return {"success": False, "token_expired": True, "msg": "⚠️ انتهت جلستك اعد إرسال رقمك"}
        if r['status'] in [200, 201, 202]:
            return {"success": True, "token_expired": False, "msg": f"✅ ━━━ تم التفعيل بنجاح ━━━\n\n🎉 {offer_name}\n💰 السعر: {price} د.ج\n\n{PAGE_FOLLOW_TEXT}"}
        if r['status'] == 402:
            return {"success": False, "token_expired": False, "msg": f"❌ رصيدك غير كافي لتفعيل {offer_name}\n💰 المطلوب: {price} د.ج"}
        srv = dz_extract_msg(r['json'])
        return {"success": False, "token_expired": False, "msg": f"⚠️ تعذر تفعيل {offer_name}\n\nℹ️ {srv or r.get('status','?')}"}
    if offer_type == "shake":
        shake_url = f"{DZ_BASE_URL}/api/v1/services/shake/{phone}"
        for _ in range(4):
            res_get = await safe_request('GET', shake_url, headers=h, timeout=8)
            if res_get['status'] == 401:
                return {"success": False, "token_expired": True, "msg": "⚠️ انتهت جلستك اعد إرسال رقمك"}
            if res_get['status'] == 200: break
            await asyncio.sleep(0.3)
        r_post = await _try_post(shake_url, "shake")
        if not r_post.get("success") and not r_post.get("token_expired"):
            fb = await _try_post(f"{DZ_BASE_URL}/api/v1/subscribers/activate-product/{phone}", "fb")
            if fb.get("success") or fb.get("token_expired"): return fb
        return r_post
    return await _try_post(f"{DZ_BASE_URL}/api/v1/subscribers/activate-product/{phone}", "activate")

async def dz_activate_offer_70_4g_async(token, phone):
    h = DZ_HEADERS.copy(); h['Authorization'] = f"Bearer {token}"
    async def _try_post(url, label):
        r = await safe_request('POST', url, json={"packageCode": "BTLINTSPEEDDAY2GO"}, headers=h, timeout=12)
        if r.get('status') == 401:
            return {"success": False, "token_expired": True, "msg": "⚠️ انتهت جلستك"}
        if r.get('status') in [200, 201, 202]:
            return {"success": True, "token_expired": False, "msg": f"✅ ━━━ تم التفعيل بنجاح ━━━\n\n🟢 عرض: 4 جيجابايت\n💰 السعر: 70 د.ج\n⏱️ الصلاحية: 24 ساعة\n\n{PAGE_FOLLOW_TEXT}"}
        if r.get('status') == 402:
            return {"success": False, "token_expired": False, "msg": "❌ رصيدك غير كافٍ"}
        srv = dz_extract_msg(r.get('json'))
        return {"success": False, "token_expired": False, "msg": f"⚠️ تعذر التفعيل\nℹ️ {srv or r.get('status','?')}"}
    shake_url = f"{DZ_BASE_URL}/api/v1/services/shake/{phone}"
    for _ in range(3):
        res_get = await safe_request('GET', shake_url, headers=h, timeout=8)
        if res_get.get('status') == 401:
            return {"success": False, "token_expired": True, "msg": "⚠️ انتهت جلستك"}
        if res_get.get('status') == 200: break
        await asyncio.sleep(0.5)
    r_post = await _try_post(shake_url, "shake")
    if not r_post.get("success") and not r_post.get("token_expired"):
        fb = await _try_post(f"{DZ_BASE_URL}/api/v1/subscribers/activate-product/{phone}", "fb")
        if fb.get("success") or fb.get("token_expired"): return fb
    return r_post

async def dz_activate_offer_90_5g_async(token, phone):
    h = DZ_HEADERS.copy(); h['Authorization'] = f"Bearer {token}"
    async def _try_post(url, label):
        r = await safe_request('POST', url, json={"packageCode": "BTL500MBDAY"}, headers=h, timeout=12)
        if r.get('status') == 401:
            return {"success": False, "token_expired": True, "msg": "⚠️ انتهت جلستك"}
        if r.get('status') in [200, 201, 202]:
            return {"success": True, "token_expired": False, "msg": f"✅ ━━━ تم التفعيل بنجاح ━━━\n\n🟣 عرض: 5 جيجابايت\n💰 السعر: 90 د.ج\n⏱️ الصلاحية: 24 ساعة\n\n{PAGE_FOLLOW_TEXT}"}
        if r.get('status') == 402:
            return {"success": False, "token_expired": False, "msg": "❌ رصيدك غير كافٍ"}
        srv = dz_extract_msg(r.get('json'))
        return {"success": False, "token_expired": False, "msg": f"⚠️ تعذر التفعيل\nℹ️ {srv or r.get('status','?')}"}
    shake_url = f"{DZ_BASE_URL}/api/v1/services/shake/{phone}"
    for _ in range(3):
        res_get = await safe_request('GET', shake_url, headers=h, timeout=8)
        if res_get.get('status') == 401:
            return {"success": False, "token_expired": True, "msg": "⚠️ انتهت جلستك"}
        if res_get.get('status') == 200: break
        await asyncio.sleep(0.5)
    r_post = await _try_post(shake_url, "shake")
    if not r_post.get("success") and not r_post.get("token_expired"):
        fb = await _try_post(f"{DZ_BASE_URL}/api/v1/subscribers/activate-product/{phone}", "fb")
        if fb.get("success") or fb.get("token_expired"): return fb
    return r_post

# ==================== أوريدو ====================
def _now_ms(): return str(int(time.time() * 1000))
def _iid(): return str(uuid.uuid4()) + _now_ms()
def _pld(x):
    return base64.b64encode(json.dumps({"platform":"android","is-physical-device":True,"device-id":x},
                                       separators=(",",":")).encode()).decode()
def _fp(): return os.urandom(32).hex()
def _corr(): return str(uuid.uuid4()) + str(int(time.time() * 100))

def _exdid(at):
    """استخراج device-id من JWT"""
    try:
        p = at.split(".")
        pad = len(p[1]) % 4
        return json.loads(base64.b64decode(p[1] + "="*(4-pad) if pad else p[1])).get("device-id")
    except: return None

def _mps(at):
    d = _exdid(at) or _iid()
    return base64.b64encode(json.dumps({"platform":"android","is-physical-device":True,
                                        "device-id":d},separators=(",",":")).encode()).decode()

def oo_quick_detect(at):
    rp = ""; is_yooz = False; is_dima = False
    try:
        p = at.split(".")
        pad = len(p[1]) % 4
        payload = json.loads(base64.b64decode(p[1] + "=" * (4 - pad) if pad else p[1]))
        rp_code = str(payload.get("ratePlan") or "")
        if rp_code in RATE_PLAN_NAMES:
            rp = RATE_PLAN_NAMES[rp_code]
            rp_up = rp.upper().replace("'", "").replace(" ", "")
            is_dima = "DIMA" in rp_up
            is_yooz = "YOOZ" in rp_up
    except: pass
    return {"rate_plan": rp, "is_yooz": is_yooz, "is_dima": is_dima}

def _base_hdrs(msisdn, iid_val, psig, corr, ts, fp=None):
    return {"user-agent":"Dart/3.11 (dart:io)","accept-encoding":"gzip","x-msisdn":msisdn,
            "x-device-fingerprint":fp or _fp(),"x-platform-origin":"mobile-android","x-correlation-id":corr,
            "platform":"android","x-version":X_VERSION,"x-signature":X_SIG,
            "x-platform-data-signature":psig,"x-timestamp":ts,"x-instance-id":iid_val}

def _web_hdrs(msisdn, at, meta, ct=""):
    ts = _now_ms()
    iid_val = meta.get("tok_instance_id") or _iid()
    psig = meta.get("tok_plat_sig") or _pld(iid_val)
    fp = meta.get("tok_fingerprint") or _fp()
    h = {"User-Agent":"Dart/3.11 (dart:io)","Accept-Encoding":"gzip","x-msisdn":msisdn,
         "x-device-fingerprint":fp,"x-platform-origin":"web",
         "authorization":f"Bearer {at}","x-correlation-id":_corr(),
         "platform":"web","x-version":X_VERSION,"x-signature":X_SIG,
         "x-platform-data-signature":psig,"x-timestamp":ts,"x-instance-id":iid_val,
         "origin":"https://my.ooredoo.dz","referer":"https://my.ooredoo.dz/"}
    if ct: h["content-type"] = ct
    return h

def ooredoo_send_otp_sync(msisdn, uid):
    """v6.8.3:
    • نفس الـ proxy لـ 4 محاولات متتالية
    • نفس الـ device-fingerprint طوال المحاولات
    • 403 = OTP SENT بنجاح → توقف فوري
    """
    START = time.time()
    OVERALL_TIMEOUT = 180
    MAX_ATTEMPTS = OO_OTP_MAX_ATTEMPTS
    SAME_PROXY_ATTEMPTS = 4
    wait = 2.5
    last_status = -1
    last_reason = ""

    # device ثابت لكل المحاولات
    iid_val = _iid()
    psig = _pld(iid_val)
    fp = _fp()

    current_proxy = None
    attempts_on_current = 0
    tried_proxies = set()

    for attempt in range(MAX_ATTEMPTS):
        if time.time() - START > OVERALL_TIMEOUT:
            last_reason = "overall_timeout"
            logging.warning(f"[OO-OTP] {msisdn} ⏰ timeout after {attempt} attempts")
            break

        if current_proxy is None or attempts_on_current >= SAME_PROXY_ATTEMPTS:
            if current_proxy:
                tried_proxies.add(current_proxy)
                _release_oo_proxy(uid, reason="switch")
            if len(tried_proxies) >= 40:
                tried_proxies.clear()
            current_proxy = _get_oo_proxy_for_user(uid, exclude=tried_proxies)
            attempts_on_current = 0
            if not current_proxy:
                last_reason = "no_proxy"
                break
            logging.info(f"[OO-OTP] {msisdn} 🔄 NEW proxy={_mask_oo_proxy(current_proxy)} (switch #{len(tried_proxies)})")

        attempts_on_current += 1
        proxy_str = current_proxy
        device = {"instance_id": iid_val, "plat_sig": psig, "fp": fp, "proxy_str": proxy_str}
        ts = _now_ms()
        nonce, chronos = "", ""

        # Step 1: checkpoint
        try:
            h3 = _base_hdrs(msisdn, iid_val, psig, _corr(), ts, fp=fp)
            h3["x-version"] = X_VERSION_OTP
            h3.update({"content-type": "application/json; charset=utf-8",
                       "x-native-integrity-token": INTEGRITY_1,
                       "x-path": "/api/auth/realms/myooredoo/protocol/openid-connect/token",
                       "x-method": "POST"})
            r3 = _oo_req_with_proxy("POST", f"{OO_BFF}/checkpoint/token", h3, b"{}",
                                    timeout=25, proxy_str=proxy_str)
            if r3 is None:
                _mark_oo_proxy_fail(proxy_str, "checkpoint_none")
                last_status, last_reason = 0, "checkpoint_none"
                logging.info(f"[OO-OTP] {msisdn} attempt {attempt+1}/{MAX_ATTEMPTS} "
                             f"proxy={_mask_oo_proxy(proxy_str)} "
                             f"({attempts_on_current}/{SAME_PROXY_ATTEMPTS}) → checkpoint FAIL")
                time.sleep(wait); wait = min(wait * 1.3, 12)
                continue
            _, rh3, _ = r3
            nonce = rh3.get("x-nonce-id") or rh3.get("X-Nonce-Id") or ""
            chronos = rh3.get("x-chronos-id") or rh3.get("X-Chronos-Id") or ""
        except Exception as e:
            logging.error(f"[OO-OTP] checkpoint exc: {e}")
            time.sleep(wait); wait = min(wait * 1.3, 12)
            continue

        # Step 2: إرسال OTP
        try:
            h4 = {"User-Agent": "Dart/3.11 (dart:io)", "Accept-Encoding": "gzip",
                  "x-msisdn": msisdn, "x-device-fingerprint": fp,
                  "x-platform-origin": "mobile-android", "platform": "android",
                  "x-version": X_VERSION_OTP, "x-signature": X_SIG, "x-timestamp": ts,
                  "x-platform-info": psig, "x-force-update": "true",
                  "x-instance-id": iid_val,
                  "content-type": "application/x-www-form-urlencoded"}
            if nonce:   h4["x-nonce-id"] = nonce
            if chronos: h4["x-chronos-id"] = chronos
            body = f"client_id={OO_CLIENT}&grant_type=password&username={msisdn}"
            r4 = _oo_req_with_proxy("POST", OO_AUTH, h4, body, timeout=35, proxy_str=proxy_str)
            if r4 is None:
                _mark_oo_proxy_fail(proxy_str, "otp_none")
                last_status, last_reason = 0, "otp_none"
                logging.info(f"[OO-OTP] {msisdn} attempt {attempt+1}/{MAX_ATTEMPTS} "
                             f"proxy={_mask_oo_proxy(proxy_str)} "
                             f"({attempts_on_current}/{SAME_PROXY_ATTEMPTS}) → NONE")
                time.sleep(wait); wait = min(wait * 1.3, 12)
                continue
            c4, _, _ = r4
            last_status = c4
            logging.info(f"[OO-OTP] {msisdn} uid={uid} attempt {attempt+1}/{MAX_ATTEMPTS} "
                         f"proxy={_mask_oo_proxy(proxy_str)} "
                         f"({attempts_on_current}/{SAME_PROXY_ATTEMPTS}) → {c4}")

            # ✅ 403 = OTP SENT بنجاح
            if c4 == 403:
                logging.info(f"[OO-OTP] {msisdn} ✅ OTP SENT (403 = success)")
                _release_oo_proxy(uid, reason="success")
                return {"device": device, "otp_sent": True, "status": 403}

            if c4 in (200, 401):
                logging.info(f"[OO-OTP] {msisdn} ✅ OTP SENT (code={c4})")
                _release_oo_proxy(uid, reason="success")
                return {"device": device, "otp_sent": True, "status": c4}

            if c4 == 429:
                logging.info(f"[OO-OTP] {msisdn} ⚠️ 429 rate-limit → switching proxy")
                attempts_on_current = SAME_PROXY_ATTEMPTS
                time.sleep(wait * 1.5); wait = min(wait * 1.3, 15)
                continue

            _mark_oo_proxy_fail(proxy_str, f"http{c4}")
            time.sleep(wait); wait = min(wait * 1.3, 12)
            continue
        except Exception as e:
            logging.error(f"[OO-OTP] send exc: {e}")
            time.sleep(wait); wait = min(wait * 1.3, 12)
            continue

    _release_oo_proxy(uid, reason="all_failed")
    logging.warning(f"[OO-OTP] {msisdn} uid={uid} ❌ FAILED | reason={last_reason} last={last_status}")
    return {"device": {"instance_id": iid_val, "plat_sig": psig, "fp": fp, "proxy_str": None},
            "otp_sent": False, "status": last_status, "reason": last_reason or "all_proxies_failed"}

def ooredoo_verify_otp_sync(msisdn, otp, device, uid):
    proxy_str = device.get("proxy_str")
    iid_val = device.get("instance_id") or _iid()
    psig = device.get("plat_sig") or _pld(iid_val)
    fp_otp = device.get("fp") or _fp()
    def _one_attempt():
        ts = _now_ms(); nonce, chronos = "", ""
        try:
            h6 = _base_hdrs(msisdn, iid_val, psig, _corr(), ts, fp=fp_otp)
            h6["x-version"] = X_VERSION_OTP
            h6.update({"content-type":"application/json; charset=utf-8",
                       "x-native-integrity-token":INTEGRITY_2,
                       "x-path":"/api/auth/realms/myooredoo/protocol/openid-connect/token","x-method":"POST"})
            r6 = _oo_req_with_proxy("POST", f"{OO_BFF}/checkpoint/token", h6, b"{}", timeout=15, proxy_str=proxy_str)
            if r6 is None: return 0, {}
            _, rh6, _ = r6
            nonce = rh6.get("x-nonce-id") or rh6.get("X-Nonce-Id") or ""
            chronos = rh6.get("x-chronos-id") or rh6.get("X-Chronos-Id") or ""
        except: pass
        h7 = {"User-Agent":"Dart/3.11 (dart:io)","Accept-Encoding":"gzip","x-msisdn":msisdn,
              "x-device-fingerprint":fp_otp,"x-platform-origin":"mobile-android",
              "platform":"android","x-version":X_VERSION_OTP,"x-signature":X_SIG,
              "x-timestamp":ts,"x-platform-info":psig,"x-force-update":"true",
              "x-instance-id":iid_val,"content-type":"application/x-www-form-urlencoded"}
        if nonce: h7["x-nonce-id"] = nonce
        if chronos: h7["x-chronos-id"] = chronos
        body = f"client_id={OO_CLIENT}&grant_type=password&username={msisdn}&otp={otp}"
        r7 = _oo_req_with_proxy("POST", OO_AUTH, h7, body, timeout=25, proxy_str=proxy_str)
        if r7 is None: return 0, {}
        c7, _, j7 = r7
        return c7, j7
    last_status = 0
    for attempt in range(OTP_VERIFY_MAX_RETRY):
        if attempt > 0: time.sleep(OTP_VERIFY_MIN_WAIT)
        try:
            c7, j7 = _one_attempt()
            last_status = c7
            logging.info(f"[OO-VERIFY] {msisdn} uid={uid} attempt {attempt+1} → {c7}")
            if c7 == 200 and isinstance(j7, dict) and "access_token" in j7:
                at = j7["access_token"]
                _release_oo_proxy(uid, reason="verify_ok")
                return {"access_token": at, "refresh_token": j7.get("refresh_token",""),
                        "expires_in": j7.get("expires_in", 0), "tok_fingerprint": fp_otp,
                        "tok_instance_id": _exdid(at) or iid_val, "tok_plat_sig": _mps(at),
                        "tok_timestamp": _now_ms(), "issued_at": int(time.time())}
            if c7 == 429:
                _release_oo_proxy(uid, reason="rate_limit"); return None
            if c7 == 0: continue
        except: continue
    _release_oo_proxy(uid, reason="verify_failed")
    if last_status in (400, 401, 403): return "wrong_otp"
    return None

def ooredoo_refresh_token_sync(msisdn, rt, device, uid):
    iid_val = device.get("instance_id") or _iid()
    psig = device.get("plat_sig") or _pld(iid_val)
    fp_otp = device.get("fp") or _fp()
    ts = _now_ms()
    tried = set()
    for _ in range(3):
        proxy_str = _get_oo_proxy_for_user(uid, exclude=tried)
        if not proxy_str or proxy_str in tried: break
        tried.add(proxy_str)
        h = _base_hdrs(msisdn, iid_val, psig, _corr(), ts, fp=fp_otp)
        h.update({"content-type":"application/x-www-form-urlencoded",
                  "x-native-integrity-token":INTEGRITY_1,
                  "x-path":"/api/auth/realms/myooredoo/protocol/openid-connect/token","x-method":"POST"})
        r = _oo_req_with_proxy("POST", f"{OO_BFF}/checkpoint/token", h, b"{}", timeout=15, proxy_str=proxy_str)
        if r is None:
            _release_oo_proxy(uid, "refresh_proxy_fail"); continue
        _, rh, _ = r
        nonce = rh.get("x-nonce-id") or rh.get("X-Nonce-Id") or ""
        chronos = rh.get("x-chronos-id") or rh.get("X-Chronos-Id") or ""
        if not nonce or not chronos:
            _release_oo_proxy(uid, "refresh_no_nonce"); continue
        h2 = {"User-Agent":"Dart/3.11 (dart:io)","Accept-Encoding":"gzip","x-msisdn":msisdn,
              "x-device-fingerprint":fp_otp,"x-nonce-id":nonce,"x-platform-origin":"mobile-android",
              "platform":"android","x-version":X_VERSION,"x-signature":X_SIG,"x-chronos-id":chronos,
              "x-timestamp":ts,"x-platform-info":psig,"x-force-update":"true","x-instance-id":iid_val,
              "content-type":"application/x-www-form-urlencoded"}
        body = f"client_id={OO_CLIENT}&grant_type=refresh_token&refresh_token={rt}"
        r2 = _oo_req_with_proxy("POST", OO_AUTH, h2, body, timeout=20, proxy_str=proxy_str)
        _release_oo_proxy(uid, "refresh_done")
        if r2 is None: continue
        c2, _, j2 = r2
        if c2 == 200 and isinstance(j2, dict) and "access_token" in j2:
            at = j2["access_token"]
            return {"access_token": at, "refresh_token": j2.get("refresh_token", rt),
                    "expires_in": j2.get("expires_in", 0),
                    "tok_instance_id": _exdid(at) or iid_val, "tok_plat_sig": _mps(at),
                    "tok_fingerprint": fp_otp, "tok_timestamp": _now_ms(), "issued_at": int(time.time())}
        if c2 == 401: return None
    return None

def oo_check_balance(msisdn, at, meta, uid):
    h = _web_hdrs(msisdn, at, meta)
    c, _, resp = _oo_req_with_proxy("GET", f"{OO_BFF}/subscriptions/getAccountInfo", h, timeout=20,
                                    proxy_str=_oo_user_to_proxy.get(uid))
    if c == 200: return {"status": "ok", "data": resp if isinstance(resp, dict) else {}}
    if c == 401: return {"status": "unauthorized"}
    return {"status": "error", "code": c}

def oo_get_active(msisdn, at, meta, uid):
    h = _web_hdrs(msisdn, at, meta)
    c, _, resp = _oo_req_with_proxy("GET", f"{OO_BFF}/bundle/getActivePackages?msisdn={msisdn}", h,
                                    timeout=20, proxy_str=_oo_user_to_proxy.get(uid))
    if c == 200: return {"status": "ok", "data": resp if isinstance(resp, dict) else {}}
    if c == 401: return {"status": "unauthorized"}
    return {"status": "error", "code": c}

def oo_activate_snapchat(msisdn, at, meta, uid):
    h = _web_hdrs(msisdn, at, meta)
    c, _, _ = _oo_req_with_proxy("POST", f"{OO_BFF}/snap-chat/apply", h, timeout=20,
                                 proxy_str=_oo_user_to_proxy.get(uid))
    if c == 200: return "ok"
    if c == 500: return "already_active"
    if c == 401: return "unauthorized"
    return "error"

def oo_activate_ramadan_72gb(msisdn, at, meta, uid):
    """v6.8.4:
    • device-id من JWT مباشرة (سبب 401 السابق)
    • إصلاح None unpack
    • نفس البروكسي 4 محاولات
    • 200 = نجاح، 401 = تبديل proxy وجرّب
    """
    jwt_device_id = _exdid(at)
    if not jwt_device_id:
        logging.error(f"[OO-RAMADAN-72GB] {msisdn} ❌ device-id missing in JWT")
        return {"status": "unauthorized", "data": {"_error": "no_device_id_in_jwt"}}

    iid_val = jwt_device_id
    psig = _pld(iid_val)
    fp = meta.get("tok_fingerprint") or _fp()

    h = {
        "x-msisdn": msisdn,
        "user-agent": "Dart/3.11 (dart:io)",
        "x-device-fingerprint": fp,
        "accept-encoding": "gzip",
        "x-platform-origin": "mobile-android",
        "authorization": f"Bearer {at}",
        "x-correlation-id": _corr(),
        "content-type": "application/json; charset=utf-8",
        "platform": "android",
        "x-version": "1.5.17",
        "x-signature": X_SIG_RAMADAN,
        "accept": "*/*",
        "x-platform-data-signature": psig,
        "x-timestamp": _now_ms(),
        "x-instance-id": iid_val,
    }
    body = json.dumps({"couponCode": ""}, separators=(",", ":"))

    MAX_ATTEMPTS = OO_72GB_MAX_ATTEMPTS
    SAME_PROXY_ATTEMPTS = 4
    wait = 2.5
    last_c, last_resp = 0, {}

    current_proxy = None
    attempts_on_current = 0
    tried_proxies = set()

    for attempt in range(MAX_ATTEMPTS):
        if current_proxy is None or attempts_on_current >= SAME_PROXY_ATTEMPTS:
            if current_proxy:
                tried_proxies.add(current_proxy)
                _release_oo_proxy(uid, reason="switch")
            if len(tried_proxies) >= 40:
                tried_proxies.clear()
            current_proxy = _get_oo_proxy_for_user(uid, exclude=tried_proxies)
            attempts_on_current = 0
            if not current_proxy:
                break
            logging.info(f"[OO-RAMADAN-72GB] {msisdn} 🔄 NEW proxy={_mask_oo_proxy(current_proxy)}")

        attempts_on_current += 1
        proxy_str = current_proxy

        h["x-timestamp"] = _now_ms()
        h["x-correlation-id"] = _corr()

        try:
            r = _oo_req_with_proxy("POST", f"{OO_BFF}/ramadan/activate", h, body,
                                   timeout=30, proxy_str=proxy_str)
            if r is None:
                last_c, last_resp = 0, {"_error": "response_none"}
                logging.info(
                    f"[OO-RAMADAN-72GB] {msisdn} attempt {attempt+1}/{MAX_ATTEMPTS} "
                    f"proxy={_mask_oo_proxy(proxy_str)} "
                    f"({attempts_on_current}/{SAME_PROXY_ATTEMPTS}) → NONE"
                )
                time.sleep(wait); wait = min(wait * 1.3, 12)
                continue
            c, _, resp = r
            last_c, last_resp = c, resp
            logging.info(
                f"[OO-RAMADAN-72GB] {msisdn} uid={uid} attempt {attempt+1}/{MAX_ATTEMPTS} "
                f"proxy={_mask_oo_proxy(proxy_str)} "
                f"({attempts_on_current}/{SAME_PROXY_ATTEMPTS}) → {c} | {str(resp)[:150]}"
            )
        except Exception as e:
            logging.error(f"[OO-RAMADAN-72GB] {msisdn} attempt {attempt+1} exc: {e}")
            last_c, last_resp = 0, {"_error": str(e)[:100]}
            time.sleep(wait); wait = min(wait * 1.3, 12)
            continue

        if last_c in (200, 201):
            resp_str = str(last_resp).lower()
            if any(k in resp_str for k in ("already", "déjà", "deja", "مفعل", "duplicate", "exist")):
                return {"status": "already", "data": last_resp}
            return {"status": "ok", "data": last_resp}

        if last_c == 401:
            if len(tried_proxies) < 2 and attempt < 8:
                logging.info(f"[OO-RAMADAN-72GB] {msisdn} ⚠️ 401 → switching proxy")
                attempts_on_current = SAME_PROXY_ATTEMPTS
                time.sleep(wait); wait = min(wait * 1.3, 10)
                continue
            return {"status": "unauthorized", "data": last_resp}

        if last_c == 404:
            return {"status": "not_allowed", "data": last_resp}

        _mark_oo_proxy_fail(proxy_str, f"http{last_c}")
        time.sleep(wait); wait = min(wait * 1.3, 12)

    return {"status": "error", "code": last_c, "data": last_resp}

def oo_purchase_20dzd_1go(msisdn, at, meta, uid):
    body = json.dumps({"bundleCode": "BTL_24H_DATA_20DZD_1Go", "validity": "day", "validityAmount": "1"},
                      separators=(",", ":"))
    iid_val = meta.get("tok_instance_id") or _iid()
    psig = meta.get("tok_plat_sig") or _pld(iid_val)
    fp = meta.get("tok_fingerprint") or _fp()
    def _mobile_hdrs(v):
        return {"x-msisdn": msisdn, "user-agent": "Dart/3.11 (dart:io)",
                "x-device-fingerprint": fp, "accept-encoding": "gzip",
                "x-platform-origin": "mobile-android", "authorization": f"Bearer {at}",
                "x-correlation-id": _corr(), "content-type": "application/json; charset=utf-8",
                "platform": "android", "x-version": v, "x-signature": X_SIG,
                "accept": "*/*", "x-platform-data-signature": psig,
                "x-timestamp": _now_ms(), "x-instance-id": iid_val}
    try:
        _oo_req_with_proxy("GET", f"{OO_BFF}/subscriptions/getAccountInfo", _web_hdrs(msisdn, at, meta),
                           timeout=12, proxy_str=_oo_user_to_proxy.get(uid))
    except: pass
    c = 0; resp = {}
    for label, h in [("mobile v1.5.16", _mobile_hdrs("1.5.16")), ("mobile v1.5.15", _mobile_hdrs("1.5.15"))]:
        c, _, resp = _oo_req_with_proxy("POST", f"{OO_BFF}/cvm/bundlePurchase", h, body, timeout=25,
                                        proxy_str=_oo_user_to_proxy.get(uid))
        logging.info(f"[OO-20DZD-1GO] {msisdn} uid={uid} [{label}] → {c}")
        if c in (200, 201): return {"status": "ok", "data": resp}
        if c in (402, 409): break
    if c in (402, 409):
        srv_code = str(resp.get("code") or "").upper() if isinstance(resp, dict) else ""
        if any(k in srv_code for k in ("CREDIT","BALANCE","NOT_ENOUGH")): return {"status": "no_balance"}
        if "ALREADY" in srv_code: return {"status": "already"}
        if any(k in srv_code for k in ("NOT_AVAILABLE","NOT_ALLOWED")): return {"status": "not_allowed"}
        return {"status": "no_balance"}
    if c == 401: return {"status": "purchase_blocked"}
    return {"status": "error", "code": c}

def oo_purchase_free_2gb(msisdn, at, meta, uid):
    body_simple = json.dumps({"bundleCode": "BTL_24H_DATA_Free_2Go"}, separators=(",", ":"))
    body_full = json.dumps({"bundleCode": "BTL_24H_DATA_Free_2Go",
                            "validity": "day", "validityAmount": "1"}, separators=(",", ":"))
    endpoints = [f"{OO_BFF}/cvm/bundlePurchase", f"{OO_BFF}/cvm/dynamic-bundle-purchase"]
    bodies = [body_simple, body_full]
    already_seen = None
    for round_idx in range(2):
        if round_idx > 0: time.sleep(2)
        for ep_label, url in enumerate(endpoints):
            for body_label, body in enumerate(bodies):
                try:
                    h = _web_hdrs(msisdn, at, meta, "application/json; charset=utf-8")
                    c, _, resp = _oo_req_with_proxy("POST", url, h, body, timeout=25,
                                                    proxy_str=_oo_user_to_proxy.get(uid))
                    logging.info(f"[OO-FREE-2GB] {msisdn} uid={uid} r{round_idx+1}/{ep_label}/{body_label} → {c}")
                except Exception as e:
                    c, resp = 0, {"_error": str(e)[:100]}
                if c in (200, 201): return {"status": "ok", "data": resp}
                resp_str = str(resp).lower()
                if any(k in resp_str for k in ("already","déjà","purchased","subscribed","duplicate","exist")):
                    already_seen = resp; continue
                if c == 401: return {"status": "unauthorized", "data": resp}
                if c == 429: time.sleep(3); break
    if already_seen is not None: return {"status": "already", "data": already_seen}
    return {"status": "error", "data": None}

# ==================== Sessions ====================
def oo_save(uid, d):
    (SESSIONS_DIR / f"oo_{uid}.json").write_text(json.dumps(d, ensure_ascii=False))

def oo_load(uid):
    f = SESSIONS_DIR / f"oo_{uid}.json"
    return json.loads(f.read_text()) if f.exists() else None

def oo_clear(uid):
    f = SESSIONS_DIR / f"oo_{uid}.json"
    if f.exists(): f.unlink()

def dz_save_session(uid, phone, token):
    try:
        (SESSIONS_DIR / f"dz_{uid}.json").write_text(json.dumps({"phone": phone, "token": token, "issued_at": time.time()}, ensure_ascii=False))
    except: pass

def dz_clear_session(uid):
    try:
        f = SESSIONS_DIR / f"dz_{uid}.json"
        if f.exists(): f.unlink()
    except: pass

def oo_free2gb_save(uid, msisdn):
    try:
        (SESSIONS_DIR / f"free2gb_{uid}.json").write_text(
            json.dumps({"msisdn": msisdn, "last": time.time()}, ensure_ascii=False))
    except: pass

def oo_free2gb_get_last(uid, msisdn):
    try:
        f = SESSIONS_DIR / f"free2gb_{uid}.json"
        if not f.exists(): return 0
        d = json.loads(f.read_text())
        if d.get("msisdn") == msisdn: return d.get("last", 0)
    except: pass
    return 0

def oo_free2gb_clear(uid):
    try:
        f = SESSIONS_DIR / f"free2gb_{uid}.json"
        if f.exists(): f.unlink()
    except: pass

def o_mask(m):
    if not m: return "?"
    if len(m) >= 6: return m[:4] + "xxxx" + m[-2:]
    return m

def dz_mask(m):
    return "0" + m[3:] if m.startswith("213") else m

def oo_ensure_valid(uid, user):
    if not user or not user.get("access_token"): return None
    issued = user.get("issued_at", 0); exp = user.get("expires_in", 0)
    if issued and exp and (time.time() - issued) < (exp - 1800): return user
    ref = ooredoo_refresh_token_sync(user["msisdn"], user.get("refresh_token",""),
                                     {"instance_id": user.get("tok_instance_id"),
                                      "plat_sig": user.get("tok_plat_sig"),
                                      "fp": user.get("tok_fingerprint")}, uid)
    if ref:
        user.update(ref); oo_save(uid, user); return user
    return None

_stop_threads = threading.Event()

def oo_auto_refresh():
    while not _stop_threads.is_set():
        try:
            time.sleep(900)
            for f in list(SESSIONS_DIR.glob("oo_*.json")):
                try:
                    uid_s = f.stem.replace("oo_", "")
                    if not uid_s.isdigit(): continue
                    u = oo_load(int(uid_s))
                    if not u or not u.get("access_token"): continue
                    issued = u.get("issued_at", 0); exp = u.get("expires_in", 0)
                    if issued and exp and (time.time() - issued) >= (exp - 600):
                        oo_ensure_valid(int(uid_s), u)
                except: pass
        except: pass

def dz_auto_refresh():
    while not _stop_threads.is_set():
        try:
            time.sleep(900)
            for f in list(SESSIONS_DIR.glob("dz_*.json")):
                try:
                    uid_s = f.stem.replace("dz_", "")
                    if not uid_s.isdigit(): continue
                    s = json.loads(f.read_text())
                    st = dj_check_balance(s["token"], s["phone"])
                    if isinstance(st, dict) and st.get("status") == "EXPIRED":
                        dz_clear_session(int(uid_s))
                except: pass
        except: pass

def steps_saver_worker():
    while not _stop_threads.is_set():
        try:
            time.sleep(30); save_steps()
        except: pass

def reset_steps_worker():
    while not _stop_threads.is_set():
        try:
            time.sleep(4 * 3600)
            for uid in list(user_steps.keys()):
                user_steps[uid] = {"step": "await_phone", "last_activity": time.time()}
            cutoff = time.time() - 3600
            for k in list(_last_otp_sent.keys()):
                if _last_otp_sent[k] < cutoff: _last_otp_sent.pop(k, None)
            save_steps()
        except: pass

def _proxy_proactive_rotate():
    while not _stop_threads.is_set():
        try:
            time.sleep(25 * 60); _rotate_proxy_session(force=True)
        except: pass

def oo_proxy_cleaner():
    while not _stop_threads.is_set():
        try:
            time.sleep(60); now = time.time(); expired = []
            with _oo_proxy_lock:
                for u, p in list(_oo_user_to_proxy.items()):
                    info = _oo_proxy_in_use.get(p)
                    if info and (now - info["since"]) >= OO_PROXY_HOLD_SECONDS:
                        expired.append(u)
            for u in expired: _release_oo_proxy(u, reason="timeout")
        except: pass

# ==================== Server Monitor ====================
SERVER_STATUS_FILE = BASE_DIR / "server_status.json"
_server_status = {"dz": True, "oo": True, "changed_at": time.time()}
_server_status_lock = threading.Lock()

def _load_server_status():
    global _server_status
    try:
        if SERVER_STATUS_FILE.exists():
            _server_status = json.loads(SERVER_STATUS_FILE.read_text())
    except: pass

def _save_server_status():
    try:
        SERVER_STATUS_FILE.write_text(json.dumps(_server_status, ensure_ascii=False))
    except: pass

def _check_dz_server_alive():
    for method, path in [("GET", "/oauth2/token"), ("GET", "/api/v1/health")]:
        try:
            r = _dz_req(method, f"{DJ_BASE}{path}", timeout=10)
            if r is not None and r.status_code < 500:
                return True
        except: pass
    return False

def _check_oo_server_alive():
    """v6.8.4: أي رد (حتى 401/403/404) = السيرفر شغّال"""
    for path in ["/actuator/health", "/subscriptions/getAccountInfo", "/"]:
        try:
            c, _, _ = _oo_req_direct("GET", f"{OO_BFF}{path}",
                                     {"x-msisdn": "213000000000",
                                      "user-agent": "Dart/3.11 (dart:io)",
                                      "x-version": "1.5.17"}, 15)
            if c and c > 0:
                return True
        except: pass
    return False

def _notify_users_server_back(network):
    if not MAIN_EVENT_LOOP: return
    async def _send():
        try:
            if network == "dz":
                rows = db_query(
                    "SELECT DISTINCT user_id FROM numbers WHERE token IS NOT NULL AND token != 'EXPIRED'",
                    fetchall=True) or []
                users = [r[0] for r in rows if r and r[0]]
                msg = (
                    "🟢 ━━━━━━━━━━━━━━━━ 🟢\n"
                    "   <b>سيرفر جيزي اشتغل!</b>\n"
                    "🟢 ━━━━━━━━━━━━━━━━ 🟢\n\n"
                    "✅ السيرفر رجع نشط الآن\n"
                    "💡 يمكنك إعادة المحاولة من /start\n\n"
                    f"📢 {CHANNEL_LINK}"
                )
            else:
                users = []
                for f in SESSIONS_DIR.glob("oo_*.json"):
                    try:
                        u = f.stem.replace("oo_", "")
                        if u.isdigit(): users.append(int(u))
                    except: pass
                msg = (
                    "🟢 ━━━━━━━━━━━━━━━━ 🟢\n"
                    "  <b>سيرفر أوريدو اشتغل!</b>\n"
                    "🟢 ━━━━━━━━━━━━━━━━ 🟢\n\n"
                    "✅ السيرفر رجع نشط الآن\n"
                    "💡 يمكنك إعادة المحاولة من /start\n\n"
                    f"📢 {CHANNEL_LINK}"
                )
            sent = 0; failed = 0
            for u in users:
                try:
                    await bot.send_message(u, msg, parse_mode='HTML')
                    sent += 1
                    await asyncio.sleep(0.05)
                except Exception:
                    failed += 1
            logging.info(f"[SERVER-MONITOR] 📢 notified {sent}/{len(users)} ({failed} failed) for {network}")
        except Exception as e:
            logging.error(f"[SERVER-MONITOR] notify exc: {e}")
    try:
        asyncio.run_coroutine_threadsafe(_send(), MAIN_EVENT_LOOP)
    except Exception as e:
        logging.error(f"[SERVER-MONITOR] schedule fail: {e}")

def server_monitor_worker():
    _load_server_status()
    time.sleep(20)
    logging.info(f"[SERVER-MONITOR] ▶️ started (prev: dz={_server_status.get('dz')}, oo={_server_status.get('oo')})")
    while not _stop_threads.is_set():
        try:
            dz_alive = _check_dz_server_alive()
            oo_alive = _check_oo_server_alive()
            with _server_status_lock:
                prev_dz = _server_status.get("dz", True)
                prev_oo = _server_status.get("oo", True)
                changed = False
                if prev_dz != dz_alive:
                    _server_status["dz"] = dz_alive
                    _server_status["changed_at"] = time.time()
                    changed = True
                    if not prev_dz and dz_alive:
                        logging.warning("[SERVER-MONITOR] 🟢 Djezzy BACK ONLINE → notifying users")
                        _notify_users_server_back("dz")
                    elif prev_dz and not dz_alive:
                        logging.error("[SERVER-MONITOR] 🔴 Djezzy DOWN")
                if prev_oo != oo_alive:
                    _server_status["oo"] = oo_alive
                    _server_status["changed_at"] = time.time()
                    changed = True
                    if not prev_oo and oo_alive:
                        logging.warning("[SERVER-MONITOR] 🟢 Ooredoo BACK ONLINE → notifying users")
                        _notify_users_server_back("oo")
                    elif prev_oo and not oo_alive:
                        logging.error("[SERVER-MONITOR] 🔴 Ooredoo DOWN")
                if changed:
                    _save_server_status()
            time.sleep(180)
        except Exception as e:
            logging.error(f"[SERVER-MONITOR] loop exc: {e}", exc_info=True)
            time.sleep(60)

# ==================== Robustness helpers ====================
HEALTH_FILE = BASE_DIR / "health.txt"
_WORKERS = {}
_WORKERS_LOCK = threading.Lock()

def _heartbeat_worker():
    while not _stop_threads.is_set():
        try: HEALTH_FILE.write_text(str(int(time.time())))
        except: pass
        time.sleep(60)

def _cleanup_worker():
    while not _stop_threads.is_set():
        try:
            time.sleep(600)
            now = time.time()
            stale = [u for u, s in list(user_steps.items())
                     if isinstance(s, dict) and (now - s.get("last_activity", 0)) > 3600]
            for u in stale: user_steps.pop(u, None)
            for k in list(_last_otp_sent.keys()):
                if now - _last_otp_sent[k] > 3600: _last_otp_sent.pop(k, None)
            if stale:
                logging.info(f"[CLEANUP] removed {len(stale)} stale users")
                save_steps()
        except Exception as e:
            logging.error(f"[CLEANUP] {e}")

def _worker_watchdog():
    while not _stop_threads.is_set():
        try:
            time.sleep(120)
            with _WORKERS_LOCK:
                dead = [(n, w) for n, w in _WORKERS.items()
                        if not w["thread"].is_alive() and not _stop_threads.is_set()]
                for name, info in dead:
                    logging.error(f"[WATCHDOG] ⚠️ worker '{name}' died → restarting")
                    try:
                        t = threading.Thread(target=info["fn"], daemon=True, name=name)
                        t.start()
                        info["thread"] = t
                    except Exception as e:
                        logging.error(f"[WATCHDOG] restart {name} failed: {e}")
        except: pass

def start_worker(fn):
    name = fn.__name__
    def _wrapped():
        while not _stop_threads.is_set():
            try:
                fn()
                if not _stop_threads.is_set(): time.sleep(5)
            except Exception as e:
                logging.error(f"[WORKER-{name}] ❌ {type(e).__name__}: {e}", exc_info=True)
                if not _stop_threads.is_set(): time.sleep(10)
    t = threading.Thread(target=_wrapped, daemon=True, name=name)
    t.start()
    with _WORKERS_LOCK:
        _WORKERS[name] = {"thread": t, "fn": _wrapped}
    return t

def _install_signal_handlers():
    def _shutdown(signum, frame):
        logging.warning(f"[SIGNAL] Received {signum}, graceful shutdown...")
        _stop_threads.set()
        try: save_steps()
        except: pass
    try:
        signal.signal(signal.SIGTERM, _shutdown)
        signal.signal(signal.SIGINT, _shutdown)
    except: pass

def _install_thread_excepthook():
    try:
        def _hook(args):
            logging.error(f"[THREAD-CRASH] {args.thread.name}: {args.exc_type.__name__}: {args.exc_value}")
        threading.excepthook = _hook
    except: pass

# ==================== Temporary messages ====================
async def send_temp(uid, text, ttl=30, parse_mode='HTML', reply_markup=None):
    try:
        msg = await bot.send_message(uid, text, parse_mode=parse_mode, reply_markup=reply_markup)
        asyncio.create_task(_auto_delete(msg.chat.id, msg.message_id, ttl))
        return msg
    except Exception as e:
        logging.warning(f"[TEMP] send fail uid={uid}: {e}")
        return None

async def _auto_delete(uid, msg_id, ttl):
    try:
        await asyncio.sleep(ttl)
        await bot.delete_message(uid, msg_id)
    except: pass

async def safe_delete(uid, msg_id):
    if not msg_id: return
    try: await bot.delete_message(uid, msg_id)
    except: pass

async def send_otp_prompt(uid, display, phone, resend_cb=None):
    _last_otp_sent[uid] = time.time()
    try: await bot.send_sticker(uid, PHONE_STICKER)
    except: pass
    mm = InlineKeyboardMarkup()
    if resend_cb: mm.add(InlineKeyboardButton("🔄 إعادة إرسال", callback_data=resend_cb))
    else: mm.add(InlineKeyboardButton("🔄 إعادة إرسال", callback_data=f"resend_otp_{phone}"))
    try:
        msg = await bot.send_message(
            uid,
            f"✅ <b>تم إرسال الرمز إلى</b> <code>{display}</code>\n\n"
            f"📱 <b>أدخل الرمز المكوّن من 6 أرقام:</b>\n\n"
            f"⏳ <i>إذا لم يصلك، انتظر دقيقة قبل إعادة الطلب</i>",
            reply_markup=mm, parse_mode='HTML'
        )
        asyncio.create_task(_auto_delete(uid, msg.message_id, 300))
        return msg
    except: return None

# ==================== نصوص ====================
WELCOME_HEADER = ("مرحبا بك في موح بوت 👋\n\n"
                  "بوت موح يقدم تفعيل عروض انترنت في مختلف الشبكات الجزائرية 🇩🇿\n\n"
                  "1️⃣ • أدخل الرقم 📱\n2️⃣ • أكمل الخطوات ✅\n"
                  "3️⃣ • إختر عرض مناسب 🛒\n4️⃣ • انتظار الرد ... 🔍")
WELCOME_FOOTER = "للبدء أرسل رقم هاتفك 📱"

async def send_welcome(cid):
    try:
        await bot.send_message(cid, WELCOME_HEADER)
        await bot.send_message(cid, WELCOME_FOOTER)
    except: pass

async def check_subscription(user_id):
    try:
        m = await bot.get_chat_member(REQUIRED_CHANNEL, user_id)
        return m.status not in ['left', 'kicked']
    except: return True

async def typing(cid):
    try: await bot.send_chat_action(cid, 'typing')
    except: pass

def _otp_can_resend(uid):
    last = _last_otp_sent.get(uid, 0)
    elapsed = time.time() - last
    if elapsed >= OTP_RESEND_COOLDOWN: return True, 0
    return False, int(OTP_RESEND_COOLDOWN - elapsed)

def back_btn(cb="main_menu"):
    m = InlineKeyboardMarkup()
    m.add(InlineKeyboardButton("↩️ رجوع", callback_data=cb))
    return m

async def send_result(uid, text, back_cb="main_menu"):
    try: await bot.send_sticker(uid, PHONE_STICKER)
    except: pass
    try:
        await bot.send_message(uid, text, reply_markup=back_btn(back_cb), parse_mode='HTML')
    except Exception as e:
        if "Forbidden" in str(e): logging.warning(f"[USER-BLOCKED] {uid}")

async def notify_group_success(offer_name, network):
    if not NOTIFY_GROUP: return
    text = (f"✅ <b>تفعيل ناجح</b>\n━━━━━━━━━━━━━━━━\n"
            f"🌐 <b>الشبكة:</b> {network}\n"
            f"🎁 <b>العرض:</b> {offer_name}\n"
            f"⏱️ <b>الوقت:</b> {datetime.now().strftime('%H:%M:%S')}")
    for attempt in range(3):
        try:
            await bot.send_message(NOTIFY_GROUP, text, parse_mode='HTML')
            return
        except Exception as e:
            logging.warning(f"[NOTIFY-GROUP] attempt {attempt+1}/3 fail: {e}")
            if attempt < 2:
                await asyncio.sleep(2 ** attempt)
    logging.error(f"[NOTIFY-GROUP] ❌ FAILED after 3 attempts | {offer_name}")

def subscription_markup():
    m = InlineKeyboardMarkup(row_width=1)
    m.add(InlineKeyboardButton("📢 اشترك في القناة", url=CHANNEL_LINK))
    m.add(InlineKeyboardButton("🔄 تحقق من الاشتراك", callback_data="check_sub"))
    return m

AVAILABLE_OFFERS = {
    "DOVINTSPEEDMONTH30GoPRE": {"name": "🚀 1500 دج","price": "1500 دج","validity": "30 يوم","data": "60 جيجا"},
    "DOVINTSPEEDMONTH15GoPRE": {"name": "🚀 1000 دج","price": "1000 دج","validity": "30 يوم","data": "30 جيجا"},
    "DOVINTSPEEDMONTH6GoPRE": {"name": "🚀 500 دج","price": "500 دج","validity": "30 يوم","data": "12 جيجا"},
    "DOVINTSPEEDWEEK3GoPRE": {"name": "🚀 300 دج","price": "300 دج","validity": "7 أيام","data": "10 جيجا"},
    "DOVINTSPEEDWEEK2GoPRE": {"name": "🚀 150 دج","price": "150 دج","validity": "7 أيام","data": "4 جيجا"},
    "DOVINTSPEEDDAY1GoPRE": {"name": "📱 100 Da - 2GB - 24H","price": "100 دج","validity": "24 ساعة","data": "2 جيجا"},
    "BTL10GB72H": {"name": "📱 190 دج - 10GB","price": "190 دج","validity": "72 ساعة","data": "10 جيجا"},
    "BTL500MBDAY": {"name": "📱 90 دج - 5GB","price": "90 دج","validity": "24 ساعة","data": "5 جيجا"},
    "BTLINTSPEEDDAY2Go": {"name": "📱 70 Da - 4GB - 24H","price": "70 دج","validity": "24 ساعة","data": "4 جيجا"},
}

def main_menu_markup(user_id=None):
    m = InlineKeyboardMarkup(row_width=1)
    m.add(InlineKeyboardButton("🔥 72 جيجا (أول نوفمبر)", callback_data="dz_quick_72gb"))
    m.add(InlineKeyboardButton("🎉 تفعيل 2 جيجا (أسبوعي)", callback_data="activate_2gb"))
    m.add(InlineKeyboardButton("🐷 كم هو رصيدي؟", callback_data="check_balance"))
    m.add(InlineKeyboardButton("🌐 عروض الإنترنت", callback_data="show_all_offers"))
    m.add(InlineKeyboardButton("💳 70 دج - 4GB", callback_data="quick_offer_70_4g"))
    m.add(InlineKeyboardButton("💳 90 دج - 5GB", callback_data="quick_offer_90_5g"))
    m.add(InlineKeyboardButton("💳 100 دج - 2GB", callback_data="offer_details_DOVINTSPEEDDAY1GoPRE"))
    m.add(InlineKeyboardButton("💳 190 دج - 10GB", callback_data="offer_details_BTL10GB72H"))
    m.add(InlineKeyboardButton("🔄 تغيير الرقم", callback_data="change_phone"))
    m.add(InlineKeyboardButton("🗑️ حذف الرقم المحفوظ", callback_data="delete_my_number"))
    if user_id and user_id == ADMIN_ID:
        m.add(InlineKeyboardButton("📊 إحصائيات", callback_data="bot_stats"))
        m.add(InlineKeyboardButton("📋 سجل البوت", callback_data="admin_menu"))
    return m

def all_offers_markup():
    m = InlineKeyboardMarkup(row_width=1)
    for code in list(AVAILABLE_OFFERS.keys()):
        o = AVAILABLE_OFFERS[code]
        m.add(InlineKeyboardButton(f"{o['name']} - {o['price']}", callback_data=f"offer_details_{code}"))
    m.add(InlineKeyboardButton("↩️ رجوع", callback_data="main_menu"))
    return m

def confirm_offer_markup(oc, ph):
    m = InlineKeyboardMarkup(row_width=2)
    m.add(InlineKeyboardButton("✅ تأكيد", callback_data=f"confirm_offer_{oc}_{ph}"),
          InlineKeyboardButton("❌ إلغاء", callback_data="main_menu"))
    return m

def get_stats_text():
    s = db_query("""SELECT total_2gb,total_3gb,total_offers,
                    oo_logins,oo_snap,oo_spins,oo_balance,dz_logins,
                    oo_soccer_enrolls,oo_20dzd_1go,oo_gift_plays,
                    oo_gift_won,oo_gifts_total,oo_free_2gb,oo_72gb,dz_72gb
                    FROM stats WHERE id=1""", fetch=True)
    if not s: s = (0,) * 16
    while len(s) < 16: s = s + (0,)
    users = db_query("SELECT COUNT(*) FROM users", fetch=True)[0] or 0
    dz = db_query("SELECT COUNT(*) FROM numbers", fetch=True)[0] or 0
    with _oo_proxy_lock:
        used = len(_oo_proxy_in_use)
        banned = sum(1 for h in _oo_proxy_health.values() if h.get("banned_until", 0) > time.time())
    with _server_status_lock:
        dz_st = "🟢" if _server_status.get("dz", True) else "🔴"
        oo_st = "🟢" if _server_status.get("oo", True) else "🔴"
    return (f"📊 <b>الإحصائيات</b>\n👥 {users} | 📱 {dz}\n"
            f"🔌 Proxies: {used}/{len(OO_PROXY_POOL)} | 🚫 {banned}\n"
            f"📡 Servers: DZ {dz_st} | OO {oo_st}\n\n"
            f"🔴 جيزي:\n  🔥 72G نوفمبر: {s[15]}\n  🎁 2G أسبوعي: {s[0]}\n  💰 العروض: {s[2]}\n\n"
            f"🟠 أوريدو:\n  🔐: {s[3]}  👻: {s[4]}\n"
            f"  ⚡ 20دج-1Go: {s[9]}\n  🎁 2Go FREE: {s[13]}\n  🔥 72Go: {s[14]}")

def oo_dynamic_menu(services, uid=None):
    m = InlineKeyboardMarkup(row_width=1)
    m.add(InlineKeyboardButton("🔥 72 جيجا (أول نوفمبر)", callback_data="oo_quick_72gb"))
    m.add(InlineKeyboardButton("💰 رصيدي", callback_data="oo_balance"))
    m.add(InlineKeyboardButton("📋 عروضي", callback_data="oo_my_offers"))
    m.add(InlineKeyboardButton("👻 سناب", callback_data="oo_snap"))
    m.add(InlineKeyboardButton("⚡ 20 دج — 1Go — 24H", callback_data="oo_quick_20_1g"))
    m.add(InlineKeyboardButton("🎁 2 جيجا مجاني — 24H", callback_data="oo_quick_free_2gb"))
    m.add(InlineKeyboardButton("🔄 تغيير الرقم", callback_data="oo_change"))
    m.add(InlineKeyboardButton("🗑️ حذف الرقم المحفوظ", callback_data="delete_my_number"))
    if uid and uid == ADMIN_ID:
        m.add(InlineKeyboardButton("📊 إحصائيات", callback_data="oo_stats"))
        m.add(InlineKeyboardButton("📋 سجل البوت", callback_data="admin_menu"))
    return m

def admin_menu_markup():
    m = InlineKeyboardMarkup(row_width=2)
    m.add(InlineKeyboardButton("📋 آخر 30 سطر", callback_data="admin_log"))
    m.add(InlineKeyboardButton("🎁 سجل 2Go", callback_data="admin_log_2g"))
    m.add(InlineKeyboardButton("❌ الأخطاء", callback_data="admin_log_err"))
    m.add(InlineKeyboardButton("🗑️ مسح السجل", callback_data="admin_log_clear"))
    m.add(InlineKeyboardButton("↩️ رجوع", callback_data="main_menu"))
    return m

async def _dz_request_new_otp(uid, phone):
    display = dz_mask(phone)
    ok2, remaining = _otp_can_resend(uid)
    if not ok2:
        mm = InlineKeyboardMarkup()
        mm.add(InlineKeyboardButton("🔄 إعادة إرسال", callback_data=f"resend_otp_{phone}"))
        await send_temp(uid, f"⏳ <b>انتظر {remaining} ثانية</b>", ttl=8, reply_markup=mm)
        return
    sending = await send_temp(uid, "🔄 <b>جاري إرسال رمز جديد...</b>", ttl=30)
    ok = await asyncio.to_thread(dj_request_otp, phone)
    await safe_delete(uid, sending.message_id if sending else None)
    if ok:
        otp_msg = await send_otp_prompt(uid, display, phone)
        user_steps[uid] = {"step": "dz_verify_otp", "phone": phone, "display": display,
                           "otp_msg_id": otp_msg.message_id if otp_msg else None,
                           "last_activity": time.time()}
    else:
        await send_temp(uid, f"⚠️ <b>انتهت الجلسة</b>\n📱 <code>{display}</code>", ttl=15)

async def show_dz_balance(uid, phone):
    row = db_query("SELECT token FROM numbers WHERE phone=? AND user_id=?", (phone, uid), fetch=True)
    if not row or not row[0] or row[0] == "EXPIRED":
        await _dz_request_new_otp(uid, phone); return
    result = await asyncio.to_thread(dj_check_balance, row[0], phone)
    if result.get("status") == "EXPIRED":
        db_query("UPDATE numbers SET token='EXPIRED' WHERE phone=? AND user_id=?", (phone, uid))
        await _dz_request_new_otp(uid, phone); return
    if result.get("status") == "FAILED":
        await send_temp(uid, "❌ <b>تعذر جلب الرصيد</b>", ttl=10); return
    await bot.send_message(uid,
        f"💳 <b>رصيد</b>\n📱 <code>{dz_mask(phone)}</code>\n💰 <b>{result.get('balance', 0)} دج</b>",
        reply_markup=back_btn("main_menu"), parse_mode='HTML')

async def dz_process(uid, phone, action):
    row = db_query("SELECT token FROM numbers WHERE phone=? AND user_id=?", (phone, uid), fetch=True)
    if not row or row[0] == "EXPIRED":
        await _dz_request_new_otp(uid, phone); return
    token = row[0]

    if action == "2gb":
        last = db_query("SELECT last_activation_2gb FROM numbers WHERE phone=?", (phone,), fetch=True)[0] or 0
        p = time.time() - last
        if p < COOLDOWN_2GB:
            r = int(COOLDOWN_2GB - p); d = r // 86400; h = (r % 86400) // 3600
            await send_temp(uid, f"❌ لم تكمل أسبوع\n⏱️ {d} ي {h} س", ttl=10); return
        res = await asyncio.to_thread(dj_activate_2gb, token, phone)
        if res == "SUCCESS":
            db_query("UPDATE numbers SET last_activation_2gb=? WHERE phone=?", (time.time(), phone))
            inc_stat("total_2gb"); await notify_group_success("2GB أسبوعي", "Djezzy 🔴")
            await send_result(uid,
                f"🎉 ━━━━━━━━━━━━━━━━ 🎉\n"
                f"       ✅ <b>تم التفعيل بنجاح</b>\n"
                f"🎉 ━━━━━━━━━━━━━━━━ 🎉\n\n"
                f"🎁 <b>العرض:</b> 2 جيجا أنترنت\n"
                f"📱 <b>الرقم:</b> <code>{dz_mask(phone)}</code>\n"
                f"⏱️ <b>الصلاحية:</b> أسبوع\n"
                f"💰 <b>السعر:</b> مجاناً\n\n"
                f"📞 تحقق: <code>*200#</code>\n\n📢 {CHANNEL_LINK}", "main_menu")
        elif res == "EXPIRED":
            db_query("UPDATE numbers SET token='EXPIRED' WHERE phone=?", (phone,))
            await _dz_request_new_otp(uid, phone)
        elif res == "LIMIT":
            await send_temp(uid, "⏰ <b>راك مفعّل 2 جيجا من قبل</b>", ttl=10)
        elif res == "NO_BALANCE":
            await send_temp(uid, "❌ رصيد غير كافي", ttl=10)
        elif res == "RATE_LIMIT":
            await send_temp(uid, "🚫 تجاوزت الحد", ttl=10)
        elif res == "NOT_ALLOWED":
            await send_temp(uid, "🚫 العرض غير متاح لرقمك", ttl=10)
        else:
            await send_temp(uid, f"❌ فشل ({res})", ttl=10)
        return

    elif action == "dz_72gb":
        check = dz_check_72gb_status(phone)
        if check["status"] == "ACTIVE":
            remaining = int(check["expires_in"])
            hh, mm = remaining // 3600, (remaining % 3600) // 60
            await bot.send_message(uid,
                f"⏰ ━━━━━━━━━━━━━━━━ ⏰\n"
                f"   <b>العرض مفعّل مسبقاً</b>\n"
                f"⏰ ━━━━━━━━━━━━━━━━ ⏰\n\n"
                f"📱 <code>{dz_mask(phone)}</code>\n"
                f"🎁 72 جيجا\n"
                f"⏳ متبقي: <b>{hh}س {mm}د</b>\n\n"
                f"💡 تحقق: <code>*200#</code>",
                reply_markup=back_btn("main_menu"), parse_mode='HTML')
            return
        if not _try_acquire_72gb_slot(uid):
            await send_temp(uid, "⏳ <b>محاولة جارية من طرف آخر...</b>", ttl=5); return
        try:
            loading = await bot.send_message(uid,
                "⚡ ━━━━━━━━━━━━━━━━ ⚡\n"
                "  <b>جاري التفعيل الفوري</b>\n"
                "⚡ ━━━━━━━━━━━━━━━━ ⚡\n\n"
                "🔍 فحص التفعيل السابق...\n"
                "📡 محاولة التفعيل...\n\n"
                "<i>لا تغلق البوت</i>",
                parse_mode='HTML')
            res = "FAILED"
            for attempt in range(2):
                res = await asyncio.to_thread(_acquire_and_activate_72gb, token, phone)
                if res in ("SUCCESS", "LIMIT", "EXPIRED", "NO_BALANCE", "NOT_ELIGIBLE"):
                    break
                if attempt == 0:
                    try:
                        await bot.edit_message_text(
                            "⚡ ━━━━━━━━━━━━━━━━ ⚡\n"
                            "   <b>محاولة ثانية...</b>\n"
                            "⚡ ━━━━━━━━━━━━━━━━ ⚡\n\n"
                            "🔄 تدوير البروكسي\n📡 إعادة المحاولة...",
                            chat_id=uid, message_id=loading.message_id, parse_mode='HTML')
                    except: pass
                    _rotate_proxy_session(force=True)
                    await asyncio.sleep(2)
            await safe_delete(uid, loading.message_id)
            if res == "SUCCESS":
                inc_stat("dz_72gb"); await notify_group_success("72 جيجا (Scan & Win)", "Djezzy 🔴")
                await send_result(uid,
                    f"🎉 ━━━━━━━━━━━━━━━━ 🎉\n"
                    f"       ✅ <b>تم التفعيل بنجاح</b>\n"
                    f"🎉 ━━━━━━━━━━━━━━━━ 🎉\n\n"
                    f"🎁 <b>العرض:</b> 72 جيجا أنترنت\n"
                    f"📱 <b>الرقم:</b> <code>{dz_mask(phone)}</code>\n"
                    f"⏱️ <b>الصلاحية:</b> 3 أيام\n"
                    f"💰 <b>السعر:</b> مجاناً (عرض نوفمبر)\n\n"
                    f"📞 تحقق: <code>*200#</code>\n\n📢 {CHANNEL_LINK}", "main_menu")
            elif res == "LIMIT":
                await bot.send_message(uid,
                    f"⏰ ━━━━━━━━━━━━━━━━ ⏰\n"
                    f"  <b>العرض مفعّل من قبل</b>\n"
                    f"⏰ ━━━━━━━━━━━━━━━━ ⏰\n\n"
                    f"📱 <code>{dz_mask(phone)}</code>\n"
                    f"🎁 72 جيجا نشط حالياً\n\n"
                    f"💡 <code>*200#</code> للتأكد",
                    reply_markup=back_btn("main_menu"), parse_mode='HTML')
            elif res == "NOT_ELIGIBLE":
                await bot.send_message(uid,
                    f"🚫 ━━━━━━━━━━━━━━━━ 🚫\n"
                    f"  <b>الرقم غير مؤهل للعرض</b>\n"
                    f"🚫 ━━━━━━━━━━━━━━━━ 🚫\n\n"
                    f"📱 <code>{dz_mask(phone)}</code>\n\n"
                    f"📞 تحقق: <code>*200#</code>",
                    reply_markup=back_btn("main_menu"), parse_mode='HTML')
            elif res == "EXPIRED":
                db_query("UPDATE numbers SET token='EXPIRED' WHERE phone=?", (phone,))
                await _dz_request_new_otp(uid, phone)
            elif res == "NO_BALANCE":
                await send_temp(uid, "❌ <b>رصيد غير كافي</b>", ttl=10)
            else:
                kb = InlineKeyboardMarkup(row_width=2)
                kb.add(InlineKeyboardButton("🔄 إعادة المحاولة", callback_data="dz_quick_72gb"),
                       InlineKeyboardButton("↩️ رجوع", callback_data="main_menu"))
                await bot.send_message(uid,
                    f"❌ ━━━━━━━━━━━━━━━━ ❌\n"
                    f"      <b>تعذّر التفعيل الآن</b>\n"
                    f"❌ ━━━━━━━━━━━━━━━━ ❌\n\n"
                    f"📱 <code>{dz_mask(phone)}</code>\n"
                    f"💡 اضغط «إعادة المحاولة» بعد 10 ثواني",
                    reply_markup=kb, parse_mode='HTML')
        finally:
            _release_72gb_slot(uid)
        return

async def send_dz_menu(uid, phone=None):
    if not phone:
        nums = db_query("SELECT phone FROM numbers WHERE user_id=? ORDER BY added_date DESC LIMIT 1", (uid,), fetchall=True)
        if nums and nums[0]: phone = nums[0][0]
    txt = f"📱 <code>{dz_mask(phone)}</code> ✅\n🔴 <b>جيزي</b>\n\nاختر العرض 🔽" if phone else "🔴 اختر العرض 🔽"
    try:
        await bot.send_message(uid, txt, reply_markup=main_menu_markup(uid), parse_mode='HTML')
    except Exception as e:
        if "Forbidden" in str(e): logging.warning(f"[USER-BLOCKED] {uid}")

async def send_oo_menu(uid, user):
    ms = user["msisdn"]; at = user["access_token"]
    qd = oo_quick_detect(at)
    services = {"rate_plan": qd.get("rate_plan") or "", "is_yooz": qd.get("is_yooz", False),
                "is_dima": qd.get("is_dima", False), "balance_value": 0, "gift_count": 0}
    rp = services.get("rate_plan") or ""
    lines = [f"📱 <code>{o_mask(ms)}</code> ✅"]
    if rp: lines.append(f"📦 {rp}")
    lines.append("💰 <b>...</b>\n\nاختر الخدمة 🔽")
    try:
        msg = await bot.send_message(uid, "\n".join(lines), reply_markup=oo_dynamic_menu(services, uid), parse_mode='HTML')
        asyncio.create_task(_update_oo_menu_bg(uid, user, msg.message_id))
    except Exception as e:
        if "Forbidden" in str(e): logging.warning(f"[USER-BLOCKED] {uid}")

async def _update_oo_menu_bg(uid, user, msg_id):
    try:
        ms = user["msisdn"]; at = user["access_token"]
        meta = {k: user.get(k, "") for k in ["tok_instance_id","tok_plat_sig","tok_fingerprint","tok_timestamp"]}
        bal_r = await asyncio.to_thread(oo_check_balance, ms, at, meta, uid)
        bal = 0
        if bal_r.get("status") == "ok":
            try: bal = float(bal_r.get("data", {}).get("accountBalance", 0) or 0)
            except: pass
        rp = (oo_quick_detect(at).get("rate_plan") or "")
        lines = [f"📱 <code>{o_mask(ms)}</code> ✅"]
        if rp: lines.append(f"📦 {rp}")
        lines.append(f"💰 <b>{bal} دج</b>\n\nاختر الخدمة 🔽")
        svc = {"rate_plan": rp, "is_yooz": oo_quick_detect(at).get("is_yooz", False),
               "is_dima": oo_quick_detect(at).get("is_dima", False), "balance_value": bal, "gift_count": 0}
        await bot.edit_message_text("\n".join(lines), chat_id=uid, message_id=msg_id,
                                    reply_markup=oo_dynamic_menu(svc, uid), parse_mode='HTML')
    except: pass

def _oo_72gb_background_worker(uid, msisdn, at, meta):
    try:
        logging.info(f"[OO-72GB-BG] ▶️ START uid={uid} msisdn={msisdn}")
        result = oo_activate_ramadan_72gb(msisdn, at, meta, uid)
        status = result.get("status", "error")
        logging.info(f"[OO-72GB-BG] ✅ DONE uid={uid} status={status}")
    except Exception as e:
        logging.error(f"[OO-72GB-BG] 💥 crash uid={uid}: {e}", exc_info=True)
        status = "error"

    with _oo_72gb_jobs_lock:
        _oo_72gb_jobs.pop(uid, None)

    if not MAIN_EVENT_LOOP: return

    async def _notify():
        try:
            if status == "ok":
                inc_stat("oo_72gb")
                _mark_oo_proxy_success(uid)
                await notify_group_success("72 جيجا (نوفمبر)", "Ooredoo 🟠")
                await send_result(uid,
                    f"🎉 ━━━━━━━━━━━━━━━━ 🎉\n"
                    f"      ✅ <b>تم التفعيل بنجاح</b>\n"
                    f"🎉 ━━━━━━━━━━━━━━━━ 🎉\n\n"
                    f"🎁 <b>العرض:</b> 72 جيجا\n"
                    f"📱 <b>الرقم:</b> <code>{o_mask(msisdn)}</code>\n"
                    f"💰 <b>السعر:</b> مجاناً (عرض نوفمبر)\n\n"
                    f"📞 تحقق: <code>*200#</code>\n\n📢 {CHANNEL_LINK}",
                    "oo_back_menu")
            elif status == "already":
                await send_temp(uid,
                    "⏰ <b>راك مفعّل 72 جيجا من قبل</b>\n\n"
                    f"📱 <code>{o_mask(msisdn)}</code>\n\n"
                    "💡 تحقق: <code>*200#</code>", ttl=15)
            elif status == "unauthorized":
                mm = InlineKeyboardMarkup()
                mm.add(InlineKeyboardButton("🔄 إعادة الدخول", callback_data="oo_change"))
                await send_temp(uid, "🔐 <b>انتهت الجلسة</b>", ttl=12, reply_markup=mm)
            elif status == "not_allowed":
                await send_temp(uid, "🚫 <b>العرض غير متاح لرقمك</b>", ttl=10)
            else:
                kb = InlineKeyboardMarkup(row_width=2)
                kb.add(InlineKeyboardButton("🔄 إعادة المحاولة", callback_data="oo_quick_72gb"),
                       InlineKeyboardButton("↩️ رجوع", callback_data="oo_back_menu"))
                await bot.send_message(uid,
                    f"❌ ━━━━━━━━━━━━━━━━ ❌\n"
                    f"    <b>تعذّر التفعيل</b>\n"
                    f"❌ ━━━━━━━━━━━━━━━━ ❌\n\n"
                    f"📱 <code>{o_mask(msisdn)}</code>\n"
                    f"⚠️ السيرفر مزدحم\n\n"
                    f"💡 اضغط «إعادة المحاولة» لاحقاً",
                    reply_markup=kb, parse_mode='HTML')
        except Exception as e:
            logging.error(f"[OO-72GB-BG] notify fail uid={uid}: {e}")

    try:
        asyncio.run_coroutine_threadsafe(_notify(), MAIN_EVENT_LOOP)
    except Exception as e:
        logging.error(f"[OO-72GB-BG] schedule notify fail: {e}")
# ==================== Admin Logs ====================
@bot.message_handler(commands=['log'], chat_types=['private'])
async def cmd_log(message):
    if message.from_user.id != ADMIN_ID: return
    args = message.text.split(); n = 30
    if len(args) > 1:
        try: n = min(int(args[1]), 100)
        except: pass
    lines = get_logs(n)
    if not lines: await bot.send_message(message.chat.id, "📭 فارغ"); return
    await bot.send_message(message.chat.id, format_logs_for_telegram(lines, f"آخر {len(lines)}"), parse_mode='HTML')

@bot.message_handler(commands=['log2g'], chat_types=['private'])
async def cmd_log2g(message):
    if message.from_user.id != ADMIN_ID: return
    lines = get_logs(50, "OO-FREE-2GB")
    if not lines: await bot.send_message(message.chat.id, "📭 فارغ"); return
    await bot.send_message(message.chat.id, format_logs_for_telegram(lines, "سجل 2Go"), parse_mode='HTML')

@bot.message_handler(commands=['logerr'], chat_types=['private'])
async def cmd_logerr(message):
    if message.from_user.id != ADMIN_ID: return
    with _LOG_LOCK: all_lines = list(_LOG_BUFFER)
    lines = [l for l in all_lines if 'ERROR' in l or 'WARNING' in l or '❌' in l][-50:]
    if not lines: await bot.send_message(message.chat.id, "✅ لا أخطاء"); return
    await bot.send_message(message.chat.id, format_logs_for_telegram(lines, "الأخطاء"), parse_mode='HTML')

@bot.message_handler(commands=['clearlog'], chat_types=['private'])
async def cmd_clearlog(message):
    if message.from_user.id != ADMIN_ID: return
    with _LOG_LOCK: _LOG_BUFFER.clear()
    await bot.send_message(message.chat.id, "🗑️ تم المسح")

@bot.message_handler(commands=['admin'], chat_types=['private'])
async def cmd_admin(message):
    if message.from_user.id != ADMIN_ID: return
    await bot.send_message(message.chat.id, "🛠️ <b>لوحة الأدمن</b>", reply_markup=admin_menu_markup(), parse_mode='HTML')

# ==================== Start ====================
_last_heartbeat = [time.time()]

@bot.message_handler(commands=['start'], chat_types=['private'])
async def cmd_start(message):
    _last_heartbeat[0] = time.time()
    uid = message.from_user.id
    now = time.time()
    await typing(message.chat.id)
    if not await check_subscription(uid):
        await bot.reply_to(message, "🔒 اشترك:", reply_markup=subscription_markup()); return
    oo_user = oo_load(uid)
    dz_row = db_query("SELECT token FROM numbers WHERE user_id=? LIMIT 1", (uid,), fetch=True)
    last_activity = user_steps.get(uid, {}).get("last_activity", 0)
    elapsed = now - last_activity if last_activity else 99999
    if elapsed < INACTIVITY_SECONDS:
        if oo_user and oo_user.get("access_token"):
            user_steps[uid] = {"step": "oo_menu", "last_activity": now}
            await send_oo_menu(uid, oo_user); return
        if dz_row and dz_row[0] and dz_row[0] != "EXPIRED":
            user_steps[uid] = {"step": "dz_menu", "last_activity": now}
            await send_dz_menu(uid); return
    user_steps[uid] = {"step": "await_phone", "last_activity": now}
    await send_welcome(message.chat.id)

# ==================== Callback ====================
@bot.callback_query_handler(func=lambda call: (
    call.message and call.message.chat and call.message.chat.type == 'private'))
async def cb_handler(call):
    _last_heartbeat[0] = time.time()
    try: await _cb_inner(call)
    except Exception as e:
        logging.error(f"[CB-CRASH] {call.from_user.id}: {e}", exc_info=True)
        try: await bot.answer_callback_query(call.id, "⚠️ خطأ")
        except: pass

async def _cb_inner(call):
    uid = call.from_user.id

    if call.data.startswith("resend_otp_"):
        target = call.data.replace("resend_otp_", "")
        await safe_delete(call.message.chat.id, call.message.message_id)
        await typing(uid)
        ok, remaining = _otp_can_resend(uid)
        if not ok:
            mm = InlineKeyboardMarkup()
            mm.add(InlineKeyboardButton("🔄 إعادة", callback_data=f"resend_otp_{target}"))
            await send_temp(uid, f"⏳ <b>{remaining} ثانية</b>", ttl=8, reply_markup=mm); return
        if target.startswith("2135"):
            oo_clear(uid)
            digits = "0" + target[3:]
            sending = await send_temp(uid,
                "🔄 <b>جاري إرسال الرمز...</b>\n\n"
                "📡 السيرفر ثقيل — قد يستغرق حتى 30 ثانية", ttl=180)
            result = await asyncio.to_thread(ooredoo_send_otp_sync, target, uid)
            await safe_delete(uid, sending.message_id if sending else None)
            if not result.get("otp_sent"):
                await send_temp(uid, "❌ <b>تعذر الإرسال</b>", ttl=10); return
            otp_msg = await send_otp_prompt(uid, digits, target)
            user_steps[uid] = {"step": "oo_await_otp", "msisdn": target,
                               "device": result["device"],
                               "otp_msg_id": otp_msg.message_id if otp_msg else None,
                               "last_activity": time.time()}
        else:
            db_query("UPDATE numbers SET token=NULL WHERE phone=? AND user_id=?", (target, uid))
            dz_clear_session(uid)
            sending = await send_temp(uid, "🔄 <b>جاري إرسال الرمز...</b>", ttl=30)
            ok2 = await asyncio.to_thread(dj_request_otp, target)
            await safe_delete(uid, sending.message_id if sending else None)
            if ok2:
                display = "0" + target[3:]
                otp_msg = await send_otp_prompt(uid, display, target)
                user_steps[uid] = {"step": "dz_verify_otp", "phone": target, "display": display,
                                   "otp_msg_id": otp_msg.message_id if otp_msg else None,
                                   "last_activity": time.time()}
            else:
                await send_temp(uid, "❌ <b>تعذر الإرسال</b>\n\n💡 جرّب بعد دقيقة", ttl=10)
        return

    if call.data != "check_sub" and not await check_subscription(uid):
        await safe_delete(call.message.chat.id, call.message.message_id)
        await bot.send_message(uid, "🔒 اشترك:", reply_markup=subscription_markup()); return

    await safe_delete(call.message.chat.id, call.message.message_id)
    await typing(uid)
    if uid in user_steps and isinstance(user_steps[uid], dict):
        user_steps[uid]["last_activity"] = time.time()

    if call.data == "admin_menu":
        if uid != ADMIN_ID: return
        await bot.send_message(uid, "🛠️ <b>لوحة الأدمن</b>", reply_markup=admin_menu_markup(), parse_mode='HTML'); return
    if call.data == "admin_log":
        if uid != ADMIN_ID: return
        lines = get_logs(30)
        await bot.send_message(uid, format_logs_for_telegram(lines, f"آخر {len(lines)}") if lines else "📭", parse_mode='HTML'); return
    if call.data == "admin_log_2g":
        if uid != ADMIN_ID: return
        lines = get_logs(50, "OO-FREE-2GB")
        await bot.send_message(uid, format_logs_for_telegram(lines, "سجل 2Go") if lines else "📭", parse_mode='HTML'); return
    if call.data == "admin_log_err":
        if uid != ADMIN_ID: return
        with _LOG_LOCK: all_lines = list(_LOG_BUFFER)
        lines = [l for l in all_lines if 'ERROR' in l or 'WARNING' in l or '❌' in l][-50:]
        await bot.send_message(uid, format_logs_for_telegram(lines, "الأخطاء") if lines else "✅", parse_mode='HTML'); return
    if call.data == "admin_log_clear":
        if uid != ADMIN_ID: return
        with _LOG_LOCK: _LOG_BUFFER.clear()
        await bot.send_message(uid, "🗑️ تم المسح"); return

    if call.data == "check_sub":
        if await check_subscription(uid): await cmd_start(call.message)
        else: await bot.send_message(uid, "❌ لم تشترك!", reply_markup=subscription_markup())
        return

    if call.data == "delete_my_number":
        user = oo_load(uid)
        dz_row = db_query("SELECT phone FROM numbers WHERE user_id=? LIMIT 1", (uid,), fetch=True)
        saved = []
        if dz_row: saved.append(f"🔴 <code>{dz_mask(dz_row[0])}</code>")
        if user and user.get("msisdn"): saved.append(f"🟠 <code>{o_mask(user['msisdn'])}</code>")
        if not saved:
            await send_temp(uid, "📭 ما عندكش رقم", ttl=8); return
        kb = InlineKeyboardMarkup(row_width=1)
        kb.add(InlineKeyboardButton("✅ تأكيد الحذف", callback_data="delete_my_number_ok"))
        kb.add(InlineKeyboardButton("❌ إلغاء", callback_data="main_menu"))
        await bot.send_message(uid, "🗑️ <b>حذف الرقم</b>\n" + "\n".join(saved), reply_markup=kb, parse_mode='HTML')
        return

    if call.data == "delete_my_number_ok":
        db_query("DELETE FROM numbers WHERE user_id=?", (uid,))
        oo_clear(uid); dz_clear_session(uid); oo_free2gb_clear(uid)
        _release_oo_proxy(uid, "deleted")
        user_steps[uid] = {"step": "await_phone", "last_activity": time.time()}
        await send_temp(uid, "✅ <b>تم الحذف</b>", ttl=5); return

    if call.data == "change_phone":
        oo_clear(uid); dz_clear_session(uid); oo_free2gb_clear(uid)
        _release_oo_proxy(uid, "change")
        user_steps[uid] = {"step": "await_phone", "last_activity": time.time()}
        await send_welcome(uid); return

    if call.data.startswith("oo_"):
        await oo_cb_handler(call); return

    if call.data == "dz_quick_72gb":
        nums = db_query("SELECT phone FROM numbers WHERE user_id=? ORDER BY added_date DESC LIMIT 1", (uid,), fetchall=True)
        if not nums:
            await send_temp(uid, "⚠️ أضف رقماً أولاً.", ttl=8); return
        await dz_process(uid, nums[0][0], "dz_72gb"); return

    if call.data == "quick_offer_70_4g":
        nums = db_query("SELECT phone FROM numbers WHERE user_id=? ORDER BY added_date DESC LIMIT 1", (uid,), fetchall=True)
        if not nums: await send_temp(uid, "⚠️ أضف رقماً.", ttl=8); return
        ph = nums[0][0]
        row = db_query("SELECT token FROM numbers WHERE phone=? AND user_id=?", (ph, uid), fetch=True)
        if not row or row[0] == "EXPIRED": await _dz_request_new_otp(uid, ph); return
        bal = await asyncio.to_thread(dj_check_balance, row[0], ph)
        if bal.get("status") == "EXPIRED":
            db_query("UPDATE numbers SET token='EXPIRED' WHERE phone=?", (ph,))
            await _dz_request_new_otp(uid, ph); return
        if bal.get("balance", 0) < 70:
            await send_temp(uid, f"❌ رصيد {bal.get('balance', 0)}", ttl=8); return
        result = await dz_activate_offer_70_4g_async(row[0], ph)
        if result.get("token_expired"):
            db_query("UPDATE numbers SET token='EXPIRED' WHERE phone=?", (ph,))
            await _dz_request_new_otp(uid, ph); return
        if result.get("success"):
            inc_stat("total_offers"); await notify_group_success("70دج — 4GB", "Djezzy 🔴")
            await bot.send_message(uid, result["msg"], parse_mode='HTML', reply_markup=main_menu_markup(uid))
        else:
            await bot.send_message(uid, result["msg"], parse_mode='HTML', reply_markup=back_btn("main_menu"))
        return

    if call.data == "quick_offer_90_5g":
        nums = db_query("SELECT phone FROM numbers WHERE user_id=? ORDER BY added_date DESC LIMIT 1", (uid,), fetchall=True)
        if not nums: await send_temp(uid, "⚠️ أضف رقماً.", ttl=8); return
        ph = nums[0][0]
        row = db_query("SELECT token FROM numbers WHERE phone=? AND user_id=?", (ph, uid), fetch=True)
        if not row or row[0] == "EXPIRED": await _dz_request_new_otp(uid, ph); return
        bal = await asyncio.to_thread(dj_check_balance, row[0], ph)
        if bal.get("status") == "EXPIRED":
            db_query("UPDATE numbers SET token='EXPIRED' WHERE phone=?", (ph,))
            await _dz_request_new_otp(uid, ph); return
        if bal.get("balance", 0) < 90:
            await send_temp(uid, "❌ رصيد", ttl=8); return
        result = await dz_activate_offer_90_5g_async(row[0], ph)
        if result.get("token_expired"):
            db_query("UPDATE numbers SET token='EXPIRED' WHERE phone=?", (ph,))
            await _dz_request_new_otp(uid, ph); return
        if result.get("success"):
            inc_stat("total_offers"); await notify_group_success("90دج — 5GB", "Djezzy 🔴")
            await bot.send_message(uid, result["msg"], parse_mode='HTML', reply_markup=main_menu_markup(uid))
        else:
            await bot.send_message(uid, result["msg"], parse_mode='HTML', reply_markup=back_btn("main_menu"))
        return

    if call.data == "check_balance":
        nums = db_query("SELECT phone FROM numbers WHERE user_id=?", (uid,), fetchall=True)
        if not nums: await send_temp(uid, "⚠️ أضف رقماً.", ttl=8); return
        phones = [n[0] for n in nums]
        if len(phones) == 1: await show_dz_balance(uid, phones[0])
        else:
            m = InlineKeyboardMarkup(row_width=1)
            for p in phones: m.add(InlineKeyboardButton(f"📱 {dz_mask(p)}", callback_data=f"balance_phone_{p}"))
            m.add(InlineKeyboardButton("↩️ رجوع", callback_data="main_menu"))
            await bot.send_message(uid, "📱 اختر:", reply_markup=m)
        return

    if call.data.startswith("balance_phone_"):
        await show_dz_balance(uid, call.data.replace("balance_phone_", "")); return

    if call.data == "activate_2gb":
        nums = db_query("SELECT phone FROM numbers WHERE user_id=? ORDER BY added_date DESC LIMIT 1", (uid,), fetchall=True)
        if not nums: await send_temp(uid, "⚠️ أضف رقماً.", ttl=8); return
        await dz_process(uid, nums[0][0], "2gb"); return

    if call.data == "show_all_offers":
        await bot.send_message(uid, "💰:", reply_markup=all_offers_markup()); return

    if call.data.startswith("offer_details_"):
        code = call.data.replace("offer_details_", "")
        o = AVAILABLE_OFFERS.get(code, {})
        nums = db_query("SELECT phone FROM numbers WHERE user_id=? ORDER BY added_date DESC LIMIT 1", (uid,), fetchall=True)
        if not nums: await send_temp(uid, "⚠️ أضف رقماً.", ttl=8); return
        ph = nums[0][0]
        d = f"💰 <b>{o.get('name')}</b>\n📦 {o.get('data')}\n⏱️ {o.get('validity')}\n💳 <b>{o.get('price')}</b>"
        await bot.send_message(uid, f"{d}\n\n📱 <code>{dz_mask(ph)}</code>\n\nتأكيد؟",
                               reply_markup=confirm_offer_markup(code, ph), parse_mode='HTML')
        return

    if call.data.startswith("confirm_offer_"):
        rest = call.data.replace("confirm_offer_", "")
        parts = rest.rsplit("_", 1)
        if len(parts) == 2:
            code, ph = parts
            row = db_query("SELECT token FROM numbers WHERE phone=? AND user_id=?", (ph, uid), fetch=True)
            if not row or row[0] == "EXPIRED": await _dz_request_new_otp(uid, ph); return
            o = AVAILABLE_OFFERS.get(code, {"name": "العرض", "price": "?"})
            price = dj_extract_price(o.get('price', '0')) or 0
            bal = await asyncio.to_thread(dj_check_balance, row[0], ph)
            if bal.get("status") == "EXPIRED":
                db_query("UPDATE numbers SET token='EXPIRED' WHERE phone=?", (ph,))
                await _dz_request_new_otp(uid, ph); return
            cur = bal.get("balance", 0)
            if price > 0 and cur < price:
                await send_temp(uid, f"❌ رصيد {cur} < {price}", ttl=8); return
            kb = InlineKeyboardMarkup(row_width=2)
            kb.add(InlineKeyboardButton("✅ تأكيد", callback_data=f"dzconfirm_offer_{code}_{ph}"),
                   InlineKeyboardButton("❌ إلغاء", callback_data="main_menu"))
            await bot.send_message(uid, f"💰 <b>{cur} دج</b> → <b>{o['name']}</b>\n💳 {price} دج\n\nتأكيد؟",
                                   reply_markup=kb, parse_mode='HTML')
        return

    if call.data.startswith("dzconfirm_offer_"):
        rest = call.data.replace("dzconfirm_offer_", "")
        code, ph = rest.rsplit("_", 1)
        row = db_query("SELECT token FROM numbers WHERE phone=? AND user_id=?", (ph, uid), fetch=True)
        if not row or row[0] == "EXPIRED": await _dz_request_new_otp(uid, ph); return
        o = AVAILABLE_OFFERS.get(code, {"name": "العرض", "price": "?"})
        price = dj_extract_price(o.get('price', '0')) or 0
        offer_type = "shake" if code.startswith("BTL") else "activate"
        result = await dz_activate_paid_offer_async(row[0], ph, code, offer_type, o.get('name', 'العرض'), price)
        if result.get("token_expired"):
            db_query("UPDATE numbers SET token='EXPIRED' WHERE phone=?", (ph,))
            await _dz_request_new_otp(uid, ph); return
        if result.get("success"):
            inc_stat("total_offers"); await notify_group_success(o.get('name', 'العرض'), "Djezzy 🔴")
            await bot.send_message(uid, result["msg"], parse_mode='HTML', reply_markup=main_menu_markup(uid))
        else:
            await bot.send_message(uid, result["msg"], parse_mode='HTML', reply_markup=back_btn("main_menu"))
        return

    if call.data == "bot_stats":
        if uid != ADMIN_ID: return
        await bot.send_message(uid, get_stats_text(), reply_markup=back_btn("main_menu"), parse_mode='HTML'); return

    if call.data in ("main_menu", "back_main"):
        await send_dz_menu(uid); return

# ==================== OO Callbacks ====================
async def oo_cb_handler(call):
    uid = call.from_user.id; data = call.data
    user = oo_load(uid)

    if data == "oo_change":
        oo_clear(uid); dz_clear_session(uid); oo_free2gb_clear(uid)
        _release_oo_proxy(uid, "change")
        user_steps[uid] = {"step": "await_phone", "last_activity": time.time()}
        await send_welcome(uid); return
    if data == "oo_back_menu":
        if user: await send_oo_menu(uid, user); return
        user_steps[uid] = {"step": "await_phone", "last_activity": time.time()}
        await send_welcome(uid); return
    if data == "oo_stats":
        if uid != ADMIN_ID: return
        await bot.send_message(uid, get_stats_text(), reply_markup=back_btn("oo_back_menu"), parse_mode='HTML'); return
    if not user or not user.get("access_token"):
        user_steps[uid] = {"step": "await_phone", "last_activity": time.time()}
        await send_welcome(uid); return
    user = await asyncio.to_thread(oo_ensure_valid, uid, user)
    if not user:
        mm = InlineKeyboardMarkup()
        mm.add(InlineKeyboardButton("🔄 إرسال رمز", callback_data="oo_change"))
        await send_temp(uid, "⚠️ <b>انتهت الجلسة</b>", ttl=10, reply_markup=mm); return
    ms = user["msisdn"]; at = user["access_token"]
    meta = {k: user.get(k, "") for k in ["tok_instance_id","tok_plat_sig","tok_fingerprint","tok_timestamp"]}

    if data == "oo_balance":
        inc_stat("oo_balance")
        r = await asyncio.to_thread(oo_check_balance, ms, at, meta, uid)
        if r.get("status") != "ok": await send_temp(uid, "❌", ttl=8); return
        b = r.get("data", {}).get("accountBalance", "?")
        await bot.send_message(uid, f"💰 <b>{b} دج</b>\n📱 <code>{o_mask(ms)}</code>",
                               reply_markup=back_btn("oo_back_menu"), parse_mode='HTML'); return

    if data == "oo_my_offers":
        inc_stat("oo_offers_view")
        r = await asyncio.to_thread(oo_get_active, ms, at, meta, uid)
        if r["status"] != "ok":
            await send_temp(uid, "❌", ttl=8); return
        await bot.send_message(uid, "📋 <b>عروضك</b>\n📭 لا باقات نشطة",
                               reply_markup=back_btn("oo_back_menu"), parse_mode='HTML')
        return

    if data == "oo_snap":
        r = await asyncio.to_thread(oo_activate_snapchat, ms, at, meta, uid)
        if r == "ok":
            inc_stat("oo_snap"); _mark_oo_proxy_success(uid)
            await notify_group_success("Snapchat", "Ooredoo 🟠")
            await send_result(uid, f"✅ <b>سناب مفعّل!</b>\n📱 <code>{o_mask(ms)}</code>", "oo_back_menu")
        elif r == "already_active":
            await send_temp(uid, "⚠️ مفعّلة مسبقاً", ttl=8)
        else:
            await send_temp(uid, "❌", ttl=8)
        return

    if data == "oo_quick_free_2gb":
        last = oo_free2gb_get_last(uid, ms)
        elapsed = time.time() - last if last else 0
        if last and elapsed < COOLDOWN_FREE_2GB_OO:
            remaining = int(COOLDOWN_FREE_2GB_OO - elapsed)
            hh = remaining // 3600; mmn = (remaining % 3600) // 60
            await send_temp(uid, f"⏰ <b>راك مفعّل</b>\n⏳ {hh} س {mmn} د", ttl=10); return
        await send_temp(uid, "⏳ <b>جاري التفعيل...</b>", ttl=30)
        r = await asyncio.to_thread(oo_purchase_free_2gb, ms, at, meta, uid)
        status = r.get("status", "error")
        if status == "ok":
            inc_stat("oo_free_2gb"); oo_free2gb_save(uid, ms); _mark_oo_proxy_success(uid)
            await notify_group_success("2Go مجاني", "Ooredoo 🟠")
            await send_result(uid, f"🎉 <b>مبروك!</b>\n✅ 2 جيجا\n📱 <code>{o_mask(ms)}</code>\n💡 <code>*200#</code>", "oo_back_menu")
            return
        if status == "already":
            oo_free2gb_save(uid, ms); await send_temp(uid, "⏰ <b>راك مفعّل من قبل</b>", ttl=10); return
        if status == "unauthorized":
            mm = InlineKeyboardMarkup()
            mm.add(InlineKeyboardButton("🔄 إعادة الدخول", callback_data="oo_change"))
            await send_temp(uid, "🔐 <b>انتهت الجلسة</b>", ttl=10, reply_markup=mm); return
        await send_temp(uid, "❌ <b>فشل</b>", ttl=10); return

    if data == "oo_quick_72gb":
        with _oo_72gb_jobs_lock:
            if uid in _oo_72gb_jobs:
                await send_temp(uid,
                    "⏳ <b>لديك محاولة جارية في الخلفية</b>\n\n"
                    f"📱 <code>{o_mask(ms)}</code>\n\n"
                    "📬 سيصلك إشعار عند الانتهاء", ttl=10)
                return
            _oo_72gb_jobs[uid] = {"msisdn": ms, "started_at": time.time()}

        await bot.send_message(uid,
            "⚡ ━━━━━━━━━━━━━━━━ ⚡\n"
            "  <b>جاري التفعيل في الخلفية</b>\n"
            "⚡ ━━━━━━━━━━━━━━━━ ⚡\n\n"
            f"📱 <code>{o_mask(ms)}</code>\n\n"
            "🔄 سنحاول باستمرار حتى النجاح\n"
            "📬 سيصلك إشعار هنا عند الانتهاء\n\n"
            "<i>يمكنك استخدام البوت بشكل طبيعي الآن</i>",
            parse_mode='HTML')

        threading.Thread(
            target=_oo_72gb_background_worker,
            args=(uid, ms, at, meta),
            daemon=True, name=f"oo72gb-{uid}",
        ).start()
        return

    if data == "oo_quick_20_1g":
        r = await asyncio.to_thread(oo_check_balance, ms, at, meta, uid)
        try: balance = float(r.get("data", {}).get("accountBalance", 0) or 0)
        except: balance = 0
        if balance < 20:
            await send_temp(uid, f"❌ رصيد {balance}", ttl=8); return
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(InlineKeyboardButton("✅ تأكيد", callback_data="oo_quick_20_1g_ok"),
               InlineKeyboardButton("❌ إلغاء", callback_data="oo_back_menu"))
        await bot.send_message(uid, f"⚡ <b>20دج — 1Go — 24H</b>\n💰 {balance} دج",
                               reply_markup=kb, parse_mode='HTML')
        return

    if data == "oo_quick_20_1g_ok":
        r = await asyncio.to_thread(oo_purchase_20dzd_1go, ms, at, meta, uid)
        status = r.get("status", "error")
        if status == "ok":
            inc_stat("oo_20dzd_1go"); _mark_oo_proxy_success(uid)
            await notify_group_success("20دج — 1Go", "Ooredoo 🟠")
            await send_result(uid, f"✅ <b>تم</b> 🎉\n📱 <code>{o_mask(ms)}</code>", "oo_back_menu")
            return
        await send_temp(uid, f"❌ فشل\n💡 {status}", ttl=10); return

# ==================== Text ====================
@bot.message_handler(func=lambda m: True, content_types=['text'], chat_types=['private'])
async def handle_text(message):
    _last_heartbeat[0] = time.time()
    try:
        await _text_inner(message)
    except Exception as e:
        logging.error(f"[TEXT-CRASH] {message.from_user.id}: {e}", exc_info=True)
        try:
            await bot.send_message(message.chat.id, "⚠️ خطأ مؤقت")
        except: pass

async def _text_inner(message):
    uid = message.from_user.id
    text = message.text.strip()
    if not await check_subscription(uid):
        await cmd_start(message); return
    now = time.time()
    cur_step = user_steps.get(uid, {}).get("step", "")
    last_activity = user_steps.get(uid, {}).get("last_activity", 0)
    if cur_step in ("dz_menu", "oo_menu") and last_activity and (now - last_activity) > INACTIVITY_SECONDS:
        user_steps[uid] = {"step": "await_phone", "last_activity": now}
        await send_welcome(uid); return
    digits = re.sub(r"\D", "", text)
    is_phone = re.match(r"^0[567]\d{8}$", digits) is not None
    if is_phone and cur_step not in ("oo_await_otp", "dz_verify_otp"):
        user_steps[uid] = {"step": "await_phone", "last_activity": now}
    step = user_steps.get(uid)
    if not step:
        user_steps[uid] = {"step": "await_phone", "last_activity": now}
        await send_welcome(uid); return

    if step.get("step") == "await_phone":
        if not is_phone:
            await send_temp(uid, "❌ رقم غير صحيح", ttl=8); return
        msisdn = "213" + digits[1:]

        if digits.startswith(("07", "06")):
            row = db_query("SELECT token FROM numbers WHERE phone=? AND user_id=?", (msisdn, uid), fetch=True)
            if row and row[0] and row[0] != "EXPIRED":
                user_steps[uid] = {"step": "dz_menu", "last_activity": now}
                await send_dz_menu(uid, msisdn); return
            sending = await send_temp(uid, "🔄 <b>جاري إرسال الرمز...</b>\n\n<i>يرجى الانتظار قليلاً</i>", ttl=30)
            ok = await asyncio.to_thread(dj_request_otp, msisdn)
            await safe_delete(uid, sending.message_id if sending else None)
            if ok:
                otp_msg = await send_otp_prompt(uid, digits, msisdn)
                user_steps[uid] = {"step": "dz_verify_otp", "phone": msisdn, "display": digits,
                                   "otp_msg_id": otp_msg.message_id if otp_msg else None,
                                   "last_activity": now}
            else:
                await send_temp(uid, "❌ <b>تعذر إرسال الرمز</b>\n\n💡 انتظر دقيقة ثم حاول مجدداً", ttl=15)
            return

        if digits.startswith("05"):
            existing = oo_load(uid)
            if existing and existing.get("msisdn") == msisdn and existing.get("access_token"):
                user_steps[uid] = {"step": "oo_menu", "last_activity": now}
                await send_oo_menu(uid, existing); return
            sending = await send_temp(uid,
                "🔄 <b>جاري إرسال الرمز...</b>\n\n"
                "📡 السيرفر ثقيل — قد يستغرق حتى 30 ثانية\n"
                "⏳ لا تغلق البوت", ttl=180)
            result = await asyncio.to_thread(ooredoo_send_otp_sync, msisdn, uid)
            await safe_delete(uid, sending.message_id if sending else None)
            if not result.get("otp_sent"):
                reason = result.get("reason", "")
                if reason == "rate_limit":
                    await send_temp(uid, "⏳ <b>تجاوزت الحد</b>\n\n💡 حاول بعد 5 دقائق", ttl=15)
                elif reason == "overall_timeout":
                    await send_temp(uid, "⏱️ <b>انتهت مدة المحاولات</b>\n\n💡 حاول مجدداً", ttl=15)
                else:
                    await send_temp(uid, "❌ <b>تعذر الإرسال</b>\n\n💡 جرّب بعد دقيقة", ttl=15)
                return
            otp_msg = await send_otp_prompt(uid, digits, msisdn)
            user_steps[uid] = {"step": "oo_await_otp", "msisdn": msisdn, "device": result["device"],
                               "otp_msg_id": otp_msg.message_id if otp_msg else None,
                               "last_activity": now}
            return

    if step.get("step") == "oo_await_otp":
        m = re.search(r"\b(\d{6})\b", text)
        if not m:
            await send_temp(uid, "⚠️ <b>أدخل 6 أرقام فقط</b>", ttl=5); return
        otp = m.group(1)
        ms = step.get("msisdn"); device = step.get("device", {})
        await safe_delete(uid, step.get("otp_msg_id"))
        try: await bot.delete_message(uid, message.message_id)
        except: pass
        verifying = await send_temp(uid, "🔍 <b>جاري التحقق...</b>", ttl=30)
        result = await asyncio.to_thread(ooredoo_verify_otp_sync, ms, otp, device, uid)
        await safe_delete(uid, verifying.message_id if verifying else None)
        if result == "wrong_otp":
            await send_temp(uid, "❌ <b>الرمز خاطئ</b>\n\n💡 أعد الإرسال", ttl=8); return
        if not result:
            await send_temp(uid, "❌ <b>فشل التحقق</b>\n\n💡 حاول مجدداً", ttl=8); return
        user = {"msisdn": ms, "device": device, **result}
        oo_save(uid, user); inc_stat("oo_logins")
        await send_temp(uid, "✅ <b>تم التأكيد بنجاح</b>\n\n🎉 مرحباً بك", ttl=3)
        user_steps[uid] = {"step": "oo_menu", "last_activity": time.time()}
        await asyncio.sleep(1)
        await send_oo_menu(uid, user)
        return

    if step.get("step") == "dz_verify_otp":
        if not text.isdigit() or len(text) != 6:
            await send_temp(uid, "⚠️ <b>أدخل 6 أرقام فقط</b>", ttl=5); return
        phone = step.get("phone")
        await safe_delete(uid, step.get("otp_msg_id"))
        try: await bot.delete_message(uid, message.message_id)
        except: pass
        verifying = await send_temp(uid, "🔍 <b>جاري التحقق...</b>", ttl=30)
        token = await asyncio.to_thread(dj_verify_otp, phone, text)
        await safe_delete(uid, verifying.message_id if verifying else None)
        if token and token != "EXPIRED":
            db_query("INSERT OR REPLACE INTO numbers (phone,user_id,token,added_date) VALUES (?,?,?,?)",
                     (phone, uid, token, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            dz_save_session(uid, phone, token); inc_stat("dz_logins")
            await send_temp(uid, "✅ <b>تم التأكيد بنجاح</b>\n\n🎉 مرحباً بك في موح بوت", ttl=3)
            user_steps[uid] = {"step": "dz_menu", "last_activity": time.time()}
            await asyncio.sleep(1)
            await send_dz_menu(uid, phone)
        else:
            await send_temp(uid, "❌ <b>الرمز خاطئ</b>\n\n💡 اضغط /start لإعادة المحاولة", ttl=8)
        return

    oo_user = oo_load(uid)
    if oo_user and oo_user.get("access_token"):
        user_steps[uid] = {"step": "oo_menu", "last_activity": now}
        await send_oo_menu(uid, oo_user); return
    if db_query("SELECT token FROM numbers WHERE user_id=? LIMIT 1", (uid,), fetch=True):
        user_steps[uid] = {"step": "dz_menu", "last_activity": now}
        await send_dz_menu(uid); return
    user_steps[uid] = {"step": "await_phone", "last_activity": now}
    await send_welcome(uid)

# ==================== Main ====================
def _install_global_handlers():
    try:
        loop = asyncio.get_running_loop()
        def _ex_handler(_loop, context):
            exc = context.get("exception")
            if exc:
                logging.error(f"[GLOBAL-LOOP-ERR] {type(exc).__name__}: {exc}")
            else:
                logging.error(f"[GLOBAL-LOOP-ERR] {context.get('message')}")
        loop.set_exception_handler(_ex_handler)
    except Exception as e:
        logging.error(f"[GLOBAL-HANDLERS] {e}")

async def _run_polling_once():
    try:
        await bot.remove_webhook()
    except Exception as e:
        logging.warning(f"[POLL] remove_webhook: {e}")
    logging.warning("[POLL] ▶️ infinity_polling starting...")
    await bot.infinity_polling(skip_pending=True, timeout=30)
    logging.warning("[POLL] ⚠️ returned unexpectedly")

async def _polling_supervisor():
    RESTART_TIMEOUT = 60 * 60
    STUCK_THRESHOLD = 60 * 15
    while not _stop_threads.is_set():
        _last_heartbeat[0] = time.time()
        task = asyncio.create_task(_run_polling_once())
        started = time.time()
        try:
            while not task.done() and not _stop_threads.is_set():
                await asyncio.sleep(30)
                now = time.time()
                if now - started > RESTART_TIMEOUT:
                    logging.warning(f"[SUPERVISOR] ⏰ restart (hourly)")
                    break
                if now - _last_heartbeat[0] > STUCK_THRESHOLD:
                    try:
                        await asyncio.wait_for(bot.get_me(), timeout=15)
                        _last_heartbeat[0] = time.time()
                    except Exception as e:
                        logging.error(f"[SUPERVISOR] ❌ API dead ({e})")
                        break
            if not task.done():
                task.cancel()
                try:
                    await asyncio.wait_for(task, timeout=10)
                except: pass
        except asyncio.CancelledError:
            task.cancel(); raise
        except Exception as e:
            logging.error(f"[SUPERVISOR] {type(e).__name__}: {e}", exc_info=True)
            task.cancel()
            try: await task
            except: pass
        if not _stop_threads.is_set():
            await asyncio.sleep(3)

async def main():
    global MAIN_EVENT_LOOP
    MAIN_EVENT_LOOP = asyncio.get_running_loop()
    print("=" * 60)
    print("🤖 البوت v6.8.4 — 2GB Free + Server Monitor + OTP fix + JWT device-id fix")
    print(f"👤 ADMIN: {ADMIN_ID}")
    print("=" * 60)
    _install_global_handlers()
    _install_signal_handlers()
    _install_thread_excepthook()
    user_steps.update(load_steps_saved())

    for fn in (oo_auto_refresh, dz_auto_refresh, steps_saver_worker,
               reset_steps_worker, _proxy_proactive_rotate, oo_proxy_cleaner,
               server_monitor_worker,
               _heartbeat_worker, _cleanup_worker, _worker_watchdog):
        start_worker(fn)

    print("✅ البوت يعمل...")
    while not _stop_threads.is_set():
        try:
            await _polling_supervisor()
        except Exception as e:
            logging.error(f"[MAIN] {type(e).__name__}: {e}", exc_info=True)
        if not _stop_threads.is_set():
            await asyncio.sleep(5)

def _run_forever():
    backoff = 5
    while True:
        try:
            asyncio.run(main())
            backoff = 5
        except KeyboardInterrupt:
            logging.warning("[RUN] Ctrl+C")
            _stop_threads.set()
            try: save_steps()
            except: pass
            break
        except Exception as e:
            logging.error(f"[RUN] ❌ {type(e).__name__}: {e}", exc_info=True)
            try: save_steps()
            except: pass
        logging.warning(f"[RUN] restarting in {backoff}s...")
        time.sleep(backoff)
        backoff = min(backoff * 2, 300)

if __name__ == "__main__":
    _run_forever()
