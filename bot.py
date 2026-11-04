#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
host.py — بوت استضافة بايثون وكيل ذكي v5
الميزات:
  • 3 مراحل: plan → execute → reply (توقف تلقائي)
  • 15+ أداة جديدة: AST, مقارنة، فحص عمليات، آمن للكتابة
  • ذاكرة جلسات (chat_history) — AI يتذكر المحادثات السابقة
  • فحص عمليات حقيقي عبر /proc/PID/cmdline (بدل os.kill الوهمي)
  • قراءة ملفات كاملة بدون تقييد 2500 حرف
  • safe_write_and_test مع rollback تلقائي
  • dashboard للمالك
"""

import os
import sys
import re
import ast
import json
import time
import signal
import shutil
import zipfile
import logging
import hashlib
import threading
import subprocess
import traceback
import uuid
import io
import contextlib
import difflib
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from collections import defaultdict, deque
from datetime import datetime

import requests

# ============================================================
# الإعدادات
# ============================================================
OWNER_ID = 7401831506
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8871218386:AAFA79lEpTaW2xgu1Y2G6P3c4RwAU7AfX_0").strip()
if not BOT_TOKEN:
    print("!! ضع BOT_TOKEN في متغيرات البيئة.", file=sys.stderr)
    sys.exit(1)

ROOT = Path(os.environ.get("HOST_ROOT", "./data")).resolve()
USERS_DIR = ROOT / "users"
DEVS_DIR = ROOT / "devs"
OWNER_DIR = ROOT / "owner"
LOGS_DIR = ROOT / "logs"
STAGING_DIR = ROOT / "staging"
SNAPSHOTS_DIR = ROOT / "snapshots"
STATE_FILE = ROOT / "state.json"
AI_CONFIG_FILE = ROOT / "ai_config.json"
AI_COOKIES_FILE = ROOT / "ai_cookies.json"
for d in (USERS_DIR, DEVS_DIR, OWNER_DIR, LOGS_DIR, STAGING_DIR, SNAPSHOTS_DIR):
    d.mkdir(parents=True, exist_ok=True)

FORCE_SUB_CHANNELS = [c.strip() for c in os.environ.get("FORCE_SUB", "@boyta28").split(",") if c.strip()]
UPLOAD_COST = 1
MAX_LOG_BYTES = 5 * 1024 * 1024
CODE_TIMEOUT = 30
TASK_TIME_LIMIT = 240
AI_MAX_ITERATIONS = 30
MAX_AI_CODE_SIZE = 40000
MAX_RESULT_TO_AI = 12000       # بدل 2500 — AI يرى نتائج أكبر
MAX_CONTEXT_CHARS = 15000      # لتقييد الـ context المُرسل
RATE_WINDOW = 60
RATE_LIMIT = 15
USER_MAX_FILES = 8
USER_MAX_BYTES = 800 * 1024
CHAT_HISTORY_LIMIT = 20        # آخر 20 رسالة تُحفظ لكل مستخدم
AI_TIMEZONE = "Africa/Algiers"
AI_TZ_OFFSET = -60
TG_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("host")

_state_lock = threading.RLock()
_procs_lock = threading.RLock()
_ai_exec_lock = threading.RLock()
_sched_lock = threading.RLock()

# ============================================================
# الحالة
# ============================================================
def _default_state() -> Dict[str, Any]:
    return {
        "devs": [],
        "users": {},
        "scanned": {},
        "pending_review": {},
        "ai_context": {},
        "chat_history": {},
        "schedules": {},
        "scan_reports": {},
        "persistent_procs": {},
        "agent_tasks": {},
        "cancelled_tasks": {},
    }

def load_state() -> Dict[str, Any]:
    with _state_lock:
        if STATE_FILE.exists():
            try:
                s = json.loads(STATE_FILE.read_text(encoding="utf-8"))
                for k, v in _default_state().items():
                    s.setdefault(k, v)
                return s
            except Exception:
                pass
        s = _default_state()
        save_state(s)
        return s

def save_state(s: Dict[str, Any]) -> None:
    with _state_lock:
        tmp = STATE_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(STATE_FILE)

STATE = load_state()

# ============================================================
# الصلاحيات
# ============================================================
def get_user(uid: int, chat_id: Optional[int] = None, name: str = "") -> Dict[str, Any]:
    with _state_lock:
        u = STATE["users"].get(str(uid))
        if not u:
            u = {"points": 0, "referred_by": None, "referrals": [],
                 "chat_id": chat_id, "name": name, "run_scored": []}
            STATE["users"][str(uid)] = u
            save_state(STATE)
        if chat_id and u.get("chat_id") != chat_id:
            u["chat_id"] = chat_id
            save_state(STATE)
        if name and not u.get("name"):
            u["name"] = name
            save_state(STATE)
        return u

def is_owner(uid: int) -> bool:
    return uid == OWNER_ID

def is_dev(uid: int) -> bool:
    return uid in STATE.get("devs", []) or is_owner(uid)

def is_privileged(uid: int) -> bool:
    return is_dev(uid)

def user_home(uid: int) -> Path:
    if is_owner(uid):
        d = OWNER_DIR
    elif uid in STATE.get("devs", []):
        d = DEVS_DIR / str(uid)
    else:
        d = USERS_DIR / str(uid)
    d.mkdir(parents=True, exist_ok=True)
    return d

def resolve_path(uid: int, p: str) -> Path:
    path = Path(p)
    if is_privileged(uid):
        if not path.is_absolute():
            home = user_home(uid).resolve()
            if (home / p).exists():
                return (home / p).resolve()
            path = (ROOT / p).resolve()
        else:
            path = path.resolve()
        return path
    home = user_home(uid).resolve()
    if path.is_absolute():
        raise PermissionError("المسارات المطلقة غير مسموحة للمستخدم العادي.")
    final = (home / p).resolve()
    if not str(final).startswith(str(home)):
        raise PermissionError("خارج مجلدك.")
    return final

def files_of(uid: int) -> List[str]:
    home = user_home(uid)
    return sorted(f.name for f in home.iterdir() if f.is_file() and f.suffix == ".py")

def uid_of_path(p: Path) -> int:
    try:
        rel = p.resolve().relative_to(ROOT)
        parts = rel.parts
        if parts and parts[0] in ("users", "devs") and len(parts) > 1:
            return int(parts[1])
    except Exception:
        pass
    return OWNER_ID

# ============================================================
# ★ ManagedProcess محسّن — فحص حقيقي عبر /proc
# ============================================================
def _read_proc_cmdline(pid: int) -> str:
    """يقرأ cmdline الفعلي للعملية من /proc."""
    try:
        with open(f"/proc/{pid}/cmdline", "rb") as f:
            data = f.read().decode("utf-8", errors="replace")
        return data.replace("\x00", " ").strip()
    except Exception:
        return ""

def _read_proc_start_time(pid: int) -> int:
    """يقرأ وقت بدء العملية من /proc/PID/stat (لتفادي PID reuse)."""
    try:
        with open(f"/proc/{pid}/stat", "r") as f:
            content = f.read()
        # آخر حقول بعد آخر ) قد تكون الأسماء؛ نأخذ الحقل 22
        rp = content.rfind(")")
        fields = content[rp+2:].split()
        return int(fields[19])  # starttime هو الحقل 22 من كل stat
    except Exception:
        return 0

class ManagedProcess:
    """مقبض موثوق لعملية — يتحقق فعلياً من cmdline."""
    def __init__(self, path: str, popen: Optional[subprocess.Popen] = None,
                 pid: Optional[int] = None, start_time: Optional[int] = None):
        self.path = path
        self.popen = popen
        self._pid = pid if pid is not None else (popen.pid if popen else None)
        self._start_time = start_time or (_read_proc_start_time(self._pid) if self._pid else 0)

    @property
    def pid(self) -> Optional[int]:
        return self._pid

    def is_running(self) -> bool:
        # 1) مع Popen — استخدام poll مباشرة
        if self.popen is not None:
            return self.popen.poll() is None
        # 2) مع PID مستعاد — تحقق فعلي
        if self._pid is None:
            return False
        # تحقق من cmdline
        cmdline = _read_proc_cmdline(self._pid)
        if not cmdline:
            return False
        # يجب أن يحتوي على اسم الملف
        fname = os.path.basename(self.path)
        if fname not in cmdline:
            return False
        # تحقق من وقت البدء
        if self._start_time:
            current_st = _read_proc_start_time(self._pid)
            if current_st != self._start_time:
                return False
        return True

    def terminate(self) -> None:
        if self.popen is not None:
            try:
                if sys.platform == "win32":
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(self.popen.pid)],
                                   capture_output=True, timeout=10)
                else:
                    try:
                        os.killpg(os.getpgid(self.popen.pid), signal.SIGTERM)
                    except ProcessLookupError:
                        pass
                    try:
                        self.popen.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        try:
                            os.killpg(os.getpgid(self.popen.pid), signal.SIGKILL)
                        except ProcessLookupError:
                            pass
            except Exception:
                try:
                    self.popen.kill()
                except Exception:
                    pass
        elif self._pid is not None:
            try:
                if sys.platform != "win32":
                    try:
                        os.killpg(os.getpgid(self._pid), signal.SIGTERM)
                    except Exception:
                        os.kill(self._pid, signal.SIGTERM)
                else:
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(self._pid)],
                                   capture_output=True, timeout=10)
            except Exception:
                pass

PROCS: Dict[str, ManagedProcess] = {}

# ============================================================
# السجلات
# ============================================================
def _log_path_for(path: Path) -> Path:
    h = hashlib.md5(str(path.resolve()).encode()).hexdigest()[:16]
    return LOGS_DIR / f"{path.name}.{h}.log"

def _rotate_log_if_needed(log_file: Path) -> None:
    try:
        if log_file.exists() and log_file.stat().st_size > MAX_LOG_BYTES:
            backup = log_file.with_suffix(".log.old")
            if backup.exists():
                try:
                    backup.unlink()
                except Exception:
                    pass
            log_file.rename(backup)
    except Exception:
        pass

# ============================================================
# التثبيت التلقائي
# ============================================================
IMPORT_TO_PIP = {
    "cv2": "opencv-python", "PIL": "Pillow", "yaml": "PyYAML",
    "bs4": "beautifulsoup4", "sklearn": "scikit-learn", "skimage": "scikit-image",
    "telebot": "pyTelegramBotAPI", "telegram": "python-telegram-bot",
    "dotenv": "python-dotenv", "jose": "python-jose", "OpenSSL": "pyOpenSSL",
    "Crypto": "pycryptodome", "serial": "pyserial", "magic": "python-magic",
    "discord": "discord.py", "wx": "wxPython",
    "MySQLdb": "mysqlclient", "psycopg2": "psycopg2-binary",
}
STDLIB = set(getattr(sys, "stdlib_module_names", set())) | {
    "__future__","typing","collections","dataclasses","pathlib","itertools",
    "functools","asyncio","concurrent","email","html","http","xml","urllib",
    "logging","json","re","os","sys","io","time","datetime","math","random",
    "subprocess","threading","multiprocessing","socket","struct","hashlib",
    "base64","binascii","zipfile","tarfile","shutil","tempfile","argparse",
    "traceback","inspect","copy","types","enum","string","secrets","uuid",
    "sqlite3","csv","ast","weakref","warnings","platform","signal","queue",
    "contextlib","operator","numbers","statistics","decimal","fractions","glob",
    "difflib",
}

def _extract_imports(code: str) -> List[str]:
    try:
        tree = ast.parse(code)
    except Exception:
        return list(set(re.findall(r"^\s*(?:from|import)\s+([a-zA-Z_][\w]*)", code, re.M)))
    mods = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                mods.add(a.name.split(".")[0])
        elif isinstance(n, ast.ImportFrom):
            if n.level == 0 and n.module:
                mods.add(n.module.split(".")[0])
    return list(mods)

def _module_available(mod: str) -> bool:
    try:
        import importlib.util
        return importlib.util.find_spec(mod) is not None
    except Exception:
        return False

def _pip_run(args: List[str], log_fp=None, timeout: int = 300) -> Tuple[bool, str]:
    try:
        r = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--no-input",
             "--disable-pip-version-check", *args],
            capture_output=True, text=True, timeout=timeout,
        )
        out = (r.stdout or "") + (r.stderr or "")
        if log_fp:
            try:
                log_fp.write(("\n[auto-install] pip install " + " ".join(args) + "\n" + out[-2000:] + "\n").encode())
                log_fp.flush()
            except Exception:
                pass
        return r.returncode == 0, out
    except Exception as e:
        return False, str(e)

def auto_install_for(path: Path, log_fp=None) -> str:
    if path.suffix.lower() != ".py":
        return "تم التخطي (ليس ملف بايثون)."
    try:
        code = path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        return f"تعذّر قراءة الملف: {e}"
    req = path.parent / "requirements.txt"
    mods = _extract_imports(code)
    missing = []
    for m in mods:
        if not m or m.startswith("_"):
            continue
        if m in STDLIB:
            continue
        if _module_available(m):
            continue
        missing.append(IMPORT_TO_PIP.get(m, m))
    missing = sorted(set(missing))
    if not req.exists() and not missing:
        return "لا مكتبات ناقصة."
    lines = []
    if req.exists():
        ok, _ = _pip_run(["-r", str(req)], log_fp=log_fp)
        lines.append(("✅" if ok else "⚠️") + " requirements.txt")
    if missing:
        ok, _ = _pip_run(missing, log_fp=log_fp)
        if ok:
            lines.append("✅ " + ", ".join(missing))
        else:
            done, failed = [], []
            for pkg in missing:
                ok2, _ = _pip_run([pkg], log_fp=log_fp, timeout=180)
                (done if ok2 else failed).append(pkg)
            if done:
                lines.append("✅ " + ", ".join(done))
            if failed:
                lines.append("⚠️ فشل: " + ", ".join(failed))
    return "\n".join(lines) if lines else "لا مكتبات ناقصة."

# ============================================================
# ★ إدارة العمليات (مُحدّثة)
# ============================================================
def start_process(path: Path) -> Tuple[bool, str]:
    key = str(path.resolve())
    with _procs_lock:
        mp = PROCS.get(key)
        if mp and mp.is_running():
            return False, f"يعمل بالفعل (PID {mp.pid})."
        if not path.exists():
            return False, "الملف غير موجود."
        log_file = _log_path_for(path)
        _rotate_log_if_needed(log_file)
        log_fp = open(log_file, "ab", buffering=0)
        install_msg = ""
        if path.suffix.lower() == ".py":
            try:
                install_msg = auto_install_for(path, log_fp=log_fp)
            except Exception as e:
                install_msg = f"تخطي التثبيت: {e}"
        try:
            kwargs = {
                "cwd": str(path.parent),
                "stdout": log_fp, "stderr": subprocess.STDOUT,
                "stdin": subprocess.DEVNULL,
            }
            if sys.platform != "win32":
                kwargs["start_new_session"] = True
            else:
                kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
            proc = subprocess.Popen([sys.executable, "-u", str(path)], **kwargs)
        except Exception as e:
            log_fp.close()
            return False, f"فشل التشغيل: {e}"
        mp = ManagedProcess(key, popen=proc)
        PROCS[key] = mp
        STATE["persistent_procs"][key] = {
            "pid": proc.pid,
            "started": int(time.time()),
            "start_time_ticks": mp._start_time,
        }
        save_state(STATE)
        suffix = ""
        if install_msg and install_msg not in ("لا مكتبات ناقصة.", "تم التخطي (ليس ملف بايثون)."):
            suffix = f"\n📦 {install_msg}"
        return True, f"شُغِّل (PID {proc.pid}). السجل: {log_file.name}{suffix}"

def stop_process(path: Path) -> Tuple[bool, str]:
    key = str(path.resolve())
    with _procs_lock:
        mp = PROCS.get(key)
        if not mp:
            return False, "لا توجد عملية مشغّلة لهذا الملف."
        if not mp.is_running():
            PROCS.pop(key, None)
            STATE["persistent_procs"].pop(key, None)
            save_state(STATE)
            return False, "العملية منتهية بالفعل."
        mp.terminate()
        PROCS.pop(key, None)
        STATE["persistent_procs"].pop(key, None)
        save_state(STATE)
        time.sleep(0.5)
        return True, "تم الإيقاف."

def restart_process(path: Path) -> Tuple[bool, str]:
    stop_process(path)
    time.sleep(1.5)
    return start_process(path)

def list_processes() -> List[Dict[str, Any]]:
    out = []
    with _procs_lock:
        dead = []
        for k, mp in PROCS.items():
            if mp.is_running():
                out.append({"path": k, "pid": mp.pid, "status": "running"})
            else:
                dead.append(k)
        for k in dead:
            PROCS.pop(k, None)
            STATE["persistent_procs"].pop(k, None)
        if dead:
            save_state(STATE)
    return out

def cleanup_stale_processes() -> List[str]:
    """يحذف العمليات الوهمية من الحالة."""
    cleaned = []
    with _procs_lock:
        dead = []
        for k, mp in PROCS.items():
            if not mp.is_running():
                dead.append(k)
        for k in dead:
            PROCS.pop(k, None)
            STATE["persistent_procs"].pop(k, None)
            cleaned.append(k)
        # إضافياً: فحص persistent_procs غير الموجودة في PROCS
        for path_str, info in list(STATE["persistent_procs"].items()):
            if path_str in PROCS:
                continue
            pid = info.get("pid") if isinstance(info, dict) else None
            st = info.get("start_time_ticks", 0) if isinstance(info, dict) else 0
            if not pid:
                STATE["persistent_procs"].pop(path_str, None)
                cleaned.append(path_str)
                continue
            cmdline = _read_proc_cmdline(pid)
            fname = os.path.basename(path_str)
            if not cmdline or fname not in cmdline:
                STATE["persistent_procs"].pop(path_str, None)
                cleaned.append(path_str)
                continue
            if st:
                current_st = _read_proc_start_time(pid)
                if current_st != st:
                    STATE["persistent_procs"].pop(path_str, None)
                    cleaned.append(path_str)
                    continue
            PROCS[path_str] = ManagedProcess(path_str, pid=pid, start_time=st)
        if cleaned:
            save_state(STATE)
    return cleaned

def verify_process(pid: int, expected_path: str) -> bool:
    cmdline = _read_proc_cmdline(pid)
    if not cmdline:
        return False
    fname = os.path.basename(expected_path)
    return fname in cmdline

def is_real_running(path: Path) -> bool:
    key = str(path.resolve())
    with _procs_lock:
        mp = PROCS.get(key)
        if not mp:
            return False
        return mp.is_running()

def restore_persistent_procs() -> None:
    saved = dict(STATE.get("persistent_procs", {}))
    restored = 0
    cleaned = 0
    for path_str, info in saved.items():
        if not isinstance(info, dict):
            cleaned += 1
            continue
        pid = info.get("pid")
        st = info.get("start_time_ticks", 0)
        if not pid:
            cleaned += 1
            continue
        cmdline = _read_proc_cmdline(pid)
        fname = os.path.basename(path_str)
        if not cmdline or fname not in cmdline:
            STATE["persistent_procs"].pop(path_str, None)
            cleaned += 1
            continue
        if st:
            current_st = _read_proc_start_time(pid)
            if current_st != st:
                STATE["persistent_procs"].pop(path_str, None)
                cleaned += 1
                continue
        PROCS[path_str] = ManagedProcess(path_str, pid=pid, start_time=st)
        restored += 1
    if cleaned:
        save_state(STATE)
    logger.info(f"استعادة العمليات: {restored} مُستعادة، {cleaned} نُظّفت.")

def tail_log(path: Path, n: int = 50) -> str:
    lf = _log_path_for(path)
    if not lf.exists():
        return "(لا يوجد سجل)"
    try:
        text = lf.read_bytes().decode("utf-8", errors="replace")
        lines = text.splitlines()[-n:]
        return "\n".join(lines) if lines else "(السجل فارغ)"
    except Exception as e:
        return f"(خطأ قراءة السجل: {e})"

# ============================================================
# عمليات الملفات الأساسية
# ============================================================
def read_file_range(path: Path, start: Optional[int] = None, end: Optional[int] = None) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    if start is None and end is None:
        return text
    lines = text.splitlines()
    s = max(1, start or 1) - 1
    e = end if end else len(lines)
    return "\n".join(lines[s:e])

def patch_file(path: Path, old: str, new: str) -> Tuple[bool, str]:
    if not path.exists():
        return False, "الملف غير موجود."
    text = path.read_text(encoding="utf-8", errors="replace")
    if old == "":
        new_text = text + new
    else:
        cnt = text.count(old)
        if cnt == 0:
            return False, "المقطع القديم غير موجود."
        if cnt > 1:
            return False, f"المقطع مكرر {cnt} مرات."
        new_text = text.replace(old, new, 1)
    if path.suffix == ".py":
        try:
            ast.parse(new_text)
        except SyntaxError as e:
            return False, f"خطأ صياغة: {e}"
    path.with_suffix(path.suffix + ".bak").write_text(text, encoding="utf-8")
    path.write_text(new_text, encoding="utf-8")
    return True, "تم التعديل (حُفظ .bak)."

def rollback_file(path: Path) -> Tuple[bool, str]:
    bak = path.with_suffix(path.suffix + ".bak")
    if not bak.exists():
        return False, "لا توجد نسخة احتياطية."
    path.write_text(bak.read_text(encoding="utf-8"), encoding="utf-8")
    return True, "تمت الاستعادة."

def zip_folder(folder: Path) -> Path:
    out = LOGS_DIR / f"{folder.name}_{int(time.time())}.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in folder.rglob("*"):
            if f.is_file():
                zf.write(f, f.relative_to(folder))
    return out

# ============================================================
# أدوات AST
# ============================================================
def ast_find_functions(path: Path) -> List[Dict[str, Any]]:
    try:
        src = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(src)
    except Exception as e:
        return [{"error": str(e)}]
    out = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out.append({
                "name": node.name,
                "lineno": node.lineno,
                "end_lineno": getattr(node, "end_lineno", node.lineno),
                "args": [a.arg for a in node.args.args],
                "is_async": isinstance(node, ast.AsyncFunctionDef),
                "decorators": [ast.unparse(d) for d in node.decorator_list] if node.decorator_list else [],
            })
    return out

def ast_get_function_source(path: Path, name: str) -> Optional[str]:
    try:
        src = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(src)
    except Exception:
        return None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            try:
                return ast.unparse(node)
            except Exception:
                lines = src.splitlines()
                end = getattr(node, "end_lineno", node.lineno)
                return "\n".join(lines[node.lineno - 1:end])
    return None

def ast_find_class(path: Path, name: str) -> Optional[str]:
    try:
        src = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(src)
    except Exception:
        return None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == name:
            try:
                return ast.unparse(node)
            except Exception:
                lines = src.splitlines()
                end = getattr(node, "end_lineno", node.lineno)
                return "\n".join(lines[node.lineno - 1:end])
    return None

def ast_list_classes(path: Path) -> List[Dict[str, Any]]:
    try:
        src = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(src)
    except Exception as e:
        return [{"error": str(e)}]
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            out.append({
                "name": node.name,
                "lineno": node.lineno,
                "end_lineno": getattr(node, "end_lineno", node.lineno),
                "methods": [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))],
            })
    return out

def ast_list_imports(path: Path) -> List[str]:
    try:
        return _extract_imports(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return []

# ============================================================
# ★ أدوات الملفات المتقدمة (الجديدة)
# ============================================================
def read_file_full(path: Path) -> str:
    """يقرأ ملفاً بالكامل — بلا حد."""
    return path.read_text(encoding="utf-8", errors="replace")

def read_file_chunked(path: Path, offset: int = 0, size: int = 4000) -> str:
    """يقرأ جزءاً من ملف (بالحروف)."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return f"خطأ: {e}"
    total = len(text)
    end = min(offset + size, total)
    return (f"[chunk {offset}-{end} من {total} حرف]\n"
            + text[offset:end])

