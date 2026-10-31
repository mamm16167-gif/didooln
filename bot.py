#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""البوت الموحّد v3 — Robust + Oxylabs + 72GB Auto"""
import telebot
from telebot.async_telebot import AsyncTeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio, sqlite3, requests, random, time, re, json, os, uuid, base64, threading, logging, urllib3, hashlib, string
from datetime import datetime, timedelta, timezone as tz
from pathlib import Path
from collections import deque
import html as _html

# ==================== 🎨 الأزرار الملوّنة ====================
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

OO_BFF = "https://apis.ooredoo.dz/api/ooredoo-bff"
OO_AUTH = "https://apis.ooredoo.dz/api/auth/realms/myooredoo/protocol/openid-connect/token"
OO_CLIENT = "myooredoo-app"
X_VERSION = "1.5.15"
X_VERSION_OTP = "1.5.16"
X_SIG = "5c7641dbb82cf11066df68afc91541c967640106a95192740b43d51a5ce6777a"
NOTIFY_GROUP = "@ifoekdjdh"

# ==================== نظام البروكسي (Oxylabs Residential) ====================
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

# ==================== 📋 Log Ring Buffer ====================
_LOG_BUFFER = deque(maxlen=500)
_LOG_LOCK = threading.Lock()

class _RingBufferHandler(logging.Handler):
    def emit(self, record):
        try:
            msg = self.format(record)
            with _LOG_LOCK:
                _LOG_BUFFER.append(msg)
        except: pass

_ring_handler = _RingBufferHandler()
_ring_handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s', datefmt='%H:%M:%S'))
_ring_handler.setLevel(logging.INFO)
logging.getLogger().addHandler(_ring_handler)

def get_logs(n=30, filter_kw=None):
    with _LOG_LOCK:
        lines = list(_LOG_BUFFER)
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

# ==================== Sessions ====================
def _new_session(headers=None, use_proxy=True):
    s = requests.Session()
    a = requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=20, max_retries=1, pool_block=False)
    s.mount('http://', a); s.mount('https://', a)
    s.verify = False
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

def _oo_req(method, url, headers, content=b"", timeout=20, use_proxy=True):
    data = content if isinstance(content, bytes) else content.encode()
    if use_proxy and _should_use_proxy():
        for proxy_attempt in range(2):
            try:
                s = _new_session(use_proxy=True)
                r = s.request(method, url, headers=headers, data=data, timeout=timeout, allow_redirects=False)
                head = r.text[:200].lstrip().lower()
                if head.startswith(("<!doctype", "<html")):
                    try: r.close()
                    except: pass
                    _mark_proxy_failed()
                    continue
                try: body = r.json()
                except: body = {"_raw": r.text[:500]}
                _mark_proxy_success()
                try: r.close()
                except: pass
                return r.status_code, dict(r.headers), body
            except Exception as e:
                logging.warning(f"[OO-REQ] proxy #{proxy_attempt+1} {method} {url[:50]}: {str(e)[:80]}")
                _rotate_proxy_session()
                if proxy_attempt == 0: time.sleep(0.3)
    try:
        s = _new_session(use_proxy=False)
        r = s.request(method, url, headers=headers, data=data, timeout=timeout, allow_redirects=False)
        try: body = r.json()
        except: body = {"_raw": r.text[:500]}
        try: r.close()
        except: pass
        return r.status_code, dict(r.headers), body
    except Exception as e:
        logging.error(f"[OO-REQ-ERR] {method} {url[:60]}: {str(e)[:100]}")
        return 0, {}, {"_error": str(e)[:100]}

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
        if isinstance(msg, dict): return msg.get("ar") or msg.get("en") or msg.get("fr") or ""
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
    needed = {'user_id': 'INTEGER', 'token': 'TEXT',
              'last_activation_2gb': 'REAL DEFAULT 0',
              'last_activation_3gb': 'REAL DEFAULT 0',
              'last_activation_offers': 'REAL DEFAULT 0', 'added_date': 'TEXT'}
    existing_nums = [r[1] for r in c.execute("PRAGMA table_info(numbers)").fetchall()]
    for col, col_type in needed.items():
        if col not in existing_nums:
            try: c.execute(f"ALTER TABLE numbers ADD COLUMN {col} {col_type}")
            except: pass
    c.execute('''CREATE TABLE IF NOT EXISTS stats (id INTEGER PRIMARY KEY)''')
    if c.execute("SELECT COUNT(*) FROM stats WHERE id = 1").fetchone()[0] == 0:
        c.execute("INSERT INTO stats (id) VALUES (1)")
    all_cols = ["total_2gb","total_3gb","total_offers","oo_logins","oo_snap","oo_spins",
                "oo_balance","oo_offers_view","dz_logins","oo_soccer_enrolls","oo_20dzd_1go",
                "oo_gift_plays","oo_gift_won","oo_gifts_total","oo_free_2gb","oo_bundles", "oo_72gb"]
    existing = [r[1] for r in c.execute("PRAGMA table_info(stats)").fetchall()]
    for col in all_cols:
        if col not in existing:
            try: c.execute(f"ALTER TABLE stats ADD COLUMN {col} INTEGER DEFAULT 0")
            except: pass
    conn.commit(); conn.close()

init_db()

def db_query(q, p=(), fetch=False, fetchall=False):
    for attempt in range(3):
        try:
            conn = sqlite3.connect(DB_PATH, timeout=15, check_same_thread=False)
            c = conn.cursor(); c.execute(q, p)
            r = None
            if fetch: r = c.fetchone()
            elif fetchall: r = c.fetchall()
            else: conn.commit()
            conn.close(); return r
        except sqlite3.OperationalError as e:
            logging.error(f"DB try {attempt+1}: {e}"); time.sleep(0.2 * (attempt + 1))
        except Exception as e:
            logging.error(f"DB: {e}"); return None
    return None

def inc_stat(field):
    try: db_query(f"UPDATE stats SET {field} = COALESCE({field}, 0) + 1 WHERE id = 1")
    except: pass

def save_steps():
    try:
        clean = {}
        for k, v in list(user_steps.items()):
            if isinstance(v, dict):
                clean[str(k)] = {kk: vv for kk, vv in v.items()
                                 if kk in ("step","phone","msisdn","display","last_activity")}
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
        if r is None: time.sleep(0.5); continue
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
        if attempt > 0:
            time.sleep(OTP_VERIFY_MIN_WAIT)
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
    endpoints = [
        f"{DJ_BASE}/api/v1/services/shake/{phone}",
        f"{DJ_BASE}/api/v1/services/walk/activate-reward/{phone}",
        f"{DJ_BASE}/api/v1/subscribers/activate-product/{phone}",
    ]
    last_code = 0
    for url in endpoints:
        r = _dz_req("POST", url, headers=h,
                    json_body={"packageCode": "GIFTWALKWIN2GO"}, timeout=20)
        if r is None: continue
        last_code = r.status_code
        if r.status_code == 401: return "EXPIRED"
        if r.status_code in (200, 201):
            try: body = r.text.lower()
            except: body = ""
            if "already" in body: return "LIMIT"
            return "SUCCESS"
        if r.status_code == 402: return "NO_BALANCE"
        if r.status_code == 429: return "RATE_LIMIT"
        time.sleep(0.3)
    if last_code == 403: return "NOT_ALLOWED"
    return "FAILED"

async def dz_activate_paid_offer_async(token, phone, package_code, offer_type, offer_name, price):
    h = DZ_HEADERS.copy(); h['Authorization'] = f"Bearer {token}"
    async def _try_post(url, label):
        r = await safe_request('POST', url, json={"packageCode": package_code}, headers=h, timeout=12)
        if r['status'] == 401: return {"success": False, "token_expired": True, "msg": "⚠️ انتهت جلستك اعد إرسال رقمك"}
        if r['status'] in [200, 201, 202]:
            return {"success": True, "token_expired": False, "msg": f"✅ ━━━ تم التفعيل بنجاح ━━━\n\n🎉 {offer_name}\n💰 السعر: {price} د.ج\n\n{PAGE_FOLLOW_TEXT}"}
        if r['status'] == 402:
            return {"success": False, "token_expired": False, "msg": f"❌ رصيدك غير كافي لتفعيل {offer_name}\n💰 المطلوب: {price} د.ج"}
        srv = dz_extract_msg(r['json']); code = r.get('status', '?')
        info = srv if srv else f"كود: {code}"
        return {"success": False, "token_expired": False, "msg": f"⚠️ تعذر تفعيل {offer_name}\n\nℹ️ {info}"}
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
        if r.get('status') == 401: return {"success": False, "token_expired": True, "msg": "⚠️ انتهت جلستك"}
        if r.get('status') in [200, 201, 202]:
            return {"success": True, "token_expired": False, "msg": f"✅ ━━━ تم التفعيل بنجاح ━━━\n\n🟢 عرض: 4 جيجابايت\n💰 السعر: 70 د.ج\n⏱️ الصلاحية: 24 ساعة\n\n{PAGE_FOLLOW_TEXT}"}
        if r.get('status') == 402: return {"success": False, "token_expired": False, "msg": "❌ رصيدك غير كافٍ"}
        srv = dz_extract_msg(r.get('json'))
        _st = r.get('status', '?')
        _info = srv if srv else f"كود: {_st}"
        return {"success": False, "token_expired": False, "msg": f"⚠️ تعذر التفعيل\nℹ️ {_info}"}
    shake_url = f"{DZ_BASE_URL}/api/v1/services/shake/{phone}"
    for _ in range(3):
        res_get = await safe_request('GET', shake_url, headers=h, timeout=8)
        if res_get.get('status') == 401: return {"success": False, "token_expired": True, "msg": "⚠️ انتهت جلستك"}
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
        if r.get('status') == 401: return {"success": False, "token_expired": True, "msg": "⚠️ انتهت جلستك"}
        if r.get('status') in [200, 201, 202]:
            return {"success": True, "token_expired": False, "msg": f"✅ ━━━ تم التفعيل بنجاح ━━━\n\n🟣 عرض: 5 جيجابايت\n💰 السعر: 90 د.ج\n⏱️ الصلاحية: 24 ساعة\n\n{PAGE_FOLLOW_TEXT}"}
        if r.get('status') == 402: return {"success": False, "token_expired": False, "msg": "❌ رصيدك غير كافٍ"}
        srv = dz_extract_msg(r.get('json'))
        _st = r.get('status', '?')
        _info = srv if srv else f"كود: {_st}"
        return {"success": False, "token_expired": False, "msg": f"⚠️ تعذر التفعيل\nℹ️ {_info}"}
    shake_url = f"{DZ_BASE_URL}/api/v1/services/shake/{phone}"
    for _ in range(3):
        res_get = await safe_request('GET', shake_url, headers=h, timeout=8)
        if res_get.get('status') == 401: return {"success": False, "token_expired": True, "msg": "⚠️ انتهت جلستك"}
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
    try:
        p = at.split("."); pad = len(p[1]) % 4
        return json.loads(base64.b64decode(p[1] + "="*(4-pad) if pad else p[1])).get("device-id")
    except: return None
