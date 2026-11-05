# -*- coding: utf-8 -*-
"""
⚡  MOODY BOT — DJEZZY ONLY
"""
import requests, time, json, threading, logging, sys, os, html, random, string
import urllib3
from datetime import datetime, timedelta, timezone
from requests.adapters import HTTPAdapter
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("moody_bot")

# ═══════════════════════════ CONFIG ═══════════════════════════
BOT_TOKEN = "7924355653:AAHeIAyfFwEP1L-UtIGmnwo31PXzFWZsjxE"
ADMIN_ID = 6860937572
PROOF_CHANNEL_ID = "@ifoekdjdh"
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# ══════════════ PROXY CONFIG (OxyLabs Residential DZ) ══════════════
OXYLABS_USER = "customer-resi_0614e541-cc-dz-city-algiers"
OXYLABS_PASS = "GfOR31Pbb6~G"
OXYLABS_HOST = "pr.oxylabs.io:7777"
OXYLABS_SESSTIME = 9

DZ_PROXY_FILE = Path("dz_proxy.json")

# ══════════════ DJEZZY CONSTANTS ══════════════
DJ_CLIENT_ID = "87pIExRhxBb3_wGsA5eSEfyATloa"
DJ_CLIENT_SECRET = "uf82p68Bgisp8Yg1Uz8Pf6_v1XYa"
DJ_BASE_URL = "https://apim.djezzy.dz/mobile-api"

# ══════════════ FAST SESSION ══════════════
_tg_session = requests.Session()
_tg_session.mount("https://", HTTPAdapter(pool_connections=100, pool_maxsize=100))

# ══════════════ STATE ══════════════
DATA_FILE = "bot_data.json"
_lock, _save_lock = threading.Lock(), threading.Lock()
_save_pending = {"flag": False}
_users, _sessions = {}, {}
_bot_stats = {"users": 0, "activations": 0}
_maintenance = False
_forced_channels = []
_otp_cooldown, _otp_cooldown_lock = {}, threading.Lock()
_user_locks, _user_locks_guard = {}, threading.Lock()

def _get_user_lock(cid):
    with _user_locks_guard:
        if cid not in _user_locks:
            _user_locks[cid] = threading.Lock()
        return _user_locks[cid]

def _check_otp_cooldown(cid):
    now = time.time()
    with _otp_cooldown_lock:
        last = _otp_cooldown.get(cid, 0)
        if now - last < 60:
            return int(60 - (now - last))
        _otp_cooldown[cid] = now
    return 0

def _do_save():
    with _save_lock:
        try:
            data = {
                "users": {str(k): v for k, v in _users.items()},
                "stats": _bot_stats,
                "maintenance": _maintenance,
                "channels": _forced_channels,
            }
            tmp = DATA_FILE + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
            os.replace(tmp, DATA_FILE)
            _save_pending["flag"] = False
        except Exception:
            pass

def _save_async():
    if _save_pending["flag"]:
        return
    _save_pending["flag"] = True
    threading.Thread(target=lambda: (time.sleep(1), _do_save()), daemon=True).start()

def _load_from_disk():
    global _users, _bot_stats, _maintenance, _forced_channels
    if not os.path.exists(DATA_FILE):
        _forced_channels = [
            {"id": "@kfodoedjtu546m", "name": "قناة البوت الرسمية", "url": "https://t.me/kfodoedjtu546m"}
        ]
        return
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        _users = {int(k): v for k, v in data.get("users", {}).items()}
        _bot_stats = data.get("stats", {"users": 0, "activations": 0})
        _maintenance = data.get("maintenance", False)
        _forced_channels = data.get("channels", [])
        if not _forced_channels:
            _forced_channels = [
                {"id": "@kfodoedjtu546m", "name": "قناة البوت الرسمية", "url": "https://t.me/kfodoedjtu546m"}
            ]
    except Exception:
        pass

def get_user(cid):
    with _lock:
        return dict(_users.get(cid)) if _users.get(cid) else None

def save_user(cid, data):
    with _lock:
        if cid not in _users:
            _users[cid] = {}
            _bot_stats["users"] += 1
        changed = False
        for k, v in data.items():
            if v is not None and _users[cid].get(k) != v:
                _users[cid][k] = v
                changed = True
    if changed:
        _save_async()

