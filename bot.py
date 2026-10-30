#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""البوت الموحّد — جيزي 🔴 + أوريدو 🟠 + 2Go FREE
   + 🔥 Proxy Pool (Lease System: بروكسي حصري لكل مستخدم)"""
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
NOTIFY_GROUP = "@ifoekdjdh"

DJ_CLIENT_ID = "87pIExRhxBb3_wGsA5eSEfyATloa"
DJ_CLIENT_SECRET = "uf82p68Bgisp8Yg1Uz8Pf6_v1XYa"
DJ_BASE = "https://apim.djezzy.dz/mobile-api"
DJ_HEADERS = {'User-Agent': "MobileApp/3.0.0", 'Accept': "application/json",
              'Content-Type': "application/json", 'accept-language': "fr", 'Connection': 'keep-alive'}
COOLDOWN_2GB = 604800
COOLDOWN_3GB = 604800
DZ_HEADERS = DJ_HEADERS
DZ_BASE_URL = DJ_BASE
PAGE_FOLLOW_TEXT = f"📢 تابع قناتنا: {CHANNEL_LINK}"

OO_BFF = "https://apis.ooredoo.dz/api/ooredoo-bff"
OO_AUTH = "https://apis.ooredoo.dz/api/auth/realms/myooredoo/protocol/openid-connect/token"
OO_CLIENT = "myooredoo-app"
X_VERSION = "1.5.17"                       # 🔧 تم التحديث من 1.5.15
X_VERSION_OTP = "1.5.16"
X_VERSION_NEW = "1.5.17"
X_SIG = "5c7641dbb82cf11066df68afc91541c967640106a95192740b43d51a5ce6777a"
X_SIG_NEW = "c66054ba6166fe08d1a6a702fb10b151102a6f4ef058fcf3d995ee511ff0d267"

# ==================== 🔥 Proxy Pool (Lease System) ====================
EMBEDDED_PROXIES_RAW = [
    "jjontghpdh36:hxr0bkngffsb1mp@104.207.51.196:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@216.26.248.195:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@45.3.44.47:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@209.50.190.53:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@216.26.243.33:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@216.26.255.157:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@65.111.24.108:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@104.207.51.28:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@216.26.225.68:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@104.207.36.192:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@65.111.8.155:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@45.3.36.187:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@104.207.59.142:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@65.111.15.134:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@216.26.244.206:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@65.111.9.144:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@104.207.39.38:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@193.56.28.245:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@216.26.240.80:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@45.3.51.89:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@65.111.3.110:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@45.3.39.243:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@216.26.239.51:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@45.3.50.95:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@209.50.167.115:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@216.26.239.172:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@104.207.60.171:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@45.3.62.79:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@65.111.25.184:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@209.50.184.56:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@45.3.43.88:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@216.26.249.112:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@209.50.186.97:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@104.207.47.112:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@216.26.249.194:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@65.111.21.110:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@45.3.45.145:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@209.50.175.249:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@104.207.53.177:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@193.56.28.203:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@65.111.6.131:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@65.111.2.66:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@104.207.59.234:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@65.111.8.82:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@65.111.7.1:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@216.26.227.221:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@209.50.187.248:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@216.26.241.216:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@104.207.63.40:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@209.50.181.8:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@65.111.4.25:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@45.3.33.4:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@65.111.12.78:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@216.26.233.24:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@104.207.59.13:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@45.3.53.29:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@151.123.177.94:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@104.207.48.57:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@209.50.184.48:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@217.181.92.169:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@209.50.191.235:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@65.111.1.70:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@216.26.239.177:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@65.111.12.10:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@65.111.23.38:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@104.207.42.210:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@216.26.236.143:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@45.3.55.75:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@104.207.53.173:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@216.26.225.156:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@216.26.240.232:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@65.111.27.180:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@104.207.63.175:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@65.111.26.170:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@216.26.240.246:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@216.26.227.20:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@45.3.48.208:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@45.3.49.205:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@104.207.46.202:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@104.207.52.99:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@216.26.248.220:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@216.26.254.49:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@104.207.56.142:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@216.26.244.240:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@209.50.168.36:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@65.111.14.201:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@209.50.176.55:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@209.50.184.142:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@216.26.232.38:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@209.50.174.144:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@104.207.36.71:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@65.111.3.54:3129",
    "jjontghpdh36:hxr0bkngffsb1mp@45.3.46.42:3129",
]

PROXY_MAX_CONCURRENT_PER = 2
PROXY_FAIL_THRESHOLD = 3
PROXY_FAIL_COOLDOWN = 300
PROXY_HEALTH_INTERVAL = 900
PROXY_HEALTH_TIMEOUT = 10
PROXY_PICK_TIMEOUT = 8
PROXY_LEASE_TTL = 900              # 🆕 15 دقيقة حجز أقصى لكل مستخدم

def _normalize_proxy(raw):
    raw = (raw or "").strip()
    if not raw: return None
    if raw.startswith(("http://", "https://")): return raw
    return f"http://{raw}"

class _ProxyEntry:
    __slots__ = ("url","name","source","sem","in_flight","total_uses",
                 "success_count","fail_count","consecutive_fails",
                 "last_used","disabled_until","last_check","status",
                 "owner_msisdn","lease_until")
    def __init__(self, url, name=None, source="manual"):
        self.url = url
        self.name = name or url
        self.source = source
        self.sem = threading.BoundedSemaphore(PROXY_MAX_CONCURRENT_PER)
        self.in_flight = 0
        self.total_uses = 0
        self.success_count = 0
        self.fail_count = 0
        self.consecutive_fails = 0
        self.last_used = 0.0
        self.disabled_until = 0.0
        self.last_check = 0.0
        self.status = "unknown"
        self.owner_msisdn = None
        self.lease_until = 0.0

    def is_available(self, now=None):
        now = now or time.time()
        return self.disabled_until <= now and self.status != "fail"

    def is_leased(self, now=None):
        now = now or time.time()
        return self.owner_msisdn is not None and self.lease_until > now

    def is_free(self, now=None):
        return self.is_available(now) and not self.is_leased(now)

class ProxyPool:
    def __init__(self):
        self._entries = {}
        self._leases = {}
        self._lock = threading.RLock()

    def add(self, url, name=None, source="manual"):
        u = _normalize_proxy(url)
        if not u: return None
        with self._lock:
            e = self._entries.get(u)
            if e: return e
            e = _ProxyEntry(u, name, source)
            self._entries[u] = e
            return e

    def remove(self, url):
        u = _normalize_proxy(url)
        if not u: return
        with self._lock:
            e = self._entries.pop(u, None)
            if e and e.owner_msisdn:
                self._leases.pop(e.owner_msisdn, None)

    def all(self):
        with self._lock:
            return list(self._entries.values())

    def healthy_count(self):
        now = time.time()
        return sum(1 for e in self._entries.values() if e.is_available(now))

    def lease_stats(self):
        now = time.time()
        with self._lock:
            total = len(self._entries)
            leased = sum(1 for e in self._entries.values() if e.is_leased(now))
            free = sum(1 for e in self._entries.values() if e.is_free(now))
            failed = sum(1 for e in self._entries.values() if not e.is_available(now))
            return {"total": total, "leased": leased, "free": free, "failed": failed}

    def _pick_free(self, exclude=None):
        exclude = set(exclude or [])
        now = time.time()
        with self._lock:
            cands = [e for e in self._entries.values()
                     if e.is_free(now) and e.url not in exclude]
        if not cands: return None
        cands.sort(key=lambda e: (e.total_uses, e.last_used))
        return cands[0]

    def acquire_for_session(self, msisdn, exclude=None, timeout=PROXY_PICK_TIMEOUT):
        if not msisdn:
            return self.acquire(exclude=exclude, timeout=timeout)
        deadline = time.time() + timeout
        tried = set(exclude or [])
        while time.time() < deadline:
            with self._lock:
                url = self._leases.get(msisdn)
                if url:
                    e = self._entries.get(url)
                    if e and e.is_available():
                        if e.sem.acquire(blocking=False):
                            e.lease_until = time.time() + PROXY_LEASE_TTL
                            e.in_flight += 1
                            e.total_uses += 1
                            e.last_used = time.time()
                            return e
                        time.sleep(0.05)
                        continue
                    else:
                        self._leases.pop(msisdn, None)
            e = self._pick_free(exclude=tried)
            if e is None:
                time.sleep(0.2); continue
            if e.sem.acquire(blocking=False):
                with self._lock:
                    e.owner_msisdn = msisdn
                    e.lease_until = time.time() + PROXY_LEASE_TTL
                    e.in_flight += 1
                    e.total_uses += 1
                    e.last_used = time.time()
                    self._leases[msisdn] = e.url
                logging.info(f"[PROXY-LEASE] 🔒 {msisdn} → {e.url.split('@')[-1]}")
                return e
            tried.add(e.url)
            time.sleep(0.05)
        return None

    def release_session(self, msisdn, reason="finished"):
        if not msisdn: return False
        with self._lock:
            url = self._leases.pop(msisdn, None)
            if not url: return False
            e = self._entries.get(url)
            if not e: return False
            e.owner_msisdn = None
            e.lease_until = 0.0
        logging.info(f"[PROXY-LEASE] 🔓 {msisdn} released ({reason})")
        return True

    def cleanup_expired_leases(self):
        now = time.time()
        freed = 0
        with self._lock:
            for msisdn, url in list(self._leases.items()):
                e = self._entries.get(url)
                expired = (e is None) or (not e.is_available(now)) or (e.lease_until <= now)
                if expired:
                    self._leases.pop(msisdn, None)
                    if e:
                        e.owner_msisdn = None
                        e.lease_until = 0.0
                    freed += 1
        if freed:
            logging.info(f"[PROXY-LEASE] ⏱️ cleanup: freed {freed} expired leases")
        return freed

    def acquire(self, sticky_url=None, exclude=None, timeout=PROXY_PICK_TIMEOUT):
        exclude = set(exclude or [])
        deadline = time.time() + timeout
        while time.time() < deadline:
            target = None
            with self._lock:
                if sticky_url:
                    u = _normalize_proxy(sticky_url)
                    e = self._entries.get(u) if u else None
                    if e and e.is_free() and e.url not in exclude:
                        target = e
                if target is None:
                    cands = [e for e in self._entries.values()
                             if e.is_free() and e.url not in exclude]
                    if cands:
                        cands.sort(key=lambda e: (e.in_flight, e.total_uses, e.last_used))
                        target = cands[0]
            if target is None:
                time.sleep(0.15); continue
            if target.sem.acquire(blocking=False):
                with self._lock:
                    target.in_flight += 1
                    target.total_uses += 1
                    target.last_used = time.time()
                return target
            time.sleep(0.05)
        return None

    def release(self, entry, success, reason=""):
        if entry is None: return
        with self._lock:
            entry.in_flight = max(0, entry.in_flight - 1)
            if success:
                entry.success_count += 1
                entry.consecutive_fails = 0
                entry.status = "ok"
            else:
                entry.fail_count += 1
                entry.consecutive_fails += 1
                if entry.consecutive_fails >= PROXY_FAIL_THRESHOLD:
                    entry.status = "fail"
                    entry.disabled_until = time.time() + PROXY_FAIL_COOLDOWN
                    if entry.owner_msisdn:
                        self._leases.pop(entry.owner_msisdn, None)
                        entry.owner_msisdn = None
                        entry.lease_until = 0.0
                    logging.warning(f"[PROXY] ❌ تعطيل {entry.url[:40]}... ({reason})")
        try: entry.sem.release()
        except ValueError: pass

    def update_health(self, url, ok):
        u = _normalize_proxy(url)
        if not u: return
        with self._lock:
            e = self._entries.get(u)
            if not e: return
            e.last_check = time.time()
            if ok:
                e.status = "ok"; e.consecutive_fails = 0; e.disabled_until = 0.0
            else:
                e.status = "fail"
                e.disabled_until = time.time() + PROXY_FAIL_COOLDOWN

_proxy_pool = ProxyPool()

# ==================== Sticky (احتياطي) ====================
_msisdn_proxy = {}
_msisdn_proxy_lock = threading.Lock()
STICKY_PROXY_TTL = 900

def _set_sticky_proxy(msisdn, url):
    if not msisdn: return
    with _msisdn_proxy_lock:
        _msisdn_proxy[msisdn] = (url, time.time())

def _get_sticky_proxy(msisdn):
    if not msisdn: return None
    with _msisdn_proxy_lock:
        v = _msisdn_proxy.get(msisdn)
        if v and time.time() - v[1] < STICKY_PROXY_TTL:
            return v[0]
    return None

def _clear_sticky_proxy(msisdn):
    with _msisdn_proxy_lock:
        _msisdn_proxy.pop(msisdn, None)

def _release_lease_for(msisdn, reason="finished"):
    if not msisdn: return
    try:
        _proxy_pool.release_session(msisdn, reason)
        _clear_sticky_proxy(msisdn)
    except Exception as e:
        logging.error(f"[LEASE-RELEASE] {e}")

# API متوافقة
def _should_use_proxy(): return True
def _get_active_proxy():
    e = _proxy_pool._pick_free() or _proxy_pool.acquire(timeout=2)
    return e.url if e else None
def _build_proxy_url(): return _get_active_proxy() or ""
def _rotate_proxy_session(force=False): return False
def _wait_proxy_slot(): pass
def _mark_proxy_failed(proxy_url=None, reason="unknown"):
    if proxy_url:
        u = _normalize_proxy(proxy_url)
        e = _proxy_pool._entries.get(u) if u else None
        if e: _proxy_pool.release(e, success=False, reason=reason)
def _mark_proxy_success(): pass

_PROXY_REQUEST_GATE = threading.BoundedSemaphore(value=200)

# ==================== فحص البروكسي (Ooredoo + Djezzy الحقيقي) ====================
def proxy_check_sync(url):
    u = _normalize_proxy(url)
    if not u: return {"ok": False, "error": "invalid"}
    try:
        s = requests.Session(); s.verify = False
        s.proxies = {"http": u, "https": u}
        # 1) Ooredoo
        oo_err = "unknown"
        try:
            r = s.get(
                "https://apis.ooredoo.dz/api/ooredoo-bff/users/status?msisdn=213555000000",
                headers={"User-Agent": "Dart/3.11 (dart:io)",
                         "x-version": X_VERSION,
                         "x-signature": X_SIG,
                         "platform": "android",
                         "x-platform-origin": "mobile-android"},
                timeout=PROXY_HEALTH_TIMEOUT, allow_redirects=False)
            txt = (r.text or "")[:400].lstrip().lower()
            if any(x in txt for x in ("<!doctype", "<html", "cloudflare", "just a moment")):
                oo_err = "ooredoo_html_block"
            elif r.status_code in (200, 400, 401, 403, 404):
                return {"ok": True, "ip": "ooredoo_ok", "target": "ooredoo"}
            else:
                oo_err = f"ooredoo_{r.status_code}"
        except Exception as e:
            oo_err = str(e)[:60]
        # 2) Djezzy
        try:
            r2 = s.get(
                f"https://apim.djezzy.dz/mobile-api/oauth2/registration"
                f"?msisdn=213555000000&client_id={DJ_CLIENT_ID}&scope=smsotp",
                headers={"User-Agent": "MobileApp/3.0.0"},
                timeout=PROXY_HEALTH_TIMEOUT)
            txt2 = (r2.text or "")[:400].lstrip().lower()
            if any(x in txt2 for x in ("<!doctype", "<html")):
                return {"ok": False, "error": f"all_block: {oo_err}|djezzy_html"}
            if r2.status_code < 500:
                return {"ok": True, "ip": "djezzy_ok", "target": "djezzy"}
            return {"ok": False, "error": f"djezzy_{r2.status_code}"}
        except Exception as e:
            return {"ok": False, "error": f"all_fail: {oo_err[:40]}|{str(e)[:40]}"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:80]}
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
_PROFILE_CACHE = {}

def _new_session(headers=None, use_proxy=False):
    s = requests.Session()
    a = requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=20, max_retries=1, pool_block=False)
    s.mount('http://', a); s.mount('https://', a)
    s.verify = False
    if headers: s.headers.update(headers)
    return s

def activate_proxy_url(url, name=None, ip=None):
    u = _normalize_proxy(url)
    if not u: return None
    now = time.time()
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    proxy_name = name or f"Proxy-{random.randint(1000,9999)}"
    db_query("INSERT OR IGNORE INTO proxies "
             "(name, url, is_default, active, status, last_check, added_date, source) "
             "VALUES (?,?,?,?,?,?,?,?)",
             (proxy_name, u, 0, 1, "ok", now, stamp, "manual"))
    db_query("UPDATE proxies SET active=1, status='ok', last_check=? WHERE url=?", (now, u))
    _proxy_pool.add(u, proxy_name, "manual")
    return proxy_name

# ==================== 🔒 _oo_req مع Lease ====================
def _oo_req(method, url, headers, content=b"", timeout=12, use_proxy=True, msisdn=None):
    data = content if isinstance(content, bytes) else content.encode()
    if not use_proxy:
        try:
            s = _new_session(use_proxy=False)
            r = s.request(method, url, headers=headers, data=data,
                          timeout=timeout, allow_redirects=False)
            try: body = r.json()
            except: body = {"_raw": r.text[:500]}
            return r.status_code, dict(r.headers), body
        except Exception as e:
            return 0, {}, {"_error": str(e)[:120]}

    last_error = "no_proxy"
    tried = set()
    for attempt in range(5):
        if msisdn:
            entry = _proxy_pool.acquire_for_session(msisdn, exclude=tried, timeout=4)
        else:
            entry = _proxy_pool.acquire(exclude=tried, timeout=4)
        if entry is None:
            break
        tried.add(entry.url)
        try:
            s = _new_session(use_proxy=False)
            s.proxies = {"http": entry.url, "https": entry.url}
            r = s.request(method, url, headers=headers, data=data,
                          timeout=min(timeout, 10), allow_redirects=False)
            head = r.text[:200].lstrip().lower()
            if head.startswith(("<!doctype", "<html")):
                _proxy_pool.release(entry, success=False, reason="html_block")
                if msisdn:
                    _proxy_pool.release_session(msisdn, "html_block")
                last_error = "html_block"
                continue
            try: body = r.json()
            except: body = {"_raw": r.text[:500]}
            _proxy_pool.release(entry, success=True)
            return r.status_code, dict(r.headers), body
        except Exception as e:
            last_error = str(e)[:120]
            _proxy_pool.release(entry, success=False, reason=last_error)
            if msisdn:
                _proxy_pool.release_session(msisdn, "exception")
            logging.warning(f"[OO-REQ] محاولة {attempt+1}/5: {last_error}")
            time.sleep(0.2)

    report_admin_alert("بروكسي Ooredoo لا يجيب", f"{method} {url[:100]}\n{last_error}")
    return 0, {}, {"_error": "proxy_unavailable", "detail": last_error}

# ==================== 🔒 _dz_req مع Lease ====================
def _dz_req(method, url, headers=None, params=None, json_body=None, data=None, timeout=10, msisdn=None):
    last_error = "no_proxy"
    tried = set()
    for attempt in range(3):
        if msisdn:
            entry = _proxy_pool.acquire_for_session(msisdn, exclude=tried, timeout=4)
        else:
            entry = _proxy_pool.acquire(exclude=tried, timeout=4)
        if entry is None:
            break
        tried.add(entry.url)
        try:
            s = _new_session(headers, use_proxy=False)
            s.proxies = {"http": entry.url, "https": entry.url}
            if method == "GET":
                r = s.get(url, params=params, timeout=timeout)
            elif method == "POST":
                if json_body is not None: r = s.post(url, params=params, json=json_body, timeout=timeout)
                elif data is not None: r = s.post(url, params=params, data=data, timeout=timeout)
                else: r = s.post(url, params=params, timeout=timeout)
            else:
                r = s.request(method, url, params=params, timeout=timeout)
            head = r.text[:200].lstrip().lower()
            if head.startswith(("<!doctype", "<html")):
                _proxy_pool.release(entry, success=False, reason="html_block")
                if msisdn:
                    _proxy_pool.release_session(msisdn, "html_block")
                last_error = "html_block"
                continue
            _proxy_pool.release(entry, success=True)
            return r
        except Exception as e:
            last_error = str(e)[:100]
            _proxy_pool.release(entry, success=False, reason=last_error)
            if msisdn:
                _proxy_pool.release_session(msisdn, "exception")
            logging.warning(f"[DZ-REQ] {method} {url[:50]} (try {attempt+1}/3): {last_error}")
            if attempt < 2: time.sleep(0.3)
    return None

# ==================== 🔒 safe_request مع Lease ====================
async def safe_request(method, url, json=None, headers=None, timeout=8, msisdn=None):
    def _sync():
        last_error = "no_proxy"
        tried = set()
        for attempt in range(3):
            if msisdn:
                entry = _proxy_pool.acquire_for_session(msisdn, exclude=tried, timeout=4)
            else:
                entry = _proxy_pool.acquire(exclude=tried, timeout=4)
            if entry is None: break
            tried.add(entry.url)
            try:
                s = _new_session(use_proxy=False)
                s.proxies = {"http": entry.url, "https": entry.url}
                r = s.request(method, url, json=json, headers=headers, timeout=timeout)
                head = r.text[:200].lstrip().lower()
                if head.startswith(("<!doctype", "<html")):
                    _proxy_pool.release(entry, success=False, reason="html_block")
                    if msisdn:
                        _proxy_pool.release_session(msisdn, "html_block")
                    last_error = "html_block"
                    continue
                try: j = r.json()
                except: j = None
                _proxy_pool.release(entry, success=True)
                return {'status': r.status_code, 'json': j,
                        'text': r.text[:500], 'proxy': entry.url}
            except Exception as e:
                last_error = str(e)[:120]
                _proxy_pool.release(entry, success=False, reason=last_error)
                if msisdn:
                    _proxy_pool.release_session(msisdn, "exception")
                if attempt < 2: time.sleep(0.2)
        report_admin_alert("بروكسي Djezzy لا يجيب", f"{method} {url[:100]}\n{last_error}")
        return {'status': 0, 'json': None, 'text': 'proxy_unavailable', 'proxy': None}
    return await asyncio.to_thread(_sync)

def dz_extract_msg(j):
    if not j: return ""
    if isinstance(j, dict):
        msg = j.get("message")
        if isinstance(msg, dict): return msg.get("ar") or msg.get("en") or msg.get("fr") or ""
        if isinstance(msg, str): return msg
    return ""

bot = AsyncTeleBot(TOKEN)
user_steps = {}
_MAIN_LOOP = None
_ADMIN_ALERT_LOCK = threading.Lock()
_ADMIN_ALERT_LAST = {}

async def _send_admin_alert_async(title, details):
    try:
        text = (f"🚨 <b>{_html.escape(str(title))}</b>\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"<pre>{_html.escape(str(details)[:2500])}</pre>")
        await bot.send_message(ADMIN_ID, text, parse_mode='HTML')
    except Exception as e:
        logging.error(f"[ADMIN-ALERT-SEND] {e}")

def report_admin_alert(kind, details, cooldown=300):
    now = time.time()
    with _ADMIN_ALERT_LOCK:
        last = _ADMIN_ALERT_LAST.get(kind, 0)
        if now - last < cooldown:
            return False
        _ADMIN_ALERT_LAST[kind] = now
    logging.error(f"[ADMIN-ALERT] {kind}: {details}")
    loop = _MAIN_LOOP
    if loop and loop.is_running():
        try:
            asyncio.run_coroutine_threadsafe(_send_admin_alert_async(kind, details), loop)
            return True
        except Exception as e:
            logging.error(f"[ADMIN-ALERT-SCHEDULE] {e}")
    return False

def _asyncio_exception_guard(loop, context):
    try:
        err = context.get("exception")
        msg = context.get("message", "خطأ asyncio غير معروف")
        details = f"{msg}\n{err or context.get('future') or context.get('task')}"
        logging.error(f"[ASYNC-GUARD] {details}", exc_info=err if isinstance(err, BaseException) else None)
        report_admin_alert("خطأ داخلي — البوت مستمر", str(details)[:1200])
    except Exception:
        logging.exception("[ASYNC-GUARD] فشل تسجيل الخطأ")

# ==================== DB ====================
def init_db():
    conn = sqlite3.connect(DB_PATH, timeout=15, check_same_thread=False)
    c = conn.cursor()
    try: c.execute("PRAGMA journal_mode=WAL")
    except: pass
    try: c.execute("PRAGMA synchronous=NORMAL")
    except: pass
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id INTEGER PRIMARY KEY, username TEXT, join_date TEXT, 
                  is_logged_in INTEGER DEFAULT 0, last_phone TEXT)''')
    try: c.execute("ALTER TABLE users ADD COLUMN last_phone TEXT")
    except: pass
    c.execute('''CREATE TABLE IF NOT EXISTS numbers 
                 (phone TEXT PRIMARY KEY, user_id INTEGER, token TEXT,
                  last_activation_1gb REAL DEFAULT 0, last_activation_2gb REAL DEFAULT 0,
                  last_activation_3gb REAL DEFAULT 0, last_activation_offers REAL DEFAULT 0,
                  added_date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS oo_gifts_log
                 (uuid TEXT PRIMARY KEY, user_id INTEGER, msisdn TEXT,
                  value TEXT, unit TEXT, validity TEXT, validity_unit TEXT,
                  earned_date TEXT, expiry_date TEXT, redeemed_date TEXT,
                  actual_expiry TEXT, status TEXT DEFAULT 'ACTIVE')''')
    c.execute('''CREATE TABLE IF NOT EXISTS stats (id INTEGER PRIMARY KEY)''')
    if c.execute("SELECT COUNT(*) FROM stats WHERE id = 1").fetchone()[0] == 0:
        c.execute("INSERT INTO stats (id) VALUES (1)")
    all_cols = ["total_1gb","total_2gb","total_3gb","total_offers","oo_logins","oo_snap","oo_youtube",
                "oo_byop30","oo_byop40","oo_bundles","oo_spins","oo_balance","oo_offers_view","dz_logins",
                "oo_gaming_view","oo_ff_bought","oo_gifts","sp_yt","sp_ig","sp_fb","sp_wa","sp_tt",
                "inet_5g","inet_10g","inet_30g","sp_data_30g","sp_data_40g","sp_data_50g","sp_data_60g",
                "sp_data_70g","sp_data_80g","sp_data_90g","oo_soccer_enrolls",
                "oo_stars_activated","oo_gifts_sent","oo_20dzd_1go", "oo_5dzd_5go",
                "oo_gift_plays","oo_gift_won","oo_gifts_total","oo_free_2gb"]
    existing = [r[1] for r in c.execute("PRAGMA table_info(stats)").fetchall()]
    for col in all_cols:
        if col not in existing:
            try: c.execute(f"ALTER TABLE stats ADD COLUMN {col} INTEGER DEFAULT 0")
            except: pass
    c.execute('''CREATE TABLE IF NOT EXISTS proxies
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT, url TEXT UNIQUE, is_default INTEGER DEFAULT 0,
                  active INTEGER DEFAULT 1, status TEXT DEFAULT 'unknown',
                  last_check REAL DEFAULT 0, added_date TEXT)''')
    for col in ["source TEXT DEFAULT 'manual'",
                "fail_count INTEGER DEFAULT 0",
                "success_count INTEGER DEFAULT 0",
                "consecutive_fails INTEGER DEFAULT 0",
                "last_used REAL DEFAULT 0",
                "disabled_until REAL DEFAULT 0"]:
        try: c.execute(f"ALTER TABLE proxies ADD COLUMN {col}")
        except: pass
    conn.commit(); conn.close()

for _db_boot_attempt in range(5):
    try:
        init_db()
        break
    except Exception as _db_boot_error:
        logging.exception(f"[DB-BOOT] محاولة {_db_boot_attempt + 1}/5 فشلت: {_db_boot_error}")
        if _db_boot_attempt < 4:
            time.sleep(2)

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
                                 if kk in ("step","phone","msisdn","display","otp_attempts","last_activity",
                                           "gift_beneficiary","gift_bundles")}
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

def _seed_and_load_proxies():
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for raw in EMBEDDED_PROXIES_RAW:
        u = _normalize_proxy(raw)
        if not u: continue
        db_query("INSERT OR IGNORE INTO proxies "
                 "(name, url, is_default, active, status, last_check, added_date, source) "
                 "VALUES (?,?,?,?,?,?,?,?)",
                 ("Embedded", u, 0, 1, "unknown", 0, stamp, "embedded"))
    rows = db_query("SELECT url, name, source FROM proxies WHERE active=1", fetchall=True) or []
    for url, name, src in rows:
        _proxy_pool.add(url, name, src or "db")
    logging.info(f"[PROXY] Pool loaded: {len(rows)} proxies")

# ==================== جيزي ====================
def dj_request_otp(phone):
    url = f"{DJ_BASE}/oauth2/registration"
    params = {'msisdn': phone, 'client_id': DJ_CLIENT_ID, 'scope': "smsotp"}
    payload = {"consent-agreement": [{"marketing-notifications": False}], "is-consent": True}
    user_agents = ["MobileApp/3.0.7", "MobileApp/3.0.0", "okhttp/4.12.0", "Dart/3.11 (dart:io)"]
    for attempt, ua in enumerate(user_agents, 1):
        h = DJ_HEADERS.copy(); h['User-Agent'] = ua
        try:
            r = _dz_req("POST", url, headers=h, params=params, json_body=payload, timeout=10, msisdn=phone)
            if r is None: continue
            logging.info(f"[DJ-OTP] {phone} UA={ua} (try {attempt}) → {r.status_code}")
            if r.status_code == 200: return True
            if r.status_code in (429, 400): return False
        except requests.exceptions.Timeout: pass
        except Exception as e: logging.error(f"DJ OTP ({ua}): {e}")
        if attempt < len(user_agents): time.sleep(1)
    report_admin_alert("فشل إرسال رمز Djezzy", "تمت كل محاولات إرسال الرمز بدون نجاح.")
    return False

def dj_verify_otp(phone, otp):
    url = f"{DJ_BASE}/oauth2/token"
    clean = ''.join(filter(str.isdigit, otp))
    if len(clean) != 6: return None
    payload = {'otp': clean, 'mobileNumber': phone, 'scope': "djezzyAppV2",
               'client_id': DJ_CLIENT_ID, 'client_secret': DJ_CLIENT_SECRET, 'grant_type': "mobile"}
    h = DJ_HEADERS.copy(); h['Content-Type'] = "application/x-www-form-urlencoded"
    for i in range(3):
        r = _dz_req("POST", url, headers=h, data=payload, timeout=20, msisdn=phone)
        if r is None: time.sleep(2); continue
        logging.info(f"[DJ-VERIFY] {phone} → {r.status_code}")
        if r.status_code == 200:
            try: return r.json().get('access_token')
            except: return None
        if r.status_code == 401: return "EXPIRED"
        time.sleep(2)
    return None

def dj_extract_balance_info(raw):
    info = {"main": 0, "due": 0}
    if not raw: return info
    data = raw.get("data", raw) if isinstance(raw, dict) else {}
    if isinstance(data, dict):
        try: info["main"] = float(data.get("mainBalance", 0) or 0)
        except: info["main"] = 0
        try: info["due"] = float(data.get("due", 0) or 0)
        except: info["due"] = 0
    return info

def dj_check_balance(token, phone):
    h = DJ_HEADERS.copy(); h['Authorization'] = f"Bearer {token}"; h['User-Agent'] = "MobileApp/3.0.7"
    for attempt in range(2):
        r = _dz_req("GET", f"{DJ_BASE}/api/v1/subscribers/main-balance/{phone}", headers=h, timeout=10, msisdn=phone)
        if r is None:
            if attempt == 0: time.sleep(1); continue
            return {"status": "FAILED", "balance": 0, "due": 0}
        logging.info(f"[DJ-BAL] {phone} (try {attempt+1}) → {r.status_code}")
        if r.status_code == 200:
            bi = dj_extract_balance_info(r.json())
            return {"status": "SUCCESS", "balance": bi["main"], "due": bi["due"]}
        if r.status_code == 401: return {"status": "EXPIRED", "balance": 0, "due": 0}
        if attempt == 0: time.sleep(1)
    return {"status": "FAILED", "balance": 0, "due": 0}

def dj_extract_price(p):
    try:
        m = re.search(r'(\d+)', str(p))
        if m: return int(m.group(1))
    except: pass
    return None

async def dz_activate_paid_offer_async(token, phone, package_code, offer_type, offer_name, price):
    h = DZ_HEADERS.copy(); h['Authorization'] = f"Bearer {token}"
    async def _try_post(url, label):
        r = await safe_request('POST', url, json={"packageCode": package_code}, headers=h, timeout=10, msisdn=phone)
        if r['status'] == 401: return {"success": False, "token_expired": True, "msg": "⚠️ انتهت جلستك اعد إرسال رقمك"}
        if r['status'] in [200, 201, 202]:
            srv = dz_extract_msg(r['json']) if r['json'] else ""
            if srv:
                low = srv.lower()
                for kw in ['غير متوفر','غير متوفرة','not available','not found','déjà','already','solde','رصيد','insufficient']:
                    if kw in low:
                        if 'رصيد' in low or 'solde' in low or 'insufficient' in low:
                            return {"success": False, "token_expired": False, "msg": f"❌ رصيدك غير كافي لتفعيل {offer_name}\n💰 المطلوب: {price} د.ج"}
                        return {"success": False, "token_expired": False, "msg": f"⚠️ {srv}"}
            return {"success": True, "token_expired": False, "msg": (
                f"✅ ━━━ تم التفعيل بنجاح ━━━\n\n🎉 {offer_name}\n💰 السعر: {price} د.ج\n\n{PAGE_FOLLOW_TEXT}")}
        if r['status'] == 402:
            return {"success": False, "token_expired": False, "msg": f"❌ رصيدك غير كافي لتفعيل {offer_name}\n💰 المطلوب: {price} د.ج"}
        srv = dz_extract_msg(r['json']); code = r.get('status', '?')
        info = srv if srv else f"كود: {code}"
        return {"success": False, "token_expired": False, "msg": f"⚠️ تعذر تفعيل {offer_name}\n\nℹ️ {info}"}
    if offer_type == "shake":
        shake_url = f"{DZ_BASE_URL}/api/v1/services/shake/{phone}"
        for _ in range(3):
            res_get = await safe_request('GET', shake_url, headers=h, timeout=8, msisdn=phone)
            if res_get['status'] == 401: return {"success": False, "token_expired": True, "msg": "⚠️ انتهت جلستك اعد إرسال رقمك"}
            if res_get['status'] == 200: break
            await asyncio.sleep(0.3)
        r_post = await _try_post(shake_url, "shake")
        if not r_post.get("success") and not r_post.get("token_expired"):
            fb = await _try_post(f"{DZ_BASE_URL}/api/v1/subscribers/activate-product/{phone}", "fb")
            if fb.get("success") or fb.get("token_expired"): return fb
            if any(k in fb.get("msg","") for k in ['رصيد','غير متوفر','تم التفعيل']): return fb
        return r_post
    return await _try_post(f"{DZ_BASE_URL}/api/v1/subscribers/activate-product/{phone}", "activate")

async def dz_activate_offer_70_4g_async(token, phone):
    h = DZ_HEADERS.copy(); h['Authorization'] = f"Bearer {token}"
    async def _try_post(url, label):
        r = await safe_request('POST', url, json={"packageCode": "BTLINTSPEEDDAY2GO"}, headers=h, timeout=10, msisdn=phone)
        if r.get('status') == 401: return {"success": False, "token_expired": True, "msg": "⚠️ انتهت جلستك"}
        if r.get('status') in [200, 201, 202]:
            return {"success": True, "token_expired": False, "msg": (f"✅ ━━━ تم التفعيل بنجاح ━━━\n\n🟢 عرض: 4 جيجابايت\n💰 السعر: 70 د.ج\n⏱️ الصلاحية: 24 ساعة\n\n{PAGE_FOLLOW_TEXT}")}
        if r.get('status') == 402: return {"success": False, "token_expired": False, "msg": "❌ رصيدك غير كافٍ"}
        srv = dz_extract_msg(r.get('json')); status = r.get('status')
        info = srv if srv else f"كود: {status}"
        return {"success": False, "token_expired": False, "msg": f"⚠️ تعذر التفعيل\nℹ️ {info}"}
    shake_url = f"{DZ_BASE_URL}/api/v1/services/shake/{phone}"
    for _ in range(3):
        res_get = await safe_request('GET', shake_url, headers=h, timeout=8, msisdn=phone)
        if res_get.get('status') == 401: return {"success": False, "token_expired": True, "msg": "⚠️ انتهت جلستك"}
        if res_get.get('status') == 200: break
        await asyncio.sleep(0.4)
    r_post = await _try_post(shake_url, "shake")
    if not r_post.get("success") and not r_post.get("token_expired"):
        fb = await _try_post(f"{DZ_BASE_URL}/api/v1/subscribers/activate-product/{phone}", "fb")
        if fb.get("success") or fb.get("token_expired"): return fb
    return r_post

async def dz_activate_offer_90_5g_async(token, phone):
    h = DZ_HEADERS.copy(); h['Authorization'] = f"Bearer {token}"
    async def _try_post(url, label):
        r = await safe_request('POST', url, json={"packageCode": "BTL500MBDAY"}, headers=h, timeout=10, msisdn=phone)
        if r.get('status') == 401: return {"success": False, "token_expired": True, "msg": "⚠️ انتهت جلستك"}
        if r.get('status') in [200, 201, 202]:
            return {"success": True, "token_expired": False, "msg": (f"✅ ━━━ تم التفعيل بنجاح ━━━\n\n🟣 عرض: 5 جيجابايت\n💰 السعر: 90 د.ج\n⏱️ الصلاحية: 24 ساعة\n\n{PAGE_FOLLOW_TEXT}")}
        if r.get('status') == 402: return {"success": False, "token_expired": False, "msg": "❌ رصيدك غير كافٍ"}
        srv = dz_extract_msg(r.get('json')); status = r.get('status')
        info = srv if srv else f"كود: {status}"
        return {"success": False, "token_expired": False, "msg": f"⚠️ تعذر التفعيل\nℹ️ {info}"}
    shake_url = f"{DZ_BASE_URL}/api/v1/services/shake/{phone}"
    for _ in range(3):
        res_get = await safe_request('GET', shake_url, headers=h, timeout=8, msisdn=phone)
        if res_get.get('status') == 401: return {"success": False, "token_expired": True, "msg": "⚠️ انتهت جلستك"}
        if res_get.get('status') == 200: break
        await asyncio.sleep(0.4)
    r_post = await _try_post(shake_url, "shake")
    if not r_post.get("success") and not r_post.get("token_expired"):
        fb = await _try_post(f"{DZ_BASE_URL}/api/v1/subscribers/activate-product/{phone}", "fb")
        if fb.get("success") or fb.get("token_expired"): return fb
    return r_post

def dj_activate_2gb(token, phone):
    h = DJ_HEADERS.copy(); h['Authorization'] = f"Bearer {token}"; h['User-Agent'] = "MobileApp/3.0.7"
    endpoints = [
        (f"{DJ_BASE}/api/v1/services/shake/{phone}", "GIFTWALKWIN2GO"),
        (f"{DJ_BASE}/api/v1/services/walk/activate-reward/{phone}", "GIFTWALKWIN2GO"),
        (f"{DJ_BASE}/api/v1/subscribers/activate-product/{phone}", "GIFTWALKWIN2GO"),
    ]
    last = 0
    for url, code in endpoints:
        r = _dz_req("POST", url, headers=h, json_body={"packageCode": code}, timeout=12, msisdn=phone)
        if r is None: continue
        last = r.status_code
        if r.status_code == 401: return "EXPIRED"
        if r.status_code in (200, 201):
            if "already" in r.text.lower(): return "LIMIT"
            return "SUCCESS"
        if r.status_code == 402: return "NO_BALANCE"
        if r.status_code == 429: return "RATE_LIMIT"
        time.sleep(0.3)
    if last == 403: return "NOT_ALLOWED"
    return "FAILED"

def dj_activate_3gb(token, phone):
    h = DJ_HEADERS.copy(); h['Authorization'] = f"Bearer {token}"
    url = f"{DJ_BASE}/api/v1/services/walk/activate-reward/{phone}"
    res = []
    for pkg in ["GIFTWALKWIN2GO", "MGMBONUS1Go"]:
        r = _dz_req("POST", url, headers=h, json_body={"packageCode": pkg}, timeout=12, msisdn=phone)
        if r is None: res.append(False); continue
        if r.status_code in [200, 201] or "success" in r.text.lower(): res.append(True)
        elif r.status_code == 401: return "EXPIRED"
        else: res.append(False)
        time.sleep(0.8)
    return "SUCCESS" if any(res) else "FAILED"

# ==================== أوريدو ====================
def _now_ms(): return str(int(time.time() * 1000))
def _iid(): return str(uuid.uuid4()) + _now_ms()
def _pld(x):
    return base64.b64encode(json.dumps({"platform":"android","is-physical-device":True,"device-id":x},
                                       separators=(",",":")).encode()).decode()
def _fp(): return os.urandom(32).hex()
def _corr(): return str(uuid.uuid4()) + _now_ms()
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
    rp = ""
    is_yooz = False
    is_dima = False
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

def ooredoo_send_otp_sync(msisdn, _network_retry=0):
    ts = _now_ms(); iid_val = _iid(); psig = _pld(iid_val)
    fp = _fp()
    device = {"instance_id": iid_val, "plat_sig": psig, "fp": fp}
    nonce, chronos = "", ""
    try:
        h3 = _base_hdrs(msisdn, iid_val, psig, _corr(), ts, fp=fp)
        h3["x-version"] = X_VERSION_OTP
        h3.update({"content-type": "application/json; charset=utf-8",
                   "x-native-integrity-token": INTEGRITY_1,
                   "x-path": "/api/auth/realms/myooredoo/protocol/openid-connect/token",
                   "x-method": "POST"})
        c3, rh3, j3 = _oo_req("POST", f"{OO_BFF}/checkpoint/token", h3, b"{}", timeout=10, msisdn=msisdn)
        if c3 == 0:
            logging.warning(f"[OO-CHECKPOINT] {msisdn} → 0 | {str(j3)[:180]}")
        nonce = rh3.get("x-nonce-id") or rh3.get("X-Nonce-Id") or ""
        chronos = rh3.get("x-chronos-id") or rh3.get("X-Chronos-Id") or ""
    except: pass
    try:
        h4 = {"User-Agent":"Dart/3.11 (dart:io)","Accept-Encoding":"gzip","x-msisdn":msisdn,
              "x-device-fingerprint":fp,"x-platform-origin":"mobile-android",
              "platform":"android","x-version":X_VERSION_OTP,"x-signature":X_SIG,
              "x-timestamp":ts,"x-platform-info":psig,"x-force-update":"true",
              "x-instance-id":iid_val,"content-type":"application/x-www-form-urlencoded; charset=utf-8"}
        if nonce: h4["x-nonce-id"] = nonce
        if chronos: h4["x-chronos-id"] = chronos
        body = f"client_id={OO_CLIENT}&grant_type=password&username={msisdn}"
        c4, _, j4 = _oo_req("POST", OO_AUTH, h4, body, timeout=15, msisdn=msisdn)
        logging.info(f"[OO-OTP] {msisdn} → {c4}")
        if c4 == 429:
            report_admin_alert("فشل إرسال رمز Ooredoo", "الخدمة رجعت 429 (تقييد مؤقت).")
            return {"device": device, "otp_sent": False, "status": 429, "reason": "rate_limit"}
        if c4 == 0:
            reason = str(j4)[:500]
            if _network_retry < 2:
                time.sleep(1.5)
                return ooredoo_send_otp_sync(msisdn, _network_retry + 1)
            report_admin_alert("فشل إرسال رمز Ooredoo", f"لا توجد استجابة بعد 3 محاولات.\n{reason}")
            return {"device": device, "otp_sent": False, "status": 0, "reason": "network"}
        if c4 == 403:
            return {"device": device, "otp_sent": True, "status": c4}
        if c4 != 429 and _network_retry < 2:
            time.sleep(1.5)
            return ooredoo_send_otp_sync(msisdn, _network_retry + 1)
        report_admin_alert("رفض إرسال رمز Ooredoo", f"الخادم رجع HTTP {c4}: {str(j4)[:500]}")
        return {"device": device, "otp_sent": False, "status": c4, "reason": "http_error"}
    except Exception as e:
        logging.error(f"❌ OOREDOO OTP: {e}")
        report_admin_alert("فشل إرسال رمز Ooredoo", str(e))
        return {"device": device, "otp_sent": False, "status": -1, "reason": "exception"}

def ooredoo_verify_otp_sync(msisdn, otp, device):
    iid_val = device.get("instance_id") or _iid()
    psig = device.get("plat_sig") or _pld(iid_val)
    fp_otp = device.get("fp") or _fp()
    ts = _now_ms()
    nonce, chronos = "", ""
    try:
        h6 = _base_hdrs(msisdn, iid_val, psig, _corr(), ts, fp=fp_otp)
        h6["x-version"] = X_VERSION_OTP
        h6.update({"content-type":"application/json; charset=utf-8",
                   "x-native-integrity-token":INTEGRITY_1,
                   "x-path":"/api/auth/realms/myooredoo/protocol/openid-connect/token","x-method":"POST"})
        _, rh6, _ = _oo_req("POST", f"{OO_BFF}/checkpoint/token", h6, b"{}", timeout=10, msisdn=msisdn)
        nonce = rh6.get("x-nonce-id") or rh6.get("X-Nonce-Id") or ""
        chronos = rh6.get("x-chronos-id") or rh6.get("X-Chronos-Id") or ""
    except: pass
    h7 = {"User-Agent":"Dart/3.11 (dart:io)","Accept-Encoding":"gzip","x-msisdn":msisdn,
          "x-device-fingerprint":fp_otp,"x-platform-origin":"mobile-android",
          "platform":"android","x-version":X_VERSION_OTP,"x-signature":X_SIG,
          "x-timestamp":ts,"x-platform-info":psig,"x-force-update":"true",
          "x-instance-id":iid_val,"content-type":"application/x-www-form-urlencoded; charset=utf-8"}
    if nonce: h7["x-nonce-id"] = nonce
    if chronos: h7["x-chronos-id"] = chronos
    body = f"client_id={OO_CLIENT}&grant_type=password&username={msisdn}&otp={otp}"
    c7, _, j7 = _oo_req("POST", OO_AUTH, h7, body, timeout=15, msisdn=msisdn)
    logging.info(f"[OO-VERIFY] {msisdn} → {c7}")
    if c7 == 200 and isinstance(j7, dict) and "access_token" in j7:
        at = j7["access_token"]
        return {"access_token": at, "refresh_token": j7.get("refresh_token",""),
                "expires_in": j7.get("expires_in", 2592000),
                "tok_fingerprint": fp_otp,
                "tok_instance_id": _exdid(at) or iid_val, "tok_plat_sig": _mps(at),
                "tok_timestamp": ts, "issued_at": int(time.time())}
    if c7 in (400, 401, 403): return "wrong_otp"
    if c7 == 0:
        report_admin_alert("فشل التحقق من رمز Ooredoo", "الخادم لم يرد أثناء التحقق.")
    return None

def ooredoo_refresh_token_sync(msisdn, rt, device):
    iid_val = device.get("instance_id") or _iid(); psig = device.get("plat_sig") or _pld(iid_val)
    fp_otp = device.get("fp") or _fp(); ts = _now_ms()
    h = _base_hdrs(msisdn, iid_val, psig, _corr(), ts, fp=fp_otp)
    h.update({"content-type":"application/x-www-form-urlencoded",
              "x-native-integrity-token":INTEGRITY_1,
              "x-path":"/api/auth/realms/myooredoo/protocol/openid-connect/token","x-method":"POST"})
    _, rh, _ = _oo_req("POST", f"{OO_BFF}/checkpoint/token", h, b"{}", timeout=10, msisdn=msisdn)
    nonce = rh.get("x-nonce-id") or rh.get("X-Nonce-Id") or ""
    chronos = rh.get("x-chronos-id") or rh.get("X-Chronos-Id") or ""
    if not nonce or not chronos: return None
    h2 = {"User-Agent":"Dart/3.11 (dart:io)","Accept-Encoding":"gzip","x-msisdn":msisdn,
          "x-device-fingerprint":fp_otp,"x-nonce-id":nonce,"x-platform-origin":"mobile-android",
          "platform":"android","x-version":X_VERSION,"x-signature":X_SIG,"x-chronos-id":chronos,
          "x-timestamp":ts,"x-platform-info":psig,"x-force-update":"true","x-instance-id":iid_val,
          "content-type":"application/x-www-form-urlencoded"}
    body = f"client_id={OO_CLIENT}&grant_type=refresh_token&refresh_token={rt}"
    c2, _, j2 = _oo_req("POST", OO_AUTH, h2, body, timeout=15, msisdn=msisdn)
    if c2 == 200 and "access_token" in j2:
        at = j2["access_token"]
        return {"access_token": at, "refresh_token": j2.get("refresh_token", rt),
                "expires_in": j2.get("expires_in", 0),
                "tok_instance_id": _exdid(at) or iid_val, "tok_plat_sig": _mps(at),
                "tok_fingerprint": fp_otp, "tok_timestamp": ts, "issued_at": int(time.time())}
    return None

def oo_check_balance(msisdn, at, meta):
    h = _web_hdrs(msisdn, at, meta)
    c, _, resp = _oo_req("GET", f"{OO_BFF}/subscriptions/getAccountInfo", h, timeout=12, msisdn=msisdn)
    if c == 200: return {"status": "ok", "data": resp if isinstance(resp, dict) else {}}
    if c == 401: return {"status": "unauthorized"}
    return {"status": "error", "code": c}

def oo_get_profile(msisdn, at, meta):
    cache_key = hashlib.md5((msisdn + at[-16:]).encode()).hexdigest()
    now = time.time()
    if cache_key in _PROFILE_CACHE:
        ts_cached, data_cached = _PROFILE_CACHE[cache_key]
        if now - ts_cached < 300:
            return data_cached
    iid_val = meta.get("tok_instance_id") or _iid()
    psig = meta.get("tok_plat_sig") or _pld(iid_val)
    fp = meta.get("tok_fingerprint") or _fp()
    h_ck = _base_hdrs(msisdn, iid_val, psig, _corr(), _now_ms(), fp=fp)
    h_ck.update({"content-type": "application/json; charset=utf-8",
                 "x-native-integrity-token": INTEGRITY_1,
                 "x-path": "/api/ooredoo-bff/userInfo/personal",
                 "x-method": "GET"})
    _, rh_ck, _ = _oo_req("POST", f"{OO_BFF}/checkpoint/token", h_ck, b"{}", timeout=10, msisdn=msisdn)
    n = rh_ck.get("x-nonce-id", "") or rh_ck.get("X-Nonce-Id", "")
    ch = rh_ck.get("x-chronos-id", "") or rh_ck.get("X-Chronos-Id", "")
    iso_ts = datetime.now(tz.utc).strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"
    h = {"user-agent": "Dart/3.11 (dart:io)","accept-encoding": "gzip", "x-msisdn": msisdn,
         "x-device-fingerprint": fp, "x-platform-origin": "mobile-android",
         "authorization": f"Bearer {at}", "x-correlation-id": _corr(),
         "platform": "android", "x-version": X_VERSION, "x-signature": X_SIG,
         "accept": "*/*", "x-platform-data-signature": psig,
         "x-timestamp": iso_ts, "x-instance-id": iid_val}
    if n: h["x-nonce-id"] = n
    if ch: h["x-chronos-id"] = ch
    c, _, resp = _oo_req("GET", f"{OO_BFF}/userInfo/personal", h, timeout=12, msisdn=msisdn)
    if c == 200 and isinstance(resp, dict):
        result = {"status": "ok", "data": resp}
        _PROFILE_CACHE[cache_key] = (now, result)
        return result
    return {"status": "unauthorized" if c == 401 else "error", "code": c}

def oo_get_active(msisdn, at, meta):
    h = _web_hdrs(msisdn, at, meta)
    c, _, resp = _oo_req("GET", f"{OO_BFF}/bundle/getActivePackages?msisdn={msisdn}", h, timeout=12, msisdn=msisdn)
    if c == 200: return {"status": "ok", "data": resp if isinstance(resp, dict) else {}}
    if c == 401: return {"status": "unauthorized"}
    return {"status": "error", "code": c}

def oo_activate_snapchat(msisdn, at, meta):
    h = _web_hdrs(msisdn, at, meta)
    c, _, _ = _oo_req("POST", f"{OO_BFF}/snap-chat/apply", h, timeout=12, msisdn=msisdn)
    if c == 200: return "ok"
    if c == 500: return "already_active"
    if c == 401: return "unauthorized"
    return "error"

def oo_purchase_20dzd_1go(msisdn, at, meta):
    body = json.dumps({"bundleCode": "BTL_24H_DATA_20DZD_1Go", "validity": "day", "validityAmount": "1"}, separators=(",", ":"))
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
    c = 0; resp = {}
    for label, h in [("mobile v1.5.17", _mobile_hdrs(X_VERSION)),
                     ("mobile v1.5.16", _mobile_hdrs("1.5.16"))]:
        c, _, resp = _oo_req("POST", f"{OO_BFF}/cvm/bundlePurchase", h, body, timeout=15, msisdn=msisdn)
        logging.info(f"[OO-20DZD-1GO] {msisdn} [{label}] → {c} | {str(resp)[:180]}")
        if c in (200, 201): return {"status": "ok", "data": resp}
        if c in (402, 409): break
    if c in (402, 409):
        srv_code = str(resp.get("code") or "").upper() if isinstance(resp, dict) else ""
        if any(k in srv_code for k in ("CREDIT", "BALANCE", "NOT_ENOUGH")): return {"status": "no_balance"}
        if "ALREADY" in srv_code: return {"status": "already"}
        return {"status": "not_allowed"}
    if c == 401: return {"status": "purchase_blocked"}
    return {"status": "error", "code": c}

def oo_purchase_5dzd_5go(msisdn, at, meta):
    body = json.dumps({"bundleCode": "ATL_DATA_5Go_5H"}, separators=(",", ":"))
    iid_val = meta.get("tok_instance_id") or _iid()
    psig = meta.get("tok_plat_sig") or _pld(iid_val)
    fp = meta.get("tok_fingerprint") or _fp()
    h = {"x-msisdn": msisdn, "user-agent": "Dart/3.11 (dart:io)",
         "x-device-fingerprint": fp, "accept-encoding": "gzip",
         "x-platform-origin": "mobile-android", "authorization": f"Bearer {at}",
         "x-correlation-id": _corr(), "content-type": "application/json; charset=utf-8",
         "platform": "android", "x-version": X_VERSION_NEW, "x-signature": X_SIG_NEW,
         "accept": "*/*", "x-platform-data-signature": psig,
         "x-timestamp": _now_ms(), "x-instance-id": iid_val}
    c, _, resp = _oo_req("POST", f"{OO_BFF}/cvm/dynamic-bundle-purchase", h, body, timeout=15, msisdn=msisdn)
    logging.info(f"[OO-5DZD-5GO] {msisdn} → {c} | {str(resp)[:200]}")
    if c in (200, 201): return {"status": "ok", "data": resp}
    if c == 401: return {"status": "unauthorized"}
    if c == 409:
        srv_code = str(resp.get("code") or "").upper() if isinstance(resp, dict) else ""
        if "CREDIT" in srv_code or "BALANCE" in srv_code or "NOT_ENOUGH" in srv_code: return {"status": "no_balance"}
        return {"status": "conflict", "msg": "هذا العرض غير متاح حالياً أو مفعل مسبقاً"}
    return {"status": "error", "code": c}

# ==================== 🎁 2Go FREE (مع معالجة YOOZ1001) ====================
def oo_purchase_free_2gb(msisdn, at, meta):
    body_simple = json.dumps({"bundleCode": "BTL_24H_DATA_Free_2Go"}, separators=(",", ":"))
    body_full = json.dumps({"bundleCode": "BTL_24H_DATA_Free_2Go", "validity": "day", "validityAmount": "1"}, separators=(",", ":"))
    def _try(url, body, label):
        try:
            h = _web_hdrs(msisdn, at, meta, "application/json; charset=utf-8")
            c, _, resp = _oo_req("POST", url, h, body, timeout=30, use_proxy=True, msisdn=msisdn)
            logging.info(f"[OO-FREE-2GB][{label}] {msisdn} → {c} | {str(resp)[:250]}")
            return c, resp
        except Exception as e:
            logging.error(f"[OO-FREE-2GB][{label}] {msisdn}: {e}")
            return 0, {"_error": str(e)[:100]}
    bp_url = f"{OO_BFF}/cvm/bundlePurchase"
    dyn_url = f"{OO_BFF}/cvm/dynamic-bundle-purchase"
    combos = [("bundlePurchase simple", bp_url, body_simple),
              ("bundlePurchase full",   bp_url, body_full),
              ("dynamic simple",        dyn_url, body_simple),
              ("dynamic full",          dyn_url, body_full)]
    last_c, last_resp = 0, None
    for label, url, body in combos:
        c, resp = _try(url, body, label)
        last_c, last_resp = c, resp

        if c in (200, 201): return {"status": "ok", "data": resp}

        if c == 500 and isinstance(resp, dict):
            code_srv = str(resp.get("code") or "").upper()
            msg_srv = str(resp.get("message") or "").upper()
            # 🆕 YOOZ1001 = Bundle Refill Not Accepted (مفعّل مسبقاً)
            if code_srv == "YOOZ1001":
                return {"status": "already", "data": resp}
            if any(k in msg_srv for k in ("ALREADY", "DÉJÀ", "REFILL", "PURCHASED", "SUBSCRIBED")):
                return {"status": "already", "data": resp}
            continue

        if c in (402, 409):
            srv = str(resp).upper()
            if any(k in srv for k in ("ALREADY", "DÉJÀ", "PURCHASED", "SUBSCRIBED", "EXIST")):
                return {"status": "already", "data": resp}
            if any(k in srv for k in ("CREDIT", "BALANCE")):
                return {"status": "no_balance", "data": resp}

        if c == 400:
            srv = str(resp).lower()
            if "already" in srv or "déjà" in srv: return {"status": "already", "data": resp}

    if last_c == 401: return {"status": "unauthorized", "data": last_resp}
    if last_c in (402, 409): return {"status": "not_allowed", "data": last_resp}
    return {"status": "error", "code": last_c, "data": last_resp}

async def oo_purchase_free_2gb_safe(msisdn, at, meta):
    try:
        result = await asyncio.wait_for(asyncio.to_thread(oo_purchase_free_2gb, msisdn, at, meta), timeout=210)
        return result if isinstance(result, dict) else {"status": "error", "data": result}
    except asyncio.TimeoutError:
        report_admin_alert("تفعيل 2GB تأخر", f"انتهت مهلة التفعيل للرقم المخفي {notify_mask(msisdn)}")
        return {"status": "error", "code": "timeout", "data": {"_error": "activation_timeout"}}
    except Exception as e:
        logging.exception(f"[OO-FREE-2GB-SAFE] {e}")
        report_admin_alert("فشل تفعيل 2GB", str(e)[:500])
        return {"status": "error", "code": "exception", "data": {"_error": str(e)[:200]}}

def oo_get_available_snakes(msisdn, at, meta):
    h = _web_hdrs(msisdn, at, meta, "application/json")
    c, _, resp = _oo_req("GET", f"{OO_BFF}/gamification/power-snake?status=AVAILABLE", h, timeout=12, msisdn=msisdn)
    logging.info(f"[OO-SNAKE-GET] {msisdn} → {c} | {str(resp)[:250]}")
    if c == 401: return {"status": "unauthorized", "snakes": [], "items": [], "raw": None}
    if c != 200: return {"status": "error", "snakes": [], "items": [], "raw": None}
    snakes = []; items_full = []
    try:
        if isinstance(resp, dict):
            data = resp.get("items") or resp.get("data") or resp.get("content") or []
            if isinstance(data, list):
                for item in data:
                    if not isinstance(item, dict): continue
                    sid = item.get("uuid") or item.get("id") or item.get("snakeId")
                    status = str(item.get("status") or "AVAILABLE").upper()
                    if sid and status == "AVAILABLE":
                        snakes.append(sid); items_full.append(item)
            elif isinstance(resp.get("uuid"), str):
                snakes.append(resp["uuid"]); items_full.append(resp)
            elif isinstance(resp.get("id"), str):
                snakes.append(resp["id"]); items_full.append(resp)
        elif isinstance(resp, list):
            for item in resp:
                if not isinstance(item, dict): continue
                sid = item.get("uuid") or item.get("id") or item.get("snakeId")
                status = str(item.get("status") or "AVAILABLE").upper()
                if sid and status == "AVAILABLE":
                    snakes.append(sid); items_full.append(item)
    except Exception as e:
        logging.warning(f"[OO-SNAKE-GET] parse err: {e}")
    return {"status": "ok", "snakes": snakes, "items": items_full, "raw": resp}

def oo_purchase_byop(msisdn, at, meta, validity="Biweekly", limited=None, unlimited=None):
    h = _web_hdrs(msisdn, at, meta, "application/json; charset=utf-8")
    body = json.dumps({"validity": validity, "limitedBundleDetails": limited or [],
                       "unlimitedBundleDetails": unlimited or []}, separators=(",", ":"))
    c, _, _ = _oo_req("POST", f"{OO_BFF}/bundle/purchase/byop", h, body, timeout=15, msisdn=msisdn)
    if c == 200: return {"status": "ok"}
    if c == 409: return {"status": "conflict", "message": "الرصيد غير كافي"}
    if c == 401: return {"status": "unauthorized"}
    return {"status": "error", "code": c}

def oo_purchase_planned(msisdn, at, meta, code):
    h = _web_hdrs(msisdn, at, meta, "application/json; charset=utf-8")
    body = json.dumps({"bundleCode": code}, separators=(",", ":"))
    c, _, _ = _oo_req("POST", f"{OO_BFF}/cvm/dynamic-bundle-purchase", h, body, timeout=15, msisdn=msisdn)
    if c == 200: return {"status": "ok"}
    if c == 409: return {"status": "conflict", "message": "الرصيد غير كافي"}
    if c == 401: return {"status": "unauthorized"}
    return {"status": "error", "code": c}

def oo_soccer_eligibility(msisdn, at, meta):
    h = _web_hdrs(msisdn, at, meta)
    c, _, resp = _oo_req("GET", f"{OO_BFF}/soccer/eligibility-check", h, timeout=12, msisdn=msisdn)
    if c == 401: return {"status": "unauthorized"}
    if c != 200: return {"status": "error", "code": c}
    if not isinstance(resp, dict): return {"status": "error", "code": c}
    status_srv = str(resp.get("status", "")).upper()
    eligible = bool(resp.get("isEligible") or resp.get("eligible") or resp.get("canActivate"))
    enrolled = (status_srv == "ACTIVE")
    selected = ""
    try:
        opts = resp.get("options", {})
        attrs = opts.get("attribute", []) if isinstance(opts, dict) else []
        for a in attrs:
            if isinstance(a, dict) and a.get("key") == "current_value":
                selected = str(a.get("value") or ""); break
    except: pass
    if status_srv == "INACTIVE" and not eligible:
        enrolled = False; eligible = False
    return {"status": "ok", "eligible": eligible, "enrolled": enrolled,
            "selected_team": selected.upper() if selected else "",
            "raw_status": status_srv, "raw": resp}

def oo_soccer_clubs(msisdn, at, meta):
    h = _web_hdrs(msisdn, at, meta)
    url = "https://apis.ooredoo.dz/cms/v2/api/soccer-clubs?locale=ar&populate=%2A"
    c, _, resp = _oo_req("GET", url, h, timeout=12, msisdn=msisdn)
    if c != 200 or not isinstance(resp, dict): return {"status": "error", "code": c}
    clubs = []
    for item in resp.get("data", []):
        attrs = item.get("attributes", {})
        code = (attrs.get("club_name") or "").upper()
        if code: clubs.append({"code": code, "colors": attrs.get("club_colors", "")})
    return {"status": "ok", "clubs": clubs}

def oo_soccer_activate(msisdn, at, meta, team="MCA"):
    team = team.upper()
    h = _web_hdrs(msisdn, at, meta, "application/json; charset=utf-8")
    c, _, resp = _oo_req("POST", f"{OO_BFF}/soccer/activate?selectedTeam={team}", h, b"{}", timeout=15, msisdn=msisdn)
    if c == 200 and isinstance(resp, dict):
        if str(resp.get("status","")).lower() == "true": return {"status": "ok", "data": resp}
        return {"status": "failed", "msg": resp.get("reason") or "فشل"}
    if c == 401: return {"status": "unauthorized"}
    if c == 409: return {"status": "already", "msg": "مسجل مسبقاً"}
    if c == 400: return {"status": "already", "msg": "الرقم مسجل مسبقاً"}
    return {"status": "error", "code": c, "resp": resp}

def oo_check_noudjoum_status(msisdn, at, meta):
    h = _web_hdrs(msisdn, at, meta)
    for url in [f"{OO_BFF}/noudjoum/status", f"{OO_BFF}/noudjoum/account", f"{OO_BFF}/noudjoum/profile"]:
        try:
            c, _, resp = _oo_req("GET", url, h, timeout=10, msisdn=msisdn)
            if c == 401: return {"status": "unauthorized"}
            if c == 200 and isinstance(resp, dict):
                enrolled = bool(resp.get("enrolled") or resp.get("isEnrolled") or
                                resp.get("active") or resp.get("isActive") or
                                resp.get("subscribed") or resp.get("points") is not None)
                return {"status": "enrolled" if enrolled else "not_enrolled",
                        "points": resp.get("points") or resp.get("balance") or 0}
        except: pass
    return {"status": "unknown"}

def oo_enroll_noudjoum(msisdn, at, meta):
    h = _web_hdrs(msisdn, at, meta, "application/json; charset=utf-8")
    c, _, resp = _oo_req("POST", f"{OO_BFF}/noudjoum/enroll", h, b"", timeout=15, msisdn=msisdn)
    logging.info(f"[NOUDJOUM-ENR] {msisdn} → {c} | {str(resp)[:200]}")
    if c in (200, 201): return {"status": "ok"}
    if c == 409: return {"status": "already"}
    if c == 401: return {"status": "unauthorized"}
    if c == 403: return {"status": "not_eligible"}
    if c == 500:
        body = str(resp).lower()
        if "not eligible" in body or "mass programme" in body: return {"status": "not_eligible"}
        return {"status": "error", "code": 500}
    if c == 400:
        body = str(resp).lower()
        if "already" in body or "déjà" in body or "activ" in body: return {"status": "already"}
        return {"status": "not_eligible"}
    return {"status": "error", "code": c}

def oo_get_beneficiary_bundles(msisdn, at, meta, beneficiary):
    h = _web_hdrs(msisdn, at, meta)
    url = f"{OO_BFF}/bundle/others/eligible-bundles?beneficiaryMsisdn={beneficiary}"
    c, _, resp = _oo_req("GET", url, h, timeout=12, msisdn=msisdn)
    logging.info(f"[GIFT-LIST] {beneficiary} → {c}")
    if c == 401: return {"status": "unauthorized"}
    if c != 200 or not isinstance(resp, dict): return {"status": "error", "code": c}
    bundles = _extract_bundles_from_response(resp)
    if not bundles: return {"status": "empty"}
    return {"status": "ok", "bundles": bundles}

def _extract_bundles_from_response(resp):
    try:
        rdata = (resp.get("body", {}).get("getBundlesResponse", {}).get("responseData", []))
        if not isinstance(rdata, list): return []
        out = []
        for item in rdata:
            b = _normalize_bundle(item)
            if b.get("code"): out.append(b)
        return out
    except Exception as e:
        logging.error(f"[GIFT-LIST] extract: {e}")
        return []

def _normalize_bundle(item):
    attrs = item.get("attributes", {}) or {}
    code = attrs.get("code", "") or ""
    name_obj = attrs.get("name", {}) or {}
    name = (name_obj.get("ar") or name_obj.get("en") or name_obj.get("fr") or code)
    price = "?"
    instances = attrs.get("instances", []) or []
    if instances and isinstance(instances[0], dict):
        inst_attrs = instances[0].get("attributes", {}) or {}
        price = inst_attrs.get("price", "?") or "?"
    amount = attrs.get("periodic-amount", "") or ""
    unit = attrs.get("periodic-unit", "") or ""
    validity = _format_validity(amount, unit)
    data_str, extras = _extract_allowances(instances)
    family = attrs.get("product-family", "") or ""
    return {"code": code, "name": name, "price": price, "data": data_str,
            "extras": extras, "validity": validity, "family": family}

def _format_validity(amount, unit):
    try: amt = int(float(amount))
    except: amt = amount
    if not amount: return ""
    units_ar = {"day": "يوم", "days": "يوم", "week": "أسبوع", "weeks": "أسبوع",
                "month": "شهر", "months": "شهر", "hour": "ساعة", "hours": "ساعة"}
    u = units_ar.get(str(unit).lower(), unit)
    return f"{amt} {u}".strip()

def _extract_allowances(instances):
    if not instances or not isinstance(instances[0], dict): return "", ""
    inst_attrs = instances[0].get("attributes", {}) or {}
    allowances = inst_attrs.get("allowances", []) or []
    data_parts = []; extras_parts = []
    dest_icons = {"YT": "▶️ YouTube", "FB": "📘 Facebook", "SC": "👻 Snapchat",
                  "IG": "📷 Instagram", "Tt": "🎵 TikTok", "WA": "💬 WhatsApp"}
    unit_map = {"GB": "جيجا", "MB": "ميجا", "DZD": "دج",
                "MINUTES": "دقيقة", "MIN": "دقيقة", "HOURS": "ساعة"}
    for a in allowances:
        if not isinstance(a, dict): continue
        aat = a.get("attributes", {}) or {}
        u_type = aat.get("usage-type", "") or ""
        u_val = aat.get("usage-value")
        u_unit = aat.get("usage-unit", "") or ""
        u_unlim = bool(aat.get("unlimited-usage"))
        dest = aat.get("destination", "any") or "any"
        if u_type == "data":
            if u_unlim:
                icon = dest_icons.get(dest, "♾️")
                extras_parts.append(f"{icon} غير محدود")
            else:
                unit_ar = unit_map.get(str(u_unit).upper(), u_unit)
                if dest == "any": data_parts.append(f"{u_val} {unit_ar}".strip())
                else:
                    icon = dest_icons.get(dest, dest)
                    extras_parts.append(f"{icon} {u_val} {unit_ar}".strip())
        elif u_type == "money": extras_parts.append(f"💰 {u_val} دج")
        elif u_type == "voice":
            if u_unlim: extras_parts.append("📞 مكالمات غير محدودة")
            else: extras_parts.append(f"📞 {u_val} دقيقة")
    return (" + ".join(data_parts) if data_parts else "",
            " | ".join(extras_parts) if extras_parts else "")

def oo_gift_purchase(msisdn, at, meta, bundle_code, beneficiary):
    h = _web_hdrs(msisdn, at, meta, "application/json; charset=utf-8")
    body = json.dumps({"bundleCode": bundle_code, "beneficiary": beneficiary}, separators=(",", ":"))
    c, _, resp = _oo_req("POST", f"{OO_BFF}/bundle/others/bundle-purchase", h, body.encode(), timeout=15, msisdn=msisdn)
    logging.info(f"[GIFT] {msisdn} → {beneficiary} | {c}")
    if c in (200, 201): return {"status": "ok", "data": resp}
    if c == 401: return {"status": "unauthorized"}
    if c == 409:
        code = str(resp.get("code") or "") if isinstance(resp, dict) else ""
        body_low = str(resp).lower()
        if "credit" in body_low or "balance" in body_low or "not_enough" in code.lower():
            return {"status": "no_balance", "msg": "رصيدك غير كافٍ"}
        return {"status": "conflict", "msg": "الإهداء غير ممكن حالياً"}
    if c == 403: return {"status": "not_allowed", "msg": "رقم المستفيد غير مؤهل"}
    if c == 400: return {"status": "bad_request", "msg": "رقم المستفيد غير صحيح"}
    return {"status": "error", "code": c, "msg": str(resp)[:150]}

# ==================== Sessions ====================
def oo_save(uid, d): (SESSIONS_DIR / f"oo_{uid}.json").write_text(json.dumps(d, ensure_ascii=False))
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

def time_until_spin(last):
    if not last: return {"avail": True, "str": ""}
    try:
        s = str(last).replace("Z", "+00:00")
        try: ldt = datetime.fromisoformat(s)
        except: ldt = datetime.fromisoformat(s.replace("Z","")).replace(tzinfo=tz(timedelta(hours=1)))
        if ldt.tzinfo is None: ldt = ldt.replace(tzinfo=tz(timedelta(hours=1)))
        next_spin = ldt + timedelta(hours=24)
        now = datetime.now(tz.utc)
        remaining = (next_spin - now).total_seconds()
        if remaining <= 0: return {"avail": True, "str": ""}
        h = int(remaining // 3600); mi = int((remaining % 3600) // 60)
        parts = []
        if h > 0: parts.append(f"{h} ساعة")
        if mi > 0: parts.append(f"{mi} دقيقة")
        if not parts: parts.append("أقل من دقيقة")
        return {"avail": False, "str": " و ".join(parts)}
    except: return {"avail": True, "str": ""}

_stop_threads = threading.Event()

def _start_resilient_worker(name, target):
    def runner():
        while not _stop_threads.is_set():
            try: target()
            except Exception:
                logging.exception(f"[WORKER-CRASH] {name} توقف؛ إعادة المحاولة بعد 5 ثوانٍ")
                report_admin_alert("خيط خلفي توقف", f"اسم الخيط: {name}\nسيتم تشغيله من جديد تلقائياً.")
            if not _stop_threads.is_set():
                _stop_threads.wait(5)
    thread = threading.Thread(target=runner, name=name, daemon=True)
    thread.start()
    return thread

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
            now = time.time()
            for uid in list(user_steps.keys()):
                st = user_steps.get(uid, {})
                if isinstance(st, dict) and (now - st.get("last_activity", 0)) > INACTIVITY_SECONDS:
                    user_steps[uid] = {"step": "await_phone", "last_activity": now}
            save_steps()
        except: pass

def _proxy_health_loop():
    time.sleep(3)
    while not _stop_threads.is_set():
        try:
            entries = _proxy_pool.all()
            if not entries:
                _stop_threads.wait(60); continue
            logging.info(f"[PROXY-HEALTH] فحص {len(entries)} بروكسي...")

            def _check_one(entry):
                if _stop_threads.is_set(): return
                res = proxy_check_sync(entry.url)
                _proxy_pool.update_health(entry.url, res.get("ok", False))
                status = "ok" if res.get("ok") else "fail"
                active = 1 if res.get("ok") else 0
                db_query("UPDATE proxies SET status=?, last_check=?, active=? WHERE url=?",
                         (status, time.time(), active, entry.url))

            threads = []
            sem = threading.Semaphore(20)
            def worker(e):
                with sem:
                    try: _check_one(e)
                    except: pass
            for e in entries:
                t = threading.Thread(target=worker, args=(e,), daemon=True)
                t.start(); threads.append(t)
            for t in threads:
                t.join(timeout=PROXY_HEALTH_TIMEOUT + 5)

            healthy = _proxy_pool.healthy_count()
            logging.info(f"[PROXY-HEALTH] ✅ {healthy}/{len(entries)} سليم")
            if healthy == 0:
                report_admin_alert("⚠️ لا يوجد بروكسي سليم",
                                   f"كل البروكسيات الـ {len(entries)} فشلت في الفحص!")
        except Exception as e:
            logging.error(f"[PROXY-HEALTH] {e}")
        _stop_threads.wait(PROXY_HEALTH_INTERVAL)

def _lease_cleanup_worker():
    while not _stop_threads.is_set():
        try:
            _proxy_pool.cleanup_expired_leases()
        except Exception as e:
            logging.error(f"[LEASE-CLEANUP] {e}")
        _stop_threads.wait(60)

# ==================== نصوص ====================
WELCOME_HEADER = ("مرحبا بك في موح بوت 👋\n\n"
    "بوت موح يقدم تفعيل عروض انترنت في مختلف الشبكات الجزائرية 🇩🇿\n\n"
    "1️⃣ • أدخل الرقم 📱\n2️⃣ • أكمل الخطوات ✅\n"
    "3️⃣ • إختر عرض مناسب 🛒\n4️⃣ • انتظار الرد ... 🔍")
WELCOME_FOOTER = "للبدء أرسل رقم هاتفك 📱"
OTP_MSG = ("✅ <b>تم إرسال الرمز بنجاح</b>\n\n"
           "📩 تفقد رسائل هاتفك، ثم أرسل الرمز المكوّن من 6 أرقام هنا 📱\n"
           "⏱️ الرمز صالح لفترة محدودة.")

SOCCER_CLUB_NAMES = {
    "MCA": "مولودية الجزائر", "MCO": "مولودية وهران", "JSS": "شبيبة الساورة",
    "MOB": "مولودية بجاية", "JSD": "شبيبة الجلفة",
}

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

async def send_otp_message(cid, display, full, markup=None):
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

def notify_mask(phone):
    if not phone: return "غير متوفر"
    value = str(phone)
    if value.startswith("213"): value = "0" + value[3:]
    if len(value) >= 7: return value[:4] + "****" + value[-2:]
    return "****"

async def notify_group_success(offer_name, network, uid=None, phone=None):
    if not NOTIFY_GROUP: return
    try:
        display_name = "مستخدم"
        if uid:
            try:
                chat = await bot.get_chat(uid)
                parts = [getattr(chat, "first_name", ""), getattr(chat, "last_name", "")]
                display_name = " ".join(p for p in parts if p).strip()
                if not display_name and getattr(chat, "username", ""):
                    display_name = "@" + chat.username
            except: pass
        display_name = _html.escape(display_name or "مستخدم")
        offer_name = _html.escape(str(offer_name))
        network = _html.escape(str(network))
        text = (f"✅ <b>تفعيل ناجح</b>\n━━━━━━━━━━━━━━━━\n"
                f"👤 <b>الزبون:</b> {display_name}\n"
                f"📱 <b>الرقم:</b> <code>{notify_mask(phone)}</code>\n"
                f"🌐 <b>الشبكة:</b> {network}\n"
                f"🎁 <b>العرض:</b> {offer_name}\n"
                f"⏱️ <b>الوقت:</b> {datetime.now().strftime('%H:%M:%S')}")
        await bot.send_message(NOTIFY_GROUP, text, parse_mode='HTML')
    except Exception as e: logging.error(f"[NOTIFY-GROUP] {e}")
    # 🆕 تحرير الحجز بعد النجاح
    if phone:
        _release_lease_for(phone, "offer_activated")

def expired_dz_btn(phone):
    m = InlineKeyboardMarkup(row_width=1)
    m.add(InlineKeyboardButton("🔄 إرسال رمز جديد", callback_data=f"resend_otp_{phone}"))
    m.add(InlineKeyboardButton("📱 إدخال الرقم من جديد", callback_data="change_phone"))
    m.add(InlineKeyboardButton("↩️ رجوع", callback_data="main_menu"))
    return m

def subscription_markup():
    m = InlineKeyboardMarkup(row_width=1)
    m.add(InlineKeyboardButton("📢 اشترك في القناة", url=CHANNEL_LINK))
    m.add(InlineKeyboardButton("🔄 تحقق من الاشتراك", callback_data="check_sub"))
    return m
    AVAILABLE_OFFERS = {
    "OFFREJEUNE1200": {"name": "🎁 IZZY 120","price": "120 دج","validity": "30 يوم","data": "10 جيجا","bonus": "يوتيوب", "description": "✅ 10 جيجا"},
    "DOVINTSPEEDMONTH30GoPRE": {"name": "🚀 1500 دج","price": "1500 دج","validity": "30 يوم","data": "60 جيجا","bonus": "سرعة", "description": "✅ 60 جيجا"},
    "DOVINTSPEEDMONTH15GoPRE": {"name": "🚀 1000 دج","price": "1000 دج","validity": "30 يوم","data": "30 جيجا","bonus": "سرعة", "description": "✅ 30 جيجا"},
    "DOVINTSPEEDMONTH6GoPRE": {"name": "🚀 500 دج","price": "500 دج","validity": "30 يوم","data": "12 جيجا","bonus": "سرعة", "description": "✅ 12 جيجا"},
    "DOVINTSPEEDWEEK3GoPRE": {"name": "🚀 300 دج","price": "300 دج","validity": "7 أيام","data": "10 جيجا","bonus": "سرعة", "description": "✅ 10 جيجا"},
    "DOVINTSPEEDWEEK2GoPRE": {"name": "🚀 150 دج","price": "150 دج","validity": "7 أيام","data": "4 جيجا","bonus": "سرعة", "description": "✅ 4 جيجا"},
    "DOVINTSPEEDDAY1GoPRE": {"name": "📱 100 Da - 2GB - 24H","price": "100 دج","validity": "24 ساعة","data": "2 جيجا","bonus": "سرعة", "description": "✅ 2 جيجا"},
    "DOVINTSPEEDDAY250MoPRE": {"name": "🚀 50 دج","price": "50 دج","validity": "24 ساعة","data": "600 ميجا","bonus": "سرعة", "description": "✅ 600 ميجا"},
    "DOVINTSPEEDDAY100MoPRE": {"name": "🚀 30 دج","price": "30 دج","validity": "24 ساعة","data": "300 ميجا","bonus": "سرعة", "description": "✅ 300 ميجا"},
    "MIXTEPRE1500": {"name": "🔄 MIXTE 1500","price": "1500 دج","validity": "30 يوم","data": "40 جيجا","bonus": "3000 دج", "description": "✅ 40 جيجا"},
    "MIXTEPRE1000": {"name": "🔄 MIXTE 1000","price": "1000 دج","validity": "30 يوم","data": "15 جيجا","bonus": "2000 دج", "description": "✅ 15 جيجا"},
    "MIXTEPRE100": {"name": "🔄 MIXTE 100","price": "100 دج","validity": "24 ساعة","data": "1 جيجا","bonus": "300 دج", "description": "✅ 1 جيجا"},
    "MIXTEONNET50": {"name": "🔄 MIXTE ON 50","price": "50 دج","validity": "24 ساعة","data": "60 دقيقة","bonus": "جيزي", "description": "✅ 60 دقيقة"},
    "FAMILY2000": {"name": "👨‍👩‍👧 FAMILY 2000","price": "2000 دج","validity": "30 يوم","data": "20 جيجا","bonus": "2000 دج", "description": "✅ 20 جيجا"},
    "FAMILY3000": {"name": "👨‍👩‍👧 FAMILY 3000","price": "3000 دج","validity": "30 يوم","data": "50 جيجا","bonus": "4000 دج", "description": "✅ 50 جيجا"},
    "FAMILY4000": {"name": "👨‍👩‍👧 FAMILY 4000","price": "4000 دج","validity": "30 يوم","data": "100 جيجا","bonus": "6000 دج", "description": "✅ 100 جيجا"},
    "BTL10GB72H": {"name": "📱 190 دج - 10GB","price": "190 دج","validity": "72 ساعة","data": "10 جيجا","bonus": "وطني", "description": "✅ 10 جيجا"},
    "BTL500MBDAY": {"name": "📱 90 دج - 5GB","price": "90 دج","validity": "24 ساعة","data": "5 جيجا","bonus": "وطني", "description": "✅ 5 جيجا"},
    "BTLDATA2WEEKS": {"name": "📱 400 دج - 4GB","price": "400 دج","validity": "15 يوم","data": "4 جيجا","bonus": "وطني", "description": "✅ 4 جيجا"},
    "2GBMONTH": {"name": "📱 250 دج - 3GB","price": "250 دج","validity": "30 يوم","data": "3 جيجا","bonus": "وطني", "description": "✅ 3 جيجا"},
    "1GBFB3DAY": {"name": "📱 70 Da - FB - 3GB - 72H","price": "70 دج","validity": "72 ساعة","data": "3 جيجا فيسبوك","bonus": "فيسبوك فقط", "description": "⚠️ فيسبوك فقط"},
    "BTLINTSPEEDDAY2Go": {"name": "📱 70 Da - 4GB - 24H","price": "70 دج","validity": "24 ساعة","data": "4 جيجا","bonus": "سرعة", "description": "✅ 4 جيجا"},
}

SPECIAL_BUNDLES = {
    "sp_yt_15d": {"icon": "▶️", "name": "يوتيوب", "app": "YT",
                  "validity": "Biweekly", "validity_ar": "15 يوم", "price": 100},
    "sp_yt_30d": {"icon": "▶️", "name": "يوتيوب", "app": "YT",
                  "validity": "Monthly",  "validity_ar": "شهر",   "price": 200},
}

INTERNET_BUNDLES = {
    "inet_5g":  {"icon": "🔴", "name": "5 جيجا - يوم", "code": "ATL_24H_DATA_90DZD_5Go", "data": "5 جيجا", "validity_ar": "يوم", "price": 90},
    "inet_10g": {"icon": "🟠", "name": "10 جيجا - 3 أيام", "code": "ATL_72H_DATA_190DZD_10Go", "data": "10 جيجا", "validity_ar": "3 أيام", "price": 190},
    "inet_30g": {"icon": "🟡", "name": "30 جيجا - أسبوع", "code": "ATL_7D_DATA_490DZD_30Go", "data": "30 جيجا", "validity_ar": "أسبوع", "price": 490},
}

NOUDJOUM_INFO_TEXT = (
    "⭐ <b>برنامج نجوم — Noudjoum</b>\n"
    "━━━━━━━━━━━━━━━━\n\n"
    "📖 <b>الوصف:</b>\n"
    "برنامج ولاء من Ooredoo يمنحك نقاط مقابل كل شحن،\n"
    "وتحوّلها إلى دقائق / SMS / إنترنت.\n\n"
    "🎁 <b>الفوائد:</b>\n"
    "• 💰 كل 250 دج شحن شهري = 5 نقاط\n"
    "• 🎉 مكافأة ترحيبية عند التسجيل\n"
    "• ⏳ النقاط صالحة 24 شهر\n\n"
    "📋 <b>الشروط:</b>\n"
    "✅ الرقم نشط\n"
    "✅ الشريحة مفعّلة منذ أكثر من 3 أشهر"
)

NOUDJOUM_SUCCESS_TEXT = (
    "🎉 <b>مبروك!</b>\n\n"
    "⭐ تم تسجيلك في برنامج نجوم بنجاح\n\n"
    "━━━━━━━━━━━━━━━━\n"
    "📱 <b>عمليات سريعة:</b>\n"
    "• <code>*511*1#</code> — رصيد النقاط\n"
    "• <code>*511*2#</code> — استبدال بدقائق\n"
    "• <code>*511*3#</code> — استبدال بجوائز"
)

NOUDJOUM_ALREADY_TEXT = (
    "✅ <b>أنت مسجّل مسبقاً في نجوم</b>\n\n"
    "📱 <code>*511*1#</code> — رصيد النقاط\n"
    "📱 <code>*511*2#</code> — استبدال بدقائق"
)

NOUDJOUM_LOCKED_TEXT = (
    "🔒 <b>غير مؤهل لبرنامج نجوم</b>\n\n"
    "❌ أحد الشروط التالية غير مستوفى:\n"
    "• الشريحة أقل من 3 أشهر\n"
    "• الرقم غير نشط\n\n"
    "📞 خدمة العملاء: <b>333</b>"
)

GIFT_INFO_TEXT = (
    "🎁 <b>إهداء اشتراك</b>\n"
    "━━━━━━━━━━━━━━━━\n\n"
    "📖 <b>الوصف:</b>\n"
    "أهدِ باقة إنترنت لأي رقم Ooredoo آخر.\n"
    "المبلغ يُخصم من <b>رصيدك</b>.\n\n"
    "⚠️ <b>ملاحظة:</b> لا يمكن الإهداء لنفس الرقم\n\n"
    "📱 <b>أدخل رقم المستفيد:</b>\n"
    "مثال: <code>05XXXXXXXX</code>"
)

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
        m.add(InlineKeyboardButton("🔧 إدارة البروكسي", callback_data="admin_proxy_menu"))
    return m

def all_offers_markup():
    m = InlineKeyboardMarkup(row_width=1)
    for code in ["DOVINTSPEEDMONTH30GoPRE","DOVINTSPEEDMONTH15GoPRE","DOVINTSPEEDMONTH6GoPRE",
                 "DOVINTSPEEDWEEK3GoPRE","DOVINTSPEEDWEEK2GoPRE","DOVINTSPEEDDAY1GoPRE",
                 "DOVINTSPEEDDAY250MoPRE","DOVINTSPEEDDAY100MoPRE",
                 "MIXTEPRE1500","MIXTEPRE1000","MIXTEPRE100","MIXTEONNET50",
                 "FAMILY2000","FAMILY3000","FAMILY4000","OFFREJEUNE1200","BTLINTSPEEDDAY2Go"]:
        if code in AVAILABLE_OFFERS:
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
    s = db_query("""SELECT total_1gb,total_2gb,total_3gb,total_offers,oo_logins,oo_snap,oo_youtube,
                    oo_byop30,oo_byop40,oo_bundles,oo_spins,oo_balance,oo_offers_view,dz_logins,
                    oo_gaming_view,oo_ff_bought,sp_yt,sp_ig,sp_fb,sp_wa,sp_tt,
                    inet_5g,inet_10g,inet_30g,oo_gifts,
                    sp_data_30g,sp_data_40g,sp_data_50g,sp_data_60g,sp_data_70g,sp_data_80g,sp_data_90g,
                    oo_soccer_enrolls,oo_stars_activated,oo_gifts_sent,oo_20dzd_1go,
                    oo_gift_plays,oo_gift_won,oo_gifts_total, oo_5dzd_5go, oo_free_2gb
                    FROM stats WHERE id=1""", fetch=True)
    if not s: s = (0,)*40
    while len(s) < 40: s = s + (0,)
    users = db_query("SELECT COUNT(*) FROM users", fetch=True)[0] or 0
    dz = db_query("SELECT COUNT(*) FROM numbers", fetch=True)[0] or 0
    lease = _proxy_pool.lease_stats()
    return (f"📊 <b>الإحصائيات</b>\n👥 {users} | 📱 {dz}\n\n"
            f"🔴 جيزي:\n  🎁 2G: {s[1]} | 3G: {s[2]}\n  💰 العروض: {s[3]}\n\n"
            f"🟠 أوريدو:\n  🔐: {s[4]}  👻: {s[5]}  🎡: {s[10]}\n"
            f"  ⚽️ Sport: {s[32]} | 🎮 FF: {s[15]}\n"
            f"  ⭐ نجوم: {s[33]} | 🎁 إهداءات: {s[34]}\n"
            f"  ⚡ 20دج-1Go: {s[35]} | ⚡ 5دج-5Go: {s[38]}\n"
            f"  🎁 2Go FREE: {s[39]}\n\n"
            f"🔒 Proxy Leases: {lease['leased']} / {lease['total']}\n"
            f"🟢 Free: {lease['free']} | 🔴 Dead: {lease['failed']}\n\n"
            f"⚡ تطبيقات: ▶️{s[16]} 📷{s[17]} 📘{s[18]} 💬{s[19]} 🎵{s[20]}\n"
            f"🌐 إنترنت: 🔴{s[21]} 🟠{s[22]} 🟡{s[23]}")

def oo_dynamic_menu(services, uid=None):
    m = InlineKeyboardMarkup(row_width=1)
    is_yooz = services.get("is_yooz", False)
    m.add(InlineKeyboardButton("💰 رصيدي", callback_data="oo_balance"))
    m.add(InlineKeyboardButton("📋 عروضي", callback_data="oo_my_offers"))
    if is_yooz:
        m.add(InlineKeyboardButton("👻 سناب", callback_data="oo_snap"))
    else:
        m.add(InlineKeyboardButton("👻 سناب 🔒", callback_data="oo_snap_locked"))
    if services.get("soccer_enrolled"):
        team = services.get("soccer_team", "")
        nm = SOCCER_CLUB_NAMES.get(team, team)
        m.add(InlineKeyboardButton(f"⚽️ {nm} ✅", callback_data="oo_soccer"))
    elif services.get("soccer_eligible"):
        m.add(InlineKeyboardButton("⚽️ Ooredoo Sport", callback_data="oo_soccer"))
    m.add(InlineKeyboardButton("⚡ عروض خاصة", callback_data="oo_special"))
    m.add(InlineKeyboardButton("🌐 إنترنت", callback_data="oo_internet"))
    m.add(InlineKeyboardButton("🎁 2Go FREE — 24H", callback_data="oo_quick_free_2gb"))
    m.add(InlineKeyboardButton("💳 5 دج — 5Go — 5H", callback_data="oo_quick_5dzd_5go"))
    m.add(InlineKeyboardButton("⚡ 20 دج — 1Go — 24H", callback_data="oo_quick_20_1g"))
    m.add(InlineKeyboardButton("🔄 تغيير الرقم", callback_data="oo_change"))
    m.add(InlineKeyboardButton("🗑️ حذف الرقم المحفوظ", callback_data="delete_my_number"))
    if uid and uid == ADMIN_ID:
        m.add(InlineKeyboardButton("📊 إحصائيات", callback_data="oo_stats"))
        m.add(InlineKeyboardButton("📋 سجل البوت", callback_data="admin_menu"))
        m.add(InlineKeyboardButton("🔧 إدارة البروكسي", callback_data="admin_proxy_menu"))
    return m

def oo_special_offers_markup():
    m = InlineKeyboardMarkup(row_width=1)
    for key, bi in SPECIAL_BUNDLES.items():
        m.add(InlineKeyboardButton(f"{bi['icon']} {bi['price']} دج - {bi['name']} ({bi['validity_ar']})", callback_data=f"oo_sp_sel_{key}"))
    m.add(InlineKeyboardButton("↩️ رجوع للقائمة", callback_data="oo_back_menu"))
    return m

def oo_internet_offers_markup():
    m = InlineKeyboardMarkup(row_width=1)
    for key, bi in INTERNET_BUNDLES.items():
        m.add(InlineKeyboardButton(f"{bi['icon']} {bi['price']} دج — {bi['data']}", callback_data=f"oo_inet_sel_{key}"))
    m.add(InlineKeyboardButton("↩️ رجوع للقائمة", callback_data="oo_back_menu"))
    return m

def oo_noudjoum_menu(state):
    m = InlineKeyboardMarkup(row_width=1)
    if state == "enrolled":
        m.add(InlineKeyboardButton("🔄 التحقق مجدداً", callback_data="oo_noudjoum_check"))
    elif state == "not_enrolled":
        m.add(InlineKeyboardButton("🌟 سجّل الآن في نجوم", callback_data="oo_noudjoum_enroll"))
    else:
        m.add(InlineKeyboardButton("🌟 سجّل الآن في نجوم", callback_data="oo_noudjoum_enroll"))
        m.add(InlineKeyboardButton("🔍 التحقق مجدداً", callback_data="oo_noudjoum_check"))
    m.add(InlineKeyboardButton("↩️ رجوع للقائمة", callback_data="oo_back_menu"))
    return m

def oo_dynamic_gift_menu(bundles, beneficiary=None):
    m = InlineKeyboardMarkup(row_width=1)
    for i, b in enumerate(bundles[:30]):
        price = b.get("price", "?")
        data_v = b.get("data", "")
        family = b.get("family", "")
        extras = b.get("extras", "")
        if "social" in family.lower(): icon = "📱"
        elif "smart" in family.lower(): icon = "✨"
        else: icon = "🌐"
        badges = ""
        if "YouTube" in extras: badges += "▶️"
        if "Snapchat" in extras: badges += "👻"
        if "مكالمات" in extras: badges += "📞"
        parts = [f"{price} دج"]
        if data_v: parts.append(str(data_v).replace("جيجا", "GB").replace("ميجا", "MB"))
        label = f"{icon}{badges} " + " | ".join(parts)
        m.add(InlineKeyboardButton(label[:60], callback_data=f"oo_gift_dyn_{i}"))
    m.add(InlineKeyboardButton("🔄 تحديث القائمة", callback_data="oo_gift_refresh"))
    m.add(InlineKeyboardButton("↩️ رجوع للقائمة", callback_data="oo_back_menu"))
    return m

def oo_format_gift_list_text(bundles, beneficiary=None):
    disp = ""
    if beneficiary:
        disp = "0" + beneficiary[3:] if beneficiary.startswith("213") else beneficiary
    lines = ["🎁 <b>قائمة العروض للإهداء</b>", "━━━━━━━━━━━━━━━━"]
    if disp: lines.append(f"📱 <b>المستفيد:</b> <code>{disp}</code>")
    lines.append(f"📦 <b>عدد العروض:</b> {len(bundles)}")
    lines.append("")
    for i, b in enumerate(bundles[:30]):
        price = b.get("price", "?")
        name = b.get("name") or b.get("code") or ""
        data_v = b.get("data", ""); extras = b.get("extras", "")
        validity = b.get("validity", ""); family = b.get("family", "")
        if "social" in family.lower(): icon = "📱"
        elif "smart" in family.lower(): icon = "✨"
        else: icon = "🌐"
        lines.append(f"<b>{i+1}.</b> {icon} <b>{name}</b>")
        if data_v: lines.append(f"   🌐 البيانات: {data_v}")
        if extras: lines.append(f"   ➕ الإضافات: {extras}")
        if validity: lines.append(f"   ⏱️ الصلاحية: {validity}")
        lines.append(f"   💳 السعر: <b>{price} دج</b>")
        lines.append("")
    lines.append("━━━━━━━━━━━━━━━━")
    lines.append("👇 <b>اختر عرضاً من الأزرار:</b>")
    return "\n".join(lines)

# ==================== DZ helpers ====================
async def _dz_request_new_otp(uid, phone):
    display = dz_mask(phone)
    loading_msg = None
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
        user_steps[uid] = {"step": "dz_verify_otp", "phone": phone,
                           "display": display, "last_activity": time.time()}
    else:
        _release_lease_for(phone, "otp_send_failed")
        await bot.send_message(uid,
            f"⚠️ <b>انتهت الجلسة</b>\n\n📱 <code>{display}</code>\n\n"
            f"❌ تعذر إرسال رمز تلقائياً",
            reply_markup=expired_dz_btn(phone), parse_mode='HTML')

async def show_dz_balance(uid, phone):
    row = db_query("SELECT token FROM numbers WHERE phone=? AND user_id=?", (phone, uid), fetch=True)
    if not row or not row[0] or row[0] == "EXPIRED":
        await _dz_request_new_otp(uid, phone)
        return
    result = await asyncio.to_thread(dj_check_balance, row[0], phone)
    if result.get("status") == "EXPIRED":
        db_query("UPDATE numbers SET token='EXPIRED' WHERE phone=? AND user_id=?", (phone, uid))
        await _dz_request_new_otp(uid, phone)
        return
    if result.get("status") == "FAILED":
        await bot.send_message(uid,
            "❌ <b>تعذر جلب الرصيد</b>\n\n"
            "💡 جرّب بعد دقيقة، أو أرسل رقمك من جديد",
            reply_markup=back_btn("main_menu"), parse_mode='HTML'); return
    bal = result.get("balance", 0); due = result.get("due", 0)
    text = (f"💳 <b>رصيد الرقم</b>\n\n📱 <code>{dz_mask(phone)}</code>\n"
            f"━━━━━━━━━━━━━━━\n💰 <b>الرصيد: {bal} دج</b>\n")
    if due > 0: text += f"⚠️ <b>الدين: {due} دج</b>\n"
    text += f"━━━━━━━━━━━━━━━"
    await bot.send_message(uid, text, reply_markup=back_btn("main_menu"), parse_mode='HTML')

async def dz_process(uid, phone, action):
    row = db_query("SELECT token FROM numbers WHERE phone=? AND user_id=?", (phone, uid), fetch=True)
    if not row or row[0] == "EXPIRED":
        await _dz_request_new_otp(uid, phone)
        return
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
            await notify_group_success("2GB أسبوعي", "Djezzy 🔴", uid, phone)
            await send_result(uid, f"✅ <b>تم التفعيل بنجاح</b> 🎉\n\n📱 <code>{dz_mask(phone)}</code>\n🎁 2 جيجا", "main_menu")
        elif res == "EXPIRED":
            db_query("UPDATE numbers SET token='EXPIRED' WHERE phone=?", (phone,))
            await _dz_request_new_otp(uid, phone)
            return
        elif res == "LIMIT":
            await bot.send_message(uid, "⚠️ <b>لم تكمل الأسبوع بعد</b>", reply_markup=back_btn("main_menu"))
        elif res == "NO_BALANCE":
            await bot.send_message(uid, "❌ <b>الرصيد غير كافي</b>", reply_markup=back_btn("main_menu"))
        elif res == "NOT_ALLOWED":
            await bot.send_message(uid, "❌ <b>هذه العملية غير متوفرة</b>",
                reply_markup=back_btn("main_menu"), parse_mode='HTML')
        else:
            await bot.send_message(uid, "❌ فشل التفعيل", reply_markup=back_btn("main_menu"))

async def send_dz_menu(uid, phone=None):
    if not phone:
        nums = db_query("SELECT phone FROM numbers WHERE user_id=? ORDER BY added_date DESC LIMIT 1", (uid,), fetchall=True)
        if nums and nums[0]: phone = nums[0][0]
    if phone:
        txt = f"📱 الرقم : <code>{dz_mask(phone)}</code> ✅\n🔴 الشبكة : <b>جيزي</b>\n\nاختر العرض 🔽"
    else: txt = "🔴 اختر العرض 🔽"
    try:
        await bot.send_message(uid, txt, reply_markup=main_menu_markup(uid), parse_mode='HTML')
    except Exception as e:
        if "Forbidden" in str(e): logging.warning(f"[USER-BLOCKED] {uid}")
        else: logging.error(f"[DZ-MENU] {uid}: {e}")

async def oo_detect_plan(msisdn, at, meta):
    async def safe(fn, *args):
        try: return await asyncio.to_thread(fn, *args)
        except: return {"status": "error"}
    prof_r, bal_r, snake_r = await asyncio.gather(
        safe(oo_get_profile, msisdn, at, meta),
        safe(oo_check_balance, msisdn, at, meta),
        safe(oo_get_available_snakes, msisdn, at, meta),
        return_exceptions=True,
    )
    s = {"rate_plan": "", "balance_value": 0,
         "spin_available": False, "spin_played": False,
         "soccer_eligible": False, "soccer_enrolled": False,
         "soccer_team": "", "is_dima": False, "is_yooz": False,
         "activation_date": "", "months_active": 0,
         "gift_count": 0}
    qd = oo_quick_detect(at)
    s["rate_plan"] = qd.get("rate_plan") or ""
    s["is_dima"] = qd.get("is_dima", False)
    s["is_yooz"] = qd.get("is_yooz", False)
    if isinstance(prof_r, dict) and prof_r.get("status") == "ok":
        d = prof_r.get("data", {})
        rp = str(d.get("ratePlan") or "").strip()
        if rp:
            s["rate_plan"] = rp
            rp_up = rp.upper().replace("'", "").replace(" ", "")
            s["is_dima"] = ("DIMA" in rp_up)
            s["is_yooz"] = ("YOOZ" in rp_up)
        start = d.get("startDate") or ""
        if start:
            s["activation_date"] = start
            try:
                sd = datetime.fromisoformat(start.replace("Z", "+00:00"))
                now_dt = datetime.now(tz.utc)
                days = (now_dt - sd).days
                s["months_active"] = days // 30
            except: pass
    if isinstance(bal_r, dict) and bal_r.get("status") == "ok":
        try: s["balance_value"] = float(bal_r.get("data", {}).get("accountBalance", 0) or 0)
        except: pass
    if isinstance(snake_r, dict) and snake_r.get("status") == "ok":
        try: s["gift_count"] = len(snake_r.get("snakes", []))
        except: pass
    return s

async def send_oo_menu(uid, user):
    ms = user["msisdn"]; at = user["access_token"]
    qd = oo_quick_detect(at)
    services = {
        "rate_plan": qd.get("rate_plan") or "",
        "is_yooz": qd.get("is_yooz", False),
        "is_dima": qd.get("is_dima", False),
        "balance_value": 0,
        "spin_available": False, "spin_played": False,
        "soccer_eligible": False, "soccer_enrolled": False, "soccer_team": "",
        "activation_date": "", "months_active": 0, "gift_count": 0,
    }
    rp = services.get("rate_plan") or ""
    lines = [f"📱 الرقم : <code>{o_mask(ms)}</code> ✅"]
    if rp: lines.append(f"📦 العرض : <b>{rp}</b>")
    lines.append(f"💰 الرصيد : <b>...</b>")
    lines.append("")
    lines.append("اختر الخدمة 🔽")
    try:
        msg = await bot.send_message(uid, "\n".join(lines),
            reply_markup=oo_dynamic_menu(services, uid), parse_mode='HTML')
    except Exception as e:
        if "Forbidden" in str(e): logging.warning(f"[USER-BLOCKED] {uid}")
        else: logging.error(f"[OO-MENU] {uid}: {e}")
        return
    asyncio.create_task(_update_oo_menu_bg(uid, user, msg.message_id))

async def _update_oo_menu_bg(uid, user, msg_id):
    try:
        ms = user["msisdn"]; at = user["access_token"]
        meta = {k: user.get(k, "") for k in ["tok_instance_id","tok_plat_sig","tok_fingerprint","tok_timestamp"]}
        new_services = await oo_detect_plan(ms, at, meta)
        rp = new_services.get("rate_plan") or ""
        bal = new_services.get("balance_value", 0)
        months = new_services.get("months_active", 0)
        act_date = new_services.get("activation_date", "")
        gift_n = new_services.get("gift_count", 0)
        lines = [f"📱 الرقم : <code>{o_mask(ms)}</code> ✅"]
        if rp: lines.append(f"📦 العرض : <b>{rp}</b>")
        lines.append(f"💰 الرصيد : <b>{bal} دج</b>")
        if gift_n > 0:
            lines.append(f"🎁 اللفات المتاحة : <b>{gift_n}</b>")
        if act_date:
            try:
                sd = datetime.fromisoformat(act_date.replace("Z", "+00:00"))
                date_str = sd.strftime("%Y-%m-%d")
                if months > 0:
                    lines.append(f"📅 الشريحة : <b>{date_str}</b> ({months} شهر)")
                else:
                    lines.append(f"📅 الشريحة : <b>{date_str}</b>")
            except: pass
        lines.append("")
        lines.append("اختر الخدمة 🔽")
        await bot.edit_message_text("\n".join(lines),
            chat_id=uid, message_id=msg_id,
            reply_markup=oo_dynamic_menu(new_services, uid),
            parse_mode='HTML')
    except Exception as e:
        logging.debug(f"[OO-MENU-UPDATE] {e}")

# ==================== Admin ====================
def admin_menu_markup():
    m = InlineKeyboardMarkup(row_width=1)
    m.add(InlineKeyboardButton("📊 الإحصائيات", callback_data="bot_stats"))
    m.add(InlineKeyboardButton("📋 آخر السجلات", callback_data="admin_log"))
    m.add(InlineKeyboardButton("🎁 سجل 2Go FREE", callback_data="admin_log_2g"))
    m.add(InlineKeyboardButton("⚠️ الأخطاء والتحذيرات", callback_data="admin_log_err"))
    m.add(InlineKeyboardButton("🗑️ مسح السجل", callback_data="admin_log_clear"))
    m.add(InlineKeyboardButton("🔧 إدارة البروكسي", callback_data="admin_proxy_menu"))
    m.add(InlineKeyboardButton("↩️ رجوع للقائمة", callback_data="main_menu"))
    return m

def admin_proxy_menu_markup():
    m = InlineKeyboardMarkup(row_width=1)
    stats = _proxy_pool.lease_stats()
    m.add(InlineKeyboardButton(
        f"📊 Pool: 🔒{stats['leased']} 🟢{stats['free']} 🔴{stats['failed']}",
        callback_data="admin_proxy_stats"))
    m.add(InlineKeyboardButton("➕ إضافة بروكسي واحد", callback_data="admin_proxy_add"))
    m.add(InlineKeyboardButton("📥 استيراد دفعة بروكسيات", callback_data="admin_proxy_import"))
    m.add(InlineKeyboardButton("📋 قائمة البروكسيات", callback_data="admin_proxy_list"))
    m.add(InlineKeyboardButton("🔄 فحص الكل الآن", callback_data="admin_proxy_check_all"))
    m.add(InlineKeyboardButton("🗑️ حذف بروكسي", callback_data="admin_proxy_del_menu"))
    m.add(InlineKeyboardButton("↩️ رجوع", callback_data="admin_menu"))
    return m

def admin_proxy_list_text(page=0, per_page=10):
    entries = _proxy_pool.all()
    if not entries: return "📋 <b>لا توجد بروكسيات</b>"
    now = time.time()
    entries.sort(key=lambda e: (e.status != "ok", e.total_uses))
    start = page * per_page
    page_entries = entries[start:start+per_page]
    lines = [f"📋 <b>البروكسيات ({start+1}-{min(start+per_page,len(entries))}/{len(entries)})</b>",
             "━━━━━━━━━━━━━━━━"]
    for i, e in enumerate(page_entries, start=start+1):
        if e.is_leased(now): icon = "🔒"
        elif e.is_available(now): icon = "🟢"
        else: icon = "🔴"
        try: host = e.url.split("@")[-1]
        except: host = e.url[:30]
        owner = f" → {e.owner_msisdn[-4:]}" if e.owner_msisdn else ""
        lines.append(f"{icon} <b>#{i}</b> <code>{host}</code>{owner}")
        lines.append(f"   ✅{e.success_count} | ❌{e.fail_count} | 🔄{e.total_uses}")
    return "\n".join(lines)

# ==================== Start ====================
@bot.message_handler(commands=['start'])
async def cmd_start(message):
    uid = message.from_user.id
    now = time.time()
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

@bot.message_handler(commands=['log'], chat_types=['private'])
async def cmd_log(message):
    if message.from_user.id != ADMIN_ID: return
    args = message.text.split(); n = 30
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

@bot.message_handler(commands=['proxystats'], chat_types=['private'])
async def cmd_proxystats(message):
    if message.from_user.id != ADMIN_ID: return
    stats = _proxy_pool.lease_stats()
    entries = _proxy_pool.all()
    total_uses = sum(e.total_uses for e in entries)
    total_ok = sum(e.success_count for e in entries)
    total_fail = sum(e.fail_count for e in entries)
    rate = (total_ok * 100 // total_uses) if total_uses else 0
    in_flight = sum(e.in_flight for e in entries)
    await bot.send_message(message.chat.id,
        f"📊 <b>حالة Proxy Pool</b>\n━━━━━━━━━━━━━━━━\n"
        f"📦 الإجمالي: <b>{stats['total']}</b>\n"
        f"🔒 محجوزة: <b>{stats['leased']}</b> | 🟢 حرة: <b>{stats['free']}</b> | 🔴 معطلة: <b>{stats['failed']}</b>\n"
        f"⚡ في التنفيذ: {in_flight}\n"
        f"🔄 استخدامات: <b>{total_uses}</b> | ✅{total_ok} ❌{total_fail}\n"
        f"📈 نسبة النجاح: <b>{rate}%</b>",
        parse_mode='HTML')

@bot.message_handler(commands=['leases'], chat_types=['private'])
async def cmd_leases(message):
    if message.from_user.id != ADMIN_ID: return
    with _proxy_pool._lock:
        active = [(m, u, _proxy_pool._entries[u]) for m, u in _proxy_pool._leases.items()
                  if u in _proxy_pool._entries]
    if not active:
        await bot.send_message(message.chat.id, "📭 لا توجد حجوزات نشطة"); return
    now = time.time()
    lines = [f"🔒 <b>الحجوزات النشطة ({len(active)})</b>", "━━━━━━━━━━━━━━━━"]
    for msisdn, url, e in active[:30]:
        remaining = max(0, int(e.lease_until - now))
        mins = remaining // 60
        host = url.split("@")[-1]
        lines.append(f"📱 <code>{notify_mask(msisdn)}</code> → <code>{host}</code>")
        lines.append(f"   ⏱️ متبقي: {mins} دقيقة")
    await bot.send_message(message.chat.id, "\n".join(lines), parse_mode='HTML')

# ==================== Main Callback Handler ====================
@bot.callback_query_handler(func=lambda call: True)
async def cb_handler(call):
    uid = call.from_user.id

    if call.data.startswith("resend_otp_"):
        target = call.data.replace("resend_otp_", "")
        try: await bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        await typing(uid)
        is_ooredoo = target.startswith("2135")
        if is_ooredoo:
            digits = "0" + target[3:]
            result = await asyncio.to_thread(ooredoo_send_otp_sync, target)
            if not result.get("otp_sent"):
                r = result.get("reason", ""); code = result.get("status", "?")
                if r == "rate_limit": msg = "⏳ <b>محاولات كثيرة</b>\n\n🔄 انتظر 60 ثانية"
                elif r == "network": msg = "❌ <b>مشكل في الاتصال</b>"
                else: msg = f"❌ <b>تعذر الإرسال</b>\n\n💡 كود: <code>{code}</code>"
                _release_lease_for(target, "resend_failed")
                await bot.send_message(uid, msg, parse_mode='HTML'); return
            user_steps[uid] = {"step": "oo_await_otp", "msisdn": target, "device": result["device"], "otp_attempts": 0, "last_activity": time.time()}
            mm = InlineKeyboardMarkup(); mm.add(InlineKeyboardButton("🔄 إعادة إرسال", callback_data=f"resend_otp_{target}"))
            await send_otp_message(uid, digits, target, mm)
        else:
            ok = await asyncio.to_thread(dj_request_otp, target)
            if ok:
                display = "0" + target[3:]
                mm = InlineKeyboardMarkup(); mm.add(InlineKeyboardButton("🔄 إعادة إرسال", callback_data=f"resend_otp_{target}"))
                await send_otp_message(uid, display, target, mm)
                user_steps[uid] = {"step": "dz_verify_otp", "phone": target, "display": display, "last_activity": time.time()}
            else:
                _release_lease_for(target, "resend_failed")
                mm = InlineKeyboardMarkup(row_width=1)
                mm.add(InlineKeyboardButton("📱 إدخال الرقم من جديد", callback_data="change_phone"))
                mm.add(InlineKeyboardButton("🔄 حاول مرة أخرى", callback_data=f"resend_otp_{target}"))
                await bot.send_message(uid, "❌ <b>تعذر إرسال الرمز</b>", reply_markup=mm, parse_mode='HTML')
        return

    if uid != ADMIN_ID and call.data != "check_sub" and not await check_subscription(uid):
        try: await bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        await bot.send_message(uid, "🔒 اشترك:", reply_markup=subscription_markup()); return
    try: await bot.delete_message(call.message.chat.id, call.message.message_id)
    except: pass
    await typing(uid)
    if uid in user_steps and isinstance(user_steps[uid], dict):
        user_steps[uid]["last_activity"] = time.time()

    # ==================== Admin Panel ====================
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
        await bot.send_message(uid, "🗑️ تم مسح السجل"); return

    # ==================== Proxy Management ====================
    if call.data == "admin_proxy_menu":
        if uid != ADMIN_ID: return
        await bot.send_message(uid, "🔧 <b>إدارة البروكسيات</b>", reply_markup=admin_proxy_menu_markup(), parse_mode='HTML'); return
    if call.data == "admin_proxy_stats":
        if uid != ADMIN_ID: return
        stats = _proxy_pool.lease_stats()
        entries = _proxy_pool.all()
        total_uses = sum(e.total_uses for e in entries)
        total_ok = sum(e.success_count for e in entries)
        total_fail = sum(e.fail_count for e in entries)
        rate = (total_ok * 100 // total_uses) if total_uses else 0
        in_flight = sum(e.in_flight for e in entries)
        text = (
            f"📊 <b>حالة Proxy Pool</b>\n━━━━━━━━━━━━━━━━\n"
            f"📦 الإجمالي: <b>{stats['total']}</b>\n"
            f"🔒 محجوزة الآن: <b>{stats['leased']}</b>\n"
            f"🟢 حرة: <b>{stats['free']}</b>\n"
            f"🔴 معطّلة: <b>{stats['failed']}</b>\n"
            f"⚡ في التنفيذ: <b>{in_flight}</b>\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"🔄 استخدامات: <b>{total_uses}</b>\n"
            f"✅ ناجح: {total_ok} | ❌ فاشل: {total_fail}\n"
            f"📈 نسبة النجاح: <b>{rate}%</b>\n"
            f"⏱️ TTL الحجز: {PROXY_LEASE_TTL//60} دقيقة\n"
            f"🔄 فحص كل: {PROXY_HEALTH_INTERVAL//60} دقيقة"
        )
        await bot.send_message(uid, text,
            reply_markup=back_btn("admin_proxy_menu"), parse_mode='HTML'); return
    if call.data == "admin_proxy_list":
        if uid != ADMIN_ID: return
        await bot.send_message(uid, admin_proxy_list_text(0),
            reply_markup=back_btn("admin_proxy_menu"), parse_mode='HTML'); return
    if call.data == "admin_proxy_add":
        if uid != ADMIN_ID: return
        user_steps[uid] = {"step": "proxy_await_url", "last_activity": time.time()}
        await bot.send_message(uid,
            "➕ <b>إضافة بروكسي</b>\n\n"
            "📋 الصيغة:\n"
            "<code>http://user:pass@host:port</code>\n"
            "<code>user:pass@host:port</code>\n"
            "<code>ip:port</code>\n\n"
            "❌ للإلغاء: <code>إلغاء</code>",
            reply_markup=back_btn("admin_proxy_menu"), parse_mode='HTML'); return
    if call.data == "admin_proxy_import":
        if uid != ADMIN_ID: return
        user_steps[uid] = {"step": "proxy_await_bulk", "last_activity": time.time()}
        await bot.send_message(uid,
            "📥 <b>استيراد دفعة</b>\n\n"
            "📝 سطر لكل بروكسي (حد أقصى 500)\n"
            "❌ للإلغاء: <code>إلغاء</code>",
            reply_markup=back_btn("admin_proxy_menu"), parse_mode='HTML'); return
    if call.data == "admin_proxy_check_all":
        if uid != ADMIN_ID: return
        entries = _proxy_pool.all()
        if not entries:
            await bot.send_message(uid, "📭 لا توجد بروكسيات", reply_markup=back_btn("admin_proxy_menu")); return
        msg = await bot.send_message(uid, f"🔄 جاري فحص {len(entries)} بروكسي...")
        ok_count = 0
        lock = threading.Lock()
        sem = threading.Semaphore(20)
        def _check(e):
            nonlocal ok_count
            with sem:
                res = proxy_check_sync(e.url)
                _proxy_pool.update_health(e.url, res.get("ok", False))
                db_query("UPDATE proxies SET status=?, last_check=?, active=? WHERE url=?",
                         ("ok" if res["ok"] else "fail", time.time(),
                          1 if res["ok"] else 0, e.url))
                if res["ok"]:
                    with lock: ok_count += 1
        threads = [threading.Thread(target=_check, args=(e,), daemon=True) for e in entries]
        for t in threads: t.start()
        for t in threads: t.join(timeout=PROXY_HEALTH_TIMEOUT + 3)
        try: await bot.delete_message(uid, msg.message_id)
        except: pass
        await bot.send_message(uid,
            f"✅ <b>تم الفحص</b>\n\n🟢 ناجح: {ok_count}\n🔴 فاشل: {len(entries)-ok_count}",
            reply_markup=back_btn("admin_proxy_menu"), parse_mode='HTML'); return
    if call.data == "admin_proxy_del_menu":
        if uid != ADMIN_ID: return
        entries = _proxy_pool.all()
        if not entries:
            await bot.send_message(uid, "📭 لا توجد بروكسيات", reply_markup=back_btn("admin_proxy_menu")); return
        m = InlineKeyboardMarkup(row_width=1)
        for i, e in enumerate(entries[:30], 1):
            try: host = e.url.split("@")[-1]
            except: host = e.url[:25]
            icon = "🟢" if e.status == "ok" else ("🔴" if e.status == "fail" else "🟡")
            m.add(InlineKeyboardButton(f"{icon} #{i} {host}", callback_data=f"admin_proxy_delok_{i-1}"))
        m.add(InlineKeyboardButton("↩️ رجوع", callback_data="admin_proxy_menu"))
        await bot.send_message(uid, "🗑️ <b>اختر بروكسي للحذف:</b>", reply_markup=m, parse_mode='HTML'); return
    if call.data.startswith("admin_proxy_delok_"):
        if uid != ADMIN_ID: return
        try: idx = int(call.data.replace("admin_proxy_delok_", ""))
        except: return
        entries = _proxy_pool.all()
        if 0 <= idx < len(entries):
            target = entries[idx]
            db_query("DELETE FROM proxies WHERE url=?", (target.url,))
            _proxy_pool.remove(target.url)
            await bot.send_message(uid, f"✅ <b>تم الحذف</b>\n<code>{target.url[:60]}</code>",
                reply_markup=back_btn("admin_proxy_menu"), parse_mode='HTML')
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
        # 🆕 حرر leases
        user = oo_load(uid)
        if user and user.get("msisdn"): _release_lease_for(user["msisdn"], "delete_number")
        dz_row = db_query("SELECT phone FROM numbers WHERE user_id=? LIMIT 1", (uid,), fetch=True)
        if dz_row: _release_lease_for(dz_row[0], "delete_number")
        db_query("DELETE FROM numbers WHERE user_id=?", (uid,))
        oo_clear(uid); dz_clear_session(uid)
        user_steps[uid] = {"step": "await_phone", "last_activity": time.time()}
        await bot.send_message(uid, "✅ <b>تم الحذف</b>\n\n💡 أرسل رقمك من جديد", reply_markup=back_btn("main_menu"), parse_mode='HTML'); return

    if call.data.startswith("oo_"):
        await oo_cb_handler(call); return

    # ==================== DZ Callbacks ====================
    if call.data == "quick_offer_70_4g":
        nums = db_query("SELECT phone FROM numbers WHERE user_id=? ORDER BY added_date DESC LIMIT 1", (uid,), fetchall=True)
        if not nums: await bot.send_message(uid, "⚠️ أضف رقماً.", reply_markup=back_btn("main_menu")); return
        ph = nums[0][0]
        row = db_query("SELECT token FROM numbers WHERE phone=? AND user_id=?", (ph, uid), fetch=True)
        if not row or row[0] == "EXPIRED":
            await _dz_request_new_otp(uid, ph); return
        bal = await asyncio.to_thread(dj_check_balance, row[0], ph)
        if bal.get("status") == "EXPIRED":
            db_query("UPDATE numbers SET token='EXPIRED' WHERE phone=?", (ph,))
            await _dz_request_new_otp(uid, ph); return
        cur = bal.get("balance", 0)
        if cur < 70:
            await bot.send_message(uid, f"❌ <b>الرصيد غير كافي</b>\n💰 {cur} دج", reply_markup=back_btn("main_menu"), parse_mode='HTML'); return
        result = await dz_activate_offer_70_4g_async(row[0], ph)
        if result.get("token_expired"):
            db_query("UPDATE numbers SET token='EXPIRED' WHERE phone=?", (ph,))
            await _dz_request_new_otp(uid, ph); return
        if result.get("success"):
            db_query("UPDATE numbers SET last_activation_offers=? WHERE phone=?", (time.time(), ph))
            inc_stat("total_offers")
            await notify_group_success("70دج — 4GB", "Djezzy 🔴", uid, ph)
            await bot.send_message(uid, result["msg"], parse_mode='HTML', reply_markup=main_menu_markup(uid))
        else:
            await bot.send_message(uid, result["msg"], parse_mode='HTML', reply_markup=back_btn("main_menu"))
        return

    if call.data == "quick_offer_90_5g":
        nums = db_query("SELECT phone FROM numbers WHERE user_id=? ORDER BY added_date DESC LIMIT 1", (uid,), fetchall=True)
        if not nums: await bot.send_message(uid, "⚠️ أضف رقماً.", reply_markup=back_btn("main_menu")); return
        ph = nums[0][0]
        row = db_query("SELECT token FROM numbers WHERE phone=? AND user_id=?", (ph, uid), fetch=True)
        if not row or row[0] == "EXPIRED":
            await _dz_request_new_otp(uid, ph); return
        bal = await asyncio.to_thread(dj_check_balance, row[0], ph)
        if bal.get("status") == "EXPIRED":
            db_query("UPDATE numbers SET token='EXPIRED' WHERE phone=?", (ph,))
            await _dz_request_new_otp(uid, ph); return
        cur = bal.get("balance", 0)
        if cur < 90:
            await bot.send_message(uid, f"❌ <b>الرصيد غير كافي</b>\n💰 {cur} دج", reply_markup=back_btn("main_menu"), parse_mode='HTML'); return
        result = await dz_activate_offer_90_5g_async(row[0], ph)
        if result.get("token_expired"):
            db_query("UPDATE numbers SET token='EXPIRED' WHERE phone=?", (ph,))
            await _dz_request_new_otp(uid, ph); return
        if result.get("success"):
            db_query("UPDATE numbers SET last_activation_offers=? WHERE phone=?", (time.time(), ph))
            inc_stat("total_offers")
            await notify_group_success("90دج — 5GB", "Djezzy 🔴", uid, ph)
            await bot.send_message(uid, result["msg"], parse_mode='HTML', reply_markup=main_menu_markup(uid))
        else:
            await bot.send_message(uid, result["msg"], parse_mode='HTML', reply_markup=back_btn("main_menu"))
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
            if not row or row[0] == "EXPIRED":
                await _dz_request_new_otp(uid, ph); return
            o = AVAILABLE_OFFERS.get(code, {"name": "العرض", "price": "?"})
            price = dj_extract_price(o.get('price', '0')) or 0
            bal = await asyncio.to_thread(dj_check_balance, row[0], ph)
            if bal.get("status") == "EXPIRED":
                db_query("UPDATE numbers SET token='EXPIRED' WHERE phone=?", (ph,))
                await _dz_request_new_otp(uid, ph); return
            cur = bal.get("balance", 0)
            if price > 0 and cur < price:
                await bot.send_message(uid, f"❌ <b>الرصيد غير كافي</b>\n💰 {cur} دج",
                    reply_markup=back_btn("main_menu"), parse_mode='HTML'); return
            kb = InlineKeyboardMarkup(row_width=2)
            kb.add(InlineKeyboardButton("✅ تأكيد", callback_data=f"dzconfirm_offer_{code}_{ph}"),
                   InlineKeyboardButton("❌ إلغاء", callback_data="main_menu"))
            await bot.send_message(uid, f"💰 <b>{cur} دج</b> → <b>{o['name']}</b>\n💳 {price} دج\n\nهل تريد التفعيل؟",
                reply_markup=kb, parse_mode='HTML')
        return
    if call.data.startswith("dzconfirm_offer_"):
        rest = call.data.replace("dzconfirm_offer_", ""); code, ph = rest.rsplit("_", 1)
        row = db_query("SELECT token FROM numbers WHERE phone=? AND user_id=?", (ph, uid), fetch=True)
        if not row or row[0] == "EXPIRED":
            await _dz_request_new_otp(uid, ph); return
        o = AVAILABLE_OFFERS.get(code, {"name": "العرض", "price": "?"})
        price = dj_extract_price(o.get('price', '0')) or 0
        offer_type = "shake" if code.startswith("BTL") else "activate"
        result = await dz_activate_paid_offer_async(row[0], ph, code, offer_type, o.get('name', 'العرض'), price)
        if result.get("token_expired"):
            db_query("UPDATE numbers SET token='EXPIRED' WHERE phone=?", (ph,))
            await _dz_request_new_otp(uid, ph); return
        if result.get("success"):
            db_query("UPDATE numbers SET last_activation_offers=? WHERE phone=?", (time.time(), ph))
            inc_stat("total_offers")
            await notify_group_success(o.get('name', 'العرض'), "Djezzy 🔴", uid, ph)
            await bot.send_message(uid, result["msg"], parse_mode='HTML', reply_markup=main_menu_markup(uid))
        else:
            await bot.send_message(uid, result["msg"], parse_mode='HTML', reply_markup=back_btn("main_menu"))
        return
    if call.data == "bot_stats":
        if uid != ADMIN_ID: await bot.send_message(uid, "⛔"); return
        await bot.send_message(uid, get_stats_text(), reply_markup=back_btn("main_menu"), parse_mode='HTML'); return
    if call.data in ("main_menu", "back_main"):
        if oo_load(uid) and not db_query("SELECT 1 FROM numbers WHERE user_id=?", (uid,), fetch=True):
            await send_oo_menu(uid, oo_load(uid))
        else:
            await send_dz_menu(uid)
        return
    if call.data == "change_phone":
        # 🆕 حرر leases
        user = oo_load(uid)
        if user and user.get("msisdn"): _release_lease_for(user["msisdn"], "change_phone")
        dz_row = db_query("SELECT phone FROM numbers WHERE user_id=? LIMIT 1", (uid,), fetch=True)
        if dz_row: _release_lease_for(dz_row[0], "change_phone")
        oo_clear(uid); dz_clear_session(uid)
        user_steps[uid] = {"step": "await_phone", "last_activity": time.time()}
        await send_welcome(uid); return

# ==================== TEXT HANDLER ====================
@bot.message_handler(func=lambda m: True, content_types=['text'], chat_types=['private'])
async def handle_text(message):
    uid = message.from_user.id
    text = message.text.strip()
    if not await check_subscription(uid):
        await cmd_start(message); return
    now = time.time()
    cur_step = user_steps.get(uid, {}).get("step", "")
    last_activity = user_steps.get(uid, {}).get("last_activity", 0)

    if cur_step == "proxy_await_url" and uid == ADMIN_ID:
        if text.lower() in ("إلغاء", "cancel"):
            user_steps[uid] = {"step": "await_phone", "last_activity": now}
            await bot.send_message(uid, "✅ تم الإلغاء", reply_markup=admin_proxy_menu_markup()); return
        u = _normalize_proxy(text)
        if not u:
            await bot.send_message(uid, "❌ صيغة غير صحيحة"); return
        msg = await bot.send_message(uid, "⏳ جاري فحص البروكسي...")
        check = await asyncio.to_thread(proxy_check_sync, u)
        try: await bot.delete_message(uid, msg.message_id)
        except: pass
        if check["ok"]:
            name = activate_proxy_url(u)
            await bot.send_message(uid,
                f"✅ <b>تمت الإضافة!</b>\n\n"
                f"🏷️ الاسم: <b>{name}</b>\n"
                f"🎯 الهدف: {check.get('target','?')}\n"
                f"📊 Pool: {_proxy_pool.healthy_count()}/{len(_proxy_pool.all())}",
                reply_markup=admin_proxy_menu_markup(), parse_mode='HTML')
        else:
            db_query("INSERT OR IGNORE INTO proxies "
                     "(name, url, is_default, active, status, last_check, added_date, source) "
                     "VALUES (?,?,?,?,?,?,?,?)",
                     ("Proxy-Failed", u, 0, 0, "fail", time.time(),
                      datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "manual"))
            await bot.send_message(uid,
                f"❌ <b>فشل الفحص</b>\n\nالسبب: <code>{check.get('error','unknown')}</code>",
                reply_markup=admin_proxy_menu_markup(), parse_mode='HTML')
        user_steps[uid] = {"step": "await_phone", "last_activity": now}
        return

    if cur_step == "proxy_await_bulk" and uid == ADMIN_ID:
        if text.lower() in ("إلغاء", "cancel"):
            user_steps[uid] = {"step": "await_phone", "last_activity": now}
            await bot.send_message(uid, "✅ تم الإلغاء", reply_markup=admin_proxy_menu_markup()); return
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        if not lines:
            await bot.send_message(uid, "❌ لا يوجد أي بروكسي"); return
        msg = await bot.send_message(uid, f"⏳ جاري فحص {len(lines)} بروكسي...\n(قد يأخذ دقيقة)")
        added, failed = 0, 0
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sem = threading.Semaphore(15)
        lock = threading.Lock()
        to_add = []
        def _chk(raw):
            nonlocal added, failed
            u = _normalize_proxy(raw)
            if not u:
                with lock: failed += 1
                return
            with sem:
                chk = proxy_check_sync(u)
                if chk["ok"]:
                    with lock:
                        added += 1
                        to_add.append((u, f"Imported-{added}"))
                else:
                    with lock: failed += 1
                    db_query("INSERT OR IGNORE INTO proxies "
                             "(name, url, is_default, active, status, last_check, added_date, source) "
                             "VALUES (?,?,?,?,?,?,?,?)",
                             ("Imported-Fail", u, 0, 0, "fail", time.time(), stamp, "imported"))
        threads = [threading.Thread(target=_chk, args=(raw,), daemon=True) for raw in lines[:500]]
        for t in threads: t.start()
        for t in threads: t.join(timeout=PROXY_HEALTH_TIMEOUT + 5)
        for u, name in to_add:
            db_query("INSERT OR IGNORE INTO proxies "
                     "(name, url, is_default, active, status, last_check, added_date, source) "
                     "VALUES (?,?,?,?,?,?,?,?)",
                     (name, u, 0, 1, "ok", time.time(), stamp, "imported"))
            _proxy_pool.add(u, name, "imported")
        try: await bot.delete_message(uid, msg.message_id)
        except: pass
        await bot.send_message(uid,
            f"✅ <b>اكتمل الاستيراد</b>\n\n🟢 مضاف: <b>{added}</b>\n🔴 فاشل: <b>{failed}</b>\n"
            f"📊 Pool: <b>{_proxy_pool.healthy_count()}/{len(_proxy_pool.all())}</b>",
            reply_markup=admin_proxy_menu_markup(), parse_mode='HTML')
        user_steps[uid] = {"step": "await_phone", "last_activity": now}
        return

    if cur_step in ("dz_menu", "oo_menu") and last_activity and (now - last_activity) > INACTIVITY_SECONDS:
        user_steps[uid] = {"step": "await_phone", "last_activity": now}
        await send_welcome(uid); return
    digits = re.sub(r"\D", "", text)
    is_phone = re.match(r"^0[567]\d{8}$", digits) is not None
    if is_phone and cur_step not in ("oo_await_otp", "dz_verify_otp", "oo_gift_await_number"):
        user_steps[uid] = {"step": "await_phone", "last_activity": now}
    step = user_steps.get(uid)
    if not step:
        user_steps[uid] = {"step": "await_phone", "last_activity": now}
        await send_welcome(uid); return

    if str(step.get("step", "")).startswith("oo_gift"):
        user = oo_load(uid)
        if user and user.get("access_token"):
            user_steps[uid] = {"step": "oo_menu", "last_activity": now}
            await send_oo_menu(uid, user)
        else:
            user_steps[uid] = {"step": "await_phone", "last_activity": now}
            await send_welcome(uid)
        return

    if step.get("step") == "await_phone":
        if not is_phone:
            await bot.send_message(uid, "❌ رقم غير صحيح"); return

        # 🆕 تحقق من ازدحام Pool
        lstats = _proxy_pool.lease_stats()
        if lstats["total"] > 0 and lstats["free"] == 0:
            await bot.send_message(uid,
                "⚠️ <b>النظام مزدحم حالياً</b>\n\n"
                "🔄 كل البروكسيات محجوزة لمستخدمين آخرين.\n"
                "💡 حاول بعد دقيقة أو دقيقتين.",
                parse_mode='HTML')
            return

        msisdn = "213" + digits[1:]
        if digits.startswith(("07", "06")):
            row = db_query("SELECT token FROM numbers WHERE phone=? AND user_id=?", (msisdn, uid), fetch=True)
            if row and row[0] and row[0] != "EXPIRED":
                bal_check = await asyncio.to_thread(dj_check_balance, row[0], msisdn)
                if bal_check.get("status") == "EXPIRED":
                    db_query("UPDATE numbers SET token='EXPIRED' WHERE phone=? AND user_id=?", (msisdn, uid))
                    dz_clear_session(uid)
                else:
                    user_steps[uid] = {"step": "dz_menu", "last_activity": now}
                    await send_dz_menu(uid, msisdn); return
            loading_msg = None
            try: loading_msg = await bot.send_message(uid, "⏳ جاري إرسال الرمز...")
            except: pass
            ok = await asyncio.to_thread(dj_request_otp, msisdn)
            if loading_msg:
                try: await bot.delete_message(uid, loading_msg.message_id)
                except: pass
            if ok:
                mm = InlineKeyboardMarkup()
                mm.add(InlineKeyboardButton("🔄 إعادة إرسال", callback_data=f"resend_otp_{msisdn}"))
                await send_otp_message(uid, digits, msisdn, mm)
                user_steps[uid] = {"step": "dz_verify_otp", "phone": msisdn, "display": digits, "last_activity": now}
            else:
                _release_lease_for(msisdn, "otp_send_failed")
                mm = InlineKeyboardMarkup(row_width=1)
                mm.add(InlineKeyboardButton("🔄 حاول مرة أخرى", callback_data="change_phone"))
                await bot.send_message(uid, "❌ <b>تعذر إرسال الرمز</b>", reply_markup=mm, parse_mode='HTML')
            return
        if digits.startswith("05"):
            existing = oo_load(uid)
            if existing and existing.get("msisdn") == msisdn and existing.get("access_token"):
                user_steps[uid] = {"step": "oo_menu", "last_activity": now}
                await send_oo_menu(uid, existing); return
            try: loading_msg = await bot.send_message(uid, "⏳ <b>جاري إرسال رمز التحقق...</b>", parse_mode='HTML')
            except: loading_msg = None
            result = await asyncio.to_thread(ooredoo_send_otp_sync, msisdn)
            if loading_msg:
                try: await bot.delete_message(uid, loading_msg.message_id)
                except: pass
            if not result.get("otp_sent"):
                r = result.get("reason", ""); code = result.get("status", "?")
                if r == "rate_limit": msg = "⏳ محاولات كثيرة، انتظر 60 ثانية"
                elif r == "network": msg = "❌ مشكل في الاتصال"
                else: msg = f"❌ تعذر الإرسال\n💡 كود: {code}"
                _release_lease_for(msisdn, "otp_send_failed")
                user_steps[uid] = {"step": "await_phone", "last_activity": now}
                await bot.send_message(uid, msg); return
            user_steps[uid] = {"step": "oo_await_otp", "msisdn": msisdn, "device": result["device"], "otp_attempts": 0, "last_activity": now}
            mm = InlineKeyboardMarkup()
            mm.add(InlineKeyboardButton("🔄 إعادة إرسال", callback_data=f"resend_otp_{msisdn}"))
            await send_otp_message(uid, digits, msisdn, mm)
            return

    if step.get("step") == "oo_gift_await_number":
        digits_g = re.sub(r"\D", "", text)
        if not re.match(r"^05\d{8}$", digits_g):
            await bot.send_message(uid, "❌ <b>رقم غير صحيح</b>\nمثال: <code>05XXXXXXXX</code>",
                reply_markup=back_btn("oo_back_menu"), parse_mode='HTML'); return
        beneficiary = "213" + digits_g[1:]
        user = oo_load(uid)
        if not user:
            await bot.send_message(uid, "❌ جلسة منتهية"); return
        ms_l = user["msisdn"]
        if beneficiary == ms_l:
            kb = InlineKeyboardMarkup(row_width=1)
            kb.add(InlineKeyboardButton("📱 أدخل رقماً آخر", callback_data="oo_gift"))
            kb.add(InlineKeyboardButton("↩️ رجوع للقائمة", callback_data="oo_back_menu"))
            await bot.send_message(uid,
                "🚫 <b>لا يمكن الإهداء لنفس الرقم</b>\n\n"
                f"📱 رقمك: <code>{digits_g}</code>",
                reply_markup=kb, parse_mode='HTML'); return
        at_l = user["access_token"]
        meta_l = {k: user.get(k, "") for k in ["tok_instance_id","tok_plat_sig","tok_fingerprint","tok_timestamp"]}
        r = await asyncio.to_thread(oo_get_beneficiary_bundles, ms_l, at_l, meta_l, beneficiary)
        if r.get("status") == "unauthorized":
            mm = InlineKeyboardMarkup()
            mm.add(InlineKeyboardButton("🔄 إرسال رمز", callback_data=f"resend_otp_{ms_l}"))
            await bot.send_message(uid, "🔐 انتهت الجلسة", reply_markup=mm); return
        if r.get("status") != "ok" or not r.get("bundles"):
            user_steps[uid] = {"step": "oo_gift_await_bundle", "gift_beneficiary": beneficiary, "last_activity": time.time()}
            await bot.send_message(uid,
                f"⚠️ <b>تعذر جلب العروض</b>\n\n✅ رقم المستفيد: <code>{digits_g}</code>",
                reply_markup=back_btn("oo_back_menu"), parse_mode='HTML'); return
        user_steps[uid] = {"step": "oo_gift_await_bundle",
                           "gift_beneficiary": beneficiary,
                           "gift_bundles": r["bundles"],
                           "last_activity": time.time()}
        await bot.send_message(uid, oo_format_gift_list_text(r["bundles"], beneficiary), parse_mode='HTML')
        await bot.send_message(uid, "👇 <b>اختر عرضاً:</b>",
            reply_markup=oo_dynamic_gift_menu(r["bundles"], beneficiary), parse_mode='HTML'); return

    if step.get("step") == "oo_await_otp":
        m = re.search(r"\b(\d{6})\b", text)
        if not m: await bot.send_message(uid, "⚠️ 6 أرقام"); return
        otp = m.group(1); ms = step.get("msisdn"); device = step.get("device", {})
        checking_msg = await bot.send_message(uid, "⏳ <b>جاري التحقق من الرمز...</b>", parse_mode='HTML')
        result = await asyncio.to_thread(ooredoo_verify_otp_sync, ms, otp, device)
        try: await bot.delete_message(uid, checking_msg.message_id)
        except: pass
        if result == "wrong_otp":
            attempts = int(step.get("otp_attempts", 0) or 0) + 1
            if attempts < 3:
                user_steps[uid]["otp_attempts"] = attempts
                user_steps[uid]["last_activity"] = time.time()
                await bot.send_message(uid, f"❌ <b>الرمز خاطئ</b>\n\n⚠️ المحاولة {attempts}/3", parse_mode='HTML')
                return
            await bot.send_message(uid, "🔄 <b>انتهت المحاولات، جاري إرسال رمز جديد...</b>", parse_mode='HTML')
            resent = await asyncio.to_thread(ooredoo_send_otp_sync, ms)
            if resent.get("otp_sent"):
                user_steps[uid] = {"step": "oo_await_otp", "msisdn": ms,
                                   "device": resent["device"], "otp_attempts": 0,
                                   "last_activity": time.time()}
                mm = InlineKeyboardMarkup()
                mm.add(InlineKeyboardButton("🔄 إعادة إرسال", callback_data=f"resend_otp_{ms}"))
                await send_otp_message(uid, "0" + ms[3:], ms, mm)
            else:
                _release_lease_for(ms, "otp_failed")
                user_steps[uid]["otp_attempts"] = 0
                await bot.send_message(uid, "❌ <b>تعذر إرسال رمز جديد، حاول بعد قليل</b>",
                                       reply_markup=back_btn("main_menu"), parse_mode='HTML')
            return
        if not result:
            await bot.send_message(uid, "❌ <b>فشل التحقق</b>", parse_mode='HTML'); return
        user = {"msisdn": ms, "device": device, **result}
        oo_save(uid, user)
        _clear_sticky_proxy(ms)   # امسح sticky فقط، لكن أبقِ الـ lease!
        inc_stat("oo_logins")
        db_query("INSERT OR IGNORE INTO users (user_id,username,join_date,is_logged_in) VALUES (?,?,?,1)",
                 (uid, message.from_user.username or message.from_user.first_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        db_query("UPDATE users SET is_logged_in=1 WHERE user_id=?", (uid,))
        user_steps[uid] = {"step": "oo_menu", "last_activity": time.time()}
        await bot.send_message(uid, "✅ <b>تم التحقق بنجاح والدخول إلى حسابك</b>", parse_mode='HTML')
        await send_oo_menu(uid, user); return

    if step.get("step") == "dz_verify_otp":
        if not text.isdigit() or len(text) != 6:
            try: await bot.send_message(uid, "❌ 6 أرقام")
            except Exception as e:
                if "Forbidden" in str(e): logging.warning(f"[USER-BLOCKED] {uid}")
            return
        phone = step.get("phone")
        checking_msg = await bot.send_message(uid, "⏳ <b>جاري التحقق من الرمز...</b>", parse_mode='HTML')
        token = await asyncio.to_thread(dj_verify_otp, phone, text)
        try: await bot.delete_message(uid, checking_msg.message_id)
        except: pass
        if token and token != "EXPIRED":
            db_query("INSERT OR REPLACE INTO numbers (phone,user_id,token,added_date) VALUES (?,?,?,?)",
                     (phone, uid, token, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            dz_save_session(uid, phone, token)
            _clear_sticky_proxy(phone)   # امسح sticky، أبقِ lease
            db_query("INSERT OR IGNORE INTO users (user_id,username,join_date,is_logged_in) VALUES (?,?,?,1)",
                     (uid, message.from_user.username or message.from_user.first_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            db_query("UPDATE users SET is_logged_in=1 WHERE user_id=?", (uid,))
            inc_stat("dz_logins")
            user_steps[uid] = {"step": "dz_menu", "last_activity": time.time()}
            try:
                await bot.send_message(uid, "✅ <b>تم التحقق بنجاح والدخول إلى حسابك</b>", parse_mode='HTML')
                await send_dz_menu(uid, phone)
            except Exception as e:
                if "Forbidden" in str(e):
                    logging.warning(f"[USER-BLOCKED] {uid}")
                else:
                    logging.error(f"[SEND-MENU-ERR] {uid}: {e}")
        else:
            _release_lease_for(phone, "verify_failed")
            try:
                await bot.send_message(uid, "❌ <b>الرمز خاطئ</b>", parse_mode='HTML')
            except Exception as e:
                if "Forbidden" in str(e): logging.warning(f"[USER-BLOCKED] {uid}")
                else: logging.error(f"[SEND-OTP-ERR] {uid}: {e}")
        return

    if oo_load(uid):
        user_steps[uid] = {"step": "oo_menu", "last_activity": now}
        u = oo_load(uid)
        if u: await send_oo_menu(uid, u)
        return
    if db_query("SELECT token FROM numbers WHERE user_id=? LIMIT 1", (uid,), fetch=True):
        user_steps[uid] = {"step": "dz_menu", "last_activity": now}
        await send_dz_menu(uid); return
    user_steps[uid] = {"step": "await_phone", "last_activity": now}
    await send_welcome(uid)

# ==================== OO Callbacks ====================
async def oo_cb_handler(call):
    uid = call.from_user.id
    data = call.data

    if data == "oo_change":
        user = oo_load(uid)
        if user and user.get("msisdn"): _release_lease_for(user["msisdn"], "oo_change")
        oo_clear(uid); dz_clear_session(uid)
        user_steps[uid] = {"step": "await_phone", "last_activity": time.time()}
        await send_welcome(uid); return

    if data == "oo_back_menu":
        user = oo_load(uid)
        if user: await send_oo_menu(uid, user); return
        user_steps[uid] = {"step": "await_phone", "last_activity": time.time()}
        await send_welcome(uid); return

    if data == "oo_stats":
        if uid != ADMIN_ID: await bot.send_message(uid, "⛔"); return
        await bot.send_message(uid, get_stats_text(), reply_markup=back_btn("oo_back_menu"), parse_mode='HTML'); return

    user = oo_load(uid)
    if not user or not user.get("access_token"):
        user_steps[uid] = {"step": "await_phone", "last_activity": time.time()}
        await send_welcome(uid); return
    user = await asyncio.to_thread(oo_ensure_valid, uid, user)
    if not user:
        mm = InlineKeyboardMarkup(); mm.add(InlineKeyboardButton("🔄 إرسال رمز", callback_data="oo_change"))
        await bot.send_message(uid, "⚠️ <b>انتهت الجلسة</b>", reply_markup=mm, parse_mode='HTML'); return
    ms = user["msisdn"]; at = user["access_token"]
    meta = {k: user.get(k, "") for k in ["tok_instance_id","tok_plat_sig","tok_fingerprint","tok_timestamp"]}

    if data == "oo_noudjoum":
        qd = oo_quick_detect(at)
        if qd.get("is_yooz"):
            await bot.send_message(uid, "❌ <b>خدمة نجوم غير متاحة لأرقام N'YOOZ</b>",
                reply_markup=back_btn("oo_back_menu"), parse_mode='HTML'); return
        st = await asyncio.to_thread(oo_check_noudjoum_status, ms, at, meta)
        prof = await asyncio.to_thread(oo_get_profile, ms, at, meta)
        months_active = 0
        if isinstance(prof, dict) and prof.get("status") == "ok":
            pd = prof.get("data", {})
            start = pd.get("startDate") or ""
            if start:
                try:
                    sd = datetime.fromisoformat(start.replace("Z", "+00:00"))
                    months_active = int((datetime.now(tz.utc) - sd).days / 30)
                except: pass
        if st.get("status") == "unauthorized":
            mm = InlineKeyboardMarkup()
            mm.add(InlineKeyboardButton("🔄 إرسال رمز", callback_data=f"resend_otp_{ms}"))
            await bot.send_message(uid, "🔐 انتهت الجلسة", reply_markup=mm); return
        if months_active > 0 and months_active < 3:
            txt = (NOUDJOUM_INFO_TEXT +
                   f"\n\n🔒 <b>غير مؤهل بعد</b>\n"
                   f"📅 شريحتك عمرها: <b>{months_active} شهر</b>\n"
                   f"⏳ تحتاج: <b>3 أشهر</b>")
            m = InlineKeyboardMarkup(row_width=1)
            m.add(InlineKeyboardButton("↩️ رجوع", callback_data="oo_back_menu"))
            await bot.send_message(uid, txt, reply_markup=m, parse_mode='HTML'); return
        txt = NOUDJOUM_INFO_TEXT
        if months_active > 0: txt += f"\n\n📅 <b>نشطة منذ:</b> {months_active} شهر"
        stv = st.get("status", "unknown")
        if stv == "enrolled": txt += f"\n\n✅ <b>مسجّل</b> — {st.get('points',0)} نقطة"
        elif stv == "not_enrolled": txt += "\n\n❌ <b>غير مسجّل — سجّل الآن</b>"
        else: txt += "\n\n⚠️ <b>جرّب التسجيل</b>"
        await bot.send_message(uid, txt, reply_markup=oo_noudjoum_menu(stv), parse_mode='HTML'); return

    if data == "oo_noudjoum_check":
        st = await asyncio.to_thread(oo_check_noudjoum_status, ms, at, meta)
        stv = st.get("status", "unknown")
        if stv == "enrolled":
            await bot.send_message(uid, f"✅ <b>مسجّل</b> — {st.get('points',0)} نقطة",
                reply_markup=oo_noudjoum_menu("enrolled"), parse_mode='HTML')
        elif stv == "not_enrolled":
            await bot.send_message(uid, "❌ <b>غير مسجّل</b>",
                reply_markup=oo_noudjoum_menu("not_enrolled"), parse_mode='HTML')
        else:
            await bot.send_message(uid, "⚠️ تعذر التحقق",
                reply_markup=oo_noudjoum_menu("unknown"), parse_mode='HTML')
        return

    if data == "oo_noudjoum_enroll":
        r = await asyncio.to_thread(oo_enroll_noudjoum, ms, at, meta)
        if r.get("status") == "unauthorized":
            mm = InlineKeyboardMarkup()
            mm.add(InlineKeyboardButton("🔄 إرسال رمز", callback_data=f"resend_otp_{ms}"))
            await bot.send_message(uid, "🔐 انتهت الجلسة", reply_markup=mm); return
        if r.get("status") == "ok":
            inc_stat("oo_stars_activated")
            await send_result(uid, NOUDJOUM_SUCCESS_TEXT, "oo_back_menu"); return
        if r.get("status") == "already":
            await bot.send_message(uid, NOUDJOUM_ALREADY_TEXT,
                reply_markup=back_btn("oo_back_menu"), parse_mode='HTML'); return
        if r.get("status") == "not_eligible":
            await bot.send_message(uid, NOUDJOUM_LOCKED_TEXT,
                reply_markup=back_btn("oo_back_menu"), parse_mode='HTML'); return
        await bot.send_message(uid, "❌ <b>فشل التسجيل</b>",
            reply_markup=back_btn("oo_back_menu"), parse_mode='HTML'); return

    if data == "oo_gift":
        user_steps[uid] = {"step": "oo_gift_await_number", "last_activity": time.time()}
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("↩️ رجوع", callback_data="oo_back_menu"))
        await bot.send_message(uid, GIFT_INFO_TEXT, reply_markup=kb, parse_mode='HTML'); return

    if data == "oo_gift_refresh":
        step = user_steps.get(uid, {})
        beneficiary = step.get("gift_beneficiary")
        if not beneficiary:
            await bot.send_message(uid, "⚠️ أعد إدخال الرقم", reply_markup=back_btn("oo_back_menu")); return
        r = await asyncio.to_thread(oo_get_beneficiary_bundles, ms, at, meta, beneficiary)
        if r.get("status") != "ok" or not r.get("bundles"):
            await bot.send_message(uid, "❌ تعذر التحديث", reply_markup=back_btn("oo_back_menu")); return
        user_steps[uid]["gift_bundles"] = r["bundles"]
        user_steps[uid]["last_activity"] = time.time()
        await bot.send_message(uid, oo_format_gift_list_text(r["bundles"], beneficiary), parse_mode='HTML')
        await bot.send_message(uid, "👇 <b>اختر عرضاً:</b>",
            reply_markup=oo_dynamic_gift_menu(r["bundles"], beneficiary), parse_mode='HTML'); return

    if data.startswith("oo_gift_dyn_"):
        try: idx = int(data.replace("oo_gift_dyn_", ""))
        except: await bot.send_message(uid, "❌", reply_markup=back_btn("oo_back_menu")); return
        step = user_steps.get(uid, {})
        bundles = step.get("gift_bundles", [])
        beneficiary = step.get("gift_beneficiary")
        if not bundles or not beneficiary or idx >= len(bundles):
            await bot.send_message(uid, "⚠️ أعد الإدخال", reply_markup=back_btn("oo_back_menu")); return
        b = bundles[idx]
        code = b.get("code"); price = b.get("price", "?")
        name = b.get("name") or code; data_v = b.get("data", "")
        extras = b.get("extras", ""); validity = b.get("validity", "")
        family = b.get("family", "")
        r = await asyncio.to_thread(oo_check_balance, ms, at, meta)
        try: bal = float(r.get("data", {}).get("accountBalance", 0) or 0) if r and r.get("status") == "ok" else 0
        except: bal = 0
        try: price_num = int(float(price))
        except: price_num = 0
        if price_num > 0 and bal < price_num:
            diff = max(0, price_num - int(bal))
            kb = InlineKeyboardMarkup(row_width=1)
            kb.add(InlineKeyboardButton("🔄 اختر عرضاً آخر", callback_data="oo_gift"))
            kb.add(InlineKeyboardButton("↩️ رجوع", callback_data="oo_back_menu"))
            await bot.send_message(uid,
                f"❌ <b>الرصيد غير كافٍ</b>\n\n"
                f"📦 <b>{name}</b>\n💳 المطلوب: <b>{price_num} دج</b>\n"
                f"💰 رصيدك: <b>{bal} دج</b>\n📊 الفرق: <b>{diff} دج</b>",
                reply_markup=kb, parse_mode='HTML'); return
        if "social" in family.lower(): cat = "📱 شبكات اجتماعية"
        elif "smart" in family.lower(): cat = "✨ سمارت"
        elif "data" in family.lower(): cat = "🌐 إنترنت"
        else: cat = "🎁 عرض"
        disp = "0" + beneficiary[3:] if beneficiary.startswith("213") else beneficiary
        lines = ["🎁 <b>تفاصيل الإهداء</b>", "━━━━━━━━━━━━━━━━", ""]
        lines.append(f"📱 <b>المستفيد:</b> <code>{disp}</code>"); lines.append("")
        lines.append(f"🏷️ <b>الفئة:</b> {cat}")
        lines.append(f"📦 <b>العرض:</b> {name}")
        if data_v: lines.append(f"🌐 <b>البيانات:</b> {data_v}")
        if extras: lines.append(f"➕ <b>الإضافات:</b> {extras}")
        if validity: lines.append(f"⏱️ <b>الصلاحية:</b> {validity}")
        lines.append(""); lines.append("━━━━━━━━━━━━━━━━")
        lines.append(f"💳 <b>السعر:</b> {price} دج")
        lines.append(f"💰 <b>رصيدك:</b> {bal} دج")
        lines.append(""); lines.append("❓ <b>هل تريد المتابعة؟</b>")
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(InlineKeyboardButton("💳 دفع", callback_data=f"oo_gift_dynok_{idx}"),
               InlineKeyboardButton("❌ إلغاء", callback_data="oo_back_menu"))
        await bot.send_message(uid, "\n".join(lines), reply_markup=kb, parse_mode='HTML'); return

    if data.startswith("oo_gift_dynok_"):
        try: idx = int(data.replace("oo_gift_dynok_", ""))
        except: await bot.send_message(uid, "❌", reply_markup=back_btn("oo_back_menu")); return
        step = user_steps.get(uid, {})
        bundles = step.get("gift_bundles", [])
        beneficiary = step.get("gift_beneficiary")
        if not bundles or not beneficiary or idx >= len(bundles):
            await bot.send_message(uid, "⚠️ أعد الإدخال", reply_markup=back_btn("oo_back_menu")); return
        b = bundles[idx]
        code = b.get("code"); price = b.get("price", "?")
        data_v = b.get("data", ""); extras = b.get("extras", ""); validity = b.get("validity", "")
        r = await asyncio.to_thread(oo_gift_purchase, ms, at, meta, code, beneficiary)
        if r.get("status") == "unauthorized":
            mm = InlineKeyboardMarkup()
            mm.add(InlineKeyboardButton("🔄 إرسال رمز", callback_data=f"resend_otp_{ms}"))
            await bot.send_message(uid, "🔐 انتهت الجلسة", reply_markup=mm); return
        if r.get("status") == "ok":
            inc_stat("oo_gifts_sent")
            disp = "0" + beneficiary[3:] if beneficiary.startswith("213") else beneficiary
            lines = ["🎉🎁 <b>مبروك!</b>", "", "✅ <b>تم إهداء الاشتراك</b>",
                     "━━━━━━━━━━━━━━━━", f"📱 <b>المستفيد:</b> <code>{disp}</code>",
                     f"📦 <b>الباقة:</b> {b.get('name') or code}"]
            if data_v: lines.append(f"🌐 <b>البيانات:</b> {data_v}")
            if extras: lines.append(f"➕ {extras}")
            if validity: lines.append(f"⏱️ <b>الصلاحية:</b> {validity}")
            lines.append(f"💳 <b>السعر:</b> {price} دج"); lines.append("")
            lines.append(PAGE_FOLLOW_TEXT)
            await send_result(uid, "\n".join(lines), "oo_back_menu")
            _release_lease_for(ms, "gift_sent")
            asyncio.create_task(_update_oo_menu_bg(uid, user, call.message.message_id))
            return
        if r.get("status") == "no_balance":
            await bot.send_message(uid, "❌ <b>الرصيد غير كافٍ</b>",
                reply_markup=back_btn("oo_back_menu"), parse_mode='HTML'); return
        if r.get("status") == "not_allowed":
            await bot.send_message(uid, "⚠️ <b>رقم المستفيد غير مؤهل</b>",
                reply_markup=back_btn("oo_back_menu"), parse_mode='HTML'); return
        await bot.send_message(uid, f"❌ <b>فشل الإهداء</b>\n💬 {r.get('msg') or r.get('code','?')}",
            reply_markup=back_btn("oo_back_menu"), parse_mode='HTML'); return

    if data == "oo_balance":
        inc_stat("oo_balance")
        r, p = await asyncio.gather(
            asyncio.to_thread(oo_check_balance, ms, at, meta),
            asyncio.to_thread(oo_get_profile, ms, at, meta),
            return_exceptions=True)
        if isinstance(r, Exception) or r.get("status") != "ok":
            await bot.send_message(uid, "❌", reply_markup=back_btn("oo_back_menu")); return
        d = r.get("data", {}); b = d.get("accountBalance", "?")
        profile_txt = ""
        if isinstance(p, dict) and p.get("status") == "ok":
            pd = p.get("data", {})
            rp = pd.get("ratePlan", "")
            if rp: profile_txt += f"\n🎁 <b>العرض:</b> {rp}"
            pt = pd.get("planType", "")
            if pt: profile_txt += f"\n📋 <b>النوع:</b> {pt}"
            st = pd.get("startDate", "")
            if st:
                try:
                    sd = datetime.fromisoformat(st.replace("Z", "+00:00"))
                    profile_txt += f"\n📅 <b>الشريحة:</b> {sd.strftime('%Y-%m-%d')}"
                except: pass
        await bot.send_message(uid, f"💰 <b>{b} دج</b>\n\n📱 <code>{o_mask(ms)}</code>{profile_txt}",
            reply_markup=back_btn("oo_back_menu"), parse_mode='HTML'); return

    if data == "oo_my_offers":
        inc_stat("oo_offers_view")
        r = await asyncio.to_thread(oo_get_active, ms, at, meta)
        if r["status"] != "ok":
            await bot.send_message(uid, "❌", reply_markup=back_btn("oo_back_menu")); return
        d = r.get("data", {}); b = d.get("accountBalance", "?")
        lines = [f"📋 <b>عروضك</b>\n💰 <b>{b} دج</b>\n"]
        snap = d.get("snapchatAllocation")
        if snap and isinstance(snap, dict):
            acc = snap.get("account", {})
            if acc and acc.get("account"):
                exp = (acc.get("expiryDate") or "")[:10]
                lines.append(f"👻 <b>Snapchat</b> — 💎 {acc.get('balance','Unlimited')}")
                if exp: lines.append(f"   📅 {exp}")
        byob = d.get("byobBundlesPackage", {})
        if isinstance(byob, dict):
            for bnd in byob.get("dynamicBundle") or []:
                if not isinstance(bnd, dict): continue
                exp_s = (bnd.get("expiryDate") or "")[:10]
                lims = bnd.get("limitedAccountListInformations", {}).get("limitedAccountListInformations", []) or []
                for lim in lims:
                    if not isinstance(lim, dict): continue
                    nraw = lim.get("limitedAccountName", ""); nlow = nraw.lower()
                    val = lim.get("limitedAccountValue", "?"); unit = lim.get("limitedAccountUnit", "")
                    rel_val = lim.get("limitedRelativeAccountValue", "")
                    if "data" in nlow: icon, name, unit_d = "📊", "داتا", ("GB" if "GB" in unit.upper() else unit)
                    elif "offnet" in nlow: icon, name, unit_d = "📞", "مكالمات خارج", "دقيقة"
                    elif "onnet" in nlow: icon, name, unit_d = "📞", "مكالمات داخل", "دقيقة"
                    else: icon, name, unit_d = "📦", nraw, unit
                    vs = f"{val} / {rel_val} {unit_d}".strip() if rel_val else f"{val} {unit_d}".strip()
                    lines.append(f"{icon} <b>{name}</b> — 💎 {vs}")
                    if exp_s: lines.append(f"   📅 {exp_s}")
                unlms = bnd.get("unlimitedAccountListInformations", {}).get("unlimitedAccountListInformations", []) or []
                for u in unlms:
                    if not isinstance(u, dict): continue
                    nraw = u.get("unlimitedAccountName", ""); nlow = nraw.lower()
                    if "youtube" in nlow: icon, name = "▶️", "YouTube غير محدود"
                    elif "snapchat" in nlow: icon, name = "👻", "Snapchat غير محدود"
                    elif "facebook" in nlow: icon, name = "📘", "Facebook غير محدود"
                    elif "instagram" in nlow: icon, name = "📷", "Instagram غير محدود"
                    elif "tiktok" in nlow: icon, name = "🎵", "TikTok غير محدود"
                    elif "whatsapp" in nlow: icon, name = "💬", "WhatsApp غير محدود"
                    else: icon, name = "♾️", f"{nraw} غير محدود"
                    lines.append(f"{icon} <b>{name}</b> — 💎 غير محدود")
                    if exp_s: lines.append(f"   📅 {exp_s}")
        if len(lines) <= 2: lines.append("📭 <i>لا توجد باقات نشطة</i>")
        await bot.send_message(uid, "\n".join(lines), reply_markup=back_btn("oo_back_menu"), parse_mode='HTML'); return

    if data == "oo_snap":
        r = await asyncio.to_thread(oo_activate_snapchat, ms, at, meta)
        if r == "ok":
            inc_stat("oo_snap")
            await notify_group_success("Snapchat", "Ooredoo 🟠", uid, ms)
            await send_result(uid, f"✅ <b>تم تفعيل سناب!</b>\n📱 <code>{o_mask(ms)}</code>", "oo_back_menu")
        elif r == "already_active":
            await bot.send_message(uid, "⚠️ <b>مفعّلة مسبقاً</b>", reply_markup=back_btn("oo_back_menu"))
        else:
            await bot.send_message(uid, "❌", reply_markup=back_btn("oo_back_menu"))
        return

    if data == "oo_snap_locked":
        qd = oo_quick_detect(at)
        if qd.get("is_yooz"):
            await bot.send_message(uid, "✅ الخدمة متاحة الآن", reply_markup=back_btn("oo_back_menu"))
        else:
            await bot.send_message(uid,
                "👻 <b>سناب شات</b>\n\n❌ <b>متاحة لأرقام N'YOOZ فقط</b>\n\n"
                f"📦 عرضك: <b>{qd.get('rate_plan') or 'غير معروف'}</b>",
                reply_markup=back_btn("oo_back_menu"), parse_mode='HTML')
        return

    if data == "oo_soccer":
        elig = await asyncio.to_thread(oo_soccer_eligibility, ms, at, meta)
        if elig.get("status") == "unauthorized":
            mm = InlineKeyboardMarkup(); mm.add(InlineKeyboardButton("🔄 إرسال رمز", callback_data=f"resend_otp_{ms}"))
            await bot.send_message(uid, "🔐 انتهت الجلسة", reply_markup=mm); return
        if elig.get("status") != "ok":
            await bot.send_message(uid, "❌ <b>تعذر فحص الأهلية</b>", reply_markup=back_btn("oo_back_menu"), parse_mode='HTML'); return
        if elig.get("enrolled"):
            team = elig.get("selected_team", "")
            nm = SOCCER_CLUB_NAMES.get(team, team) if team else "غير معروف"
            m = InlineKeyboardMarkup(row_width=1)
            m.add(InlineKeyboardButton("🔄 تحقق مجدداً", callback_data="oo_soccer"))
            m.add(InlineKeyboardButton("↩️ رجوع", callback_data="oo_back_menu"))
            await bot.send_message(uid,
                f"✅ <b>راك مشترك مسبقاً</b>\n\n"
                f"📱 <code>{o_mask(ms)}</code>\n🏆 النادي: <b>{nm} ({team})</b>\n\n"
                f"⚽️ كل هدف = <b>1 جيجابايت</b>",
                reply_markup=m, parse_mode='HTML'); return
        if not elig.get("eligible"):
            await bot.send_message(uid, "❌ <b>رقمك ماشي مؤهّل</b>",
                reply_markup=back_btn("oo_back_menu"), parse_mode='HTML'); return
        r = await asyncio.to_thread(oo_soccer_clubs, ms, at, meta)
        if r["status"] != "ok":
            await bot.send_message(uid, "❌ تعذر جلب الأندية", reply_markup=back_btn("oo_back_menu")); return
        clubs = r.get("clubs", [])
        m = InlineKeyboardMarkup(row_width=2)
        for c in clubs[:20]:
            code = c["code"]; nm = SOCCER_CLUB_NAMES.get(code, code)
            m.add(InlineKeyboardButton(f"🏆 {nm}", callback_data=f"oo_soccer_confirm_{code}"))
        m.add(InlineKeyboardButton("↩️ رجوع", callback_data="oo_back_menu"))
        await bot.send_message(uid,
            "⚽️ <b>Ooredoo Sport</b>\n\n🎁 كل هدف = 1 جيجابايت\n⚠️ ما تقدرش تبدل\n\n🏆 <b>اختر ناديك:</b>",
            reply_markup=m, parse_mode='HTML'); return

    if data.startswith("oo_soccer_confirm_"):
        team = data.replace("oo_soccer_confirm_", "").upper()
        nm = SOCCER_CLUB_NAMES.get(team, team)
        r = await asyncio.to_thread(oo_soccer_activate, ms, at, meta, team)
        if r["status"] == "unauthorized":
            mm = InlineKeyboardMarkup(); mm.add(InlineKeyboardButton("🔄 إرسال رمز", callback_data=f"resend_otp_{ms}"))
            await bot.send_message(uid, "🔐 انتهت الجلسة", reply_markup=mm); return
        if r["status"] == "ok":
            inc_stat("oo_soccer_enrolls")
            await bot.send_message(uid,
                f"🎉🎁 <b>مبروك!</b>\n\n✅ <b>تم الاشتراك</b>\n\n"
                f"📱 <code>{o_mask(ms)}</code>\n🏆 النادي: <b>{nm} ({team})</b>\n\n⚽️ كل هدف = 1 جيجابايت 🎁",
                reply_markup=back_btn("oo_back_menu"), parse_mode='HTML'); return
        if r["status"] == "already":
            await bot.send_message(uid, "✅ <b>راك مشترك مسبقاً</b>",
                reply_markup=back_btn("oo_back_menu"), parse_mode='HTML'); return
        msg = r.get("msg") or f"كود: {r.get('code','?')}"
        await bot.send_message(uid, f"❌ <b>فشل الاشتراك</b>\n💬 {msg}",
            reply_markup=back_btn("oo_back_menu"), parse_mode='HTML'); return

    if data == "oo_special":
        await bot.send_message(uid, "⚡ <b>عروض خاصة</b>\n\nاختر:",
            reply_markup=oo_special_offers_markup(), parse_mode='HTML'); return
    if data.startswith("oo_sp_sel_"):
        key = data.replace("oo_sp_sel_", "")
        if key not in SPECIAL_BUNDLES:
            await bot.send_message(uid, "❌", reply_markup=back_btn("oo_back_menu")); return
        bi = SPECIAL_BUNDLES[key]
        m = InlineKeyboardMarkup(row_width=1)
        m.add(InlineKeyboardButton("🛒 اشترِ الآن ✅", callback_data=f"oo_sp_confirm_{key}"))
        m.add(InlineKeyboardButton("↩️ رجوع", callback_data="oo_back_menu"))
        await bot.send_message(uid, f"{bi['icon']} <b>{bi['name']}</b>\n\n📅 {bi['validity_ar']}\n💳 {bi['price']} دج",
            reply_markup=m, parse_mode='HTML'); return
    if data.startswith("oo_sp_confirm_"):
        key = data.replace("oo_sp_confirm_", "")
        if key not in SPECIAL_BUNDLES:
            await bot.send_message(uid, "❌", reply_markup=back_btn("oo_back_menu")); return
        bi = SPECIAL_BUNDLES[key]
        r = await asyncio.to_thread(oo_check_balance, ms, at, meta)
        if r is None or r["status"] != "ok":
            await bot.send_message(uid, "❌", reply_markup=back_btn("oo_back_menu")); return
        try: balance = float(r.get("data", {}).get("accountBalance", 0) or 0)
        except: balance = 0
        if balance < bi['price']:
            await bot.send_message(uid, f"❌ <b>الرصيد غير كافي</b>\n💵 {balance} دج",
                reply_markup=back_btn("oo_back_menu"), parse_mode='HTML'); return
        if bi.get("limited"):
            r2 = await asyncio.to_thread(oo_purchase_byop, ms, at, meta, bi['validity'], bi['limited'], [])
        elif bi.get("app"):
            r2 = await asyncio.to_thread(oo_purchase_byop, ms, at, meta, bi['validity'], None, [bi['app']])
        else: r2 = {"status": "error"}
        if r2["status"] == "ok":
            inc_stat("oo_bundles")
            await send_result(uid, f"✅ <b>تم التفعيل</b> 🎉\n📱 <code>{o_mask(ms)}</code>", "oo_back_menu")
            _release_lease_for(ms, "special_activated")
            asyncio.create_task(_update_oo_menu_bg(uid, user, call.message.message_id))
        elif r2["status"] == "conflict":
            await bot.send_message(uid, f"⚠️ {r2.get('message','؟')}", reply_markup=back_btn("oo_back_menu"))
        else: await bot.send_message(uid, "❌", reply_markup=back_btn("oo_back_menu"))
        return

    if data == "oo_internet":
        await bot.send_message(uid, "🌐 <b>عروض الإنترنت</b>\n\nاختر:",
            reply_markup=oo_internet_offers_markup(), parse_mode='HTML'); return
    if data.startswith("oo_inet_sel_"):
        key = data.replace("oo_inet_sel_", "")
        if key not in INTERNET_BUNDLES:
            await bot.send_message(uid, "❌", reply_markup=back_btn("oo_back_menu")); return
        bi = INTERNET_BUNDLES[key]
        m = InlineKeyboardMarkup(row_width=1)
        m.add(InlineKeyboardButton("🛒 اشترِ الآن ✅", callback_data=f"oo_inet_confirm_{key}"))
        m.add(InlineKeyboardButton("↩️ رجوع", callback_data="oo_back_menu"))
        await bot.send_message(uid, f"{bi['icon']} <b>{bi['name']}</b>\n🌐 {bi['data']}\n💳 {bi['price']} دج",
            reply_markup=m, parse_mode='HTML'); return
    if data.startswith("oo_inet_confirm_"):
        key = data.replace("oo_inet_confirm_", "")
        if key not in INTERNET_BUNDLES:
            await bot.send_message(uid, "❌", reply_markup=back_btn("oo_back_menu")); return
        bi = INTERNET_BUNDLES[key]
        r = await asyncio.to_thread(oo_check_balance, ms, at, meta)
        if r is None or r["status"] != "ok":
            await bot.send_message(uid, "❌", reply_markup=back_btn("oo_back_menu")); return
        try: balance = float(r.get("data", {}).get("accountBalance", 0) or 0)
        except: balance = 0
        if balance < bi['price']:
            await bot.send_message(uid, "❌ <b>الرصيد غير كافي</b>", reply_markup=back_btn("oo_back_menu")); return
        r2 = await asyncio.to_thread(oo_purchase_planned, ms, at, meta, bi['code'])
        if r2["status"] == "ok":
            inc_stat("oo_bundles")
            await send_result(uid, f"✅ <b>تم التفعيل</b> 🎉\n{bi['name']}", "oo_back_menu")
            _release_lease_for(ms, "internet_activated")
            asyncio.create_task(_update_oo_menu_bg(uid, user, call.message.message_id))
        elif r2["status"] == "conflict":
            await bot.send_message(uid, f"⚠️ {r2.get('message','؟')}", reply_markup=back_btn("oo_back_menu"))
        else: await bot.send_message(uid, "❌", reply_markup=back_btn("oo_back_menu"))
        return

    if data == "oo_quick_5dzd_5go":
        r = await asyncio.to_thread(oo_check_balance, ms, at, meta)
        if r is None or r.get("status") != "ok":
            await bot.send_message(uid, "❌ تعذر فحص الرصيد", reply_markup=back_btn("oo_back_menu")); return
        try: balance = float(r.get("data", {}).get("accountBalance", 0) or 0)
        except: balance = 0
        if balance < 5:
            await bot.send_message(uid,
                f"❌ <b>الرصيد غير كافي</b>\n\n💰 رصيدك: <b>{balance} دج</b>\n💳 المطلوب: <b>5 دج</b>",
                reply_markup=back_btn("oo_back_menu"), parse_mode='HTML'); return
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(InlineKeyboardButton("✅ تأكيد", callback_data="oo_quick_5dzd_5go_ok"),
               InlineKeyboardButton("❌ إلغاء", callback_data="oo_back_menu"))
        await bot.send_message(uid,
            f"💳 <b>عرض 5 دج — 5Go — 5H</b>\n\n"
            f"🌐 <b>5 جيجا</b>\n⏱️ <b>5 ساعات</b>\n"
            f"💳 <b>5 دج</b>\n\n💰 رصيدك: <b>{balance} دج</b>\n\n❓ تريد التفعيل؟",
            reply_markup=kb, parse_mode='HTML'); return

    if data == "oo_quick_5dzd_5go_ok":
        r = await asyncio.to_thread(oo_purchase_5dzd_5go, ms, at, meta)
        if r.get("status") == "unauthorized":
            mm = InlineKeyboardMarkup()
            mm.add(InlineKeyboardButton("🔄 إرسال رمز", callback_data=f"resend_otp_{ms}"))
            await bot.send_message(uid, "🔐 انتهت الجلسة", reply_markup=mm, parse_mode='HTML'); return
        if r.get("status") == "ok":
            inc_stat("oo_5dzd_5go")
            await notify_group_success("5دج — 5Go", "Ooredoo 🟠", uid, ms)
            await send_result(uid,
                f"✅ <b>تم التفعيل</b> 🎉\n\n"
                f"📱 <code>{o_mask(ms)}</code>\n⚡ <b>5 جيجا</b> — 5 ساعات\n"
                f"💳 <b>5 دج</b>\n\n{PAGE_FOLLOW_TEXT}", "oo_back_menu")
            asyncio.create_task(_update_oo_menu_bg(uid, user, call.message.message_id))
            return
        if r.get("status") == "no_balance":
            await bot.send_message(uid, f"❌ <b>الرصيد غير كافي</b>\n💳 المطلوب: <b>5 دج</b>",
                reply_markup=back_btn("oo_back_menu"), parse_mode='HTML'); return
        if r.get("status") == "conflict":
            await bot.send_message(uid, f"⚠️ <b>{r.get('msg', 'غير متاح')}</b>",
                reply_markup=back_btn("oo_back_menu"), parse_mode='HTML'); return
        await bot.send_message(uid, "❌ <b>فشل التفعيل</b>",
            reply_markup=back_btn("oo_back_menu"), parse_mode='HTML'); return

    # ==================== 🎁 2Go FREE ====================
    if data == "oo_quick_free_2gb":
        await bot.send_message(uid, "⏳ <b>جاري تفعيل 2 جيجا المجاني...</b>", parse_mode='HTML')
        r = await oo_purchase_free_2gb_safe(ms, at, meta)
        status = r.get("status", "error")
        if status == "ok":
            inc_stat("oo_free_2gb")
            await notify_group_success("2Go مجاني — 24H", "Ooredoo 🟠", uid, ms)
            await send_result(uid,
                f"🎉 <b>مبروك عليك!</b>\n\n"
                f"✅ <b>تم تفعيل 2 جيجا</b>\n\n"
                f"📱 <code>{o_mask(ms)}</code>\n🎁 <b>2 جيجا</b>\n"
                f"⏱️ <b>24 ساعة</b>\n💰 <b>مجاني 100%</b> 🎉\n\n"
                f"💡 اطلب <code>*200#</code>", "oo_back_menu")
            if uid == ADMIN_ID:
                await bot.send_message(uid, f"<b>🔍 تفاصيل:</b>\n<pre>{_html.escape(str(r.get('data',{}))[:1500])}</pre>", parse_mode='HTML')
            return
        if status == "already":
            await bot.send_message(uid,
                f"⏰ <b>راك مفعّل من قبل</b>\n\n"
                f"📱 <code>{o_mask(ms)}</code>\n🎁 <b>2 جيجا — 24H</b>\n\n"
                f"⏳ انتظر 24 ساعة",
                reply_markup=back_btn("oo_back_menu"), parse_mode='HTML'); return
        if status == "unauthorized":
            mm = InlineKeyboardMarkup()
            mm.add(InlineKeyboardButton("🔄 إعادة الدخول", callback_data="oo_change"))
            await bot.send_message(uid, "🔐 <b>انتهت الجلسة</b>", reply_markup=mm, parse_mode='HTML'); return
        if status == "not_allowed":
            await bot.send_message(uid, "🚫 <b>العرض غير متاح لرقمك</b>",
                reply_markup=back_btn("oo_back_menu"), parse_mode='HTML'); return
        await bot.send_message(uid, "❌ <b>فشل التفعيل</b>\n💡 حاول لاحقاً",
            reply_markup=back_btn("oo_back_menu"), parse_mode='HTML')
        if uid == ADMIN_ID:
            await bot.send_message(uid, f"<b>🔍 تفاصيل:</b>\ncode={r.get('code')}\n<pre>{_html.escape(str(r.get('data',{}))[:1500])}</pre>", parse_mode='HTML')
        return

    # ==================== ⚡ 20 دج ====================
    if data == "oo_quick_20_1g":
        r = await asyncio.to_thread(oo_check_balance, ms, at, meta)
        if r is None or r.get("status") != "ok":
            await bot.send_message(uid, "❌ تعذر فحص الرصيد", reply_markup=back_btn("oo_back_menu")); return
        try: balance = float(r.get("data", {}).get("accountBalance", 0) or 0)
        except: balance = 0
        if balance < 20:
            await bot.send_message(uid,
                f"❌ <b>الرصيد غير كافي</b>\n\n💰 <b>{balance} دج</b>\n💳 المطلوب: <b>20 دج</b>",
                reply_markup=back_btn("oo_back_menu"), parse_mode='HTML'); return
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(InlineKeyboardButton("✅ تأكيد", callback_data="oo_quick_20_1g_ok"),
               InlineKeyboardButton("❌ إلغاء", callback_data="oo_back_menu"))
        await bot.send_message(uid,
            f"⚡ <b>20 دج — 1Go — 24H</b>\n\n"
            f"🌐 <b>1 جيجا</b>\n⏱️ <b>24 ساعة</b>\n"
            f"💳 <b>20 دج</b>\n\n💰 رصيدك: <b>{balance} دج</b>",
            reply_markup=kb, parse_mode='HTML'); return

    if data == "oo_quick_20_1g_ok":
        r = await asyncio.to_thread(oo_purchase_20dzd_1go, ms, at, meta)
        if r.get("status") in ("unauthorized", "purchase_blocked"):
            mm = InlineKeyboardMarkup()
            mm.add(InlineKeyboardButton("🔄 حاول مجدداً", callback_data="oo_quick_20_1g"))
            mm.add(InlineKeyboardButton("↩️ رجوع", callback_data="oo_back_menu"))
            await bot.send_message(uid,
                f"⚠️ <b>خدمة الشراء غير متاحة مؤقتاً</b>\n\n"
                f"📱 <code>{o_mask(ms)}</code>\n💡 جرّب بعد دقيقة",
                reply_markup=mm, parse_mode='HTML'); return
        if r.get("status") == "ok":
            inc_stat("oo_20dzd_1go")
            await notify_group_success("20دج — 1Go", "Ooredoo 🟠", uid, ms)
            await send_result(uid,
                f"✅ <b>تم التفعيل</b> 🎉\n\n"
                f"📱 <code>{o_mask(ms)}</code>\n⚡ <b>1 جيجا</b> — 24 ساعة\n"
                f"💳 <b>20 دج</b>\n\n{PAGE_FOLLOW_TEXT}", "oo_back_menu")
            asyncio.create_task(_update_oo_menu_bg(uid, user, call.message.message_id))
            return
        if r.get("status") == "no_balance":
            await bot.send_message(uid, f"❌ <b>الرصيد غير كافي</b>",
                reply_markup=back_btn("oo_back_menu"), parse_mode='HTML'); return
        if r.get("status") == "already":
            await bot.send_message(uid, f"⚠️ <b>مفعّل مسبقاً</b>\n📱 <code>{o_mask(ms)}</code>",
                reply_markup=back_btn("oo_back_menu"), parse_mode='HTML'); return
        if r.get("status") == "not_allowed":
            await bot.send_message(uid, f"🚫 <b>العرض غير متاح لرقمك</b>",
                reply_markup=back_btn("oo_back_menu"), parse_mode='HTML'); return
        await bot.send_message(uid, "❌ <b>فشل التفعيل</b>",
            reply_markup=back_btn("oo_back_menu"), parse_mode='HTML'); return

# ==================== Main ====================
async def main():
    global _MAIN_LOOP
    _MAIN_LOOP = asyncio.get_running_loop()
    _MAIN_LOOP.set_exception_handler(_asyncio_exception_guard)
    print("=" * 60)
    print("🤖 البوت الموحّد — جيزي 🔴 + أوريدو 🟠 + 2Go FREE + 🔒 Lease Proxy Pool")
    print(f"👤 الأدمن: {ADMIN_ID}")
    print("=" * 60)
    saved = load_steps_saved()
    user_steps.update(saved)
    print(f"📥 {len(saved)} حالة")

    _seed_and_load_proxies()
    print(f"🔥 Pool محمّل: {len(_proxy_pool.all())} بروكسي (فحص أولي جاري...)")

    _start_resilient_worker("oo_auto_refresh", oo_auto_refresh)
    _start_resilient_worker("dz_auto_refresh", dz_auto_refresh)
    _start_resilient_worker("steps_saver", steps_saver_worker)
    _start_resilient_worker("reset_steps", reset_steps_worker)
    _start_resilient_worker("proxy_health", _proxy_health_loop)
    _start_resilient_worker("lease_cleanup", _lease_cleanup_worker)   # 🆕
    print("🔄 خيوط جاهزة (بما فيها lease_cleanup)")
    print("✅ البوت يعمل الآن...")
    while not _stop_threads.is_set():
        try:
            await bot.infinity_polling(skip_pending=True, timeout=30)
            logging.warning("[POLLING] انتهى الاتصال؛ إعادة الاتصال بعد 3 ثوانٍ")
        except (KeyboardInterrupt, SystemExit):
                    raise
        except Exception as e:
            logging.exception(f"[POLLING-CRASH] {e} — إعادة الاتصال بعد 8 ثوانٍ")
            report_admin_alert("اتصال Telegram توقف", f"Polling error: {e}\nسيتم إعادة الاتصال تلقائياً بعد 8 ثوانٍ.")
            print(f"⚠️ Polling error: {e}; reconnecting in 8s", flush=True)
        if not _stop_threads.is_set():
            await asyncio.sleep(8)

def run_forever():
    global _stop_threads, _MAIN_LOOP
    while True:
        try:
            asyncio.run(main())
            logging.warning("[SUPERVISOR] انتهت الحلقة؛ إعادة التشغيل بعد 5 ثوانٍ")
        except (KeyboardInterrupt, SystemExit):
            _stop_threads.set()
            print("\n⚠️ إيقاف...")
            save_steps()
            return
        except Exception as e:
            logging.exception(f"[SUPERVISOR-CRASH] {e}")
            report_admin_alert("عملية البوت توقفت", f"سيتم إعادة التشغيل تلقائياً بعد 10 ثوانٍ.\n{e}")
            _stop_threads.set()
            _MAIN_LOOP = None
            _stop_threads = threading.Event()
        time.sleep(10)

if __name__ == "__main__":
    run_forever()