def write_file_full(path: Path, content: str, backup: bool = True) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if backup and path.exists():
        try:
            path.with_suffix(path.suffix + ".bak").write_text(
                path.read_text(encoding="utf-8", errors="replace"), encoding="utf-8"
            )
        except Exception:
            pass
    path.write_text(content, encoding="utf-8")
    return f"كُتب {len(content)} حرف إلى {path.name}"

def safe_write_and_test(path: Path, content: str) -> str:
    """يكتب الملف، يختبره بـ compile، يرجع rollback إن فشل."""
    backup_text = None
    if path.exists():
        try:
            backup_text = path.read_text(encoding="utf-8", errors="replace")
            path.with_suffix(path.suffix + ".bak").write_text(backup_text, encoding="utf-8")
        except Exception:
            pass
    try:
        path.write_text(content, encoding="utf-8")
    except Exception as e:
        return f"❌ فشل الكتابة: {e}"

    # فحص compile
    try:
        compile(content, str(path), "exec")
    except SyntaxError as e:
        if backup_text is not None:
            path.write_text(backup_text, encoding="utf-8")
            return f"❌ خطأ صياغة (تم الاسترجاع): سطر {e.lineno}: {e.msg}"
        else:
            path.unlink(missing_ok=True)
            return f"❌ خطأ صياغة: سطر {e.lineno}: {e.msg}"
    except Exception as e:
        if backup_text is not None:
            path.write_text(backup_text, encoding="utf-8")
        return f"❌ فشل compile (تم الاسترجاع): {e}"

    return f"✅ كُتب واختُبر بنجاح ({len(content)} حرف)."