def _mps(at):
    d = _exdid(at) or _iid()
    return base64.b64encode(json.dumps({"platform":"android","is-physical-device":True,
                                        "device-id":d},separators=(",",":")).encode()).decode()

def oo_quick_detect(at):
    rp = ""; is_yooz = False; is_dima = False
    try:
        p = at.split("."); pad = len(p[1]) % 4
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

def ooredoo_send_otp_sync(msisdn):
    ts = _now_ms(); iid_val = _iid(); psig = _pld(iid_val); fp = _fp()
    device = {"instance_id": iid_val, "plat_sig": psig, "fp": fp}
    nonce, chronos = "", ""
    try:
        h3 = _base_hdrs(msisdn, iid_val, psig, _corr(), ts, fp=fp)
        h3["x-version"] = X_VERSION_OTP
        h3.update({"content-type": "application/json; charset=utf-8",
                   "x-native-integrity-token": INTEGRITY_1,
                   "x-path": "/api/auth/realms/myooredoo/protocol/openid-connect/token",
                   "x-method": "POST"})
        _, rh3, _ = _oo_req("POST", f"{OO_BFF}/checkpoint/token", h3, b"{}", timeout=20)
        nonce = rh3.get("x-nonce-id") or rh3.get("X-Nonce-Id") or ""
        chronos = rh3.get("x-chronos-id") or rh3.get("X-Chronos-Id") or ""
    except: pass
    try:
        h4 = {"User-Agent":"Dart/3.11 (dart:io)","Accept-Encoding":"gzip","x-msisdn":msisdn,
              "x-device-fingerprint":fp,"x-platform-origin":"mobile-android",
              "platform":"android","x-version":X_VERSION_OTP,"x-signature":X_SIG,
              "x-timestamp":ts,"x-platform-info":psig,"x-force-update":"true",
              "x-instance-id":iid_val,"content-type":"application/x-www-form-urlencoded"}
        if nonce: h4["x-nonce-id"] = nonce
        if chronos: h4["x-chronos-id"] = chronos
        body = f"client_id={OO_CLIENT}&grant_type=password&username={msisdn}"
        c4, _, _ = _oo_req("POST", OO_AUTH, h4, body, timeout=30)
        if c4 == 429: return {"device": device, "otp_sent": False, "status": 429, "reason": "rate_limit"}
        if c4 == 0: return {"device": device, "otp_sent": False, "status": 0, "reason": "network"}
        return {"device": device, "otp_sent": True, "status": c4}
    except Exception as e:
        return {"device": device, "otp_sent": False, "status": -1, "reason": "exception"}

def ooredoo_verify_otp_sync(msisdn, otp, device):
    iid_val = device.get("instance_id") or _iid()
    psig = device.get("plat_sig") or _pld(iid_val)
    fp_otp = device.get("fp") or _fp()

    def _one_attempt():
        ts = _now_ms()
        nonce, chronos = "", ""
        try:
            h6 = _base_hdrs(msisdn, iid_val, psig, _corr(), ts, fp=fp_otp)
            h6["x-version"] = X_VERSION_OTP
            h6.update({"content-type":"application/json; charset=utf-8",
                       "x-native-integrity-token":INTEGRITY_2,
                       "x-path":"/api/auth/realms/myooredoo/protocol/openid-connect/token","x-method":"POST"})
            _, rh6, _ = _oo_req("POST", f"{OO_BFF}/checkpoint/token", h6, b"{}", timeout=15)
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
        c7, _, j7 = _oo_req("POST", OO_AUTH, h7, body, timeout=30)
        return c7, j7

    last_status = 0
    for attempt in range(OTP_VERIFY_MAX_RETRY):
        if attempt > 0:
            time.sleep(OTP_VERIFY_MIN_WAIT)
        try:
            c7, j7 = _one_attempt()
            last_status = c7
            if c7 == 200 and isinstance(j7, dict) and "access_token" in j7:
                at = j7["access_token"]
                return {"access_token": at, "refresh_token": j7.get("refresh_token",""),
                        "expires_in": j7.get("expires_in", 0), "tok_fingerprint": fp_otp,
                        "tok_instance_id": _exdid(at) or iid_val, "tok_plat_sig": _mps(at),
                        "tok_timestamp": _now_ms(), "issued_at": int(time.time())}
            if c7 == 429:
                return None
        except Exception as e:
            continue
    if last_status in (400, 401, 403):
        return "wrong_otp"
    return None

def ooredoo_refresh_token_sync(msisdn, rt, device):
    iid_val = device.get("instance_id") or _iid(); psig = device.get("plat_sig") or _pld(iid_val)
    fp_otp = device.get("fp") or _fp(); ts = _now_ms()
    h = _base_hdrs(msisdn, iid_val, psig, _corr(), ts, fp=fp_otp)
    h.update({"content-type":"application/x-www-form-urlencoded",
              "x-native-integrity-token":INTEGRITY_1,
              "x-path":"/api/auth/realms/myooredoo/protocol/openid-connect/token","x-method":"POST"})
    _, rh, _ = _oo_req("POST", f"{OO_BFF}/checkpoint/token", h, b"{}", timeout=15)
    nonce = rh.get("x-nonce-id") or rh.get("X-Nonce-Id") or ""
    chronos = rh.get("x-chronos-id") or rh.get("X-Chronos-Id") or ""
    if not nonce or not chronos: return None
    h2 = {"User-Agent":"Dart/3.11 (dart:io)","Accept-Encoding":"gzip","x-msisdn":msisdn,
          "x-device-fingerprint":fp_otp,"x-nonce-id":nonce,"x-platform-origin":"mobile-android",
          "platform":"android","x-version":X_VERSION,"x-signature":X_SIG,"x-chronos-id":chronos,
          "x-timestamp":ts,"x-platform-info":psig,"x-force-update":"true","x-instance-id":iid_val,
          "content-type":"application/x-www-form-urlencoded"}
    body = f"client_id={OO_CLIENT}&grant_type=refresh_token&refresh_token={rt}"
    c2, _, j2 = _oo_req("POST", OO_AUTH, h2, body, timeout=30)
    if c2 == 200 and "access_token" in j2:
        at = j2["access_token"]
        return {"access_token": at, "refresh_token": j2.get("refresh_token", rt),
                "expires_in": j2.get("expires_in", 0),
                "tok_instance_id": _exdid(at) or iid_val, "tok_plat_sig": _mps(at),
                "tok_fingerprint": fp_otp, "tok_timestamp": _now_ms(), "issued_at": int(time.time())}
    return None

def oo_check_balance(msisdn, at, meta):
    h = _web_hdrs(msisdn, at, meta)
    c, _, resp = _oo_req("GET", f"{OO_BFF}/subscriptions/getAccountInfo", h, timeout=20)
    if c == 200: return {"status": "ok", "data": resp if isinstance(resp, dict) else {}}
    if c == 401: return {"status": "unauthorized"}
    return {"status": "error", "code": c}

def oo_get_active(msisdn, at, meta):
    h = _web_hdrs(msisdn, at, meta)
    c, _, resp = _oo_req("GET", f"{OO_BFF}/bundle/getActivePackages?msisdn={msisdn}", h, timeout=20)
    if c == 200: return {"status": "ok", "data": resp if isinstance(resp, dict) else {}}
    if c == 401: return {"status": "unauthorized"}
    return {"status": "error", "code": c}

def oo_activate_snapchat(msisdn, at, meta):
    h = _web_hdrs(msisdn, at, meta)
    c, _, _ = _oo_req("POST", f"{OO_BFF}/snap-chat/apply", h, timeout=20)
    if c == 200: return "ok"
    if c == 500: return "already_active"
    if c == 401: return "unauthorized"
    return "error"