def delete_user(cid):
    with _lock:
        _users.pop(cid, None)
    _save_async()

def get_session(cid):
    with _lock:
        return dict(_sessions.get(cid)) if _sessions.get(cid) else {}

def set_session(cid, data):
    with _lock:
        if cid not in _sessions:
            _sessions[cid] = {}
        _sessions[cid].update({k: v for k, v in data.items() if v is not None})

def clear_session(cid):
    with _lock:
        _sessions.pop(cid, None)

def mask_phone(m):
    if not m:
        return "—"
    s = str(m).strip()
    if s.startswith("213") and len(s) == 12:
        s = "0" + s[3:]
    return s[:2] + "xxxxxxx" + s[-2:] if len(s) >= 8 else s

def get_user_display(cid):
    u = get_user(cid) or {}
    return f"@{u['username']}" if u.get("username") else (u.get("first_name") or "غير معروف")

# ══════════════ TELEGRAM HELPERS ══════════════
def _fmt_rows(rows):
    formatted = []
    for row in rows:
        new_row = []
        for btn in row:
            if isinstance(btn, dict):
                new_row.append(btn)
            elif isinstance(btn, (tuple, list)):
                d = {"text": str(btn[0]), "callback_data": str(btn[1])}
                new_row.append(d)
        formatted.append(new_row)
    return formatted

def tg_request(method, **kwargs):
    try:
        return _tg_session.post(f"{TELEGRAM_API}/{method}", json=kwargs, timeout=5).json()
    except Exception:
        return None