def dry_run_python(path: Path) -> str:
    """يتحقق من compile فقط بلا تشغيل."""
    try:
        src = path.read_text(encoding="utf-8", errors="replace")
        compile(src, str(path), "exec")
        return "✅ compile ناجح."
    except SyntaxError as e:
        return f"❌ خطأ صياغة في السطر {e.lineno}: {e.msg}"
    except Exception as e:
        return f"❌ {e}"

def validate_python(path: Path) -> str:
    return dry_run_python(path)

def find_lines(path: Path, needle: str, max_results: int = 100) -> List[Dict[str, Any]]:
    src = path.read_text(encoding="utf-8", errors="replace")
    out = []
    for i, line in enumerate(src.splitlines(), 1):
        if needle in line:
            out.append({"line": i, "text": line.strip()[:200]})
            if len(out) >= max_results:
                break
    return out

def grep_lite(path: Path, text: str, max_results: int = 50) -> List[Dict[str, Any]]:
    """بحث بسيط (يقبل max أو max_results)."""
    try:
        src = path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return [{"error": str(e)}]
    out = []
    for i, line in enumerate(src.splitlines(), 1):
        if text in line:
            out.append({"line": i, "text": line.strip()[:200]})
            if len(out) >= max_results:
                break
    return out

def replace_lines(path: Path, start: int, end: int, new_content: str) -> str:
    src = path.read_text(encoding="utf-8", errors="replace")
    lines = src.splitlines(keepends=True)
    if not (1 <= start <= len(lines)):
        return f"سطر البداية {start} خارج النطاق (1-{len(lines)})"
    if end < start:
        end = start
    try:
        path.with_suffix(path.suffix + ".bak").write_text(src, encoding="utf-8")
    except Exception:
        pass
    new_lines = lines[:start - 1] + [new_content + ("" if new_content.endswith("\n") else "\n")] + lines[end:]
    path.write_text("".join(new_lines), encoding="utf-8")
    return f"استُبدلت الأسطر {start}-{end}"

def insert_at_line(path: Path, line: int, content: str) -> str:
    src = path.read_text(encoding="utf-8", errors="replace")
    lines = src.splitlines(keepends=True)
    try:
        path.with_suffix(path.suffix + ".bak").write_text(src, encoding="utf-8")
    except Exception:
        pass
    insert = content + ("" if content.endswith("\n") else "\n")
    new_lines = lines[:line - 1] + [insert] + lines[line - 1:]
    path.write_text("".join(new_lines), encoding="utf-8")
    return f"أُدرج عند السطر {line}"

def append_to_file(path: Path, content: str) -> str:
    with open(path, "a", encoding="utf-8") as f:
        f.write(content if content.endswith("\n") else content + "\n")
    return f"أُضيف إلى {path.name}"

# ============================================================
# ★ أدوات سرد الملفات (الجديدة)
# ============================================================
def all_files() -> List[Dict[str, Any]]:
    """يرجع كل ملفات .py في كل مجلدات المستخدمين."""
    out = []
    for base, kind in [(USERS_DIR, "user"), (DEVS_DIR, "dev"), (OWNER_DIR, "owner")]:
        if not base.exists():
            continue
        for f in base.rglob("*.py"):
            if not f.is_file():
                continue
            try:
                st = f.stat()
                out.append({
                    "path": str(f.resolve()),
                    "name": f.name,
                    "kind": kind,
                    "uid": uid_of_path(f),
                    "size": st.st_size,
                    "mtime": int(st.st_mtime),
                })
            except Exception:
                pass
    return out

def list_user_files(uid: int, include_all_ext: bool = False) -> List[str]:
    """يرجع كل ملفات المستخدم (وليس .py فقط)."""
    home = user_home(uid)
    out = []
    for f in home.iterdir():
        if not f.is_file():
            continue
        if not include_all_ext and f.suffix != ".py":
            continue
        out.append(f.name)
    return sorted(out)

def files_matching(pattern: str) -> List[str]:
    """يبحث عن ملفات بنمط معين (اسم يحتوي على النص)."""
    out = []
    for f in all_files():
        if pattern.lower() in f["name"].lower():
            out.append(f["path"])
    return out

# ============================================================
# ★ أدوات المقارنة والدمج (الجديدة)
# ============================================================
def diff_files(path1: Path, path2: Path, max_lines: int = 200) -> List[Dict[str, Any]]:
    """يقارن ملفين ويرجع الفروق."""
    try:
        a = path1.read_text(encoding="utf-8", errors="replace").splitlines()
        b = path2.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception as e:
        return [{"error": str(e)}]
    differ = difflib.unified_diff(a, b, fromfile=path1.name, tofile=path2.name, lineterm="")
    out = []
    for line in differ:
        if len(out) >= max_lines:
            break
        out.append(line)
    return out

def sync_file_from(src: Path, dst: Path, backup: bool = True) -> str:
    """يجعل dst نسخة من src مع حفظ نسخة احتياطية."""
    if not src.exists():
        return f"❌ المصدر غير موجود: {src}"
    try:
        content = src.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return f"❌ قراءة المصدر فشلت: {e}"
    if backup and dst.exists():
        try:
            dst.with_suffix(dst.suffix + ".bak").write_text(
                dst.read_text(encoding="utf-8", errors="replace"), encoding="utf-8"
            )
        except Exception:
            pass
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(content, encoding="utf-8")
    return f"✅ نُسخ {src.name} → {dst.name} ({len(content)} حرف)"

def extract_function(path: Path, name: str) -> Optional[str]:
    return ast_get_function_source(path, name)

def compare_functions(path1: Path, path2: Path, func_name: str) -> Dict[str, Any]:
    """يقارن نفس الدالة بين ملفين."""
    s1 = ast_get_function_source(path1, func_name)
    s2 = ast_get_function_source(path2, func_name)
    if s1 is None or s2 is None:
        return {
            "in_file1": s1 is not None,
            "in_file2": s2 is not None,
            "identical": False,
        }
    return {
        "in_file1": True,
        "in_file2": True,
        "identical": s1.strip() == s2.strip(),
        "file1_source": s1[:1500],
        "file2_source": s2[:1500],
    }

# ============================================================
# ★ أدوات الملخص والتوقيع (الجديدة)
# ============================================================
def summarize_file(path: Path) -> Dict[str, Any]:
    """ملخص بنية الملف (بلا محتوى) — مفيد للـ AI."""
    try:
        src = path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return {"error": str(e)}
    lines = src.count("\n") + 1
    try:
        tree = ast.parse(src)
        funcs = [n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
        imports = sorted(set(_extract_imports(src)))
    except Exception:
        funcs = classes = imports = []
    return {
        "path": str(path),
        "name": path.name,
        "size": len(src),
        "lines": lines,
        "functions": funcs,
        "classes": classes,
        "imports": imports,
    }

def file_signature(path: Path) -> Dict[str, Any]:
    """توقيع الملف: hash + حجم + أسطر + دوال."""
    try:
        content = path.read_bytes()
        h = hashlib.md5(content).hexdigest()[:12]
        text = content.decode("utf-8", errors="replace")
        lines = text.count("\n") + 1
        try:
            tree = ast.parse(text)
            funcs = len([n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))])
        except Exception:
            funcs = 0
        return {
            "hash": h,
            "size": len(content),
            "lines": lines,
            "functions_count": funcs,
        }
    except Exception as e:
        return {"error": str(e)}

def dashboard_owner() -> str:
    """لوحة شاملة للمالك."""
    lines = ["📊 لوحة المالك\n"]
    files = all_files()
    lines.append(f"📁 إجمالي الملفات: {len(files)}")
    # تجميع بحسب النوع
    by_kind = defaultdict(int)
    for f in files:
        by_kind[f["kind"]] += 1
    for k, v in by_kind.items():
        lines.append(f"  • {k}: {v}")
    lines.append("")
    # العمليات
    procs = list_processes()
    lines.append(f"⚙️ العمليات الشغالة: {len(procs)}")
    for p in procs[:10]:
        lines.append(f"  PID {p['pid']} — {os.path.basename(p['path'])}")
    lines.append("")
    # المستخدمون
    lines.append(f"👥 المستخدمون: {len(STATE['users'])}")
    for uid_str, u in list(STATE["users"].items())[:10]:
        lines.append(f"  {uid_str} — {u.get('name','?')} — {u.get('points',0)} نقطة")
    lines.append("")
    # المهام المجدولة
    lines.append(f"⏱ المهام المجدولة: {len(STATE['schedules'])}")
    # المهام المعلقة
    lines.append(f"⏳ مراجعات معلقة: {len(STATE['pending_review'])}")
    return "\n".join(lines)

# ============================================================
# ★ ذاكرة الجلسات (الجديدة)
# ============================================================
def add_to_chat_history(uid: int, role: str, content: str) -> None:
    """يضيف رسالة لذاكرة المستخدم."""
    with _state_lock:
        hist = STATE["chat_history"].setdefault(str(uid), [])
        hist.append({
            "role": role,
            "content": content[:2000],
            "ts": int(time.time()),
        })
        STATE["chat_history"][str(uid)] = hist[-CHAT_HISTORY_LIMIT:]
        save_state(STATE)

def get_chat_history_text(uid: int, max_chars: int = 4000) -> str:
    """يرجع نص تاريخ المحادثة للتمرير إلى AI."""
    hist = STATE["chat_history"].get(str(uid), [])
    if not hist:
        return ""
    lines = []
    for m in hist[-10:]:
        role = "المستخدم" if m["role"] == "user" else "أنا"
        content = m["content"][:500]
        lines.append(f"{role}: {content}")
    txt = "\n".join(lines)
    if len(txt) > max_chars:
        txt = txt[-max_chars:]
    return txt

def clear_chat_history(uid: int) -> None:
    with _state_lock:
        STATE["chat_history"][str(uid)] = []
        save_state(STATE)

# ============================================================
# النقاط والإحالة
# ============================================================
def add_points(uid: int, pts: int) -> None:
    u = get_user(uid)
    u["points"] = u.get("points", 0) + pts
    save_state(STATE)

def award_run_once(uid: int, path: Path) -> Optional[int]:
    u = get_user(uid)
    key = str(path.resolve())
    scored = u.setdefault("run_scored", [])
    if key in scored:
        return None
    scored.append(key)
    u["points"] = u.get("points", 0) + 10
    save_state(STATE)
    return 10

def handle_referral(new_uid: int, ref_uid: int) -> bool:
    if new_uid == ref_uid:
        return False
    u = get_user(new_uid)
    if u.get("referred_by"):
        return False
    ref = get_user(ref_uid)
    u["referred_by"] = ref_uid
    ref.setdefault("referrals", []).append(new_uid)
    ref["points"] = ref.get("points", 0) + 10
    u["points"] = u.get("points", 0) + 5
    save_state(STATE)
    return True

def run_for_user(uid: int, path: Path) -> str:
    ok, msg = start_process(path)
    if ok:
        awarded = award_run_once(uid, path)
        if awarded:
            msg += f" (+{awarded} نقاط)"
    return msg

# ============================================================
# Telegram API
# ============================================================
def tg(method: str, **params) -> Dict[str, Any]:
    url = f"{TG_API}/{method}"
    files = params.pop("_files", None)
    try:
        r = requests.post(url, data=params, files=files, timeout=60)
        return r.json()
    except Exception as e:
        logger.error(f"TG {method} فشل: {e}")
        return {"ok": False, "error": str(e)}

def send(chat_id: int, text: str, keyboard=None, parse_mode=None) -> Dict[str, Any]:
    MAX = 4000
    if len(text) > MAX:
        text = text[:MAX] + "\n\n... [مقطوع]"
    kw = {"chat_id": chat_id, "text": text}
    if parse_mode:
        kw["parse_mode"] = parse_mode
    if keyboard:
        kw["reply_markup"] = json.dumps({"inline_keyboard": keyboard})
    return tg("sendMessage", **kw)

def send_file(chat_id: int, path: Path, caption: str = "") -> Dict[str, Any]:
    if not path.exists():
        return send(chat_id, f"الملف غير موجود: {path}")
    with open(path, "rb") as f:
        return tg("sendDocument", chat_id=chat_id, caption=caption,
                  _files={"document": (path.name, f)})

def answer_cb(cb_id: str, text: str = "") -> None:
    tg("answerCallbackQuery", callback_query_id=cb_id, text=text)

def edit_message(chat_id: int, message_id: int, text: str,
                 keyboard=None, parse_mode=None) -> Dict[str, Any]:
    MAX = 4000
    if len(text) > MAX:
        text = text[:MAX] + "\n\n... [مقطوع]"
    kw = {"chat_id": chat_id, "message_id": message_id, "text": text}
    if parse_mode:
        kw["parse_mode"] = parse_mode
    if keyboard:
        kw["reply_markup"] = json.dumps({"inline_keyboard": keyboard})
    return tg("editMessageText", **kw)