def oo_purchase_20dzd_1go(msisdn, at, meta):
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
    def _do(method, url, h, data=b"", t=20):
        try:
            s = _new_session(use_proxy=True)
            d = data if isinstance(data, bytes) else (data.encode() if isinstance(data, str) else data)
            r = s.request(method, url, headers=h, data=d, timeout=t, allow_redirects=False)
            try: b = r.json()
            except: b = {"_raw": r.text[:500]}
            return r.status_code, dict(r.headers), b
        except Exception as e:
            return 0, {}, {"_error": str(e)[:100]}
    try: _do("GET", f"{OO_BFF}/subscriptions/getAccountInfo", _web_hdrs(msisdn, at, meta), b"", 12)
    except: pass
    c = 0; resp = {}
    for label, h in [("mobile v1.5.16", _mobile_hdrs("1.5.16")),
                     ("mobile v1.5.15", _mobile_hdrs("1.5.15"))]:
        c, _, resp = _do("POST", f"{OO_BFF}/cvm/bundlePurchase", h, body, 30)
        if c in (200, 201): return {"status": "ok", "data": resp}
        if c in (402, 409): break
    if c in (402, 409):
        srv_code = str(resp.get("code") or "").upper() if isinstance(resp, dict) else ""
        if any(k in srv_code for k in ("CREDIT", "BALANCE", "NOT_ENOUGH")): return {"status": "no_balance"}
        if "ALREADY" in srv_code: return {"status": "already"}
        if any(k in srv_code for k in ("NOT_AVAILABLE", "NOT_ALLOWED")): return {"status": "not_allowed"}
        return {"status": "no_balance"}
    if c == 401: return {"status": "purchase_blocked"}
    return {"status": "error", "code": c}

# ==================== 🎁 72GB Gamification ====================
def oo_check_72gb_status(msisdn, at, meta):
    h = _web_hdrs(msisdn, at, meta)
    h["x-version"] = "1.5.17"
    url = f"{OO_BFF}/gamification/status"
    c, _, resp = _oo_req("GET", url, h, timeout=15)
    if c == 200 and isinstance(resp, dict):
        return {"status": "ok", "data": resp}
    if c == 401: 
        return {"status": "unauthorized"}
    return {"status": "error", "code": c}

def oo_claim_72gb(msisdn, at, meta):
    h = _web_hdrs(msisdn, at, meta, "application/json; charset=utf-8")
    h["x-version"] = "1.5.17"
    endpoints = [
        f"{OO_BFF}/gamification/play",
        f"{OO_BFF}/gamification/claim",
        f"{OO_BFF}/gamification/reward",
        f"{OO_BFF}/gamification/play-and-win"
    ]
    body = json.dumps({})
    for url in endpoints:
        c, _, resp = _oo_req("POST", url, h, body, timeout=15)
        if c in (200, 201):
            return {"status": "ok", "data": resp, "endpoint": url}
    return {"status": "error"}

def oo_purchase_free_2gb(msisdn, at, meta):
    body_simple = json.dumps({"bundleCode": "BTL_24H_DATA_Free_2Go"}, separators=(",", ":"))
    body_full = json.dumps({"bundleCode": "BTL_24H_DATA_Free_2Go",
                            "validity": "day", "validityAmount": "1"}, separators=(",", ":"))
    endpoints = [
        ("bundlePurchase", f"{OO_BFF}/cvm/bundlePurchase"),
        ("dynamic-bundle", f"{OO_BFF}/cvm/dynamic-bundle-purchase"),
    ]
    bodies = [("simple", body_simple), ("full", body_full)]
    def _try(url, body, label):
        try:
            h = _web_hdrs(msisdn, at, meta, "application/json; charset=utf-8")
            c, _, resp = _oo_req("POST", url, h, body, timeout=30, use_proxy=True)
            return c, resp
        except Exception as e:
            return 0, {"_error": str(e)[:100]}
    already_seen = None
    for round_idx in range(2):
        if round_idx > 0:
            time.sleep(2)
        for ep_label, url in endpoints:
            for body_label, body in bodies:
                c, resp = _try(url, body, f"r{round_idx+1}|{ep_label}|{body_label}")
                if c in (200, 201):
                    return {"status": "ok", "data": resp}
                resp_str = str(resp).lower()
                if any(k in resp_str for k in ("already", "déjà", "purchased", "subscribed", "duplicate", "exist")):
                    already_seen = resp
                    continue
                if c == 401:
                    return {"status": "unauthorized", "data": resp}
                if c == 429:
                    time.sleep(3)
                    break
    if already_seen is not None:
        return {"status": "already", "data": already_seen}
    return {"status": "error", "data": None}

# ==================== Sessions ====================
def oo_save(uid, d): (SESSIONS_DIR / f"oo_{uid}.json").write_text(json.dumps(d, ensure_ascii=False))
def oo_load(uid):
    f = SESSIONS_DIR / f"oo_{uid}.json"
    return json.loads(f.read_text()) if f.exists() else None
def oo_clear(uid):
    f = SESSIONS_DIR / f"oo_{uid}.json"
    if f.exists(): f.unlink()

def dz_save_session(uid, phone, token):
    try: (SESSIONS_DIR / f"dz_{uid}.json").write_text(json.dumps({"phone": phone, "token": token, "issued_at": time.time()}, ensure_ascii=False))
    except: pass
def dz_load_session(uid):
    try:
        f = SESSIONS_DIR / f"dz_{uid}.json"
        return json.loads(f.read_text()) if f.exists() else None
    except: return None
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
        if d.get("msisdn") == msisdn:
            return d.get("last", 0)
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
def dz_mask(m): return "0" + m[3:] if m.startswith("213") else m

def oo_ensure_valid(uid, user):
    if not user or not user.get("access_token"): return None
    issued = user.get("issued_at", 0); exp = user.get("expires_in", 0)
    if issued and exp and (time.time() - issued) < (exp - 1800): return user
    ref = ooredoo_refresh_token_sync(user["msisdn"], user.get("refresh_token",""),
        {"instance_id": user.get("tok_instance_id"), "plat_sig": user.get("tok_plat_sig"),
         "fp": user.get("tok_fingerprint")})
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
                    s = dz_load_session(int(uid_s))
                    if not s: continue
                    st = dj_check_balance(s["token"], s["phone"])
                    if isinstance(st, dict) and st.get("status") == "EXPIRED": dz_clear_session(int(uid_s))
                except: pass
        except: pass

def steps_saver_worker():
    while not _stop_threads.is_set():
        try: time.sleep(30); save_steps()
        except: pass

def reset_steps_worker():
    while not _stop_threads.is_set():
        try:
            time.sleep(4 * 3600)
            for uid in list(user_steps.keys()):
                user_steps[uid] = {"step": "await_phone", "last_activity": time.time()}
            cutoff = time.time() - 3600
            for k in list(_last_otp_sent.keys()):
                if _last_otp_sent[k] < cutoff:
                    _last_otp_sent.pop(k, None)
            save_steps()
        except: pass

def _proxy_proactive_rotate():
    while not _stop_threads.is_set():
        try:
            time.sleep(25 * 60)
            _rotate_proxy_session(force=True)
        except: pass

def oo_auto_claim_72gb_worker():
    while not _stop_threads.is_set():
        try:
            time.sleep(300)
            for f in list(SESSIONS_DIR.glob("oo_*.json")):
                try:
                    uid_s = f.stem.replace("oo_", "")
                    if not uid_s.isdigit(): continue
                    uid = int(uid_s)
                    u = oo_load(uid)
                    if not u or not u.get("access_token"): continue
                    ms = u["msisdn"]; at = u["access_token"]
                    meta = {k: u.get(k, "") for k in ["tok_instance_id","tok_plat_sig","tok_fingerprint","tok_timestamp"]}
                    
                    r = oo_check_72gb_status(ms, at, meta)
                    if r.get("status") == "ok":
                        d = r.get("data", {})
                        played = d.get("played", True)
                        enable = d.get("gameUIEnable", False)
                        if enable and not played:
                            logging.info(f"[AUTO-72GB] Trying to claim for {ms}...")
                            claim = oo_claim_72gb(ms, at, meta)
                            if claim.get("status") == "ok":
                                inc_stat("oo_72gb")
                                logging.info(f"[AUTO-72GB] SUCCESS for {ms} via {claim.get('endpoint')}")
                                if MAIN_EVENT_LOOP:
                                    asyncio.run_coroutine_threadsafe(
                                        bot.send_message(uid, "🎉 <b>مبروك!</b>\n\n✅ تم تفعيل عرض 72 جيجا أوتوماتيكياً في الخلفية لرقمك!\n\n💡 اطلب <code>*200#</code> باش تتأكد.", parse_mode='HTML'),
                                        MAIN_EVENT_LOOP
                                    )
                except: pass
        except: pass

# ==================== نصوص ====================
WELCOME_HEADER = ("مرحبا بك في موح بوت 👋\n\n"
    "بوت موح يقدم تفعيل عروض انترنت في مختلف الشبكات الجزائرية 🇩🇿\n\n"
    "1️⃣ • أدخل الرقم 📱\n2️⃣ • أكمل الخطوات ✅\n"
    "3️⃣ • إختر عرض مناسب 🛒\n4️⃣ • انتظار الرد ... 🔍")