def tg_send(cid, text, keyboard=None):
    payload = {"chat_id": cid, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    if keyboard is not None:
        payload["reply_markup"] = keyboard
    return tg_request("sendMessage", **payload)

def tg_inline(cid, text, rows):
    return tg_send(cid, text, {"inline_keyboard": _fmt_rows(rows)})

def tg_edit(cid, msg_id, text, rows=None):
    payload = {"chat_id": cid, "message_id": msg_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    if rows is not None:
        payload["reply_markup"] = {"inline_keyboard": _fmt_rows(rows)}
    return tg_request("editMessageText", **payload)

def tg_answer_cb(cb_id, text=None, show_alert=False):
    payload = {"callback_query_id": cb_id}
    if text:
        payload["text"] = text
        if show_alert:
            payload["show_alert"] = True
    return tg_request("answerCallbackQuery", **payload)

def send_proof(provider, user_display, phone, action):
    masked = mask_phone(phone)
    msg = (
        f"<b>🎯 إشعار تفعيل جديد</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🌐 <b>الشبكة :</b> {provider}\n"
        f"👤 <b>المستخدم :</b> {user_display}\n"
        f"📱 <b>الرقم :</b> <code>{masked}</code>\n"
        f"📦 <b>الخدمة :</b> {action}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"⚡ <i>تمت العملية بنجاح بواسطة بوت مودي</i>"
    )
    tg_send(PROOF_CHANNEL_ID, msg)

# ═══════════════ Proxy Management ═══════════════
_current_session = ["".join(random.choices(string.ascii_lowercase + string.digits, k=8))]
_proxy_lock = threading.Lock()
_last_rotate = [0.0]
ROTATE_COOLDOWN = 2
_fail_count = [0]
_fail_until = [0.0]
_fail_lock = threading.Lock()

def _load_dz_proxy():
    if DZ_PROXY_FILE.exists():
        try:
            d = json.loads(DZ_PROXY_FILE.read_text(encoding="utf-8"))
            if isinstance(d, dict) and "template" in d:
                return d
        except:
            pass
    default = {"template": f"{OXYLABS_USER}-{{SESSION}}-sesstime-{OXYLABS_SESSTIME}:{OXYLABS_PASS}@{OXYLABS_HOST}"}
    _save_dz_proxy(default)
    return default

def _save_dz_proxy(d):
    try:
        DZ_PROXY_FILE.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    except:
        pass

def _build_proxy_url():
    dz = _load_dz_proxy()
    tpl = dz.get("template", "")
    if not tpl or "{SESSION}" not in tpl:
        return None
    with _proxy_lock:
        sess = _current_session[0]
    return f"http://{tpl.replace('{SESSION}', sess)}"

def _rotate_session(force=False):
    with _proxy_lock:
        now = time.time()
        if not force and now - _last_rotate[0] < ROTATE_COOLDOWN:
            return
        _last_rotate[0] = now
        _current_session[0] = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

def _should_use_proxy():
    with _fail_lock:
        return time.time() > _fail_until[0]

def _mark_proxy_failed():
    with _fail_lock:
        _fail_count[0] += 1
        if _fail_count[0] >= 5:
            _fail_until[0] = time.time() + 60
            _fail_count[0] = 0
    _rotate_session(force=True)

def _mark_proxy_success():
    with _fail_lock:
        _fail_count[0] = 0
        _fail_until[0] = 0.0

# ══════════════ HTTP REQUEST ══════════════
def make_http_request(method, url, timeout=8, **kwargs):
    use_proxy = _should_use_proxy()
    proxy_url = _build_proxy_url() if use_proxy else None
    proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None

    try:
        resp = requests.request(method, url, timeout=(4, timeout), verify=False, proxies=proxies, **kwargs)
        if use_proxy:
            _mark_proxy_success()
        _rotate_session()
        return resp
    except (requests.exceptions.ProxyError, requests.exceptions.ConnectionError) as e:
        logger.warning(f"Proxy Error: {e}")
        if use_proxy:
            _mark_proxy_failed()
            try:
                return requests.request(method, url, timeout=(4, timeout), verify=False, **kwargs)
            except Exception:
                return None
        return None
    except Exception as e:
        logger.error(f"HTTP Error: {e}")
        return None

# ══════════════ DJEZZY LOGIC ══════════════
def dj_req_otp(msisdn):
    url = f"{DJ_BASE_URL}/oauth2/registration"
    params = {'msisdn': msisdn, 'client_id': DJ_CLIENT_ID, 'scope': "smsotp"}
    payload = {"consent-agreement": [{"marketing-notifications": False}], "is-consent": True}
    headers = {'User-Agent': "MobileApp/3.0.7", 'Accept': "application/json", 'Content-Type': "application/json"}
    r = make_http_request("POST", url, headers=headers, params=params, json=payload)
    return bool(r and r.status_code in [200, 201, 202])

def dj_login_otp(mobile, otp):
    payload = {
        'otp': otp, 'mobileNumber': mobile, 'scope': "djezzyAppV2",
        'client_id': DJ_CLIENT_ID, 'client_secret': DJ_CLIENT_SECRET, 'grant_type': "mobile",
    }
    hdrs = {'User-Agent': "MobileApp/3.0.7", 'Content-Type': "application/x-www-form-urlencoded"}
    r = make_http_request("POST", f"{DJ_BASE_URL}/oauth2/token", headers=hdrs, data=payload)
    if r and r.status_code == 200:
        return f"Bearer {r.json().get('access_token')}"
    return None

def dj_get_balance(token, phone):
    h = {'User-Agent': "MobileApp/3.0.7", 'Accept': "application/json", 'authorization': token}
    r = make_http_request("GET", f"{DJ_BASE_URL}/api/v1/subscribers/main-balance/{phone}", headers=h)
    if r and r.status_code == 200:
        return r.json()
    return None

def dj_activate_6gb(token, phone):
    h = {'User-Agent': "MobileApp/3.0.7", 'Accept': "application/json", 'Content-Type': "application/json", 'authorization': token}
    url = f"{DJ_BASE_URL}/api/v1/services/walk/activate-reward/{phone}"
    r = make_http_request("POST", url, headers=h, json={"packageCode": "GIFTWALKWIN6GDAY"})
    if not r:
        return {"error": "net"}
    if r.status_code in [200, 201, 202]:
        return {"success": True}
    if r.status_code in [400, 409, 500]:
        return {"error": "already_used"}
    return {"error": "already_used"}

# ══════════════ FORCED SUBSCRIPTION ══════════════
def send_forced_sub(cid):
    if cid == ADMIN_ID or not _forced_channels:
        return False
    
    ch = _forced_channels[0]
    try:
        ch_id = ch.get("id") if isinstance(ch, dict) else ch
        r = requests.get(f"{TELEGRAM_API}/getChatMember", params={"chat_id": ch_id, "user_id": cid}, timeout=4).json()
        if r.get("ok") and r.get("result", {}).get("status") in ["creator", "administrator", "member"]:
            return False
    except Exception:
        pass

    url = ch.get("url", f"https://t.me/{str(ch).replace('@', '')}") if isinstance(ch, dict) else f"https://t.me/{str(ch).replace('@', '')}"
    txt = (
        "🔒 <b>عذراً عزيزي، للتمكن من استخدام البوت</b>\n"
        "يجب عليك الاشتراك في قناتنا الرسمية أولاً 👇"
    )
    rows = [
        [{"text": "📢 الاشتراك في القناة", "url": url}],
        [{"text": "✅ تحقق من الاشتراك", "callback_data": "check_sub"}]
    ]
    tg_inline(cid, txt, rows)
    return True

# ══════════════ WELCOME & MENUS ══════════════
def get_welcome_text():
    return (
        "🌟 <b>أهلاً بك في بوت مودي</b>\n"
        "━━━━━━━━━━━━━━━\n"
        "نظام آلي متكامل لتفعيل عروض جيزي 🇩🇿\n\n"
        "📌 <i>يرجى إرسال رقم هاتفك (جيزي 07) للبدء:</i>"
    )

def show_main_menu(cid, user):
    if not user or not user.get("msisdn"):
        set_session(cid, {"state": "awaiting_phone"})
        return tg_send(cid, "📱 <i>أرسل رقم هاتفك (07..) للبدء:</i>")
    txt = (
        f"👋 <b>مرحباً بك مجدداً</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📱 <b>الرقم :</b> <code>{mask_phone(user.get('msisdn'))}</code>\n"
        f"🟢 <b>الحالة :</b> متصل\n"
        f"━━━━━━━━━━━━━━━\n"
        f"<i>اختر الخدمة المطلوبة من الأسفل 👇</i>"
    )
    rows = [
        [("🎁 تفعيل 6 جيقا (24 ساعة)", "dj_confirm_6gb")],
        [("💰 رصيدي", "dj_check_balance")],
        [("🚪 تسجيل الخروج", "logout")],
    ]
    if cid == ADMIN_ID:
        rows.append([("⚙️ لوحة التحكم", "admin_panel")])
    tg_inline(cid, txt, rows)

# ══════════════ ACTIONS ══════════════
def cb_dj_balance(cid, user, msg_id, cb_id):
    tg_answer_cb(cb_id, "⏳ جاري الجلب...")
    tg_edit(cid, msg_id, "💰 <i>جاري جلب الرصيد...</i>")
    res = dj_get_balance(user['token'], user['msisdn'])
    bal = f"{res['data']['mainBalance']:.2f} دج" if res and 'data' in res else "0.00 دج"
    tg_edit(cid, msg_id, f"💳 <b>رصيدك الحالي:</b> {bal}", [[("🔄 تحديث", "dj_check_balance"), ("🔙 رجوع", "menu")]])

def cb_dj_6gb(cid, user, msg_id, cb_id):
    tg_edit(cid, msg_id, "⚡ <i>جاري تفعيل العرض، يرجى الانتظار...</i>")

    def _do():
        lock = _get_user_lock(cid)
        if not lock.acquire(timeout=15):
            return
        try:
            u = get_user(cid)
            res = dj_activate_6gb(u['token'], u['msisdn'])
            
            if res.get("success"):
                with _lock:
                    _bot_stats["activations"] += 1
                _save_async()
                tg_answer_cb(cb_id, "🎉 مبروك! تم تفعيل العرض بنجاح", show_alert=True)
                tg_edit(cid, msg_id, "🎉 <b>مبروك عزيزي!</b>\n\nتم تفعيل عرض 6 جيقا بنجاح.\n⏰ صالح لمدة 24 ساعة.", [[("🏠 القائمة الرئيسية", "menu")]])
                send_proof("Djezzy", get_user_display(cid), u['msisdn'], "6GB / 24H")
            
            elif res.get("error") == "already_used":
                # ══════════════ حساب توقيت الجزائر حتى 12:00 منتصف الليل (00:00) ══════════════
                dz_tz = timezone(timedelta(hours=1))
                now_dz = datetime.now(dz_tz)
                
                # الهدف هو منتصف الليل (00:00)
                target = now_dz.replace(hour=0, minute=0, second=0, microsecond=0)
                
                # إذا كنا في وقت متأخر من اليوم (مثلاً 14:00)، سيكون الهدف هو منتصف ليل اليوم الموالي
                if now_dz >= target:
                    target += timedelta(days=1)
                
                delta = target - now_dz
                hours, remainder = divmod(delta.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                
                alert_text = (
                    f"⚠️ راك مفعل من قبل!\n\n"
                    f"يرجى الانتظار حتى الساعة 12:00 منتصف الليل (بتوقيت الجزائر 🇩🇿)\n"
                    f"⏳ الوقت المتبقي: {hours:02d} ساعة و {minutes:02d} دقيقة"
                )
                tg_answer_cb(cb_id, alert_text, show_alert=True)
                tg_edit(cid, msg_id, f"⚠️ <b>راك مفعل من قبل!</b>\n\nالعرض مسجل مسبقاً على هذا الرقم.\n🔁 يرجى المحاولة بعد الساعة 12:00 منتصف الليل.", [[("🔙 رجوع", "menu")]])
            
            else:
                # في حال كان هناك مشكل في الاتصال (net)، نعرض البطاقة الزمنية أيضاً لتفادي رسالة الفشل المزعجة
                dz_tz = timezone(timedelta(hours=1))
                now_dz = datetime.now(dz_tz)
                target = now_dz.replace(hour=0, minute=0, second=0, microsecond=0)
                if now_dz >= target:
                    target += timedelta(days=1)
                
                delta = target - now_dz
                hours, remainder = divmod(delta.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                
                alert_text = (
                    f"⚠️ العرض غير متاح حالياً!\n\n"
                    f"يرجى الانتظار حتى الساعة 12:00 منتصف الليل (بتوقيت الجزائر 🇩🇿)\n"
                    f"⏳ الوقت المتبقي: {hours:02d} ساعة و {minutes:02d} دقيقة"
                )
                tg_answer_cb(cb_id, alert_text, show_alert=True)
                tg_edit(cid, msg_id, f"⚠️ <b>العرض غير متاح حالياً!</b>\n\nيرجى المحاولة بعد الساعة 12:00 منتصف الليل.", [[("🔙 رجوع", "menu")]])
        finally:
            lock.release()

    threading.Thread(target=_do, daemon=True).start()

# ══════════════ OTP SENDER UI ══════════════
def send_otp_ui(cid, msisdn, msg_id=None):
    set_session(cid, {"state": "awaiting_otp", "msisdn": msisdn, "provider": "djezzy", "otp_time": time.time()})
    btns = [[("🔄 إعادة المحاولة", "retry_otp"), ("❌ إلغاء", "cancel_op")]]
    
    txt = (
        "📩 <b>تم إرسال طلب الرمز</b>\n"
        "يرجى إدخال رمز الـ OTP (6 أرقام) هنا:\n"
        "⚠️ <i>لديك 3 دقائق لإدخال الرمز.</i>"
    )

    if msg_id:
        tg_edit(cid, msg_id, txt, btns)
    else:
        res = tg_send(cid, txt, {"inline_keyboard": _fmt_rows(btns)})
        if res and res.get("ok"):
            msg_id = res["result"]["message_id"]

    def _bg():
        res = dj_req_otp(msisdn)
        if not res:
            txt_err = "❌ <b>فشل الإرسال.</b>\nتأكد من الرقم أو جرب الإعادة لاحقاً."
            if msg_id: tg_edit(cid, msg_id, txt_err, btns)
            else: tg_send(cid, txt_err)

    threading.Thread(target=_bg, daemon=True).start()

# ══════════════ CALLBACK HANDLER ══════════════
def handle_callback(cid, msg_id, data, cb_id):
    try:
        user = get_user(cid)
        if data == "check_sub":
            tg_answer_cb(cb_id, "⏳ جاري التحقق...")
            if send_forced_sub(cid):
                return
            tg_edit(cid, msg_id, "✅ <b>تم التحقق بنجاح!</b>")
            if user and user.get("msisdn"):
                show_main_menu(cid, user)
            else:
                set_session(cid, {"state": "awaiting_phone"})
                tg_send(cid, get_welcome_text())
            return
        if send_forced_sub(cid):
            return
        
        if data == "retry_otp":
            sess = get_session(cid)
            if sess and sess.get("msisdn") and sess.get("provider"):
                wait = _check_otp_cooldown(cid)
                if wait > 0:
                    tg_answer_cb(cb_id, f"⚠️ يرجى الانتظار {wait} ثانية قبل إعادة الإرسال.", show_alert=True)
                    return
                tg_answer_cb(cb_id, "🔄 إعادة الإرسال...")
                send_otp_ui(cid, sess.get("msisdn"), msg_id=msg_id)
            return
            
        if data == "cancel_op":
            tg_answer_cb(cb_id, "❌ تم الإلغاء")
            clear_session(cid)
            return tg_edit(cid, msg_id, get_welcome_text())
            
        if data == "menu":
            tg_answer_cb(cb_id)
            if not user or not user.get("msisdn"):
                set_session(cid, {"state": "awaiting_phone"})
                return tg_edit(cid, msg_id, "📱 أرسل رقمك (07..) للبدء:")
            return show_main_menu(cid, user)
            
        if data == "logout":
            tg_answer_cb(cb_id, "👋")
            delete_user(cid)
            clear_session(cid)
            set_session(cid, {"state": "awaiting_phone"})
            return tg_edit(cid, msg_id, get_welcome_text())
        
        if cid == ADMIN_ID:
            if data == "admin_panel":
                tg_answer_cb(cb_id)
                return show_admin_panel(cid, msg_id)
            if data == "admin_maint":
                global _maintenance
                _maintenance = not _maintenance
                _save_async()
                tg_answer_cb(cb_id, "✅")
                return show_admin_panel(cid, msg_id)
            if data == "admin_channels":
                tg_answer_cb(cb_id)
                return show_channels_menu(cid, msg_id)
            if data == "admin_add_ch":
                tg_answer_cb(cb_id)
                set_session(cid, {"state": "admin_ch_link"})
                return tg_edit(cid, msg_id, "📢 أرسل رابط القناة:", [[("🔙 إلغاء", "admin_channels")]])
            if data == "admin_del_ch_menu":
                tg_answer_cb(cb_id)
                rows = [[(f"❌ حذف {ch.get('name', 'قناة') if isinstance(ch, dict) else ch}", f"admin_del_ch_{i}")] for i, ch in enumerate(_forced_channels)]
                rows.append([("🔙 رجوع", "admin_channels")])
                return tg_edit(cid, msg_id, "اختر للحذف:", rows)
            if data.startswith("admin_del_ch_"):
                idx = int(data.split("_")[-1])
                if 0 <= idx < len(_forced_channels):
                    del _forced_channels[idx]
                    _save_async()
                    tg_answer_cb(cb_id, "✅")
                    return show_channels_menu(cid, msg_id)
            if data == "admin_broadcast":
                tg_answer_cb(cb_id)
                set_session(cid, {"state": "admin_broadcast_input"})
                return tg_edit(cid, msg_id, "📣 أرسل رسالة الإذاعة:", [[("🔙 إلغاء", "admin_panel")]])
            if data == "admin_stats":
                tg_answer_cb(cb_id)
                txt = f"📊 <b>إحصائيات البوت</b>\n👥 المستخدمون: {_bot_stats.get('users', 0)}\n⚡ التفعيلات: {_bot_stats.get('activations', 0)}"
                return tg_edit(cid, msg_id, txt, [[("🔙 رجوع", "admin_panel")]])
        
        if not user or not user.get("msisdn"):
            return tg_answer_cb(cb_id, "❌ /start")
        if data == "dj_check_balance": return cb_dj_balance(cid, user, msg_id, cb_id)
        if data == "dj_confirm_6gb": return cb_dj_6gb(cid, user, msg_id, cb_id)
        tg_answer_cb(cb_id)
    except Exception as e:
        logger.error(f"CB Error: {e}")

# ══════════════ TEXT HANDLER ══════════════
def handle_text(cid, text):
    try:
        text = text.strip()
        if _maintenance and cid != ADMIN_ID:
            return tg_send(cid, "🔧 البوت في وضع الصيانة حالياً.")
        sess = get_session(cid)
        state = sess.get("state", "")
        user = get_user(cid)
        
        if text.lower() == "/admin" and cid == ADMIN_ID:
            clear_session(cid)
            return show_admin_panel(cid)
            
        if text.lower() in ["/start", "رجوع", "إلغاء", "الغاء", "/menu"]:
            clear_session(cid)
            if send_forced_sub(cid):
                return
            if user and user.get("msisdn"):
                return show_main_menu(cid, user)
            set_session(cid, {"state": "awaiting_phone"})
            return tg_send(cid, get_welcome_text())
        
        if cid == ADMIN_ID:
            if state == "admin_broadcast_input":
                users = list(_users.keys())
                tg_send(cid, f"⏳ جاري الإرسال لـ {len(users)} مستخدم...")
                sent = 0
                for u in users:
                    try:
                        tg_send(u, f"📢 <b>رسالة إدارية:</b>\n\n{text}")
                        sent += 1
                        time.sleep(0.05)
                    except:
                        pass
                tg_send(cid, f"✅ تم الإرسال لـ {sent}")
                clear_session(cid)
                return show_admin_panel(cid)
            if state == "admin_ch_link":
                ch_id = text.strip()
                if "t.me/" in ch_id:
                    ch_id = ch_id.split("t.me/")[-1].strip("/")
                if not ch_id.startswith("@"):
                    ch_id = "@" + ch_id
                set_session(cid, {"state": "admin_ch_name", "tmp_ch_id": ch_id})
                return tg_send(cid, f"✅ المعرف: {html.escape(ch_id)}\nأرسل الاسم:")
            if state == "admin_ch_name":
                ch_name = text.strip()
                ch_id = sess.get("tmp_ch_id")
                _forced_channels.append({"id": ch_id, "name": ch_name, "url": f"https://t.me/{ch_id.replace('@', '')}"})
                _save_async()
                clear_session(cid)
                tg_send(cid, "✅ تم الإضافة!")
                return show_channels_menu(cid)
                
        if state == "awaiting_phone" or (not state and (not user or not user.get("msisdn"))):
            dg = "".join(c for c in text if c.isdigit())
            if len(dg) < 10:
                return tg_send(cid, "❌ <b>رقم غير صحيح.</b>\nيرجى إرسال رقم صحيح:")
            if not dg.startswith("07"):
                return tg_send(cid, "❌ <b>يجب أن يبدأ الرقم بـ 07 (جيزي).</b>\nحاول مجدداً:")
            msisdn = "213" + dg[1:]
            wait = _check_otp_cooldown(cid)
            if wait > 0:
                return tg_send(cid, f"⚠️ يرجى الانتظار {wait} ثانية قبل طلب رمز جديد.")
            send_otp_ui(cid, msisdn)
            return
            
        if state == "awaiting_otp":
            otp_time = sess.get("otp_time", 0)
            if time.time() - otp_time > 180:
                clear_session(cid)
                set_session(cid, {"state": "awaiting_phone"})
                return tg_send(cid, "⏳ <b>انتهت مدة صلاحية الرمز (3 دقائق).</b>\nيرجى إرسال رقمك مجدداً للبدء من جديد.")
            
            if not text.isdigit() or len(text) != 6:
                return tg_send(cid, "❌ <b>الرمز يجب أن يكون 6 أرقام.</b>\nتأكد وحاول مجدداً:")
                
            msisdn = sess.get("msisdn")
            tg_send(cid, "⏳ <i>جاري التحقق من الرمز...</i>")

            def _verify():
                token = dj_login_otp(msisdn, text)
                if not token:
                    return tg_send(cid, "❌ <b>الرمز غير صحيح!</b>\nتأكد من الرمز، أو اضغط (إعادة المحاولة) لطلب رمز جديد.")
                save_user(cid, {"msisdn": msisdn, "provider": "djezzy", "token": token})
                clear_session(cid)
                tg_send(cid, "🎉 <b>تم تسجيل الدخول بنجاح!</b>")
                show_main_menu(cid, get_user(cid))

            threading.Thread(target=_verify, daemon=True).start()
            return
            
        if user and user.get("msisdn"):
            show_main_menu(cid, user)
        else:
            clear_session(cid)
            set_session(cid, {"state": "awaiting_phone"})
            tg_send(cid, get_welcome_text())
    except Exception as e:
        logger.error(f"Text Error: {e}")

# ══════════════ ADMIN PANEL FUNCTIONS ══════════════
def show_admin_panel(cid, msg_id=None):
    txt = "⚙️ <b>لوحة تحكم الأدمن</b>\n━━━━━━━━━━━━━━━"
    rows = [
        [("⚡ حالة البوت: يعمل 🟢", "admin_status")],
        [("🛠️ الصيانة: " + ("مفتوح 🔴" if _maintenance else "مغلق 🟢"), "admin_maint")],
        [("📢 إدارة القنوات (" + str(len(_forced_channels)) + ")", "admin_channels")],
        [("📣 إذاعة عامة", "admin_broadcast")],
        [("📊 إحصائيات", "admin_stats")],
        [("👤 لوحة المستخدم", "menu")],
    ]
    if msg_id:
        tg_edit(cid, msg_id, txt, rows)
    else:
        tg_inline(cid, txt, rows)

def show_channels_menu(cid, msg_id=None):
    txt = f"📢 <b>إدارة القنوات</b>\nلديك {len(_forced_channels)} قناة.\n\n"
    if _forced_channels:
        for i, ch in enumerate(_forced_channels, 1):
            name = html.escape(str(ch.get('name', 'قناة') if isinstance(ch, dict) else ch))
            txt += f"{i}. {name}\n"
    else:
        txt += "لا توجد قنوات مضافة."
    rows = [
        [("➕ إضافة قناة", "admin_add_ch"), ("❌ حذف قناة", "admin_del_ch_menu")],
        [("🔙 رجوع", "admin_panel")],
    ]
    if msg_id:
        tg_edit(cid, msg_id, txt, rows)
    else:
        tg_inline(cid, txt, rows)

# ══════════════ POLLING ══════════════
def polling_loop():
    try:
        requests.post(f"{TELEGRAM_API}/setMyCommands", json={"commands": [
            {"command": "start", "description": "بدء البوت"},
            {"command": "admin", "description": "لوحة التحكم"},
        ]})
        requests.get(f"{TELEGRAM_API}/deleteWebhook", params={"drop_pending_updates": "true"})
    except:
        pass
    offset = None
    while True:
        try:
            r = _tg_session.get(f"{TELEGRAM_API}/getUpdates", params={"timeout": 15, "offset": offset}, timeout=(5, 20))
            data = r.json()
            if data and data.get("ok"):
                for upd in data.get("result", []):
                    offset = upd["update_id"] + 1
                    if msg := upd.get("message"):
                        cid = msg.get("chat", {}).get("id")
                        text = (msg.get("text") or "").strip()
                        if cid and text:
                            if frm := msg.get("from"):
                                save_user(cid, {"first_name": frm.get("first_name"), "username": frm.get("username")})
                            threading.Thread(target=handle_text, args=(cid, text), daemon=True).start()
                    elif cbq := upd.get("callback_query"):
                        msg = cbq.get("message", {})
                        threading.Thread(target=handle_callback, args=(
                            msg.get("chat", {}).get("id"),
                            msg.get("message_id"),
                            cbq.get("data", ""),
                            cbq.get("id"),
                        ), daemon=True).start()
        except Exception:
            time.sleep(0.1)

if __name__ == "__main__":
    _load_from_disk()
    logger.info("Moody Bot Started (Algeria Time 00:00 Sync)")
    polling_loop()