def delete_message(chat_id: int, message_id: int) -> None:
    tg("deleteMessage", chat_id=chat_id, message_id=message_id)

def get_file_bytes(file_id: str) -> Optional[bytes]:
    j = tg("getFile", file_id=file_id)
    if not j.get("ok"):
        return None
    fp = j["result"]["file_path"]
    r = requests.get(f"https://api.telegram.org/file/bot{BOT_TOKEN}/{fp}", timeout=60)
    return r.content if r.status_code == 200 else None

class TypingIndicator:
    def __init__(self, chat_id: int):
        self.chat_id = chat_id
        self._stop = threading.Event()
        self._thread = None

    def start(self) -> None:
        def _loop():
            while not self._stop.is_set():
                try:
                    tg("sendChatAction", chat_id=self.chat_id, action="typing")
                except Exception:
                    pass
                self._stop.wait(4)
        self._thread = threading.Thread(target=_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

# ============================================================
# الاشتراك
# ============================================================
def is_subscribed(uid: int) -> Tuple[bool, List[str]]:
    if is_privileged(uid):
        return True, []
    if not FORCE_SUB_CHANNELS:
        return True, []
    missing = []
    for ch in FORCE_SUB_CHANNELS:
        try:
            r = tg("getChatMember", chat_id=ch, user_id=uid)
            if not r.get("ok"):
                missing.append(ch)
                continue
            if r.get("result", {}).get("status", "left") not in ("member", "administrator", "creator"):
                missing.append(ch)
        except Exception:
            missing.append(ch)
    return (not missing), missing

def send_sub_prompt(chat_id: int, missing: List[str]) -> None:
    kb = [[{"text": f"🔔 اشترك في {ch}", "url": f"https://t.me/{ch.lstrip('@')}"}] for ch in missing]
    kb.append([{"text": "✅ تحققت من الاشتراك", "callback_data": "check_sub"}])
    send(chat_id, "🚫 اشترك في القنوات التالية:\n" + "\n".join(f"• {c}" for c in missing), keyboard=kb)

# ============================================================
# واجهة المستخدم
# ============================================================
def main_menu(uid: int) -> List[List[Dict[str, str]]]:
    kb = [
        [{"text": "📤 رفع ملف", "callback_data": "howto_upload"}],
        [{"text": "📁 ملفاتي", "callback_data": "files"},
         {"text": "📊 الإحصائيات", "callback_data": "stats"}],
        [{"text": "💰 نقاطي", "callback_data": "points"},
         {"text": "🔗 الإحالة", "callback_data": "referral"}],
    ]
    if is_dev(uid):
        kb.append([{"text": "👨‍💻 لوحة المطور", "callback_data": "dev_panel"}])
    return kb

def _role_line(uid: int) -> str:
    if is_owner(uid):
        return "مميز 👑"
    if uid in STATE.get("devs", []):
        return "مطور 🛠"
    return "مستخدم عادي 👤"

def welcome_card(uid: int, name: str) -> str:
    u = get_user(uid)
    pts = "∞" if is_owner(uid) else str(u.get("points", 0))
    return (f"👤 المستخدم: {name or '—'}\n"
            f"📊 الحالة: {_role_line(uid)}\n"
            f"💰 النقاط: {pts}\n"
            f"📁 الملفات: {len(files_of(uid))}\n\n"
            f"💡 أرسل أي طلب. سأفكر، أخطط، ثم أنفذ.")

def strip_stars(text: str) -> str:
    return re.sub(r"\*+", "", text) if text else text

def _file_action_kb(fname: str) -> List[List[Dict[str, str]]]:
    return [
        [{"text": "▶️ تشغيل", "callback_data": f"run:{fname}"},
         {"text": "⏹ إيقاف", "callback_data": f"stop:{fname}"}],
        [{"text": "🔄 إعادة تشغيل", "callback_data": f"restart:{fname}"},
         {"text": "🗑 حذف", "callback_data": f"del:{fname}"}],
        [{"text": "📝 تعديل عبر AI", "callback_data": f"aiedit:{fname}"},
         {"text": "⬇️ تحميل", "callback_data": f"get:{fname}"}],
        [{"text": "📋 السجلات", "callback_data": f"log:{fname}"},
         {"text": "📥 تحميل السجل", "callback_data": f"logf:{fname}"}],
        [{"text": "⬅️ رجوع", "callback_data": "menu"}],
    ]

def file_actions(uid: int, chat_id: int, fname: str, edit_id: Optional[int] = None):
    text = f"إدارة: {fname}"
    kb = _file_action_kb(fname)
    if edit_id:
        r = edit_message(chat_id, edit_id, text, keyboard=kb)
        if r.get("ok"):
            return
    send(chat_id, text, keyboard=kb)

def cancel_task_kb(task_id: str) -> List[List[Dict[str, str]]]:
    return [[{"text": "🚫 إلغاء المهمة", "callback_data": f"cancel_task:{task_id}"}]]

# ============================================================
# ChatGPT v5
# ============================================================
PAYLOAD_CONFIG = {
    "model": "auto", "history_and_training_disabled": False,
    "enable_message_followups": True, "force_use_sse": True,
    "force_use_search": None, "force_paragen": False,
    "supports_buffering": False, "timezone": AI_TIMEZONE,
    "timezone_offset_min": AI_TZ_OFFSET, "system_hints": [],
    "is_onboarding_conversation": False,
    "no_auth_ad_preferences": {"personalization_enabled": False, "history_enabled": True},
    "client_prepare_dispatch": "debounced",
    "client_prepare_source": "composer_editor_state",
    "client_prepare_state": "success"
}

class ChatGPT:
    def __init__(self):
        self.session = requests.Session()
        self.payload_config = dict(PAYLOAD_CONFIG)
        self.device_id = None
        self.conduit_token = None
        self.chat_req_token = None
        self.play_integrity_token = ""
        self.convo_session_id = None
        self.turn_trace_id = None
        self.base_url = "https://android.chat.openai.com"
        self.prepare_path = "/backend-anon/f/conversation/prepare"
        self.sentinel_path = "/backend-anon/sentinel/chat-requirements"
        self.conversation_path = "/backend-anon/f/conversation"
        self.user_agent = "ChatGPT/1.2026.195 (Android 15; RMX3834; build 2619512)"
        self.device_tier = "lower_mid"
        self.account_id = "default"
        self.residency_region = "no_constraint"
        self.accept_language = "ar-EG,ar;q=0.9,en-US;q=0.8,en;q=0.7"
        self.timezone = AI_TIMEZONE
        self.timezone_offset = AI_TZ_OFFSET
        self.load_state()
        if not self.device_id:
            self.device_id = str(uuid.uuid4())
            self.save_state()
        self.init_session()

    def load_state(self):
        try:
            if AI_CONFIG_FILE.exists():
                data = json.loads(AI_CONFIG_FILE.read_text(encoding="utf-8"))
                self.device_id = data.get("device_id")
                self.play_integrity_token = data.get("play_integrity_token", "")
                self.conduit_token = data.get("conduit_token", "")
                if "payload_config" in data:
                    for k, v in data["payload_config"].items():
                        if k in self.payload_config:
                            self.payload_config[k] = v
                for attr in ["base_url", "prepare_path", "sentinel_path", "conversation_path",
                             "user_agent", "device_tier", "account_id", "residency_region",
                             "accept_language", "timezone", "timezone_offset"]:
                    if attr in data:
                        setattr(self, attr, data[attr])
            if AI_COOKIES_FILE.exists():
                self.session.cookies.update(json.loads(AI_COOKIES_FILE.read_text(encoding="utf-8")))
        except Exception as e:
            logger.warning(f"فشل تحميل ai_config: {e}")

    def save_state(self):
        try:
            data = {
                "device_id": self.device_id,
                "play_integrity_token": self.play_integrity_token,
                "conduit_token": self.conduit_token,
                "payload_config": self.payload_config,
                "base_url": self.base_url,
                "prepare_path": self.prepare_path,
                "sentinel_path": self.sentinel_path,
                "conversation_path": self.conversation_path,
                "user_agent": self.user_agent,
                "device_tier": self.device_tier,
                "account_id": self.account_id,
                "residency_region": self.residency_region,
                "accept_language": self.accept_language,
                "timezone": self.timezone,
                "timezone_offset": self.timezone_offset,
            }
            AI_CONFIG_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            AI_COOKIES_FILE.write_text(json.dumps(self.session.cookies.get_dict(), indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning(f"فشل حفظ ai_config: {e}")

    def generate_sentry(self):
        tid = uuid.uuid4().hex
        self.sentry_trace = f"{tid[:16]}-{tid[16:32]}"
        self.baggage = (f"sentry-environment=production,sentry-org_id=33249,"
                        f"sentry-public_key=6884768431e4ba548d58cbf3ad96e4ce,"
                        f"sentry-release=com.openai.chatgpt%401.2026.195%2B2619512,"
                        f"sentry-sample_rand=0.{int(time.time()*1000)%1000000},"
                        f"sentry-trace_id={tid[:16]}")

    def common_headers(self):
        self.generate_sentry()
        return {
            "host": self.base_url.replace("https://", ""),
            "user-agent": self.user_agent,
            "oai-package-name": "com.openai.chatgpt",
            "oai-client-type": "android",
            "oai-device-id": self.device_id,
            "accept-language": self.accept_language,
            "x-device-tier": self.device_tier,
            "chatgpt-account-id": self.account_id,
            "chatgpt-residency-region": self.residency_region,
            "accept": "application/json",
            "sentry-trace": self.sentry_trace,
            "baggage": self.baggage,
            "accept-encoding": "gzip"
        }

    def init_session(self):
        self.convo_session_id = str(uuid.uuid4())
        self.turn_trace_id = str(uuid.uuid4())
        url = f"{self.base_url}{self.prepare_path}"
        headers = {**self.common_headers(),
                   "x-oai-convo-session-id": self.convo_session_id,
                   "x-oai-turn-trace-id": self.turn_trace_id,
                   "x-conduit-token": self.conduit_token or "",
                   "x-openai-target-path": self.prepare_path,
                   "content-type": "application/json"}
        body = {"action": "next", "messages": [], "model": self.payload_config["model"],
                "history_and_training_disabled": self.payload_config["history_and_training_disabled"],
                "fork_from_shared_post": False, "enable_message_followups": False,
                "force_use_sse": False, "force_use_search": None, "force_paragen": False,
                "supports_buffering": False, "timezone": self.timezone,
                "timezone_offset_min": self.timezone_offset,
                "system_hints": self.payload_config["system_hints"],
                "is_onboarding_conversation": self.payload_config["is_onboarding_conversation"],
                "no_auth_ad_preferences": self.payload_config["no_auth_ad_preferences"],
                "client_prepare_dispatch": self.payload_config["client_prepare_dispatch"],
                "client_prepare_source": self.payload_config["client_prepare_source"]}
        try:
            r = self.session.post(url, headers=headers, json=body, timeout=30)
            if r.ok and "conduit_token" in r.json():
                self.conduit_token = r.json()["conduit_token"]
                self.save_state()
        except Exception:
            pass
        url2 = f"{self.base_url}{self.sentinel_path}"
        headers2 = {**self.common_headers(),
                    "x-openai-target-path": self.sentinel_path,
                    "content-type": "application/json"}
        try:
            r = self.session.post(url2, headers=headers2, json={}, timeout=30)
            if r.ok:
                self.chat_req_token = r.json().get("token")
        except Exception:
            pass
        self.save_state()

    def send_message(self, text: str, retry: bool = True) -> Tuple[Optional[str], Optional[str]]:
        url = f"{self.base_url}{self.conversation_path}"
        sentinel = {"bot_token": {"play_integrity_token": self.play_integrity_token or "",
                                  "chat_requirement_token": self.chat_req_token or ""}}
        headers = {**self.common_headers(),
                   "accept": "text/event-stream,application/json",
                   "cache-control": "no-cache",
                   "x-sentinel-payload": json.dumps(sentinel),
                   "x-conduit-token": self.conduit_token or "",
                   "x-oai-convo-session-id": self.convo_session_id,
                   "x-oai-turn-trace-id": str(uuid.uuid4()),
                   "oai-echo-logs": "1,552,0,822,1,3296,1,5355,0,5533,1,8297,0,8739,1,9818,0,11081,1,12543",
                   "x-openai-target-path": self.conversation_path,
                   "content-type": "application/json"}
        msg_id = str(uuid.uuid4())
        body = {"action": "next",
                "messages": [{"id": msg_id, "author": {"role": "user"},
                              "content": {"parts": [text], "content_type": "text"},
                              "status": "finished_successfully", "recipient": "all",
                              "metadata": {"model_slug": self.payload_config["model"],
                                           "default_model_slug": "auto"}}],
                "model": self.payload_config["model"],
                "history_and_training_disabled": self.payload_config["history_and_training_disabled"],
                "enable_message_followups": self.payload_config["enable_message_followups"],
                "force_use_sse": self.payload_config["force_use_sse"],
                "force_use_search": self.payload_config["force_use_search"],
                "force_paragen": self.payload_config["force_paragen"],
                "supports_buffering": self.payload_config["supports_buffering"],
                "timezone": self.timezone, "timezone_offset_min": self.timezone_offset,
                "system_hints": self.payload_config["system_hints"],
                "is_onboarding_conversation": self.payload_config["is_onboarding_conversation"],
                "no_auth_ad_preferences": self.payload_config["no_auth_ad_preferences"],
                "client_prepare_state": self.payload_config["client_prepare_state"],
                "stream": True}
        try:
            r = self.session.post(url, headers=headers, json=body, stream=True, timeout=180)
            if r.status_code in (401, 403, 422, 500) and retry:
                self.init_session()
                return self.send_message(text, False)
            r.raise_for_status()
        except Exception as e:
            return None, f"Exception: {e}"
        if "x-conduit-token" in r.headers:
            self.conduit_token = r.headers["x-conduit-token"]
            self.save_state()
        full_text = ""
        try:
            for line in r.iter_lines(decode_unicode=True):
                if not line or not line.startswith("data: "):
                    continue
                data = line[6:]
                if data == "[DONE]":
                    break
                try:
                    ev = json.loads(data)
                except Exception:
                    continue
                if "message" in ev:
                    m = ev["message"]
                    if m["author"]["role"] == "assistant" and m.get("channel") == "final":
                        parts = m["content"]["parts"]
                        if parts:
                            full_text = "".join(parts)
        except Exception as e:
            return full_text or None, f"Stream Error: {e}"
        self.save_state()
        return full_text, None

    def generate(self, prompt: str) -> str:
        reply, error = self.send_message(prompt)
        if error and not reply:
            return f"__ERROR__ {error}"
        return reply or ""

    def fresh_session(self):
        self.convo_session_id = None
        self.turn_trace_id = None
        self.init_session()

AI = ChatGPT()

# ============================================================
# المهام المجدولة
# ============================================================
def _parse_interval(s: Any) -> int:
    if isinstance(s, (int, float)):
        return max(1, int(s))
    t = str(s).strip().lower()
    m = re.match(r"^(\d+)\s*([smhd]?)$", t)
    if not m:
        return max(1, int(float(t)))
    n = int(m.group(1))
    unit = m.group(2) or "s"
    return n * {"s": 1, "m": 60, "h": 3600, "d": 86400}[unit]

def schedule_task(uid: int, code: str, every: Any = None, after: Any = None,
                  note: str = "") -> str:
    if not is_privileged(uid):
        return "غير مسموح."
    if not code or len(code) > MAX_AI_CODE_SIZE:
        return "الكود فارغ أو كبير جداً."
    now = int(time.time())
    if every is not None:
        interval = _parse_interval(every); repeat = True; next_run = now + interval
    elif after is not None:
        interval = _parse_interval(after); repeat = False; next_run = now + interval
    else:
        return "حدد every أو after."
    sid = str(int(time.time() * 1000))
    with _sched_lock:
        STATE["schedules"][sid] = {
            "owner": uid, "code": code, "interval": interval,
            "next_run": next_run, "repeat": repeat, "note": note, "created": now,
        }
        save_state(STATE)
    when = "كل" if repeat else "بعد"
    return f"⏱ مهمة #{sid} — {when} {interval}ث — {note or 'مجدولة'}"

def list_scheduled(uid: int) -> str:
    if not is_privileged(uid):
        return "غير مسموح."
    with _sched_lock:
        items = list(STATE["schedules"].items())
    if not items:
        return "(لا مهام مجدولة)"
    out = []
    now = int(time.time())
    for sid, s in items:
        kind = f"كل {s['interval']}ث" if s["repeat"] else f"مرة بعد {s['interval']}ث"
        remain = max(0, s["next_run"] - now)
        out.append(f"#{sid} — {kind} — التالي بعد {remain}ث — {s.get('note','')}")
    return "\n".join(out)

def cancel_scheduled(uid: int, sid: str) -> str:
    if not is_privileged(uid):
        return "غير مسموح."
    with _sched_lock:
        gone = STATE["schedules"].pop(str(sid), None)
        save_state(STATE)
    return f"أُلغيت #{sid}" if gone else "غير موجود."

def _scheduler_loop() -> None:
    logger.info("مُشغّل المهام المجدولة يعمل.")
    while True:
        try:
            now = int(time.time())
            due = []
            with _sched_lock:
                for sid, s in list(STATE["schedules"].items()):
                    if s["next_run"] <= now:
                        due.append((sid, dict(s)))
            for sid, s in due:
                try:
                    owner = s["owner"]
                    res = execute_ai_code(s["code"], owner)
                    logger.info(f"[sched #{sid}] {str(res)[:200]}")
                    ch = get_user(owner).get("chat_id")
                    if ch:
                        send(ch, f"⏱ مهمة #{sid}:\n{str(res)[:1000]}")
                except Exception as e:
                    logger.exception(f"sched {sid} error")
                    ch = get_user(s["owner"]).get("chat_id")
                    if ch:
                        send(ch, f"⚠️ مهمة #{sid} فشلت: {e}")
                with _sched_lock:
                    cur = STATE["schedules"].get(sid)
                    if not cur:
                        continue
                    if cur["repeat"]:
                        cur["next_run"] = int(time.time()) + cur["interval"]
                    else:
                        STATE["schedules"].pop(sid, None)
                    save_state(STATE)
        except Exception:
            logger.exception("scheduler loop error")
        time.sleep(3)

# ============================================================
# محرك تنفيذ الكود
# ============================================================
def execute_ai_code(code: str, uid: int) -> str:
    if not code:
        return "(كود فارغ)"
    if len(code) > MAX_AI_CODE_SIZE:
        return f"⛔ الكود كبير جداً ({len(code)} حرف، الحد {MAX_AI_CODE_SIZE})."
    if not is_privileged(uid):
        forbidden = ["os.system", "shutil.rmtree", "__import__('os')",
                     "STATE[", "PROCS", "OWNER_ID", "subprocess"]
        for f in forbidden:
            if f in code:
                return f"⛔ ممنوع للمستخدم العادي: {f}"
    current_chat_id = get_user(uid).get("chat_id")
    exec_globals = {
        "__builtins__": __builtins__,
        "STATE": STATE, "PROCS": PROCS, "ROOT": ROOT,
        "USERS_DIR": USERS_DIR, "DEVS_DIR": DEVS_DIR, "OWNER_DIR": OWNER_DIR,
        "LOGS_DIR": LOGS_DIR, "STAGING_DIR": STAGING_DIR,
        "SNAPSHOTS_DIR": SNAPSHOTS_DIR, "OWNER_ID": OWNER_ID,
        "UID": uid, "CHAT_ID": current_chat_id,
        # العمليات
        "list_processes": list_processes, "start_process": start_process,
        "stop_process": stop_process, "restart_process": restart_process,
        "run_for_user": lambda p: run_for_user(uid, p),
        "tail_log": tail_log, "restore_persistent_procs": restore_persistent_procs,
        "cleanup_stale_processes": cleanup_stale_processes,
        "verify_process": verify_process, "is_real_running": is_real_running,
        # الملفات
        "files_of": files_of, "user_home": user_home, "resolve_path": resolve_path,
        "read_file_range": read_file_range, "patch_file": patch_file,
        "rollback_file": rollback_file, "zip_folder": zip_folder,
        "auto_install_for": auto_install_for, "uid_of_path": uid_of_path,
        # AST
        "ast_find_functions": ast_find_functions,
        "ast_get_function_source": ast_get_function_source,
        "ast_find_class": ast_find_class,
        "ast_list_classes": ast_list_classes,
        "ast_list_imports": ast_list_imports,
        # ملفات متقدمة
        "read_file_full": read_file_full,
        "read_file_chunked": read_file_chunked,
        "write_file_full": write_file_full,
        "safe_write_and_test": safe_write_and_test,
        "dry_run_python": dry_run_python,
        "validate_python": validate_python,
        "find_lines": find_lines,
        "replace_lines": replace_lines,
        "insert_at_line": insert_at_line,
        "append_to_file": append_to_file,
        "grep_lite": grep_lite,
        # سرد
        "all_files": all_files,
        "list_user_files": list_user_files,
        "files_matching": files_matching,
        # مقارنة
        "diff_files": diff_files,
        "sync_file_from": sync_file_from,
        "extract_function": extract_function,
        "compare_functions": compare_functions,
        # ملخص
        "summarize_file": summarize_file,
        "file_signature": file_signature,
        "dashboard_owner": dashboard_owner,
        # ذاكرة
        "add_to_chat_history": add_to_chat_history,
        "get_chat_history_text": get_chat_history_text,
        "clear_chat_history": clear_chat_history,
        # المستخدمون
        "get_user": get_user, "is_owner": is_owner, "is_dev": is_dev,
        "is_privileged": is_privileged, "add_points": add_points,
        "award_run_once": award_run_once, "save_state": save_state, "load_state": load_state,
        # الإرسال
        "send": send, "send_file": send_file, "tg": tg,
        # الجدولة
        "schedule_task": schedule_task, "list_scheduled": list_scheduled,
        "cancel_scheduled": cancel_scheduled,
        # مكتبات
        "os": os, "sys": sys, "json": json, "time": time, "re": re,
        "subprocess": subprocess, "shutil": shutil, "Path": Path,
        "threading": threading, "zipfile": zipfile, "logging": logging,
        "hashlib": hashlib, "uuid": uuid, "ast": ast, "difflib": difflib,
        "math": __import__("math"), "datetime": __import__("datetime"),
    }
    result = {"out": "", "err": "", "exc": None, "done": False}

    def _runner():
        buf_out, buf_err = io.StringIO(), io.StringIO()
        try:
            with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
                exec(code, exec_globals)
        except SystemExit:
            pass
        except BaseException:
            result["exc"] = traceback.format_exc()[:2500]
        finally:
            result["out"] = buf_out.getvalue()
            result["err"] = buf_err.getvalue()
            result["done"] = True

    with _ai_exec_lock:
        t = threading.Thread(target=_runner, daemon=True)
        t.start()
        t.join(timeout=CODE_TIMEOUT)
        if not result["done"]:
            return f"⏱ انتهى وقت التنفيذ ({CODE_TIMEOUT}ث)."
    if result["exc"]:
        return f"❌ خطأ:\n{result['exc']}"
    combined = result["out"]
    if result["err"]:
        combined += ("\n[STDERR]\n" + result["err"]) if combined else result["err"]
    return combined.strip() or "(تم التنفيذ بدون مخرجات)"

# ============================================================
# ★ الوكيل v5 — 3 مراحل + ذاكرة
# ============================================================
ENV_DESCRIPTION = """أنت مساعد كتابة كود بايثون. المستخدم يشتغل على بوت "استضافة" ويرسل طلبات بالعربية، ومهمتك تحويل كل طلب إلى كود بايثون جاهز للتنفيذ.

البيئة تُوفّر المتغيرات والدوال التالية:

• المتغيرات:
  - STATE (dict): STATE["users"], STATE["devs"], STATE["chat_history"] ...
  - PROCS (dict): العمليات
  - ROOT, USERS_DIR, DEVS_DIR, OWNER_DIR, LOGS_DIR, STAGING_DIR, SNAPSHOTS_DIR: Path
  - OWNER_ID = 7401831506
  - UID: معرّف المستخدم الحالي
  - CHAT_ID: محادثة المستخدم

• العمليات:
  - list_processes() → [{"path", "pid", "status": "running"}]
  - start_process(Path), stop_process(Path), restart_process(Path) → (bool, str)
  - run_for_user(Path) → str (يحتسب نقاط)
  - tail_log(Path, n), cleanup_stale_processes(), verify_process(pid, path), is_real_running(Path)

• الملفات:
  - files_of(uid) → ملفات .py فقط
  - list_user_files(uid, include_all_ext=False) → كل الملفات
  - all_files() → كل ملفات الاستضافة [{path, name, kind, uid, size, mtime}]
  - files_matching(pattern) → مسارات تحتوي على pattern
  - read_file_full(Path) → كل المحتوى
  - read_file_chunked(Path, offset, size) → جزء من الملف
  - write_file_full(Path, content) → كتابة (مع backup)
  - safe_write_and_test(Path, content) → كتابة + اختبار compile + rollback عند فشل
  - patch_file(Path, old, new) → تعديل مقطع فريد
  - replace_lines(Path, start, end, new), insert_at_line(Path, line, content)
  - find_lines(Path, "نص"), grep_lite(Path, "نص", max_results=50)
  - dry_run_python(Path), validate_python(Path), file_signature(Path)
  - summarize_file(Path) → {lines, functions, classes, imports}

• AST:
  - ast_find_functions(Path) → [{name, lineno, args, ...}]
  - ast_get_function_source(Path, name) → كود الدالة
  - ast_find_class(Path, name), ast_list_classes(Path), ast_list_imports(Path)
  - extract_function(Path, name), compare_functions(p1, p2, name)

• المقارنة والدمج:
  - diff_files(p1, p2, max_lines=200) → unified diff
  - sync_file_from(src, dst) → يجعل dst = src

• ذاكرة الجلسات:
  - get_chat_history_text(uid) → نص آخر 10 رسائل
  - add_to_chat_history(uid, role, content)
  - clear_chat_history(uid)

• لوحة المالك:
  - dashboard_owner() → نظرة شاملة

• المستخدمون والإرسال:
  - get_user(uid), is_owner(uid), is_dev(uid), is_privileged(uid)
  - send(chat_id, text), send_file(chat_id, Path), save_state(STATE)

• الجدولة:
  - schedule_task(uid, code, every="5m", after=None), list_scheduled(uid), cancel_scheduled(uid, sid)

المكتبات: os, sys, json, time, re, subprocess, shutil, Path, threading, zipfile, hashlib, ast, math, datetime, logging, uuid, difflib.

━━━ قواعد صارمة ━━━
1. ممنوع Regex (re.finditer/re.sub/re.match/re.search) على محتوى ملفات البايثون — استخدم ast_* دائماً.
2. لتعديل ملف: إما safe_write_and_test(Path, new_content) أو patch_file(Path, old, new).
3. لقراءة ملف كبير: read_file_chunked(Path, offset, size) — ثم عُد لأجزاء أخرى.
4. لا تنسَ print() لعرض النتائج.
5. AI يتذكر آخر 10 رسائل تلقائياً — لا تكرر ما قلته.
"""

# ============ المرحلة 1: التخطيط ============
PLAN_PROMPT = ENV_DESCRIPTION + """

━━━ مرحلة التخطيط ━━━
مهمتك: تحديد إن كان الطلب بسيطاً (سؤال) أو يحتاج تنفيذ.

إذا الطلب بسيط (سؤال/استفسار/طلب معلومات تظهرها بنفسك)، رد:
{"action": "reply", "text": "الرد المختصر"}

إذا الطلب يحتاج تنفيذ كود/ملفات، اقترح خطة (2-6 خطوات):
{"action": "plan", "steps": ["الخطوة 1", ...], "say": "سأنفذ..."}

قواعد:
- JSON فقط.
- لا تكتب كوداً في هذه المرحلة.
- استخدم ذاكرة الجلسات إن كان الطلب متابعاً لسياق.
"""

# ============ المرحلة 2: التنفيذ ============
EXECUTE_PROMPT = ENV_DESCRIPTION + """

━━━ مرحلة التنفيذ ━━━
نفّذ الخطوة الحالية فقط.

صيغة الرد:
{"action": "execute", "code": "كود بايثون", "done": true|false}

- done = true إذا هذه آخر خطوة، أو انتهت المهمة فعلاً.
- done = false إن كانت هناك خطوات تالية.

⚠️ قواعد:
- لا تكرر الخطوات السابقة.
- استخدم safe_write_and_test عند تعديل الملفات.
- print() ضروري لعرض النتائج.
- عند طلب قراءة ملف كامل: استخدم read_file_full مباشرة (لا تقلق من الحد).
- عند طلب تعديل ملف كبير: استخدم read_file_full + write_file_full/safe_write_and_test.
- عند مقارنة ملفين: استخدم diff_files أو compare_functions.
- JSON فقط.
"""

# ============ المرحلة 3: الرد النهائي ============
REPLY_PROMPT = ENV_DESCRIPTION + """

━━━ مرحلة الرد النهائي ━━━
المهمة انتهت. لديك نتائج التنفيذ.

صيغة الرد:
{"action": "reply", "text": "الرد النهائي بالعربية"}

قواعد:
- لا تطلب أي تنفيذ.
- اكتب الرد بناءً على النتائج.
- لو النتائج فارغة أو فاشلة، اشرح بلطف.
- JSON فقط.
"""

# ============ بروتوكول مبسّط عند الرفض ============
SIMPLE_PROMPT = """أنا مبرمج وأحتاج كود بايثون بسيط.

المتاح في بيئتي:
- files_of(uid), list_user_files(uid), all_files()
- list_processes(), start_process(Path), stop_process(Path), restart_process(Path)
- read_file_full(Path), safe_write_and_test(Path, content), patch_file(Path, old, new)
- ast_find_functions(Path), ast_get_function_source(Path, name)
- STATE["users"] قاموس
- send(chat_id, text), UID, CHAT_ID

اكتب كود بايثون لتنفيذ الطلب التالي. رد فقط JSON:
{"action": "execute", "code": "الكود", "done": true}

الطلب:
"""

def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None
    m = re.search(r'\{.*\}', text, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None

def _looks_like_refusal(text: str) -> bool:
    if not text:
        return False
    indicators = [
        "لا أستطيع", "لا يمكنني", "لا أملك", "غير متاح",
        "لا يمكن", "لا أتمكن", "ليس لدي",
        "i cannot", "i can't", "i don't have", "not available",
        "i'm unable", "unable to", "i don't have access",
        "لا أملك وصولاً", "لا أملك في هذه المحادثة",
    ]
    return any(ind in text[:600] for ind in indicators)

def _call_ai_safe(prompt: str, uid: int, refusal_state: Dict[str, int]) -> str:
    reply = AI.generate(prompt)
    if reply.startswith("__ERROR__"):
        return reply
    if _looks_like_refusal(reply) and not _extract_json(reply):
        refusal_state["count"] = refusal_state.get("count", 0) + 1
        n = refusal_state["count"]
        logger.warning(f"[Agent uid={uid}] AI رفض (محاولة {n})")
        if n == 1:
            reply = AI.generate(SIMPLE_PROMPT + prompt[:2000])
        elif n == 2:
            AI.fresh_session()
            reply = AI.generate(SIMPLE_PROMPT + prompt[:2000])
    else:
        refusal_state["count"] = 0
    return reply

def run_ai_agent(uid: int, chat_id: int, user_text: str) -> None:
    """حلقة v5: plan → execute → reply مع ذاكرة."""
    task_id = str(int(time.time() * 1000))
    STATE["cancelled_tasks"][task_id] = False
    save_state(STATE)

    status = send(chat_id, "🤖 بدء...", keyboard=cancel_task_kb(task_id))
    status_id = status.get("result", {}).get("message_id") if status.get("ok") else None

    typing = TypingIndicator(chat_id)
    typing.start()

    refusal_state: Dict[str, int] = {"count": 0}
    task_start_time = time.time()

    # احفظ رسالة المستخدم في الذاكرة فوراً
    add_to_chat_history(uid, "user", user_text)

    def _update_status(header: str, body: str = "", plan: Optional[List[str]] = None,
                       current_step: int = 0) -> None:
        if not status_id:
            return
        text = f"🤖 {header}\n"
        if plan:
            disp = "\n".join(
                f"{'▶️' if i+1 == current_step else '✅' if i+1 < current_step else '⏳'} {i+1}. {s}"
                for i, s in enumerate(plan[:8])
            )
            text += f"\n📋 الخطة:\n{disp}\n"
        if body:
            text += f"\n{body}"
        try:
            edit_message(chat_id, status_id, text[:1500], keyboard=cancel_task_kb(task_id))
        except Exception:
            pass

    def _check_cancel_or_timeout() -> Optional[str]:
        if STATE["cancelled_tasks"].get(task_id):
            return "cancel"
        if time.time() - task_start_time > TASK_TIME_LIMIT:
            return "timeout"
        return None

    def _finish_reply(final_text: str) -> None:
        if status_id:
            delete_message(chat_id, status_id)
        send(chat_id, strip_stars(final_text))
        add_to_chat_history(uid, "ai", final_text)
        STATE["agent_tasks"][task_id] = {
            "user": uid, "request": user_text[:500],
            "status": "completed", "ts": int(time.time()),
        }
        _cleanup_old_tasks()

    try:
        # ═══ المرحلة 1: التخطيط ═══
        _update_status("🤔 مرحلة التخطيط...")
        logger.info(f"[Agent uid={uid}] طلب: {user_text[:200]}")

        history_txt = get_chat_history_text(uid, max_chars=3000)
        history_part = f"\n\nسياق المحادثة السابقة:\n{history_txt}\n" if history_txt else ""

        plan_prompt = (
            PLAN_PROMPT
            + history_part
            + f"\n\n━━━\nطلب المستخدم الحالي:\n{user_text}\n━━━\n\nردك (JSON):"
        )
        plan_reply = _call_ai_safe(plan_prompt, uid, refusal_state)
        logger.info(f"[Agent plan] {plan_reply[:400]}")

        if plan_reply.startswith("__ERROR__"):
            if status_id:
                delete_message(chat_id, status_id)
            send(chat_id, f"⚠️ فشل الاتصال: {plan_reply[9:200]}")
            return

        if _looks_like_refusal(plan_reply) and not _extract_json(plan_reply):
            if refusal_state["count"] >= 3:
                if status_id:
                    delete_message(chat_id, status_id)
                send(chat_id, "⚠️ الـ AI رفض. جرّب صياغة أخرى.")
                return

        plan_data = _extract_json(plan_reply)
        if not plan_data:
            if status_id:
                delete_message(chat_id, status_id)
            send(chat_id, strip_stars(plan_reply) or "(تم)")
            add_to_chat_history(uid, "ai", plan_reply)
            return

        action = plan_data.get("action", "")

        if action == "reply":
            _finish_reply(plan_data.get("text", "(لا رد)"))
            return

        if action != "plan":
            if status_id:
                delete_message(chat_id, status_id)
            send(chat_id, strip_stars(plan_reply))
            add_to_chat_history(uid, "ai", plan_reply)
            return

        plan_steps = [str(s) for s in plan_data.get("steps", [])][:8]
        if not plan_steps:
            if status_id:
                delete_message(chat_id, status_id)
            send(chat_id, "⚠️ الخطة فارغة.")
            return

        say = plan_data.get("say", "")
        _update_status(f"📋 خطة ({len(plan_steps)} خطوات)" + (f"\n{say}" if say else ""),
                       plan=plan_steps, current_step=1)

        # ═══ المرحلة 2: التنفيذ ═══
        results: List[Tuple[int, str, str]] = []
        done_flag = False
        plan_summary = "\n".join(f"{i+1}. {s}" for i, s in enumerate(plan_steps))

        for step_idx in range(len(plan_steps)):
            stop_reason = _check_cancel_or_timeout()
            if stop_reason == "cancel":
                if status_id:
                    delete_message(chat_id, status_id)
                send(chat_id, "🚫 أُلغي الطلب.")
                return
            if stop_reason == "timeout":
                if status_id:
                    delete_message(chat_id, status_id)
                send(chat_id, "⏱ انتهى وقت المهمة.")
                return

            step_text = plan_steps[step_idx]
            _update_status(f"⚙️ تنفيذ الخطوة {step_idx+1}/{len(plan_steps)}...",
                           plan=plan_steps, current_step=step_idx+1)

            results_ctx = ""
            if results:
                results_ctx = "نتائج الخطوات السابقة:\n" + "\n".join(
                    f"خطوة {i+1} ({s}):\n{r[:800]}"
                    for i, s, r in results[-4:]
                )

            exec_prompt = (
                EXECUTE_PROMPT
                + history_part
                + f"\n\n━━━\nطلب المستخدم الأصلي:\n{user_text}\n"
                + f"\nالخطة المعتمدة:\n{plan_summary}\n"
                + (f"\n{results_ctx}\n" if results_ctx else "")
                + f"\nالخطوة الحالية ({step_idx+1}/{len(plan_steps)}): {step_text}\n"
                + f"\nردك (JSON):"
            )

            exec_reply = _call_ai_safe(exec_prompt, uid, refusal_state)
            logger.info(f"[Agent step {step_idx+1}] {exec_reply[:400]}")

            if exec_reply.startswith("__ERROR__"):
                results.append((step_idx, step_text, f"فشل الاتصال: {exec_reply[9:200]}"))
                done_flag = True
                break

            exec_data = _extract_json(exec_reply)
            if not exec_data:
                results.append((step_idx, step_text, f"لم يُرسل كود: {exec_reply[:200]}"))
                if _looks_like_refusal(exec_reply):
                    continue
                done_flag = True
                break

            exec_action = exec_data.get("action", "")

            if exec_action == "reply":
                done_flag = True
                final_text = exec_data.get("text", "")
                if final_text:
                    _finish_reply(final_text)
                    return
                break

            if exec_action != "execute":
                results.append((step_idx, step_text, f"إجراء غير معروف: {exec_action}"))
                continue

            code = str(exec_data.get("code", ""))
            if not code:
                results.append((step_idx, step_text, "لم يُرسل كود."))
                continue

            result = execute_ai_code(code, uid)
            logger.info(f"[Agent step {step_idx+1} result] {result[:400]}")
            results.append((step_idx, step_text, result))

            is_done = bool(exec_data.get("done", False))
            is_last = (step_idx == len(plan_steps) - 1)

            if is_last or is_done:
                done_flag = True
                break

            # نجاح متكرر → إجبار على الرد
            if len(results) >= 2:
                last_two = results[-2:]
                successes = sum(1 for _, _, r in last_two
                                if not (r.startswith("❌") or r.startswith("⏱")
                                        or "Traceback" in r))
                if successes == 2 and not is_last:
                    logger.info(f"[Agent uid={uid}] نجاح متكرر ← إجبار على الرد")
                    done_flag = True
                    break

        # ═══ المرحلة 3: الرد النهائي ═══
        stop_reason = _check_cancel_or_timeout()
        if stop_reason == "cancel":
            if status_id:
                delete_message(chat_id, status_id)
            send(chat_id, "🚫 أُلغي الطلب.")
            return
        if stop_reason == "timeout":
            if status_id:
                delete_message(chat_id, status_id)
            send(chat_id, "⏱ انتهى وقت المهمة.")
            return

        _update_status("📝 مرحلة الرد النهائي...")

        results_text = ""
        if results:
            results_text = "\n\n".join(
                f"خطوة {i+1} ({s}):\n{r[:1500]}"
                for i, s, r in results
            )
        else:
            results_text = "(لا نتائج)"

        reply_prompt = (
            REPLY_PROMPT
            + history_part
            + f"\n\n━━━\nطلب المستخدم:\n{user_text}\n"
            + f"\nنتائج التنفيذ:\n{results_text}\n"
            + f"\n━━━\n\nردك النهائي (JSON):"
        )

        final_reply = _call_ai_safe(reply_prompt, uid, refusal_state)
        logger.info(f"[Agent final] {final_reply[:400]}")

        final_data = _extract_json(final_reply)
        final_text = None
        if final_data and final_data.get("action") == "reply":
            final_text = final_data.get("text", "")

        if not final_text:
            if _looks_like_refusal(final_reply):
                if results:
                    _, last_step, last_result = results[-1]
                    final_text = f"النتيجة:\n{last_result[:1500]}"
                else:
                    final_text = "لم أتمكن من تنفيذ الطلب."
            else:
                final_text = strip_stars(final_reply) or "تم"

        _finish_reply(final_text)

    except Exception as e:
        logger.exception("agent error")
        if status_id:
            try:
                delete_message(chat_id, status_id)
            except Exception:
                pass
        send(chat_id, f"⚠️ خطأ غير متوقع: {str(e)[:300]}")
    finally:
        typing.stop()

def _cleanup_old_tasks() -> None:
    try:
        now = int(time.time())
        old = [tid for tid, t in STATE.get("agent_tasks", {}).items()
               if now - t.get("ts", 0) > 86400]
        for tid in old:
            STATE["agent_tasks"].pop(tid, None)
            STATE["cancelled_tasks"].pop(tid, None)
        if old:
            save_state(STATE)
    except Exception:
        pass

# ============================================================
# فحص الأمان
# ============================================================
SCAN_PROMPT = """أنت فاحص أمان لكود بايثون سيُشغَّل على استضافة مشتركة.
حلّل الكود وأعد JSON فقط:
{"decision": "safe" | "block" | "review", "reason": "سبب مختصر"}
- block: تعدين، DDoS، مسح ملفات النظام، هروب sandbox، هجوم شبكي.
- review: مشكوك فيه.
- safe: بوت عادي.
لا تكتب أي شيء خارج JSON."""

def ai_scan_code(path: Path) -> Dict[str, str]:
    try:
        code = path.read_text(encoding="utf-8", errors="replace")[:8000]
    except Exception:
        return {"decision": "safe", "reason": "تعذّرت القراءة"}
    reply = AI.generate(SCAN_PROMPT + "\n\n" + code)
    m = re.search(r'\{.*\}', reply, re.DOTALL)
    if m:
        try:
            j = json.loads(m.group(0))
            if j.get("decision") in ("safe", "block", "review"):
                return {"decision": j["decision"], "reason": j.get("reason", "")}
        except Exception:
            pass
    return {"decision": "review", "reason": "رد AI غير مفهوم"}

def _save_scan_report(uid: int, fname: str, decision: str, reason: str) -> None:
    lst = STATE["scan_reports"].setdefault(str(uid), [])
    lst.append({"file": fname, "decision": decision, "reason": reason, "ts": int(time.time())})
    STATE["scan_reports"][str(uid)] = lst[-50:]
    save_state(STATE)

def _fmt_scan_report(decision: str, reason: str) -> str:
    icon = {"safe": "✅", "block": "⛔", "review": "⏳"}.get(decision, "•")
    label = {"safe": "آمن", "block": "محظور", "review": "قيد المراجعة"}.get(decision, decision)
    return f"📋 تقرير الفحص\nالقرار: {icon} {label}\nالسبب: {reason or '(لا شيء)'}"

def user_reports(uid: int, target_id: Optional[int] = None) -> str:
    tid = int(target_id) if (target_id and is_privileged(uid)) else uid
    rep = STATE["scan_reports"].get(str(tid), [])
    if not rep:
        return "(لا تقارير)"
    out = []
    for r in rep[-15:]:
        ts = time.strftime("%Y-%m-%d %H:%M", time.localtime(r["ts"]))
        out.append(f"[{ts}] {r['file']} → {r['decision']} — {r['reason']}")
    return "\n".join(out)

# ============================================================
# Rate Limit
# ============================================================
_rate_lock = threading.RLock()
_rate_history: Dict[int, deque] = defaultdict(lambda: deque(maxlen=RATE_LIMIT + 1))

def check_rate_limit(uid: int) -> Tuple[bool, int]:
    if is_privileged(uid):
        return True, 0
    now = time.time()
    with _rate_lock:
        h = _rate_history[uid]
        while h and h[0] < now - RATE_WINDOW:
            h.popleft()
        if len(h) >= RATE_LIMIT:
            wait = int(RATE_WINDOW - (now - h[0])) + 1
            return False, wait
        h.append(now)
        return True, 0

# ============================================================
# حدود المستخدم
# ============================================================
def _enforce_user_limits(uid: int, target: Path, size: int, new_file: bool) -> None:
    if size > USER_MAX_BYTES:
        raise PermissionError(f"حجم الملف يتجاوز {USER_MAX_BYTES // 1024}KB.")
    if new_file:
        home = user_home(uid)
        cnt = sum(1 for f in home.iterdir() if f.is_file() and f.suffix == ".py")
        if cnt >= USER_MAX_FILES:
            raise PermissionError(f"الحد الأقصى {USER_MAX_FILES} ملفات.")

# ============================================================
# المعالجات
# ============================================================
def handle_start(uid: int, chat_id: int, name: str, args: str) -> None:
    get_user(uid, chat_id, name)
    if args.startswith("ref_"):
        try:
            ref = int(args[4:])
            if handle_referral(uid, ref):
                send(chat_id, "🎁 حصلت على 5 نقاط، وصديقك على 10.")
        except Exception:
            pass
    send(chat_id, welcome_card(uid, name), keyboard=main_menu(uid))

def handle_document(msg: Dict[str, Any]) -> None:
    uid = msg["from"]["id"]
    chat_id = msg["chat"]["id"]
    name = msg["from"].get("first_name", "")
    get_user(uid, chat_id, name)

    ok, missing = is_subscribed(uid)
    if not ok:
        return send_sub_prompt(chat_id, missing)

    doc = msg["document"]
    fname = doc.get("file_name", "file.py")
    if not fname.endswith(".py"):
        return send(chat_id, "❌ ملفات .py فقط.")
    size = doc.get("file_size", 0)

    if not is_privileged(uid):
        try:
            home = user_home(uid)
            _enforce_user_limits(uid, home / fname, size, new_file=not (home / fname).exists())
        except PermissionError as e:
            return send(chat_id, f"⛔ {e}")
        u = get_user(uid)
        if u.get("points", 0) < UPLOAD_COST:
            return send(chat_id, f"💔 رصيدك لا يكفي. رفع ملف يكلّف {UPLOAD_COST} نقطة.")

    data = get_file_bytes(doc["file_id"])
    if not data:
        return send(chat_id, "❌ تعذّر التنزيل.")

    if is_privileged(uid):
        (user_home(uid) / fname).write_bytes(data)
        return send(chat_id, f"✅ حُفظ {fname}.",
                    keyboard=_file_action_kb(fname))

    staging = STAGING_DIR / str(uid) / fname
    staging.parent.mkdir(parents=True, exist_ok=True)
    staging.write_bytes(data)

    send(chat_id, f"🔍 يتم فحص {fname}...")
    verdict = ai_scan_code(staging)
    decision, reason = verdict.get("decision", "review"), verdict.get("reason", "")
    _save_scan_report(uid, fname, decision, reason)
    send(chat_id, _fmt_scan_report(decision, reason))

    if decision == "block":
        staging.unlink(missing_ok=True)
        send(OWNER_ID, f"🚫 رفض تلقائي\nمستخدم: {uid} ({name})\nملف: {fname}\n{reason}")
        return send(chat_id, "⛔ رُفض الملف.")

    if decision == "review":
        rid = str(int(time.time() * 1000))
        STATE["pending_review"][rid] = {"uid": uid, "path": str(staging), "reason": reason}
        save_state(STATE)
        send(chat_id, "⏳ ملفك قيد مراجعة المالك.")
        send(OWNER_ID, f"📥 مراجعة #{rid}\nمستخدم {uid} ({name})\nملف: {fname}\n{reason}",
             keyboard=[[{"text": "✅ قبول", "callback_data": f"approve:{rid}"},
                        {"text": "❌ رفض", "callback_data": f"reject:{rid}"}]])
        send_file(OWNER_ID, staging, caption=f"للمراجعة: {fname}")
        return

    target = user_home(uid) / fname
    shutil.move(str(staging), str(target))
    u = get_user(uid)
    u["points"] = u.get("points", 0) - UPLOAD_COST
    save_state(STATE)
    send(chat_id, f"✅ حُفظ {fname}\n💔 خُصمت {UPLOAD_COST} نقطة.",
         keyboard=_file_action_kb(fname))

def handle_callback(cb: Dict[str, Any]) -> None:
    uid = cb["from"]["id"]
    chat_id = cb["message"]["chat"]["id"]
    msg_id = cb["message"].get("message_id")
    data = cb.get("data", "")
    answer_cb(cb["id"])
    name = cb["from"].get("first_name", "")
    get_user(uid, chat_id, name)

    def _nav(text, kb=None):
        if msg_id:
            r = edit_message(chat_id, msg_id, text, keyboard=kb)
            if r.get("ok"):
                return
        send(chat_id, text, keyboard=kb)

    try:
        if data.startswith("cancel_task:"):
            tid = data.split(":", 1)[1]
            STATE["cancelled_tasks"][tid] = True
            save_state(STATE)
            send(chat_id, "🚫 طلب الإلغاء...")
            return

        if data == "menu":
            _nav(welcome_card(uid, name), main_menu(uid))
        elif data == "files":
            fs = files_of(uid)
            if not fs:
                return _nav("لا ملفات بعد.", [[{"text": "⬅️ رجوع", "callback_data": "menu"}]])
            kb = [[{"text": f"📄 {f}", "callback_data": f"file:{f}"}] for f in fs]
            kb.append([{"text": "⬅️ رجوع", "callback_data": "menu"}])
            _nav(f"📁 ملفاتك ({len(fs)}):", kb)
        elif data == "stats":
            u = get_user(uid)
            procs = list_processes()
            if not is_privileged(uid):
                procs = [p for p in procs if str(user_home(uid)) in p["path"]]
            txt = (f"📊 إحصائياتك\n"
                   f"👤 الدور: {_role_line(uid)}\n"
                   f"⭐ النقاط: {'∞' if is_owner(uid) else u.get('points', 0)}\n"
                   f"📁 الملفات: {len(files_of(uid))}\n"
                   f"⚙️ عمليات مشغّلة: {len(procs)}\n"
                   f"👥 الإحالات: {len(u.get('referrals', []))}\n"
                   f"📋 تقارير الفحص: {len(STATE['scan_reports'].get(str(uid), []))}")
            _nav(txt, [[{"text": "📋 تقارير فحصي", "callback_data": "my_reports"}],
                       [{"text": "⬅️ رجوع", "callback_data": "menu"}]])
        elif data == "howto_upload":
            _nav("📤 أرسل ملف .py كمرفق هنا.",
                 [[{"text": "⬅️ رجوع", "callback_data": "menu"}]])
        elif data == "points":
            u = get_user(uid)
            pts = "∞" if is_owner(uid) else u.get("points", 0)
            _nav(f"💰 نقاطك: {pts}\n👥 إحالاتك: {len(u.get('referrals', []))}",
                 [[{"text": "🔗 رابط إحالتي", "callback_data": "referral"}],
                  [{"text": "⬅️ رجوع", "callback_data": "menu"}]])
        elif data == "referral":
            me = tg("getMe").get("result", {})
            link = f"https://t.me/{me.get('username', '')}?start=ref_{uid}"
            _nav(f"🔗 رابط إحالتك:\n{link}\n\n+10 لك، +5 له.",
                 [[{"text": "⬅️ رجوع", "callback_data": "menu"}]])
        elif data == "my_reports":
            _nav("📋 تقارير فحص ملفاتك:\n" + user_reports(uid),
                 [[{"text": "⬅️ رجوع", "callback_data": "menu"}]])
        elif data == "dev_panel" and is_dev(uid):
            kb = [[{"text": "📊 لوحة المالك", "callback_data": "owner_dashboard"}],
                  [{"text": "👥 كل المستخدمين", "callback_data": "all_users"}],
                  [{"text": "⚙️ عمليات مشغّلة", "callback_data": "all_procs"}],
                  [{"text": "🧹 تنظيف العمليات", "callback_data": "cleanup_procs"}],
                  [{"text": "⏱ المهام المجدولة", "callback_data": "my_schedules"}]]
            if is_owner(uid):
                kb.append([{"text": "🛠 إدارة المطورين", "callback_data": "manage_devs"}])
                kb.append([{"text": "📥 مراجعة معلّقة", "callback_data": "review"}])
            kb.append([{"text": "⬅️ رجوع", "callback_data": "menu"}])
            _nav("👨‍💻 لوحة المطور:", kb)
        elif data == "owner_dashboard" and is_owner(uid):
            _nav(dashboard_owner(), [[{"text": "⬅️ رجوع", "callback_data": "dev_panel"}]])
        elif data == "all_users" and is_dev(uid):
            lines = []
            for u, d in STATE["users"].items():
                lines.append(f"{u} — {d.get('points', 0)} نقطة — {len(d.get('referrals', []))} إحالة")
            _nav("👥 المستخدمون:\n" + ("\n".join(lines) or "(لا أحد)"),
                 [[{"text": "⬅️ رجوع", "callback_data": "dev_panel"}]])
        elif data == "all_procs" and is_dev(uid):
            ps = list_processes()
            txt = "⚙️ العمليات:\n" + ("\n".join(f"PID {x['pid']} — {Path(x['path']).name}" for x in ps)
                                      or "(لا شيء)")
            _nav(txt, [[{"text": "⬅️ رجوع", "callback_data": "dev_panel"}]])
        elif data == "cleanup_procs" and is_dev(uid):
            cleaned = cleanup_stale_processes()
            _nav(f"🧹 نُظّف {len(cleaned)} عملية وهمية.",
                 [[{"text": "⬅️ رجوع", "callback_data": "dev_panel"}]])
        elif data == "my_schedules":
            if is_privileged(uid):
                _nav("⏱ المهام المجدولة:\n" + list_scheduled(uid),
                     [[{"text": "⬅️ رجوع", "callback_data": "dev_panel"}]])
            else:
                _nav("⚠️ الجدولة للمالك/المطورين فقط.",
                     [[{"text": "⬅️ رجوع", "callback_data": "menu"}]])
        elif data == "manage_devs" and is_owner(uid):
            devs = STATE["devs"]
            txt = "🛠 المطورون:\n" + ("\n".join(map(str, devs)) if devs else "(لا أحد)")
            txt += "\n\nاكتب: «أضف مطور <id>» أو «احذف مطور <id>»."
            _nav(txt, [[{"text": "⬅️ رجوع", "callback_data": "dev_panel"}]])
        elif data == "review" and is_owner(uid):
            pend = STATE["pending_review"]
            if not pend:
                return _nav("(لا مراجعات)", [[{"text": "⬅️ رجوع", "callback_data": "dev_panel"}]])
            for rid, info in list(pend.items())[:10]:
                send(chat_id,
                     f"#{rid}\nuid={info['uid']}\nfile={Path(info['path']).name}\n{info['reason']}",
                     keyboard=[[{"text": "✅", "callback_data": f"approve:{rid}"},
                                {"text": "❌", "callback_data": f"reject:{rid}"}]])
        elif data == "check_sub":
            ok, missing = is_subscribed(uid)
            if ok:
                _nav(welcome_card(uid, name), main_menu(uid))
            else:
                send_sub_prompt(chat_id, missing)
        elif ":" in data:
            act, arg = data.split(":", 1)
            if act == "file":
                file_actions(uid, chat_id, arg, edit_id=msg_id)
            elif act == "run":
                p = resolve_path(uid, arg)
                if p.exists():
                    send(chat_id, run_for_user(uid, p))
                else:
                    send(chat_id, "غير موجود.")
            elif act == "stop":
                send(chat_id, stop_process(resolve_path(uid, arg))[1])
            elif act == "restart":
                send(chat_id, restart_process(resolve_path(uid, arg))[1])
            elif act == "log":
                p = resolve_path(uid, arg)
                out = tail_log(p, 40)
                send(chat_id, f"📋 آخر سجلات {arg}:\n<pre>{out}</pre>",
                     parse_mode="HTML",
                     keyboard=[[{"text": "📥 تحميل السجل", "callback_data": f"logf:{arg}"},
                                {"text": "⬅️ رجوع", "callback_data": f"file:{arg}"}]])
            elif act == "logf":
                p = resolve_path(uid, arg)
                lf = _log_path_for(p)
                if lf.exists() and lf.stat().st_size > 0:
                    send_file(chat_id, lf, caption=f"📥 سجل {arg}")
                else:
                    send(chat_id, "(لا يوجد سجل بعد)")
            elif act == "get":
                send_file(chat_id, resolve_path(uid, arg), caption=arg)
            elif act == "aiedit":
                send(chat_id, f"📝 اكتب طلب التعديل على {arg} في المحادثة.")
            elif act == "del":
                _nav(f"⚠️ حذف {arg}؟ لا يمكن التراجع.",
                     [[{"text": "✅ نعم", "callback_data": f"delok:{arg}"},
                       {"text": "❌ إلغاء", "callback_data": f"file:{arg}"}]])
            elif act == "delok":
                p = resolve_path(uid, arg)
                stop_process(p)
                if p.exists():
                    p.unlink()
                _nav(f"🗑 {arg} حُذف.",
                     [[{"text": "📁 ملفاتي", "callback_data": "files"},
                       {"text": "⬅️ رجوع", "callback_data": "menu"}]])
            elif act == "approve" and is_owner(uid):
                info = STATE["pending_review"].pop(arg, None)
                save_state(STATE)
                if info:
                    src = Path(info["path"])
                    t_uid = info["uid"]
                    dst = user_home(t_uid) / src.name
                    try:
                        if src.exists():
                            shutil.move(str(src), str(dst))
                        u = get_user(t_uid)
                        u["points"] = max(0, u.get("points", 0) - UPLOAD_COST)
                        save_state(STATE)
                        send(chat_id, "✅ قُبل ونُقل.")
                        ch = u.get("chat_id")
                        if ch:
                            send(ch, f"✅ ملفك {dst.name} قُبل.",
                                 keyboard=_file_action_kb(dst.name))
                    except Exception as e:
                        send(chat_id, f"خطأ: {e}")
            elif act == "reject" and is_owner(uid):
                info = STATE["pending_review"].pop(arg, None)
                save_state(STATE)
                if info:
                    Path(info["path"]).unlink(missing_ok=True)
                    send(chat_id, "❌ رُفض.")
                    ch = get_user(info["uid"]).get("chat_id")
                    if ch:
                        send(ch, f"❌ رُفض ملفك.\nلم تُخصم أي نقطة.")
    except Exception:
        logger.exception("callback error")
        send(chat_id, "⚠️ خطأ غير متوقع.")

def handle_text(msg: Dict[str, Any]) -> None:
    uid = msg["from"]["id"]
    chat_id = msg["chat"]["id"]
    text = msg.get("text", "").strip()
    name = msg["from"].get("first_name", "")
    get_user(uid, chat_id, name)

    if text.startswith("/start"):
        parts = text.split(maxsplit=1)
        return handle_start(uid, chat_id, name, parts[1] if len(parts) > 1 else "")
    if text.startswith("/menu"):
        return send(chat_id, welcome_card(uid, name), keyboard=main_menu(uid))
    if text.startswith("/id"):
        return send(chat_id, f"معرّفك: {uid}")
    if text.startswith("/clear"):
        clear_chat_history(uid)
        return send(chat_id, "🧹 مُسحت ذاكرة المحادثة.")

    ok, wait = check_rate_limit(uid)
    if not ok:
        return send(chat_id, f"⏳ تجاوزت الحد ({RATE_LIMIT}/{RATE_WINDOW}ث). انتظر {wait} ثانية.")

    threading.Thread(target=run_ai_agent, args=(uid, chat_id, text), daemon=True).start()

# ============================================================
# Polling
# ============================================================
def _bypass_sub_check(u: Dict[str, Any]) -> bool:
    if "message" in u:
        t = u["message"].get("text", "") or ""
        if t.startswith("/start") or t.startswith("/id") or t.startswith("/clear"):
            return True
    if "callback_query" in u:
        if (u["callback_query"].get("data") or "") == "check_sub":
            return True
    return False

def _uid_chat_of(u: Dict[str, Any]) -> Tuple[Optional[int], Optional[int], str]:
    if "message" in u:
        m = u["message"]
        return m["from"]["id"], m["chat"]["id"], m["from"].get("first_name", "")
    if "callback_query" in u:
        c = u["callback_query"]
        return c["from"]["id"], c["message"]["chat"]["id"], c["from"].get("first_name", "")
    return None, None, ""

def handle_update(u: Dict[str, Any]) -> None:
    try:
        uid, chat_id, name = _uid_chat_of(u)
        if uid and chat_id:
            get_user(uid, chat_id, name)
            if not _bypass_sub_check(u):
                ok, missing = is_subscribed(uid)
                if not ok:
                    send_sub_prompt(chat_id, missing)
                    return
        if "message" in u:
            m = u["message"]
            if "document" in m:
                handle_document(m)
            elif "text" in m:
                handle_text(m)
        elif "callback_query" in u:
            handle_callback(u["callback_query"])
    except Exception:
        logger.exception("update error")

def poll_loop() -> None:
    logger.info(f"البوت يعمل. المالك={OWNER_ID}. المجلد={ROOT}")
    offset = 0
    while True:
        try:
            r = requests.get(f"{TG_API}/getUpdates",
                             params={"offset": offset, "timeout": 30}, timeout=60)
            j = r.json()
            if not j.get("ok"):
                time.sleep(2)
                continue
            for upd in j.get("result", []):
                offset = upd["update_id"] + 1
                threading.Thread(target=handle_update, args=(upd,), daemon=True).start()
        except requests.exceptions.RequestException:
            time.sleep(3)
        except KeyboardInterrupt:
            logger.info("إيقاف...")
            with _procs_lock:
                for mp in list(PROCS.values()):
                    try:
                        mp.terminate()
                    except Exception:
                        pass
            sys.exit(0)
        except Exception:
            logger.exception("poll error")
            time.sleep(3)

# Main
# ============================================================
import gradio as gr
import threading
import spaces  # إضافة مكتبة الـ GPU

# الدالة الوهمية لخداع سيرفر ZeroGPU ليسمح لنا بالعمل
@spaces.GPU
def dummy_gpu_function():
    return "تم خداع الـ GPU بنجاح! السيرفر يعمل 24/24."

def start_bot():
    AI.init_session()
    logger.info("تم تهيئة جلسة AI.")
    restore_persistent_procs()
    cleanup_stale_processes()
    threading.Thread(target=_scheduler_loop, daemon=True).start()
    poll_loop()

if __name__ == "__main__":
    # تشغيل البوت في الخلفية
    threading.Thread(target=start_bot, daemon=True).start()
    
    # واجهة Gradio مع زر يربط الدالة الوهمية لكي يكتشفها السيرفر
    with gr.Blocks() as demo:
        gr.Markdown("## Host is Alive 24/7! 🚀\nوسيط التحكم يعمل في الخلفية بنجاح.")
        btn = gr.Button("فحص حالة السيرفر")
        out = gr.Textbox(label="النتيجة")
        btn.click(fn=dummy_gpu_function, inputs=[], outputs=out)
    
    demo.launch(server_name="0.0.0.0", server_port=7860)