WELCOME_FOOTER = "للبدء أرسل رقم هاتفك 📱"
OTP_MSG = ("✅ <b>تم إرسال الرمز بنجاح</b>\n\n"
           "يرجى نسخ أو كتابة الرمز المكون من 6 أرقام الذي تلقيته في رسالة على هاتفك 📱\n\n"
           "⏳ <i>إذا لم يصلك، انتظر <b>دقيقة واحدة</b> قبل إعادة الطلب</i>")

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
    if elapsed >= OTP_RESEND_COOLDOWN:
        return True, 0
    return False, int(OTP_RESEND_COOLDOWN - elapsed)

async def send_otp_message(cid, display, full, markup=None):
    _last_otp_sent[cid] = time.time()
    try: await bot.send_sticker(cid, PHONE_STICKER)
    except: pass
    try: await bot.send_message(cid, OTP_MSG, reply_markup=markup, parse_mode='HTML')
    except: pass

def back_btn(cb="main_menu"):
    m = InlineKeyboardMarkup(); m.add(InlineKeyboardButton("↩️ رجوع", callback_data=cb)); return m

async def send_result(uid, text, back_cb="main_menu"):
    try: await bot.send_sticker(uid, PHONE_STICKER)
    except: pass
    try:
        await bot.send_message(uid, text, reply_markup=back_btn(back_cb), parse_mode='HTML')
    except Exception as e:
        if "Forbidden" in str(e): logging.warning(f"[USER-BLOCKED] {uid}")
        else: logging.error(f"[SEND-RESULT] {uid}: {e}")

async def notify_group_success(offer_name, network):
    if not NOTIFY_GROUP: return
    try:
        text = (f"✅ <b>تفعيل ناجح</b>\n━━━━━━━━━━━━━━━━\n"
                f"🌐 <b>الشبكة:</b> {network}\n"
                f"🎁 <b>العرض:</b> {offer_name}\n"
                f"⏱️ <b>الوقت:</b> {datetime.now().strftime('%H:%M:%S')}")
        await bot.send_message(NOTIFY_GROUP, text, parse_mode='HTML')
    except Exception as e: logging.error(f"[NOTIFY-GROUP] {e}")

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

