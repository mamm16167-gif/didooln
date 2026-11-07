# -*- coding: utf-8 -*-
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from curl_cffi import requests  # 🎯 المكتبة الجديدة
import json, urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TOKEN = "7776492585:AAGxdB_8makFSF561lHyrZTgbS4pKh8FB5o"
bot = telebot.TeleBot(TOKEN)

MOBILIS_BASE = "https://mcare.mobilis.dz"
user_data = {}

def get_headers(token=None):
    h = {
        "user-agent": "Dart/3.12 (dart:io)",
        "x-device-model": "RMX3830",
        "x-os-version": "15",
        "accept-language": "ar",
        "accept-encoding": "gzip",
        "content-type": "application/json",
        "x-app-version": "1.0.1+11",
        "x-device-manufacturer": "realme",
        "x-platform": "android",
    }
    if token:
        h["authorization"] = f"Bearer {token}"
    return h

def safe_json(response):
    if response.status_code != 200:
        return None
    if "application/json" not in response.headers.get("Content-Type", ""):
        return None
    try:
        return response.json()
    except:
        return None

def mobilis_send_otp(msisdn, session):
    url = f"{MOBILIS_BASE}/api/account/v1/auth/login/otp/send"
    payload = {"msisdn": msisdn} 
    headers = get_headers()
    
    # 🎯 نجربو 3 بصمات مختلفة (Safari iOS, Chrome Android, Safari Desktop)
    for impersonate in ["safari_ios", "chrome_android", "safari15_5"]:
        try:
            print(f"[TRY] Impersonate: {impersonate}")
            r = session.post(url, json=payload, headers=headers, impersonate=impersonate, timeout=15)
            data = safe_json(r)
            if data and data.get("success"):
                print(f"[SUCCESS] WAF bypassed with: {impersonate}")
                return True
            else:
                print(f"[FAIL] {impersonate} | Status: {r.status_code} | {r.text[:100]}")
        except Exception as e:
            print(f"[ERROR] {impersonate}: {e}")
    
    return False

def mobilis_verify_otp(msisdn, otp, session):
    url = f"{MOBILIS_BASE}/api/account/v1/auth/login/otp/verify"
    payload = {"msisdn": msisdn, "otp": otp}
    headers = get_headers()
    
    try:
        r = session.post(url, json=payload, headers=headers, impersonate="safari_ios", timeout=15)
        data = safe_json(r)
        if data and data.get("success"):
            auth_header = r.headers.get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                return auth_header.replace("Bearer ", "").strip()
        return None
    except Exception as e:
        print(f"Error verify_otp: {e}")
        return None

def mobilis_get_balance(token):
    url = f"{MOBILIS_BASE}/api/account/v1/balance"
    headers = get_headers(token)
    try:
        r = requests.get(url, headers=headers, impersonate="safari_ios", timeout=15)
        return safe_json(r)
    except: return None

# ═══════════════════════════ أوامر البوت ═══════════════════════════
@bot.message_handler(commands=['start'])
def start(message):
    user_data[message.chat.id] = {"step": "phone"}
    bot.send_message(message.chat.id, "📱 مرحباً بك.\n\nأرسل رقمك (يبدأ بـ 05 أو 06):")

@bot.message_handler(func=lambda m: user_data.get(m.chat.id, {}).get("step") == "phone")
def handle_phone(message):
    text = message.text.strip()
    if not text.isdigit() or len(text) < 10 or not text.startswith(("05", "06")):
        bot.send_message(message.chat.id, "❌ رقم غير صحيح.")
        return
    
    msisdn = "213" + text[1:]
    session = requests.Session()
    user_data[message.chat.id] = {"step": "otp", "msisdn": msisdn, "session": session}
    
    msg = bot.send_message(message.chat.id, "⏳ جاري إرسال الرمز...")
    if mobilis_send_otp(msisdn, session):
        bot.edit_message_text("✅ تم إرسال الرمز. أدخل OTP:", message.chat.id, msg.message_id)
    else:
        bot.edit_message_text("❌ فشل الإرسال (WAF). تحقق من الكونسول.", message.chat.id, msg.message_id)

@bot.message_handler(func=lambda m: user_data.get(m.chat.id, {}).get("step") == "otp")
def handle_otp(message):
    otp = message.text.strip()
    if not otp.isdigit() or len(otp) != 6:
        bot.send_message(message.chat.id, "❌ 6 أرقام فقط.")
        return
    
    data = user_data[message.chat.id]
    msg = bot.send_message(message.chat.id, "⏳ جاري التحقق...")
    
    token = mobilis_verify_otp(data["msisdn"], otp, data["session"])
    if token:
        user_data[message.chat.id]["token"] = token
        user_data[message.chat.id]["step"] = "menu"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("💰 فحص الرصيد", callback_data="check_balance"))
        bot.edit_message_text("✅ تم الدخول! اختر:", message.chat.id, msg.message_id, reply_markup=markup)
    else:
        bot.edit_message_text("❌ الرمز خاطئ أو فشل التحقق.", message.chat.id, msg.message_id)

@bot.callback_query_handler(func=lambda call: call.data == "check_balance")
def cb_balance(call):
    data = user_data.get(call.message.chat.id)
    if not data or "token" not in data: return bot.answer_callback_query(call.id, "❌ أرسل /start")
    
    bot.answer_callback_query(call.id, "⏳ جاري الجلب...")
    res = mobilis_get_balance(data["token"])
    
    if res and res.get("success"):
        d = res.get("data", {})
        bot.send_message(call.message.chat.id, f"💰 <b>الرصيد:</b> <code>{d.get('balance', '0.00')}</code> دج", parse_mode='HTML')
    else:
        bot.send_message(call.message.chat.id, "❌ فشل جلب الرصيد.")

if __name__ == "__main__":
    print("🚀 Mobilis Bot (curl_cffi WAF Bypass)")
    bot.infinity_polling(skip_pending=True)