# ==================== Menus ====================
def main_menu_markup(user_id=None):
    m = InlineKeyboardMarkup(row_width=1)
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
                    oo_gift_won,oo_gifts_total,oo_free_2gb,oo_72gb
                    FROM stats WHERE id=1""", fetch=True)
    if not s: s = (0,)*15
    while len(s) < 15: s = s + (0,)
    users = db_query("SELECT COUNT(*) FROM users", fetch=True)[0] or 0
    dz = db_query("SELECT COUNT(*) FROM numbers", fetch=True)[0] or 0
    return (f"📊 <b>الإحصائيات</b>\n👥 {users} | 📱 {dz}\n\n"
            f"🔴 جيزي:\n"
            f"  🎁 2G أسبوعي: {s[0]}\n"
            f"  💰 العروض: {s[2]}\n\n"
            f"🟠 أوريدو:\n  🔐: {s[3]}  👻: {s[4]}\n"
            f"  ⚡ 20دج-1Go: {s[9]}\n"
            f"  🎁 2Go FREE: {s[13]}\n"
            f"  🔥 72Go: {s[14]}")

def oo_dynamic_menu(services, uid=None):
    m = InlineKeyboardMarkup(row_width=1)
    m.add(InlineKeyboardButton("💰 رصيدي", callback_data="oo_balance"))
    m.add(InlineKeyboardButton("📋 عروضي", callback_data="oo_my_offers"))
    m.add(InlineKeyboardButton("👻 سناب", callback_data="oo_snap"))
    m.add(InlineKeyboardButton("⚡ 20 دج — 1Go — 24H", callback_data="oo_quick_20_1g"))
    m.add(InlineKeyboardButton("🎁 2 جيجا مجاني — 24H", callback_data="oo_quick_free_2gb"))
    m.add(InlineKeyboardButton("🔥 72 جيجا (أول نوفمبر)", callback_data="oo_quick_72gb"))
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
    display = dz_mask(phone); loading_msg = None
    ok2, remaining = _otp_can_resend(uid)
    if not ok2:
        mm = InlineKeyboardMarkup()
        mm.add(InlineKeyboardButton("🔄 إعادة إرسال", callback_data=f"resend_otp_{phone}"))
        await bot.send_message(uid,
            f"⏳ <b>انتظر قليلاً</b>\n\n💡 يمكنك إعادة الطلب بعد <b>{remaining}</b> ثانية",
            reply_markup=mm, parse_mode='HTML')
        return
    try: loading_msg = await bot.send_message(uid, "⏳ جاري إرسال رمز جديد...")
    except: pass
    ok = await asyncio.to_thread(dj_request_otp, phone)
    if loading_msg:
        try: await bot.delete_message(uid, loading_msg.message_id)
        except: pass
    if ok:
        mm = InlineKeyboardMarkup()
        mm.add(InlineKeyboardButton("🔄 إعادة إرسال", callback_data=f"resend_otp_{phone}"))
        await send_otp_message(uid, display, phone, mm)
        user_steps[uid] = {"step": "dz_verify_otp", "phone": phone, "display": display, "last_activity": time.time()}
    else:
        await bot.send_message(uid,
            f"⚠️ <b>انتهت الجلسة</b>\n\n📱 <code>{display}</code>\n\n❌ تعذر إرسال رمز تلقائياً",
            reply_markup=back_btn("main_menu"), parse_mode='HTML')

async def show_dz_balance(uid, phone):
    row = db_query("SELECT token FROM numbers WHERE phone=? AND user_id=?", (phone, uid), fetch=True)
    if not row or not row[0] or row[0] == "EXPIRED":
        await _dz_request_new_otp(uid, phone); return
    result = await asyncio.to_thread(dj_check_balance, row[0], phone)
    if result.get("status") == "EXPIRED":
        db_query("UPDATE numbers SET token='EXPIRED' WHERE phone=? AND user_id=?", (phone, uid))
        await _dz_request_new_otp(uid, phone); return
    if result.get("status") == "FAILED":
        await bot.send_message(uid, "❌ <b>تعذر جلب الرصيد</b>\n\n💡 جرّب بعد دقيقة",
            reply_markup=back_btn("main_menu"), parse_mode='HTML'); return
    bal = result.get("balance", 0)
    text = f"💳 <b>رصيد الرقم</b>\n\n📱 <code>{dz_mask(phone)}</code>\n━━━━━━━━━━━━━━━\n💰 <b>الرصيد: {bal} دج</b>"
    await bot.send_message(uid, text, reply_markup=back_btn("main_menu"), parse_mode='HTML')

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
            await bot.send_message(uid, f"❌ لم تكمل أسبوع\n⏱️ {d} ي {h} س", reply_markup=back_btn("main_menu")); return
        res = await asyncio.to_thread(dj_activate_2gb, token, phone)
        if res == "SUCCESS":
            db_query("UPDATE numbers SET last_activation_2gb=? WHERE phone=?", (time.time(), phone))
            inc_stat("total_2gb")
            await notify_group_success("2GB أسبوعي", "Djezzy 🔴")
            await send_result(uid,
                f"✅ <b>تم التفعيل بنجاح</b> 🎉\n\n"
                f"📱 <code>{dz_mask(phone)}</code>\n"
                f"🎁 <b>2 جيجا</b> — أسبوع\n\n"
                f"💡 اطلب <code>*200#</code> باش تتأكد",
                "main_menu")
        elif res == "EXPIRED":
            db_query("UPDATE numbers SET token='EXPIRED' WHERE phone=?", (phone,))
            await _dz_request_new_otp(uid, phone); return
        elif res == "LIMIT":
            await bot.send_message(uid,
                "⏰ <b>راك مفعّل 2 جيجا من قبل</b>\n\n"
                "🎁 العرض: 2 جيجا — أسبوع\n\n"
                "💡 ما تقدرش تفعّلو مرتين، انتظر يخلص العرض\n"
                "📞 اطلب <code>*200#</code> باش تتأكد من الباقة",
                reply_markup=back_btn("main_menu"), parse_mode='HTML')
        elif res == "NO_BALANCE":
            await bot.send_message(uid, "❌ رصيد غير كافي (يلزم رصيد رمزي)",
                reply_markup=back_btn("main_menu"))
        elif res == "RATE_LIMIT":
            await bot.send_message(uid, "🚫 تجاوزت الحد المسموح، جرّب بعد دقائق",
                reply_markup=back_btn("main_menu"))
        elif res == "NOT_ALLOWED":
            await bot.send_message(uid, "🚫 العرض غير متاح لرقمك",
                reply_markup=back_btn("main_menu"))
        else:
            await bot.send_message(uid, f"❌ فشل التفعيل ({res})",
                reply_markup=back_btn("main_menu"))
        return

async def send_dz_menu(uid, phone=None):
    if not phone:
        nums = db_query("SELECT phone FROM numbers WHERE user_id=? ORDER BY added_date DESC LIMIT 1", (uid,), fetchall=True)
        if nums and nums[0]: phone = nums[0][0]
    if phone: txt = f"📱 الرقم : <code>{dz_mask(phone)}</code> ✅\n🔴 الشبكة : <b>جيزي</b>\n\nاختر العرض 🔽"
    else: txt = "🔴 اختر العرض 🔽"
    try: await bot.send_message(uid, txt, reply_markup=main_menu_markup(uid), parse_mode='HTML')
    except Exception as e:
        if "Forbidden" in str(e): logging.warning(f"[USER-BLOCKED] {uid}")
        else: logging.error(f"[DZ-MENU] {uid}: {e}")

async def send_oo_menu(uid, user):
    ms = user["msisdn"]; at = user["access_token"]
    qd = oo_quick_detect(at)
    services = {"rate_plan": qd.get("rate_plan") or "", "is_yooz": qd.get("is_yooz", False),
        "is_dima": qd.get("is_dima", False), "balance_value": 0, "gift_count": 0}
    rp = services.get("rate_plan") or ""
    lines = [f"📱 الرقم : <code>{o_mask(ms)}</code> ✅"]
    if rp: lines.append(f"📦 العرض : <b>{rp}</b>")
    lines.append(f"💰 الرصيد : <b>...</b>"); lines.append(""); lines.append("اختر الخدمة 🔽")
    try:
        msg = await bot.send_message(uid, "\n".join(lines), reply_markup=oo_dynamic_menu(services, uid), parse_mode='HTML')
        asyncio.create_task(_update_oo_menu_bg(uid, user, msg.message_id))
    except Exception as e:
        if "Forbidden" in str(e): logging.warning(f"[USER-BLOCKED] {uid}")

async def _update_oo_menu_bg(uid, user, msg_id):
    try:
        ms = user["msisdn"]; at = user["access_token"]
        meta = {k: user.get(k, "") for k in ["tok_instance_id","tok_plat_sig","tok_fingerprint","tok_timestamp"]}
        bal_r = await asyncio.to_thread(oo_check_balance, ms, at, meta)
        bal = 0
        if bal_r.get("status") == "ok":
            try: bal = float(bal_r.get("data", {}).get("accountBalance", 0) or 0)
            except: pass
        rp = (oo_quick_detect(at).get("rate_plan") or "")
        lines = [f"📱 الرقم : <code>{o_mask(ms)}</code> ✅"]
        if rp: lines.append(f"📦 العرض : <b>{rp}</b>")
        lines.append(f"💰 الرصيد : <b>{bal} دج</b>")
        lines.append(""); lines.append("اختر الخدمة 🔽")
        svc = {"rate_plan": rp, "is_yooz": oo_quick_detect(at).get("is_yooz", False),
               "is_dima": oo_quick_detect(at).get("is_dima", False), "balance_value": bal, "gift_count": 0}
        await bot.edit_message_text("\n".join(lines), chat_id=uid, message_id=msg_id,
            reply_markup=oo_dynamic_menu(svc, uid), parse_mode='HTML')
    except: pass

# ==================== 📋 Admin Log Commands ====================
@bot.message_handler(commands=['log'], chat_types=['private'])
async def cmd_log(message):
    if message.from_user.id != ADMIN_ID: return
    args = message.text.split()
    n = 30
    if len(args) > 1:
        try: n = min(int(args[1]), 100)
        except: pass
    lines = get_logs(n)
    if not lines:
        await bot.send_message(message.chat.id, "📭 السجل فارغ"); return
    await bot.send_message(message.chat.id, format_logs_for_telegram(lines, f"آخر {len(lines)} سطر"), parse_mode='HTML')

@bot.message_handler(commands=['log2g'], chat_types=['private'])
async def cmd_log2g(message):
    if message.from_user.id != ADMIN_ID: return
    lines = get_logs(50, "OO-FREE-2GB")
    if not lines:
        await bot.send_message(message.chat.id, "📭 لا توجد سجلات 2Go"); return
    await bot.send_message(message.chat.id, format_logs_for_telegram(lines, "سجل 2Go"), parse_mode='HTML')

@bot.message_handler(commands=['logerr'], chat_types=['private'])
async def cmd_logerr(message):
    if message.from_user.id != ADMIN_ID: return
    with _LOG_LOCK:
        all_lines = list(_LOG_BUFFER)
    lines = [l for l in all_lines if 'ERROR' in l or 'WARNING' in l or '❌' in l][-50:]
    if not lines:
        await bot.send_message(message.chat.id, "✅ لا توجد أخطاء"); return
    await bot.send_message(message.chat.id, format_logs_for_telegram(lines, "الأخطاء"), parse_mode='HTML')

@bot.message_handler(commands=['clearlog'], chat_types=['private'])
async def cmd_clearlog(message):
    if message.from_user.id != ADMIN_ID: return
    with _LOG_LOCK:
        _LOG_BUFFER.clear()
    await bot.send_message(message.chat.id, "🗑️ تم مسح السجل")

@bot.message_handler(commands=['admin'], chat_types=['private'])
async def cmd_admin(message):
    if message.from_user.id != ADMIN_ID: return
    await bot.send_message(message.chat.id, "🛠️ <b>لوحة الأدمن</b>", reply_markup=admin_menu_markup(), parse_mode='HTML')

# ==================== Start ====================
@bot.message_handler(commands=['start'], chat_types=['private'])
async def cmd_start(message):
    uid = message.from_user.id; now = time.time()
    await typing(message.chat.id)
    if not await check_subscription(uid):
        await bot.reply_to(message, "🔒 اشترك في القناة:", reply_markup=subscription_markup()); return
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

# ==================== Callback Handler ====================
@bot.callback_query_handler(func=lambda call: (
    call.message and call.message.chat and call.message.chat.type == 'private'
))
async def cb_handler(call):
    try:
        await _cb_inner(call)
    except Exception as e:
        logging.error(f"[CB-CRASH] user={call.from_user.id} data={call.data}: {e}", exc_info=True)
        try:
            await bot.answer_callback_query(call.id, "⚠️ حدث خطأ مؤقت، جرّب مرة أخرى")
        except Exception: pass

async def _cb_inner(call):
    uid = call.from_user.id
    if call.data.startswith("resend_otp_"):
        target = call.data.replace("resend_otp_", "")
        try: await bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        await typing(uid)
        ok, remaining = _otp_can_resend(uid)
        if not ok:
            mm = InlineKeyboardMarkup()
            mm.add(InlineKeyboardButton("🔄 إعادة إرسال", callback_data=f"resend_otp_{target}"))
            await bot.send_message(uid,
                f"⏳ <b>انتظر قليلاً</b>\n\n💡 يمكنك إعادة الطلب بعد <b>{remaining}</b> ثانية",
                reply_markup=mm, parse_mode='HTML')
            return
        if target.startswith("2135"):
            oo_clear(uid)
            digits = "0" + target[3:]
            result = await asyncio.to_thread(ooredoo_send_otp_sync, target)
            if not result.get("otp_sent"):
                await bot.send_message(uid, "❌ تعذر الإرسال"); return
            user_steps[uid] = {"step": "oo_await_otp", "msisdn": target, "device": result["device"], "last_activity": time.time()}
            mm = InlineKeyboardMarkup(); mm.add(InlineKeyboardButton("🔄 إعادة إرسال", callback_data=f"resend_otp_{target}"))
            await send_otp_message(uid, digits, target, mm)
        else:
            db_query("UPDATE numbers SET token=NULL WHERE phone=? AND user_id=?", (target, uid))
            dz_clear_session(uid)
            ok2 = await asyncio.to_thread(dj_request_otp, target)
            if ok2:
                display = "0" + target[3:]
                mm = InlineKeyboardMarkup(); mm.add(InlineKeyboardButton("🔄 إعادة إرسال", callback_data=f"resend_otp_{target}"))
                await send_otp_message(uid, display, target, mm)
                user_steps[uid] = {"step": "dz_verify_otp", "phone": target, "display": display, "last_activity": time.time()}
            else:
                await bot.send_message(uid, "❌ تعذر إرسال الرمز", reply_markup=back_btn("main_menu"))
        return
    if call.data != "check_sub" and not await check_subscription(uid):
        try: await bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        await bot.send_message(uid, "🔒 اشترك:", reply_markup=subscription_markup()); return
    try: await bot.delete_message(call.message.chat.id, call.message.message_id)
    except: pass
    await typing(uid)
    if uid in user_steps and isinstance(user_steps[uid], dict):
        user_steps[uid]["last_activity"] = time.time()

    if call.data == "admin_menu":
        if uid != ADMIN_ID: return
        await bot.send_message(uid, "🛠️ <b>لوحة الأدمن</b>", reply_markup=admin_menu_markup(), parse_mode='HTML')
        return
    if call.data == "admin_log":
        if uid != ADMIN_ID: return
        lines = get_logs(30)
        if not lines: await bot.send_message(uid, "📭 السجل فارغ"); return
        await bot.send_message(uid, format_logs_for_telegram(lines, f"آخر {len(lines)} سطر"), parse_mode='HTML')
        return
    if call.data == "admin_log_2g":
        if uid != ADMIN_ID: return
        lines = get_logs(50, "OO-FREE-2GB")
        if not lines: await bot.send_message(uid, "📭 لا توجد سجلات 2Go"); return
        await bot.send_message(uid, format_logs_for_telegram(lines, "سجل 2Go"), parse_mode='HTML')
        return
    if call.data == "admin_log_err":
        if uid != ADMIN_ID: return
        with _LOG_LOCK:
            all_lines = list(_LOG_BUFFER)
        lines = [l for l in all_lines if 'ERROR' in l or 'WARNING' in l or '❌' in l][-50:]
        if not lines: await bot.send_message(uid, "✅ لا توجد أخطاء"); return
        await bot.send_message(uid, format_logs_for_telegram(lines, "الأخطاء"), parse_mode='HTML')
        return
    if call.data == "admin_log_clear":
        if uid != ADMIN_ID: return
        with _LOG_LOCK:
            _LOG_BUFFER.clear()
        await bot.send_message(uid, "🗑️ تم مسح السجل")
        return

    if call.data == "check_sub":
        if await check_subscription(uid): await cmd_start(call.message)
        else: await bot.send_message(uid, "❌ لم تشترك!", reply_markup=subscription_markup())
        return

    if call.data == "delete_my_number":
        user = oo_load(uid)
        dz_row = db_query("SELECT phone FROM numbers WHERE user_id=? LIMIT 1", (uid,), fetch=True)
        saved = []
        if dz_row: saved.append(f"🔴 <code>{dz_mask(dz_row[0])}</code> (جيزي)")
        if user and user.get("msisdn"): saved.append(f"🟠 <code>{o_mask(user['msisdn'])}</code> (أوريدو)")
        if not saved:
            await bot.send_message(uid, "📭 ما عندكش رقم محفوظ", reply_markup=back_btn("main_menu")); return
        kb = InlineKeyboardMarkup(row_width=1)
        kb.add(InlineKeyboardButton("✅ تأكيد الحذف", callback_data="delete_my_number_ok"))
        kb.add(InlineKeyboardButton("❌ إلغاء", callback_data="main_menu"))
        await bot.send_message(uid, "🗑️ <b>حذف الرقم المحفوظ</b>\n\n📱 <b>الأرقام:</b>\n" + "\n".join(saved),
            reply_markup=kb, parse_mode='HTML'); return

    if call.data == "delete_my_number_ok":
        db_query("DELETE FROM numbers WHERE user_id=?", (uid,))
        oo_clear(uid); dz_clear_session(uid); oo_free2gb_clear(uid)
        user_steps[uid] = {"step": "await_phone", "last_activity": time.time()}
        await bot.send_message(uid, "✅ <b>تم الحذف</b>\n\n💡 أرسل رقمك من جديد", reply_markup=back_btn("main_menu"), parse_mode='HTML'); return

    if call.data == "change_phone":
        oo_clear(uid); dz_clear_session(uid); oo_free2gb_clear(uid)
        user_steps[uid] = {"step": "await_phone", "last_activity": time.time()}
        await send_welcome(uid); return

    if call.data.startswith("oo_"):
        await oo_cb_handler(call); return

    if call.data == "quick_offer_70_4g":
        nums = db_query("SELECT phone FROM numbers WHERE user_id=? ORDER BY added_date DESC LIMIT 1", (uid,), fetchall=True)
        if not nums: await bot.send_message(uid, "⚠️ أضف رقماً.", reply_markup=back_btn("main_menu")); return
        ph = nums[0][0]
        row = db_query("SELECT token FROM numbers WHERE phone=? AND user_id=?", (ph, uid), fetch=True)
        if not row or row[0] == "EXPIRED": await _dz_request_new_otp(uid, ph); return
        bal = await asyncio.to_thread(dj_check_balance, row[0], ph)
        if bal.get("status") == "EXPIRED":
            db_query("UPDATE numbers SET token='EXPIRED' WHERE phone=?", (ph,))
            await _dz_request_new_otp(uid, ph); return
        cur = bal.get("balance", 0)
        if cur < 70:
            await bot.send_message(uid, f"❌ رصيد غير كافي\n💰 {cur} دج", reply_markup=back_btn("main_menu")); return
        result = await dz_activate_offer_70_4g_async(row[0], ph)
        if result.get("token_expired"):
            db_query("UPDATE numbers SET token='EXPIRED' WHERE phone=?", (ph,))
            await _dz_request_new_otp(uid, ph); return
        if result.get("success"):
            inc_stat("total_offers")
            await notify_group_success("70دج — 4GB", "Djezzy 🔴")
            await bot.send_message(uid, result["msg"], parse_mode='HTML', reply_markup=main_menu_markup(uid))
        else: await bot.send_message(uid, result["msg"], parse_mode='HTML', reply_markup=back_btn("main_menu"))
        return

    if call.data == "quick_offer_90_5g":
        nums = db_query("SELECT phone FROM numbers WHERE user_id=? ORDER BY added_date DESC LIMIT 1", (uid,), fetchall=True)
        if not nums: await bot.send_message(uid, "⚠️ أضف رقماً.", reply_markup=back_btn("main_menu")); return
        ph = nums[0][0]
        row = db_query("SELECT token FROM numbers WHERE phone=? AND user_id=?", (ph, uid), fetch=True)
        if not row or row[0] == "EXPIRED": await _dz_request_new_otp(uid, ph); return
        bal = await asyncio.to_thread(dj_check_balance, row[0], ph)
        if bal.get("status") == "EXPIRED":
            db_query("UPDATE numbers SET token='EXPIRED' WHERE phone=?", (ph,))
            await _dz_request_new_otp(uid, ph); return
        cur = bal.get("balance", 0)
        if cur < 90:
            await bot.send_message(uid, f"❌ رصيد غير كافي\n💰 {cur} دج", reply_markup=back_btn("main_menu")); return
        result = await dz_activate_offer_90_5g_async(row[0], ph)
        if result.get("token_expired"):
            db_query("UPDATE numbers SET token='EXPIRED' WHERE phone=?", (ph,))
            await _dz_request_new_otp(uid, ph); return
        if result.get("success"):
            inc_stat("total_offers")
            await notify_group_success("90دج — 5GB", "Djezzy 🔴")
            await bot.send_message(uid, result["msg"], parse_mode='HTML', reply_markup=main_menu_markup(uid))
        else: await bot.send_message(uid, result["msg"], parse_mode='HTML', reply_markup=back_btn("main_menu"))
        return

    if call.data == "check_balance":
        nums = db_query("SELECT phone FROM numbers WHERE user_id=?", (uid,), fetchall=True)
        if not nums: await bot.send_message(uid, "⚠️ أضف رقماً.", reply_markup=back_btn("main_menu")); return
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
        if not nums: await bot.send_message(uid, "⚠️ أضف رقماً.", reply_markup=back_btn("main_menu")); return
        await dz_process(uid, nums[0][0], "2gb"); return
    if call.data == "show_all_offers":
        await bot.send_message(uid, "💰:", reply_markup=all_offers_markup()); return
    if call.data.startswith("offer_details_"):
        code = call.data.replace("offer_details_", "")
        o = AVAILABLE_OFFERS.get(code, {})
        nums = db_query("SELECT phone FROM numbers WHERE user_id=? ORDER BY added_date DESC LIMIT 1", (uid,), fetchall=True)
        if not nums: await bot.send_message(uid, "⚠️ أضف رقماً.", reply_markup=back_btn("main_menu")); return
        ph = nums[0][0]
        d = f"💰 <b>{o.get('name')}</b>\n📦 {o.get('data')}\n⏱️ {o.get('validity')}\n💳 <b>{o.get('price')}</b>"
        await bot.send_message(uid, f"{d}\n\n📱 <code>{dz_mask(ph)}</code>\n\nهل تريد التفعيل؟",
            reply_markup=confirm_offer_markup(code, ph), parse_mode='HTML'); return
    if call.data.startswith("confirm_offer_"):
        rest = call.data.replace("confirm_offer_", ""); parts = rest.rsplit("_", 1)
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
                await bot.send_message(uid, f"❌ رصيد غير كافي\n💰 {cur} دج", reply_markup=back_btn("main_menu"), parse_mode='HTML'); return
            kb = InlineKeyboardMarkup(row_width=2)
            kb.add(InlineKeyboardButton("✅ تأكيد", callback_data=f"dzconfirm_offer_{code}_{ph}"),
                   InlineKeyboardButton("❌ إلغاء", callback_data="main_menu"))
            await bot.send_message(uid, f"💰 <b>{cur} دج</b> → <b>{o['name']}</b>\n💳 {price} دج\n\nتأكيد؟",
                reply_markup=kb, parse_mode='HTML')
        return
    if call.data.startswith("dzconfirm_offer_"):
        rest = call.data.replace("dzconfirm_offer_", ""); code, ph = rest.rsplit("_", 1)
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
            inc_stat("total_offers")
            await notify_group_success(o.get('name', 'العرض'), "Djezzy 🔴")
            await bot.send_message(uid, result["msg"], parse_mode='HTML', reply_markup=main_menu_markup(uid))
        else: await bot.send_message(uid, result["msg"], parse_mode='HTML', reply_markup=back_btn("main_menu"))
        return
    if call.data == "bot_stats":
        if uid != ADMIN_ID: await bot.send_message(uid, "⛔"); return
        await bot.send_message(uid, get_stats_text(), reply_markup=back_btn("main_menu"), parse_mode='HTML'); return
    if call.data in ("main_menu", "back_main"):
        await send_dz_menu(uid); return

# ==================== OO Callbacks ====================
async def oo_cb_handler(call):
    uid = call.from_user.id
    data = call.data
    user = oo_load(uid)
    if data == "oo_change":
        oo_clear(uid); dz_clear_session(uid); oo_free2gb_clear(uid)
        user_steps[uid] = {"step": "await_phone", "last_activity": time.time()}
        await send_welcome(uid); return
    if data == "oo_back_menu":
        if user: await send_oo_menu(uid, user); return
        user_steps[uid] = {"step": "await_phone", "last_activity": time.time()}
        await send_welcome(uid); return
    if data == "oo_stats":
        if uid != ADMIN_ID: await bot.send_message(uid, "⛔"); return
        await bot.send_message(uid, get_stats_text(), reply_markup=back_btn("oo_back_menu"), parse_mode='HTML'); return
    if not user or not user.get("access_token"):
        user_steps[uid] = {"step": "await_phone", "last_activity": time.time()}
        await send_welcome(uid); return
    user = await asyncio.to_thread(oo_ensure_valid, uid, user)
    if not user:
        mm = InlineKeyboardMarkup(); mm.add(InlineKeyboardButton("🔄 إرسال رمز", callback_data="oo_change"))
        await bot.send_message(uid, "⚠️ <b>انتهت الجلسة</b>", reply_markup=mm, parse_mode='HTML'); return
    ms = user["msisdn"]; at = user["access_token"]
    meta = {k: user.get(k, "") for k in ["tok_instance_id","tok_plat_sig","tok_fingerprint","tok_timestamp"]}

    if data == "oo_balance":
        inc_stat("oo_balance")
        r = await asyncio.to_thread(oo_check_balance, ms, at, meta)
        if r.get("status") != "ok":
            await bot.send_message(uid, "❌", reply_markup=back_btn("oo_back_menu")); return
        b = r.get("data", {}).get("accountBalance", "?")
        await bot.send_message(uid, f"💰 <b>{b} دج</b>\n\n📱 <code>{o_mask(ms)}</code>",
            reply_markup=back_btn("oo_back_menu"), parse_mode='HTML'); return

    if data == "oo_my_offers":
        inc_stat("oo_offers_view")
        r = await asyncio.to_thread(oo_get_active, ms, at, meta)
        if r["status"] != "ok":
            await bot.send_message(uid, "❌", reply_markup=back_btn("oo_back_menu")); return
        d = r.get("data", {}); b = d.get("accountBalance", "?")
        lines = [f"📋 <b>عروضك</b>\n💰 <b>{b} دج</b>\n"]
        if len(lines) <= 2: lines.append("📭 <i>لا توجد باقات نشطة</i>")
        await bot.send_message(uid, "\n".join(lines), reply_markup=back_btn("oo_back_menu"), parse_mode='HTML'); return

    if data == "oo_snap":
        r = await asyncio.to_thread(oo_activate_snapchat, ms, at, meta)
        if r == "ok":
            inc_stat("oo_snap")
            await notify_group_success("Snapchat", "Ooredoo 🟠")
            await send_result(uid, f"✅ <b>تم تفعيل سناب!</b>\n📱 <code>{o_mask(ms)}</code>", "oo_back_menu")
        elif r == "already_active":
            await bot.send_message(uid, "⚠️ مفعّلة مسبقاً", reply_markup=back_btn("oo_back_menu"))
        else: await bot.send_message(uid, "❌", reply_markup=back_btn("oo_back_menu"))
        return

    if data == "oo_quick_20_1g":
        r = await asyncio.to_thread(oo_check_balance, ms, at, meta)
        try: balance = float(r.get("data", {}).get("accountBalance", 0) or 0)
        except: balance = 0
        if balance < 20:
            await bot.send_message(uid, f"❌ رصيد غير كافي\n💰 {balance} دج", reply_markup=back_btn("oo_back_menu")); return
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(InlineKeyboardButton("✅ تأكيد", callback_data="oo_quick_20_1g_ok"),
               InlineKeyboardButton("❌ إلغاء", callback_data="oo_back_menu"))
        await bot.send_message(uid, f"⚡ <b>20دج — 1Go — 24H</b>\n💰 رصيدك: <b>{balance} دج</b>",
            reply_markup=kb, parse_mode='HTML'); return

    if data == "oo_quick_20_1g_ok":
        r = await asyncio.to_thread(oo_purchase_20dzd_1go, ms, at, meta)
        status = r.get("status", "error")
        if status == "ok":
            inc_stat("oo_20dzd_1go")
            await notify_group_success("20دج — 1Go", "Ooredoo 🟠")
            await send_result(uid, f"✅ <b>تم التفعيل</b> 🎉\n📱 <code>{o_mask(ms)}</code>\n⚡ 1 جيجا — 24H", "oo_back_menu")
            return
        await bot.send_message(uid, f"❌ فشل التفعيل\n💡 كود: {r.get('code', status)}",
            reply_markup=back_btn("oo_back_menu"), parse_mode='HTML')
        return

    if data == "oo_quick_free_2gb":
        last = oo_free2gb_get_last(uid, ms)
        elapsed = time.time() - last if last else 0
        if last and elapsed < COOLDOWN_FREE_2GB_OO:
            remaining = int(COOLDOWN_FREE_2GB_OO - elapsed)
            hh = remaining // 3600
            mmn = (remaining % 3600) // 60
            await bot.send_message(uid,
                f"⏰ <b>راك مفعّل من قبل</b>\n"
                f"━━━━━━━━━━━━━━━━\n\n"
                f"📱 <code>{o_mask(ms)}</code>\n"
                f"🎁 <b>2 جيجا مجاني — 24H</b>\n\n"
                f"⏳ <b>المتبقي:</b> {hh} س {mmn} د\n\n"
                f"💡 رجع بعد انتهاء المدة",
                reply_markup=back_btn("oo_back_menu"), parse_mode='HTML')
            return

        await bot.send_message(uid, "⏳ <b>جاري تفعيل 2 جيجا المجاني...</b>\n\n⏱️ انتظر قليلاً", parse_mode='HTML')
        r = await asyncio.to_thread(oo_purchase_free_2gb, ms, at, meta)
        status = r.get("status", "error")

        if status == "ok":
            inc_stat("oo_free_2gb")
            oo_free2gb_save(uid, ms)
            await notify_group_success("2Go مجاني — 24H", "Ooredoo 🟠")
            await send_result(uid,
                f"🎉 <b>مبروك عليك!</b>\n━━━━━━━━━━━━━━━━\n\n"
                f"✅ <b>تم تفعيل 2 جيجا</b>\n\n"
                f"📱 <code>{o_mask(ms)}</code>\n🎁 <b>2 جيجا</b>\n"
                f"⏱️ صالحة <b>24 ساعة</b>\n💰 <b>مجاني 100%</b> 🎉\n\n"
                f"💡 اطلب <code>*200#</code> باش تشوف رصيدك",
                "oo_back_menu")
            if uid == ADMIN_ID:
                await bot.send_message(uid, f"<b>🔍 تفاصيل للأدمن:</b>\n<pre>{_html.escape(str(r.get('data',{}))[:1500])}</pre>", parse_mode='HTML')
            return

        if status == "already":
            oo_free2gb_save(uid, ms)
            hh = COOLDOWN_FREE_2GB_OO // 3600
            await bot.send_message(uid,
                f"⏰ <b>راك مفعّل من قبل</b>\n━━━━━━━━━━━━━━━━\n\n"
                f"📱 <code>{o_mask(ms)}</code>\n"
                f"🎁 <b>2 جيجا مجاني — 24H</b>\n\n"
                f"⏳ <b>انتظر {hh} ساعة</b> وأعد المحاولة\n\n"
                f"💡 اطلب <code>*200#</code> باش تتأكد",
                reply_markup=back_btn("oo_back_menu"), parse_mode='HTML')
            return

        if status == "unauthorized":
            bal_check = await asyncio.to_thread(oo_check_balance, ms, at, meta)
            if bal_check.get("status") == "unauthorized":
                mm = InlineKeyboardMarkup()
                mm.add(InlineKeyboardButton("🔄 إعادة الدخول", callback_data="oo_change"))
                await bot.send_message(uid, "🔐 <b>انتهت الجلسة</b>\n\n💡 أعد إدخال الرقم", reply_markup=mm, parse_mode='HTML')
                return
            await bot.send_message(uid, "⚠️ <b>تعذر التفعيل مؤقتاً</b>\n\n💡 حاول بعد قليل",
                reply_markup=back_btn("oo_back_menu"), parse_mode='HTML')
            if uid == ADMIN_ID:
                await bot.send_message(uid, f"<b>🔍 تفاصيل للأدمن:</b>\n<pre>{_html.escape(str(r.get('data',{}))[:1500])}</pre>", parse_mode='HTML')
            return

        if status == "not_allowed":
            await bot.send_message(uid, "🚫 <b>العرض غير متاح لرقمك</b>",
                reply_markup=back_btn("oo_back_menu"), parse_mode='HTML')
            if uid == ADMIN_ID:
                await bot.send_message(uid, f"<b>🔍 تفاصيل للأدمن:</b>\n<pre>{_html.escape(str(r.get('data',{}))[:1500])}</pre>", parse_mode='HTML')
            return

        await bot.send_message(uid, "❌ <b>فشل التفعيل</b>\n💡 حاول لاحقاً",
            reply_markup=back_btn("oo_back_menu"), parse_mode='HTML')
        if uid == ADMIN_ID:
            await bot.send_message(uid, f"<b>🔍 تفاصيل للأدمن:</b>\ncode={r.get('code')}\n<pre>{_html.escape(str(r.get('data',{}))[:1500])}</pre>", parse_mode='HTML')
        return

    if data == "oo_quick_72gb":
        r = await asyncio.to_thread(oo_check_72gb_status, ms, at, meta)
        if r.get("status") == "ok":
            d = r.get("data", {})
            played = d.get("played", True)
            enable = d.get("gameUIEnable", False)
            
            if not enable:
                await bot.send_message(uid, "🚫 <b>اللعبة غير متاحة لحسابك حالياً.</b>\n\n💡 جرب لاحقاً.", reply_markup=back_btn("oo_back_menu"))
                return
                
            if played:
                await bot.send_message(uid, "⏰ <b>راك لعبت وخذيت الجائزة ديجا في هذي الحملة.</b>\n\n💡 انتظر الحملة الجاية.", reply_markup=back_btn("oo_back_menu"))
                return
                
            await bot.send_message(uid, "⏳ <b>جاري محاولة تفعيل 72 جيجا...</b>\n\n💡 قد تتطلب العملية بعض الوقت.", parse_mode='HTML')
            claim = await asyncio.to_thread(oo_claim_72gb, ms, at, meta)
            if claim.get("status") == "ok":
                inc_stat("oo_72gb")
                await notify_group_success("72 جيجا (أول نوفمبر)", "Ooredoo 🟠")
                await send_result(uid, f"🎉 <b>مبروك!</b>\n\n✅ تم تفعيل 72 جيجا بنجاح لرقمك!\n\n💡 تحقق من رصيدك بـ <code>*200#</code>", "oo_back_menu")
            else:
                await bot.send_message(uid, "⚠️ <b>اللعبة متاحة لكن التفعيل لم ينجح بعد.</b>\n\n💡 يرجى المحاولة بعد قليل (قد يكون المؤقت الداخلي لم ينتهِ).\n⏳ <b>البوت سيحاول تفعيلها تلقائياً في الخلفية.</b>", reply_markup=back_btn("oo_back_menu"))
        else:
            await bot.send_message(uid, "❌ تعبر جلب حالة اللعبة.", reply_markup=back_btn("oo_back_menu"))
        return

# ==================== TEXT HANDLER ====================
@bot.message_handler(func=lambda m: True, content_types=['text'], chat_types=['private'])
async def handle_text(message):
    try:
        await _text_inner(message)
    except Exception as e:
        logging.error(f"[TEXT-CRASH] user={message.from_user.id}: {e}", exc_info=True)
        try:
            await bot.send_message(message.chat.id, "⚠️ حدث خطأ مؤقت، جرّب مرة أخرى")
        except Exception: pass

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
            await bot.send_message(uid, "❌ رقم غير صحيح"); return
        msisdn = "213" + digits[1:]
        if digits.startswith(("07", "06")):
            row = db_query("SELECT token FROM numbers WHERE phone=? AND user_id=?", (msisdn, uid), fetch=True)
            if row and row[0] and row[0] != "EXPIRED":
                user_steps[uid] = {"step": "dz_menu", "last_activity": now}
                await send_dz_menu(uid, msisdn); return
            ok = await asyncio.to_thread(dj_request_otp, msisdn)
            if ok:
                mm = InlineKeyboardMarkup(); mm.add(InlineKeyboardButton("🔄 إعادة إرسال", callback_data=f"resend_otp_{msisdn}"))
                await send_otp_message(uid, digits, msisdn, mm)
                user_steps[uid] = {"step": "dz_verify_otp", "phone": msisdn, "display": digits, "last_activity": now}
            else:
                await bot.send_message(uid, "❌ تعذر إرسال الرمز", reply_markup=back_btn("main_menu"))
            return
        if digits.startswith("05"):
            existing = oo_load(uid)
            if existing and existing.get("msisdn") == msisdn and existing.get("access_token"):
                user_steps[uid] = {"step": "oo_menu", "last_activity": now}
                await send_oo_menu(uid, existing); return
            result = await asyncio.to_thread(ooredoo_send_otp_sync, msisdn)
            if not result.get("otp_sent"):
                await bot.send_message(uid, "❌ تعذر الإرسال"); return
            user_steps[uid] = {"step": "oo_await_otp", "msisdn": msisdn, "device": result["device"], "last_activity": now}
            mm = InlineKeyboardMarkup(); mm.add(InlineKeyboardButton("🔄 إعادة إرسال", callback_data=f"resend_otp_{msisdn}"))
            await send_otp_message(uid, digits, msisdn, mm)
            return

    if step.get("step") == "oo_await_otp":
        m = re.search(r"\b(\d{6})\b", text)
        if not m:
            await bot.send_message(uid, "⚠️ أرسل 6 أرقام فقط"); return
        otp = m.group(1); ms = step.get("msisdn"); device = step.get("device", {})
        wait_msg = None
        try:
            wait_msg = await bot.send_message(uid, "🔍 جاري التحقق... انتظر ثوانٍ")
        except: pass
        result = await asyncio.to_thread(ooredoo_verify_otp_sync, ms, otp, device)
        if wait_msg:
            try: await bot.delete_message(uid, wait_msg.message_id)
            except: pass
        if result == "wrong_otp":
            await bot.send_message(uid, "❌ الرمز خاطئ، جرّب مرة أخرى"); return
        if not result:
            await bot.send_message(uid,
                "❌ <b>فشل التحقق</b>\n\n"
                "💡 تحقق من الرمز أو أعد الإرسال",
                parse_mode='HTML'); return
        user = {"msisdn": ms, "device": device, **result}
        oo_save(uid, user)
        inc_stat("oo_logins")
        user_steps[uid] = {"step": "oo_menu", "last_activity": time.time()}
        await send_oo_menu(uid, user); return

    if step.get("step") == "dz_verify_otp":
        if not text.isdigit() or len(text) != 6:
            await bot.send_message(uid, "❌ 6 أرقام"); return
        phone = step.get("phone")
        wait_msg = None
        try:
            wait_msg = await bot.send_message(uid, "🔍 جاري التحقق... انتظر ثوانٍ")
        except: pass
        token = await asyncio.to_thread(dj_verify_otp, phone, text)
        if wait_msg:
            try: await bot.delete_message(uid, wait_msg.message_id)
            except: pass
        if token and token != "EXPIRED":
            db_query("INSERT OR REPLACE INTO numbers (phone,user_id,token,added_date) VALUES (?,?,?,?)",
                     (phone, uid, token, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            dz_save_session(uid, phone, token)
            inc_stat("dz_logins")
            user_steps[uid] = {"step": "dz_menu", "last_activity": time.time()}
            await send_dz_menu(uid, phone)
        else:
            await bot.send_message(uid,
                "❌ <b>الرمز خاطئ</b>\n\n"
                "💡 أعد المحاولة أو أرسل /start",
                parse_mode='HTML')
        return

    oo_user = oo_load(uid)
    if oo_user:
        user_steps[uid] = {"step": "oo_menu", "last_activity": now}
        await send_oo_menu(uid, oo_user); return
    if db_query("SELECT token FROM numbers WHERE user_id=? LIMIT 1", (uid,), fetch=True):
        user_steps[uid] = {"step": "dz_menu", "last_activity": now}
        await send_dz_menu(uid); return
    user_steps[uid] = {"step": "await_phone", "last_activity": now}
    await send_welcome(uid)

# ==================== Main (Robust — لا يتوقف أبداً) ====================
_last_heartbeat = [time.time()]

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
    logging.warning("[POLL] ⚠️ infinity_polling returned unexpectedly")

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
                    logging.warning(f"[SUPERVISOR] ⏰ {RESTART_TIMEOUT}s reached — proactive restart")
                    break
                if now - _last_heartbeat[0] > STUCK_THRESHOLD:
                    logging.warning(f"[SUPERVISOR] 🚨 No updates for {int(now-_last_heartbeat[0])}s — checking API...")
                    try:
                        await asyncio.wait_for(bot.get_me(), timeout=15)
                        logging.warning("[SUPERVISOR] ✅ API OK — resetting heartbeat")
                        _last_heartbeat[0] = time.time()
                    except Exception as e:
                        logging.error(f"[SUPERVISOR] ❌ API dead ({e}) — restarting polling")
                        break
            if not task.done():
                task.cancel()
                try:
                    await asyncio.wait_for(task, timeout=10)
                except Exception:
                    pass
        except asyncio.CancelledError:
            task.cancel()
            raise
        except Exception as e:
            logging.error(f"[SUPERVISOR] {type(e).__name__}: {e}", exc_info=True)
            task.cancel()
            try: await task
            except Exception: pass
        if not _stop_threads.is_set():
            await asyncio.sleep(3)

async def main():
    global MAIN_EVENT_LOOP
    MAIN_EVENT_LOOP = asyncio.get_running_loop()
    
    print("=" * 60)
    print("🤖 البوت الموحّد v3 — Robust + 72GB Auto Claimer")
    print(f"👤 الأدمن: {ADMIN_ID}")
    print("=" * 60)
    _install_global_handlers()
    user_steps.update(load_steps_saved())
    
    for fn in (oo_auto_refresh, dz_auto_refresh, steps_saver_worker,
               reset_steps_worker, _proxy_proactive_rotate, oo_auto_claim_72gb_worker):
        threading.Thread(target=fn, daemon=True, name=fn.__name__).start()
        
    print("✅ البوت يعمل...")
    while not _stop_threads.is_set():
        try:
            await _polling_supervisor()
        except Exception as e:
            logging.error(f"[MAIN] {type(e).__name__}: {e}", exc_info=True)
        if not _stop_threads.is_set():
            await asyncio.sleep(5)

def _run_forever():
    while True:
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            logging.warning("[RUN] ⚠️ Ctrl+C — restart in 2s...")
            try: save_steps()
            except: pass
            time.sleep(2)
        except Exception as e:
            logging.error(f"[RUN] ❌ asyncio.run crashed: {type(e).__name__}: {e}", exc_info=True)
            try: save_steps()
            except: pass
            time.sleep(5)

if __name__ == "__main__":
    _run_forever()
