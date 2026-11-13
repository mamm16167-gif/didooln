import telebot
import os
import subprocess
import sys
import time
import threading
import psutil
import zipfile
import shutil
import json
import requests
from telebot import types
import signal
import hashlib
import secrets
from datetime import datetime, timedelta

# ==================== الإعدادات الأساسية ====================
BOT_TOKEN = "7584028388:AAFtZGYWWtImarQPI6eLJX7h1jyw_YhFqg0"
OWNER_ID = 7376168639
MAIN_PASSWORD = "@kjhhvbhgddsdojh"
REFERRAL_POINTS = 2  # نقاط لكل دعوة

bot = telebot.TeleBot(BOT_TOKEN)
authorized_users = []
bot_processes = {}
bot_folders = {}
uploaded_files = {}
login_attempts = {}
referral_system = {}  # نظام الإحالة
user_points = {}  # نقاط المستخدمين
referral_links = {}  # روابط الإحالة
bot_active = True  # حالة البوت الرئيسي (شغال أو موقوف)
owner_notified = False  # للتأكد من إرسال إشعار واحد فقط

# ==================== إنشاء المجلدات ====================
BOTS_DIR = "uploaded_bots"
UPLOADS_DIR = "uploads"
EXTRACTED_DIR = "extracted"
DATA_FILE = "bot_data.json"
REFERRAL_FILE = "referral_data.json"

for directory in [BOTS_DIR, UPLOADS_DIR, EXTRACTED_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

# ==================== دوال تحميل وحفظ البيانات ====================
def load_data():
    """تحميل جميع البيانات"""
    data = {
        "authorized_users": [],
        "uploaded_files": {},
        "main_password": MAIN_PASSWORD,
        "user_points": {},
        "referral_system": {},
        "referral_links": {}
    }
    
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
                data.update(loaded_data)
        except:
            pass
    
    return data

def save_data():
    """حفظ جميع البيانات"""
    data = {
        "authorized_users": authorized_users,
        "uploaded_files": uploaded_files,
        "main_password": MAIN_PASSWORD,
        "user_points": user_points,
        "referral_system": referral_system,
        "referral_links": referral_links
    }
    
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_referral_data():
    """تحميل بيانات الإحالة"""
    if os.path.exists(REFERRAL_FILE):
        try:
            with open(REFERRAL_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_referral_data():
    """حفظ بيانات الإحالة"""
    data = {
        "referral_system": referral_system,
        "user_points": user_points,
        "referral_links": referral_links
    }
    with open(REFERRAL_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# تحميل البيانات عند بدء التشغيل
data = load_data()
authorized_users = data.get("authorized_users", [])
uploaded_files = data.get("uploaded_files", {})
MAIN_PASSWORD = data.get("main_password", MAIN_PASSWORD)
user_points = data.get("user_points", {})
referral_system = data.get("referral_system", {})
referral_links = data.get("referral_links", {})

# ==================== دوال التحقق من صلاحية البوت ====================
def is_bot_active():
    """التحقق مما إذا كان البوت شغال"""
    return bot_active

def bot_active_only(func):
    """ديكوريتور للتحقق من أن البوت شغال قبل تنفيذ أي أمر"""
    def wrapper(message):
        if not is_bot_active() and message.chat.id != OWNER_ID:
            bot.send_message(message.chat.id, 
                           "⚠️ **البوت متوقف حالياً**\n"
                           "يرجى المحاولة لاحقاً أو التواصل مع المالك.",
                           parse_mode="Markdown")
            return
        return func(message)
    return wrapper

def owner_only(func):
    """ديكوريتور للتأكد أن المستخدم هو المالك"""
    def wrapper(message):
        if message.chat.id != OWNER_ID:
            bot.send_message(message.chat.id, "❌ هذه الميزة متاحة للمالك فقط", parse_mode="Markdown")
            return
        return func(message)
    return wrapper

# ==================== نظام الإحالة ====================
def generate_referral_code(user_id):
    """توليد كود إحالة فريد"""
    unique_string = f"{user_id}_{secrets.token_hex(8)}"
    return hashlib.md5(unique_string.encode()).hexdigest()[:10]

def create_referral_link(user_id):
    """إنشاء رابط إحالة للمستخدم"""
    if str(user_id) not in referral_links:
        code = generate_referral_code(user_id)
        referral_links[str(user_id)] = {
            'code': code,
            'created_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'clicks': 0,
            'successful_referrals': 0
        }
        save_referral_data()
        save_data()
    
    return f"https://t.me/{bot.get_me().username}?start=ref_{referral_links[str(user_id)]['code']}"

def process_referral(code, new_user_id):
    """معالجة دخول مستخدم جديد عبر رابط إحالة"""
    for inviter_id, data in referral_links.items():
        if data['code'] == code:
            # تسجيل الإحالة
            inviter_id = int(inviter_id)
            
            # تحديث إحصائيات المُحيل
            referral_links[str(inviter_id)]['clicks'] += 1
            referral_links[str(inviter_id)]['successful_referrals'] += 1
            
            # إضافة نقاط للمُحيل
            if inviter_id not in user_points:
                user_points[inviter_id] = 0
            user_points[inviter_id] += REFERRAL_POINTS
            
            # تسجيل في نظام الإحالة
            if inviter_id not in referral_system:
                referral_system[inviter_id] = []
            referral_system[inviter_id].append({
                'user_id': new_user_id,
                'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'points_earned': REFERRAL_POINTS
            })
            
            save_referral_data()
            save_data()
            
            # إشعار المُحيل
            try:
                bot.send_message(inviter_id,
                               f"🎉 **مبروك! تم تسجيل مستخدم جديد عبر رابطك!**\n\n"
                               f"👤 المستخدم الجديد: `{new_user_id}`\n"
                               f"⭐ نقاط مكتسبة: +{REFERRAL_POINTS}\n"
                               f"💰 إجمالي نقاطك: {user_points[inviter_id]}\n\n"
                               f"استمر في دعوة أصدقائك لكسب المزيد!",
                               parse_mode="Markdown")
            except:
                pass
            
            return inviter_id
    return None

# ==================== دوال القوائم ====================
def get_main_menu():
    """القائمة الرئيسية للمستخدمين العاديين"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("📤 رفع ملف جديد"), types.KeyboardButton("📋 الملفات المرفوعة"))
    markup.row(types.KeyboardButton("🚀 تشغيل ملف"), types.KeyboardButton("⏹️ إيقاف تشغيل"))
    markup.row(types.KeyboardButton("🔄 إعادة تشغيل"), types.KeyboardButton("🗑️ حذف ملف"))
    markup.row(types.KeyboardButton("📊 سرعة البوت"), types.KeyboardButton("📞 التواصل مع المالك"))
    markup.row(types.KeyboardButton("📊 حالة السيرفر"), types.KeyboardButton("🔗 نظام الإحالة"))
    markup.row(types.KeyboardButton("💰 نقاطي"), types.KeyboardButton("🚪 تسجيل الخروج"))
    return markup

def get_owner_menu():
    """القائمة الخاصة بالمالك"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("📤 رفع ملف جديد"), types.KeyboardButton("📋 الملفات المرفوعة"))
    markup.row(types.KeyboardButton("🚀 تشغيل ملف"), types.KeyboardButton("⏹️ إيقاف تشغيل"))
    markup.row(types.KeyboardButton("🔄 إعادة تشغيل"), types.KeyboardButton("🗑️ حذف ملف"))
    markup.row(types.KeyboardButton("📊 سرعة البوت"), types.KeyboardButton("📞 التواصل مع المالك"))
    markup.row(types.KeyboardButton("📊 حالة السيرفر"), types.KeyboardButton("🔗 نظام الإحالة"))
    markup.row(types.KeyboardButton("💰 نقاطي"), types.KeyboardButton("⚙️ لوحة التحكم"))
    markup.row(types.KeyboardButton("🚪 تسجيل الخروج"))
    return markup

def get_login_menu():
    """قائمة تسجيل الدخول"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🔐 تسجيل الدخول"))
    return markup

def get_admin_commands_menu():
    """قائمة الأوامر السرية للمالك"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🔑 تغيير كلمة المرور", callback_data="admin_change_password"),
        types.InlineKeyboardButton("👥 إدارة المستخدمين", callback_data="admin_manage_users"),
        types.InlineKeyboardButton("📊 إحصائيات متقدمة", callback_data="admin_stats"),
        types.InlineKeyboardButton("📢 إرسال رسالة للمستخدمين", callback_data="admin_broadcast"),
        types.InlineKeyboardButton("🎁 إدارة نقاط المستخدمين", callback_data="admin_manage_points"),
        types.InlineKeyboardButton("🔗 إحصائيات الإحالة", callback_data="admin_referral_stats"),
        types.InlineKeyboardButton("🤖 التحكم بالبوت الرئيسي", callback_data="admin_bot_control"),
        types.InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data="admin_back")
    )
    return markup

def get_bot_control_menu():
    """قائمة التحكم بالبوت الرئيسي"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✅ تشغيل البوت", callback_data="bot_start"),
        types.InlineKeyboardButton("⛔ إيقاف البوت", callback_data="bot_stop"),
        types.InlineKeyboardButton("🔄 إعادة تشغيل البوت", callback_data="bot_restart"),
        types.InlineKeyboardButton("📊 حالة البوت", callback_data="bot_status"),
        types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_back_to_commands")
    )
    return markup

def get_welcome_message(is_owner=False):
    """رسالة الترحيب"""
    if is_owner:
        return """👋 **مرحباً بك يا مالك البوت!**

📤 **جميع الميزات متاحة لك:**
• رفع ملفات بايثون وتشغيلها
• رفع ملفات مضغوطة وفك ضغطها
• تشغيل عدة بوتات في نفس الوقت
• قياس سرعة البوت والاستجابة
• التواصل المباشر مع المالك
• **لوحة تحكم المالك (مخفية عن المستخدمين)**
• إشعارات عند دخول مستخدمين جدد
• **التحكم بالبوت الرئيسي (تشغيل/إيقاف)**
• **إرسال رسائل للمستخدمين**
• **إرسال نقاط للمستخدمين**

🔧 استخدم الأزرار أدناه للتحكم:"""
    else:
        return """👋 **مرحباً بك في بوت الاستضافة الذكي!**

📤 **الميزات المتاحة لك:**
• رفع ملفات بايثون وتشغيلها
• رفع ملفات مضغوطة وفك ضغطها
• تشغيل عدة بوتات في نفس الوقت
• قياس سرعة البوت والاستجابة
• التواصل المباشر مع المالك
• **نظام الإحالة: اكسب النقاط بدعوة أصدقائك**

🔧 استخدم الأزرار أدناه للتحكم:"""

# ==================== دوال قياس السرعة ====================
def measure_speed():
    """قياس سرعة الاتصال والاستجابة"""
    start_time = time.time()
    try:
        response = requests.get("https://api.telegram.org", timeout=5)
        telegram_time = (time.time() - start_time) * 1000
        
        cpu_start = time.time()
        for i in range(1000000):
            pass
        cpu_time = (time.time() - cpu_start) * 1000
        
        return {
            'telegram': telegram_time,
            'cpu': cpu_time,
            'total': telegram_time + cpu_time
        }
    except:
        return None

# ==================== دوال المالك (يجب تعريفها قبل استخدامها) ====================
def change_password_secret(call):
    """تغيير كلمة المرور"""
    msg = bot.send_message(call.message.chat.id,
                          "🔑 **تغيير كلمة المرور**\n\n"
                          "الرجاء إدخال كلمة المرور الجديدة:\n"
                          "📌 يجب أن تكون 6 أحرف على الأقل\n\n"
                          "💡 **ملاحظة:** هذه الميزة سرية ولا تظهر للمستخدمين",
                          parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_password_change)

def process_password_change(message):
    global MAIN_PASSWORD
    
    if message.chat.id != OWNER_ID:
        return
    
    new_password = message.text
    
    if len(new_password) < 6:
        bot.send_message(message.chat.id, 
                        "❌ **كلمة المرور يجب أن تكون 6 أحرف على الأقل**\n"
                        "الرجاء المحاولة مرة أخرى من لوحة التحكم.", 
                        reply_markup=get_owner_menu(),
                        parse_mode="Markdown")
        return
    
    old_password = MAIN_PASSWORD
    MAIN_PASSWORD = new_password
    save_data()
    
    bot.send_message(message.chat.id,
                    f"✅ **تم تغيير كلمة المرور بنجاح!**\n\n"
                    f"🔑 **كلمة المرور القديمة:** `{old_password}`\n"
                    f"🔑 **كلمة المرور الجديدة:** `{new_password}`\n\n"
                    f"⚠️ **يرجى حفظ كلمة المرور الجديدة في مكان آمن**",
                    reply_markup=get_owner_menu(),
                    parse_mode="Markdown")

def manage_users_secret(call):
    """إدارة المستخدمين"""
    if not authorized_users:
        bot.edit_message_text("📭 **لا يوجد مستخدمين مسجلين حالياً**",
                            call.message.chat.id, call.message.message_id,
                            reply_markup=get_admin_commands_menu(), parse_mode="Markdown")
        return
    
    users_text = "👥 **قائمة المستخدمين المسجلين:**\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for i, user_id in enumerate(authorized_users, 1):
        points = user_points.get(user_id, 0)
        users_text += f"{i}. `{user_id}` (نقاط: {points})\n"
        markup.add(types.InlineKeyboardButton(
            f"❌ حذف المستخدم {i}", 
            callback_data=f"remove_user_{user_id}"
        ))
    
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_back_to_commands"))
    
    bot.edit_message_text(users_text, call.message.chat.id, call.message.message_id,
                         reply_markup=markup, parse_mode="Markdown")

def stats_secret(call):
    """إحصائيات متقدمة"""
    cpu = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    total_referrals = sum(len(refs) for refs in referral_system.values())
    total_points = sum(user_points.values())
    
    stats_text = f"""📊 **إحصائيات متقدمة:**

🤖 **حالة البوت الرئيسي:**
• الحالة: {"🟢 شغال" if bot_active else "🔴 متوقف"}

👥 **المستخدمين:**
• المسجلين: {len(authorized_users)}
• المالك: `{OWNER_ID}`
• نقاط المستخدمين: {total_points}
• إجمالي الإحالات: {total_referrals}

📁 **الملفات:**
• إجمالي الملفات: {len(uploaded_files)}
• العمليات العاملة: {len(bot_processes)}

🔐 **الأمان:**
• كلمة المرور الحالية: `{MAIN_PASSWORD}`
• محاولات الدخول الفاشلة: {len(login_attempts)}

💻 **النظام:**
• CPU: {cpu}%
• RAM: {memory.percent}%
• DISK: {disk.percent}%

📂 **المجلدات:**
• uploads: {os.path.exists(UPLOADS_DIR)}
• extracted: {os.path.exists(EXTRACTED_DIR)}
• uploaded_bots: {os.path.exists(BOTS_DIR)}

⏰ **الوقت:**
• {time.strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    bot.edit_message_text(stats_text, call.message.chat.id, call.message.message_id,
                         reply_markup=get_admin_commands_menu(), parse_mode="Markdown")

def broadcast_message(call):
    """إرسال رسالة لجميع المستخدمين"""
    if not authorized_users:
        bot.send_message(call.message.chat.id,
                        "📭 **لا يوجد مستخدمين مسجلين لإرسال الرسالة لهم**",
                        reply_markup=get_admin_commands_menu(),
                        parse_mode="Markdown")
        return
    
    msg = bot.send_message(call.message.chat.id,
                          "📢 **إرسال رسالة للمستخدمين**\n\n"
                          f"👥 عدد المستخدمين المستهدفين: {len(authorized_users)}\n\n"
                          "الرجاء إرسال الرسالة التي تريد نشرها لجميع المستخدمين:",
                          parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_broadcast)

def process_broadcast(message):
    """معالجة إرسال الرسالة للمستخدمين"""
    if message.chat.id != OWNER_ID:
        return
    
    broadcast_text = message.text
    success_count = 0
    fail_count = 0
    
    status_msg = bot.send_message(message.chat.id,
                                 "📤 **جاري إرسال الرسالة للمستخدمين...**\n"
                                 f"👥 العدد: {len(authorized_users)}",
                                 parse_mode="Markdown")
    
    for user_id in authorized_users:
        try:
            bot.send_message(user_id,
                           f"📢 **رسالة من المالك:**\n\n{broadcast_text}",
                           parse_mode="Markdown")
            success_count += 1
            time.sleep(0.5)
        except:
            fail_count += 1
    
    result_text = f"""✅ **تم إرسال الرسالة بنجاح!**

📊 **النتيجة:**
• ✅ تم الإرسال: {success_count} مستخدم
• ❌ فشل الإرسال: {fail_count} مستخدم
• 👥 إجمالي المستخدمين: {len(authorized_users)}

📝 **نص الرسالة:**
{broadcast_text}"""
    
    bot.edit_message_text(result_text, message.chat.id, status_msg.message_id,
                         reply_markup=get_admin_commands_menu(), parse_mode="Markdown")

def admin_referral_stats(call):
    """إحصائيات الإحالة للمالك"""
    if call.message.chat.id != OWNER_ID:
        return
    
    total_referrals = sum(len(refs) for refs in referral_system.values())
    total_points = sum(user_points.values())
    active_users = len([u for u in user_points if user_points[u] > 0])
    
    # ترتيب المستخدمين حسب النقاط
    top_users = sorted(user_points.items(), key=lambda x: x[1], reverse=True)[:5]
    
    top_text = "\n".join([f"{i+1}. ID: `{uid}` - {points} نقطة" 
                          for i, (uid, points) in enumerate(top_users)])
    
    text = f"""📊 **إحصائيات نظام الإحالة**

👥 **إجمالي المستخدمين:** {len(authorized_users)}
🎁 **إجمالي النقاط الموزعة:** {total_points}
🔄 **إجمالي الإحالات:** {total_referrals}
💫 **المستخدمين النشطين:** {active_users}

🏆 **أفضل 5 مستخدمين:**
{top_text}

⚙️ **إعدادات النظام:**
• نقاط كل إحالة: {REFERRAL_POINTS}
• إجمالي الروابط المنشأة: {len(referral_links)}"""
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                         reply_markup=get_admin_commands_menu(), parse_mode="Markdown")

def handle_bot_control(call):
    """معالجة أوامر التحكم بالبوت"""
    global bot_active
    
    if call.message.chat.id != OWNER_ID:
        bot.answer_callback_query(call.id, "❌ هذه الميزة غير متاحة لك")
        return
    
    if call.data == "bot_start":
        if bot_active:
            bot.answer_callback_query(call.id, "✅ البوت شغال بالفعل!")
        else:
            bot_active = True
            bot.edit_message_text("✅ **تم تشغيل البوت بنجاح**\nجميع المستخدمين يمكنهم الآن استخدام البوت.",
                                call.message.chat.id, call.message.message_id,
                                parse_mode="Markdown")
            
            # إشعار جميع المستخدمين أن البوت عاد للعمل
            for user_id in authorized_users:
                try:
                    bot.send_message(user_id,
                                   "✅ **البوت عاد للعمل!**\nيمكنك الآن استخدام جميع الميزات.",
                                   parse_mode="Markdown")
                except:
                    pass
    
    elif call.data == "bot_stop":
        if not bot_active:
            bot.answer_callback_query(call.id, "⚠️ البوت متوقف بالفعل!")
        else:
            bot_active = False
            bot.edit_message_text("⛔ **تم إيقاف البوت بنجاح**\nلن يتمكن المستخدمون من استخدام البوت حتى يتم تشغيله مرة أخرى.",
                                call.message.chat.id, call.message.message_id,
                                parse_mode="Markdown")
            
            # إشعار جميع المستخدمين أن البوت توقف
            for user_id in authorized_users:
                try:
                    bot.send_message(user_id,
                                   "⚠️ **البوت متوقف حالياً للصيانة**\nسنعود قريباً إن شاء الله.",
                                   parse_mode="Markdown")
                except:
                    pass
    
    elif call.data == "bot_restart":
        bot.edit_message_text("🔄 **جاري إعادة تشغيل البوت...**",
                            call.message.chat.id, call.message.message_id,
                            parse_mode="Markdown")
        
        # إيقاف البوت مؤقتاً
        bot_active = False
        time.sleep(2)
        
        # تشغيل البوت مرة أخرى
        bot_active = True
        
        bot.send_message(call.message.chat.id,
                        "✅ **تم إعادة تشغيل البوت بنجاح**",
                        parse_mode="Markdown")
        
        # إشعار المستخدمين
        for user_id in authorized_users:
            try:
                bot.send_message(user_id,
                               "✅ **تم إعادة تشغيل البوت**\nيمكنك الآن استخدام البوت.",
                               parse_mode="Markdown")
            except:
                pass
    
    elif call.data == "bot_status":
        status_text = f"""📊 **حالة البوت الرئيسي**

🤖 **الحالة:** {"🟢 شغال" if bot_active else "🔴 متوقف"}
👥 **المستخدمين النشطين:** {len(authorized_users)}
📁 **الملفات المرفوعة:** {len(uploaded_files)}
🔄 **العمليات العاملة:** {len(bot_processes)}
💰 **إجمالي النقاط:** {sum(user_points.values())}

⚙️ **معلومات إضافية:**
• آخر تحديث: {time.strftime('%Y-%m-%d %H:%M:%S')}
• وقت التشغيل: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(psutil.boot_time()))}"""
        
        bot.edit_message_text(status_text,
                            call.message.chat.id, call.message.message_id,
                            reply_markup=get_bot_control_menu(),
                            parse_mode="Markdown")

def forward_to_owner(message):
    """توجيه الرسائل للمالك"""
    if message.text:
        bot.send_message(OWNER_ID,
                        f"✉️ **رسالة جديدة:**\n\n"
                        f"👤 **المرسل:** {message.from_user.first_name}\n"
                        f"🆔 **الايدي:** `{message.from_user.id}`\n"
                        f"💬 **الرسالة:**\n{message.text}",
                        parse_mode="Markdown")
        
        bot.send_message(message.chat.id, "✅ **تم إرسال رسالتك للمالك**", parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, "❌ **الرجاء إرسال نص فقط**", parse_mode="Markdown")

def monitor_processes():
    """مراقبة العمليات العاملة"""
    while True:
        dead_processes = []
        for name, info in bot_processes.items():
            if info['process'].poll() is not None:
                dead_processes.append(name)
        
        for name in dead_processes:
            del bot_processes[name]
        
        time.sleep(30)

def cleanup():
    """تنظيف الموارد عند الإيقاف"""
    print("\n🛑 جاري إيقاف جميع العمليات...")
    for name, info in bot_processes.items():
        try:
            info['process'].terminate()
            time.sleep(1)
            if info['process'].poll() is None:
                info['process'].kill()
            print(f"✅ تم إيقاف {name}")
        except:
            pass
    print("✅ تم إيقاف جميع العمليات")
    save_data()

# ==================== معالج /start ====================
@bot.message_handler(commands=['start'])
@bot_active_only
def start(message):
    global owner_notified
    
    user_id = message.chat.id
    
    # إشعار المالك عند أول تشغيل للبوت
    if not owner_notified and user_id == OWNER_ID:
        bot.send_message(OWNER_ID,
                        "✅ **البوت شغال وجاهز للعمل**\n"
                        "يمكنك استخدام لوحة التحكم للتحكم في البوت.",
                        parse_mode="Markdown")
        owner_notified = True
    
    # التحقق من وجود كود إحالة
    args = message.text.split()
    if len(args) > 1 and args[1].startswith('ref_'):
        referral_code = args[1][4:]  # إزالة 'ref_' من البداية
        if user_id not in authorized_users and user_id != OWNER_ID:
            process_referral(referral_code, user_id)
            bot.send_message(user_id,
                           "🎉 **تم تسجيل دخولك عبر رابط صديق!**\n"
                           "صديقك حصل على نقاط إضافية\n\n"
                           "يمكنك الآن تسجيل الدخول:",
                           parse_mode="Markdown")
    
    if user_id == OWNER_ID:
        # قائمة المالك
        markup = get_owner_menu()
        welcome_msg = get_welcome_message(is_owner=True)
    elif user_id in authorized_users:
        # قائمة المستخدمين العاديين
        markup = get_main_menu()
        welcome_msg = get_welcome_message(is_owner=False)
        
        # عرض النقاط إذا كانت موجودة
        points = user_points.get(user_id, 0)
        welcome_msg += f"\n💰 **نقاطك:** {points}"
    else:
        markup = get_login_menu()
        welcome_msg = "🔐 **بوت استضافة البوتات**\nالرجاء تسجيل الدخول أولاً للوصول إلى لوحة التحكم."
    
    bot.send_message(user_id, welcome_msg, reply_markup=markup, parse_mode="Markdown")

# ==================== معالج النصوص للأزرار ====================
@bot.message_handler(func=lambda msg: msg.text == "⚙️ لوحة التحكم")
@owner_only
def owner_control_panel(message):
    """لوحة تحكم المالك"""
    bot.send_message(message.chat.id,
                    "⚙️ **لوحة تحكم المالك**\n\n"
                    "مرحباً بك في لوحة التحكم الخاصة بك. هذه الميزات متاحة لك فقط:\n\n"
                    "• 🔑 تغيير كلمة المرور\n"
                    "• 👥 إدارة المستخدمين\n"
                    "• 📊 إحصائيات متقدمة\n"
                    "• 📢 إرسال رسالة لجميع المستخدمين\n"
                    "• 🎁 إدارة نقاط المستخدمين\n"
                    "• 🔗 إحصائيات الإحالة\n"
                    "• 🤖 التحكم بالبوت الرئيسي\n\n"
                    "اختر ما تريد:",
                    reply_markup=get_admin_commands_menu(),
                    parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text == "📊 سرعة البوت")
@bot_active_only
def bot_speed(message):
    if message.chat.id not in authorized_users and message.chat.id != OWNER_ID:
        return
    
    waiting_msg = bot.send_message(message.chat.id, "🔄 **جاري قياس السرعة...**", parse_mode="Markdown")
    
    speeds = measure_speed()
    
    if speeds:
        speed_text = f"""📊 **نتيجة قياس السرعة:**

⚡ **سرعة الاتصال بتليجرام:** `{speeds['telegram']:.2f} ms`
💻 **سرعة معالجة البوت:** `{speeds['cpu']:.2f} ms`
⏱️ **السرعة الإجمالية:** `{speeds['total']:.2f} ms`

📡 **حالة البوت:** 🟢 ممتاز
✅ البوت يعمل بكفاءة عالية"""
    else:
        speed_text = "❌ **فشل قياس السرعة**"
    
    bot.edit_message_text(speed_text, message.chat.id, waiting_msg.message_id, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text == "📞 التواصل مع المالك")
@bot_active_only
def contact_owner(message):
    if message.chat.id not in authorized_users and message.chat.id != OWNER_ID:
        return
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📱 مراسلة المالك", url=f"https://t.me/sakaki_zlt"))
    markup.add(types.InlineKeyboardButton("✉️ إرسال رسالة", callback_data="send_message"))
    
    bot.send_message(message.chat.id,
                    f"👤 **معلومات المالك:**\n"
                    f"• المعرف: @sakaki_zlt\n"
                    f"• الايدي: `{OWNER_ID}`\n\n"
                    f"اختر طريقة التواصل:",
                    reply_markup=markup,
                    parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text == "📋 الملفات المرفوعة")
@bot_active_only
def list_uploaded_files(message):
    if message.chat.id not in authorized_users and message.chat.id != OWNER_ID:
        return
    
    if not uploaded_files:
        bot.send_message(message.chat.id, "📁 **لا توجد ملفات مرفوعة**", parse_mode="Markdown")
        return
    
    text = "📋 **الملفات المرفوعة:**\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for file_id, file_info in uploaded_files.items():
        status = "🟢 يعمل" if file_info['name'] in bot_processes else "🔴 متوقف"
        text += f"**{file_info['name']}**\n"
        text += f"الحالة: {status}\n"
        text += f"الحجم: `{file_info['size'] / 1024:.2f} KB`\n"
        text += f"التاريخ: `{file_info['date']}`\n"
        text += "─" * 20 + "\n"
        
        markup.add(types.InlineKeyboardButton(
            f"⚙️ إدارة {file_info['name']}", 
            callback_data=f"manage_{file_id}"
        ))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text == "🚀 تشغيل ملف")
@bot_active_only
def run_file_prompt(message):
    if message.chat.id not in authorized_users and message.chat.id != OWNER_ID:
        return
    
    if not uploaded_files:
        bot.send_message(message.chat.id, "📁 **لا توجد ملفات للتشغيل**", parse_mode="Markdown")
        return
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for file_id, file_info in uploaded_files.items():
        if file_info['type'] == 'python' or file_info['name'].endswith('.py'):
            markup.add(types.InlineKeyboardButton(
                f"🚀 {file_info['name']}", 
                callback_data=f"run_{file_id}"
            ))
    
    bot.send_message(message.chat.id, "🚀 **اختر الملف للتشغيل:**", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text == "⏹️ إيقاف تشغيل")
@bot_active_only
def stop_file_prompt(message):
    if message.chat.id not in authorized_users and message.chat.id != OWNER_ID:
        return
    
    if not bot_processes:
        bot.send_message(message.chat.id, "📭 **لا توجد عمليات تعمل حالياً**", parse_mode="Markdown")
        return
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for process_name in bot_processes.keys():
        markup.add(types.InlineKeyboardButton(
            f"⏹️ {process_name}", 
            callback_data=f"stop_{process_name}"
        ))
    
    bot.send_message(message.chat.id, "⏹️ **اختر العملية لإيقافها:**", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text == "🔄 إعادة تشغيل")
@bot_active_only
def restart_file_prompt(message):
    if message.chat.id not in authorized_users and message.chat.id != OWNER_ID:
        return
    
    if not bot_processes:
        bot.send_message(message.chat.id, "📭 **لا توجد عمليات تعمل حالياً**", parse_mode="Markdown")
        return
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for process_name in bot_processes.keys():
        markup.add(types.InlineKeyboardButton(
            f"🔄 {process_name}", 
            callback_data=f"restart_{process_name}"
        ))
    
    bot.send_message(message.chat.id, "🔄 **اختر العملية لإعادة تشغيلها:**", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text == "🗑️ حذف ملف")
@bot_active_only
def delete_file_prompt(message):
    if message.chat.id not in authorized_users and message.chat.id != OWNER_ID:
        return
    
    if not uploaded_files:
        bot.send_message(message.chat.id, "📁 **لا توجد ملفات للحذف**", parse_mode="Markdown")
        return
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for file_id, file_info in uploaded_files.items():
        markup.add(types.InlineKeyboardButton(
            f"🗑️ {file_info['name']}", 
            callback_data=f"delete_{file_id}"
        ))
    
    bot.send_message(message.chat.id, "🗑️ **اختر الملف للحذف:**", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text == "📊 حالة السيرفر")
@bot_active_only
def server_status(message):
    if message.chat.id not in authorized_users and message.chat.id != OWNER_ID:
        return
    
    cpu = psutil.cpu_percent(interval=1)
    cpu_freq = psutil.cpu_freq()
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    boot_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(psutil.boot_time()))
    
    total_files = len(uploaded_files)
    running_processes = len(bot_processes)
    total_users = len(authorized_users)
    
    status = f"""📊 **حالة السيرفر:**

💻 **المعالج (CPU):**
• الاستخدام: `{cpu}%`
• الأنوية: `{psutil.cpu_count()}`
• التردد: `{cpu_freq.current:.0f} MHz`

🧠 **الذاكرة (RAM):**
• المستخدم: `{memory.used / (1024**3):.1f}GB`
• الإجمالي: `{memory.total / (1024**3):.1f}GB`
• النسبة: `{memory.percent}%`

💾 **المساحة (DISK):**
• المستخدم: `{disk.used / (1024**3):.1f}GB`
• الإجمالي: `{disk.total / (1024**3):.1f}GB`
• النسبة: `{disk.percent}%`

🤖 **معلومات البوت:**
• الملفات المرفوعة: `{total_files}`
• العمليات العاملة: `{running_processes}`
• المستخدمين المسجلين: `{total_users}`
• مجلد الرفع: `{UPLOADS_DIR}/`

⏰ **معلومات إضافية:**
• وقت تشغيل السيرفر: `{boot_time}`
"""
    
    bot.send_message(message.chat.id, status, parse_mode='Markdown')

@bot.message_handler(func=lambda msg: msg.text == "🔗 نظام الإحالة")
@bot_active_only
def referral_system_menu(message):
    if message.chat.id not in authorized_users and message.chat.id != OWNER_ID:
        return
    
    user_id = message.chat.id
    points = user_points.get(user_id, 0)
    
    # إنشاء رابط الإحالة
    if str(user_id) not in referral_links:
        create_referral_link(user_id)
    
    link = referral_links[str(user_id)]
    referral_count = len(referral_system.get(user_id, []))
    
    text = f"""🔗 **نظام الإحالة**

💰 **نقاطك الحالية:** {points}
🎁 **نقاط كل دعوة:** +{REFERRAL_POINTS}
👥 **عدد المدعوين:** {referral_count}

📊 **إحصائيات رابطك:**
• عدد النقرات: {link['clicks']}
• عدد الناجحين: {link['successful_referrals']}

🔗 **رابط الإحالة الخاص بك:**
`{create_referral_link(user_id)}`

📌 **كيف تعمل؟**
1. أرسل الرابط لأصدقائك
2. عندما يسجل أحدهم عبر رابطك، تحصل على {REFERRAL_POINTS} نقاط
3. استخدم النقاط لرفع ملفات إضافية

✨ **مميزات النقاط:**
• {REFERRAL_POINTS} نقاط = رفع ملف إضافي
• يمكنك رفع المزيد من الملفات حسب نقاطك
• النقاط لا تنتهي صلاحيتها"""
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📋 سجل الإحالات", callback_data="referral_history"))
    markup.add(types.InlineKeyboardButton("🎁 استبدال النقاط", callback_data="redeem_points"))
    markup.add(types.InlineKeyboardButton("📤 مشاركة الرابط", url=f"https://t.me/share/url?url={create_referral_link(user_id)}"))
    
    bot.send_message(user_id, text, reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text == "💰 نقاطي")
@bot_active_only
def show_points(message):
    if message.chat.id not in authorized_users and message.chat.id != OWNER_ID:
        return
    
    user_id = message.chat.id
    points = user_points.get(user_id, 0)
    referrals = len(referral_system.get(user_id, []))
    
    text = f"""💰 **نقاطي**

**رصيدك الحالي:** {points} نقطة
**عدد المدعوين:** {referrals}

📊 **معلومات النقاط:**
• كل دعوة = {REFERRAL_POINTS} نقاط
• يمكنك استخدام النقاط لرفع ملفات إضافية
• كل {REFERRAL_POINTS} نقاط = رفع ملف واحد

💡 **نصائح لكسب المزيد:**
• شارك رابط الإحالة في مجموعات
• أرسل الرابط لأصدقائك المهتمين بالبرمجة
• كلما زاد عدد المدعوين، زادت نقاطك"""
    
    bot.send_message(user_id, text, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text == "📤 رفع ملف جديد")
@bot_active_only
def upload_file_prompt(message):
    if message.chat.id != OWNER_ID and message.chat.id not in authorized_users:
        return
    
    user_id = message.chat.id
    points = user_points.get(user_id, 0)
    
    # المالك يمكنه رفع عدد غير محدود
    if user_id != OWNER_ID:
        # حساب عدد الملفات التي رفعها المستخدم
        user_files = [f for f in uploaded_files.values() if f.get('user_id') == user_id]
        
        # التحقق من النقاط (كل مستخدم له ملف مجاني واحد)
        if len(user_files) >= 1:  # الملف الأول مجاني
            if len(user_files) - 1 >= points:  # باقي الملفات تحتاج نقاط
                needed = (len(user_files) - points)
                bot.send_message(user_id,
                               f"❌ **لا يمكنك رفع المزيد من الملفات**\n\n"
                               f"📁 ملفاتك الحالية: {len(user_files)}\n"
                               f"💰 نقاطك: {points}\n"
                               f"🎁 تحتاج إلى {needed} نقاط إضافية\n\n"
                               f"ادعُ أصدقاءك عبر نظام الإحالة لكسب المزيد من النقاط!",
                               parse_mode="Markdown")
                return
    
    msg = bot.send_message(user_id,
                          "📤 **رفع ملف جديد**\n\n"
                          "اختر نوع الملف الذي تريد رفعه:\n"
                          "• ملف بايثون `.py`\n"
                          "• ملف مضغوط `.zip`\n"
                          "• ملف `.py.zip`\n\n"
                          "الرجاء إرسال الملف الآن:",
                          parse_mode="Markdown")
    bot.register_next_step_handler(msg, handle_file_upload)

def handle_file_upload(message):
    if message.content_type != 'document':
        bot.send_message(message.chat.id, "❌ **الرجاء إرسال ملف صحيح**", 
                        reply_markup=get_owner_menu() if message.chat.id == OWNER_ID else get_main_menu(), 
                        parse_mode="Markdown")
        return
    
    try:
        waiting_msg = bot.send_message(message.chat.id, "⏳ **جاري معالجة الملف...**", parse_mode="Markdown")
        
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        file_name = message.document.file_name
        
        # التحقق من نوع الملف
        if not (file_name.endswith('.py') or file_name.endswith('.zip') or file_name.endswith('.py.zip')):
            bot.edit_message_text("❌ **الرجاء رفع ملف بايثون أو ملف مضغوط فقط**", 
                                message.chat.id, waiting_msg.message_id, parse_mode="Markdown")
            return
        
        # إنشاء اسم فريد للملف
        timestamp = int(time.time())
        unique_name = f"{timestamp}_{file_name}"
        file_path = os.path.join(UPLOADS_DIR, unique_name)
        
        # حفظ الملف
        with open(file_path, 'wb') as f:
            f.write(downloaded_file)
        
        # حفظ معلومات الملف
        file_id = f"{timestamp}"
        uploaded_files[file_id] = {
            'name': file_name,
            'path': file_path,
            'type': 'python' if file_name.endswith('.py') else 'zip',
            'size': message.document.file_size,
            'date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'user_id': message.chat.id,
            'uploader': message.from_user.first_name
        }
        save_data()
        
        # إشعار المالك برفع ملف جديد
        if message.chat.id != OWNER_ID:
            bot.send_message(OWNER_ID,
                           f"📤 **تم رفع ملف جديد**\n\n"
                           f"👤 **الرافع:** {message.from_user.first_name}\n"
                           f"📁 **الملف:** `{file_name}`\n"
                           f"📊 **الحجم:** `{message.document.file_size / 1024:.2f} KB`\n"
                           f"⏰ **الوقت:** {time.strftime('%Y-%m-%d %H:%M:%S')}",
                           parse_mode="Markdown")
        
        # إظهار خيارات الملف
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("🚀 تشغيل", callback_data=f"run_{file_id}"),
            types.InlineKeyboardButton("📝 معلومات", callback_data=f"info_{file_id}")
        )
        if file_name.endswith('.zip'):
            markup.add(types.InlineKeyboardButton("📂 فك الضغط", callback_data=f"extract_{file_id}"))
        
        bot.edit_message_text(
            f"✅ **تم رفع الملف بنجاح!**\n\n"
            f"📁 **الملف:** `{file_name}`\n"
            f"📊 **الحجم:** `{message.document.file_size / 1024:.2f} KB`\n"
            f"📅 **التاريخ:** `{time.strftime('%Y-%m-%d %H:%M:%S')}`\n\n"
            f"اختر الإجراء المناسب:",
            message.chat.id,
            waiting_msg.message_id,
            reply_markup=markup,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ **خطأ:** `{str(e)}`", parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text == "🚪 تسجيل الخروج")
@bot_active_only
def logout(message):
    if message.chat.id in authorized_users:
        authorized_users.remove(message.chat.id)
        save_data()
        
        if message.chat.id != OWNER_ID:
            bot.send_message(OWNER_ID,
                           f"🚪 **تسجيل خروج**\n\n"
                           f"👤 **المستخدم:** {message.from_user.first_name}\n"
                           f"🆔 **الايدي:** `{message.chat.id}`\n"
                           f"⏰ **الوقت:** {time.strftime('%Y-%m-%d %H:%M:%S')}",
                           parse_mode="Markdown")
        
        bot.send_message(message.chat.id, "✅ **تم تسجيل الخروج**", reply_markup=get_login_menu(), parse_mode="Markdown")
    elif message.chat.id == OWNER_ID:
        bot.send_message(message.chat.id, "👑 **أنت المالك، لا يمكنك تسجيل الخروج**", 
                        reply_markup=get_owner_menu(), parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, "❌ **أنت لست مسجل دخول**", reply_markup=get_login_menu(), parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text == "🔐 تسجيل الدخول")
@bot_active_only
def login_prompt(message):
    msg = bot.send_message(message.chat.id, "🔑 **أدخل كلمة المرور:**", parse_mode="Markdown")
    bot.register_next_step_handler(msg, check_password)

def check_password(message):
    user_id = message.chat.id
    
    if user_id not in login_attempts:
        login_attempts[user_id] = {'count': 0, 'first_attempt': time.time()}
    
    current_time = time.time()
    for uid in list(login_attempts.keys()):
        if current_time - login_attempts[uid]['first_attempt'] > 3600:
            del login_attempts[uid]
    
    if message.text == MAIN_PASSWORD:
        if user_id not in authorized_users and user_id != OWNER_ID:
            authorized_users.append(user_id)
            save_data()
            
            bot.send_message(OWNER_ID,
                           f"🔔 **دخول مستخدم جديد!**\n\n"
                           f"👤 **الاسم:** {message.from_user.first_name}\n"
                           f"🆔 **الايدي:** `{user_id}`\n"
                           f"⏰ **الوقت:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                           f"🌐 **اليوزر:** @{message.from_user.username if message.from_user.username else 'لا يوجد'}",
                           parse_mode="Markdown")
        
        if user_id in login_attempts:
            del login_attempts[user_id]
        
        if user_id == OWNER_ID:
            reply_markup = get_owner_menu()
            welcome_msg = "✅ **مرحباً بك يا مالك البوت! تم تسجيل الدخول بنجاح**"
        else:
            reply_markup = get_main_menu()
            welcome_msg = "✅ **تم تسجيل الدخول بنجاح!**"
            
        bot.send_message(message.chat.id,
                        welcome_msg + "\nيمكنك الآن رفع وإدارة الملفات.",
                        reply_markup=reply_markup,
                        parse_mode="Markdown")
    else:
        login_attempts[user_id]['count'] += 1
        
        if login_attempts[user_id]['count'] >= 5:
            bot.send_message(message.chat.id, 
                           "❌ **تم تجاوز الحد الأقصى للمحاولات!\n"
                           "الرجاء المحاولة بعد ساعة**", 
                           reply_markup=get_login_menu(), 
                           parse_mode="Markdown")
            
            bot.send_message(OWNER_ID,
                           f"⚠️ **تنبيه أمني!**\n\n"
                           f"👤 **المستخدم:** {message.from_user.first_name}\n"
                           f"🆔 **الايدي:** `{user_id}`\n"
                           f"🔴 **محاولات فاشلة:** 5\n"
                           f"⏰ **الوقت:** {time.strftime('%Y-%m-%d %H:%M:%S')}",
                           parse_mode="Markdown")
        else:
            remaining = 5 - login_attempts[user_id]['count']
            bot.send_message(message.chat.id, 
                           f"❌ **كلمة مرور خاطئة**\n"
                           f"⚠️ المحاولات المتبقية: {remaining}", 
                           reply_markup=get_login_menu(), 
                           parse_mode="Markdown")

# ==================== معالج الردود على الأزرار ====================
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    # التحقق من أن المستخدم مصرح له
    if call.message.chat.id != OWNER_ID and call.message.chat.id not in authorized_users:
        bot.answer_callback_query(call.id, "❌ يجب تسجيل الدخول أولاً")
        return
    
    # التحقق من أن البوت شغال (إلا إذا كان المالك)
    if not bot_active and call.message.chat.id != OWNER_ID:
        bot.answer_callback_query(call.id, "⚠️ البوت متوقف حالياً")
        return
    
    # معالجة أوامر المالك
    if call.data.startswith("admin_"):
        if call.message.chat.id != OWNER_ID:
            bot.answer_callback_query(call.id, "❌ هذه الميزة غير متاحة لك")
            return
        
        if call.data == "admin_change_password":
            change_password_secret(call)
        elif call.data == "admin_manage_users":
            manage_users_secret(call)
        elif call.data == "admin_stats":
            stats_secret(call)
        elif call.data == "admin_broadcast":
            broadcast_message(call)
        elif call.data == "admin_referral_stats":
            admin_referral_stats(call)
        elif call.data == "admin_bot_control":
            bot_control_menu(call)
        elif call.data == "admin_back":
            bot.edit_message_text("✅ تم العودة للقائمة الرئيسية", 
                                call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id, "القائمة الرئيسية:", 
                            reply_markup=get_owner_menu())
        elif call.data == "admin_back_to_commands":
            bot.edit_message_text("⚙️ **لوحة تحكم المالك**\n\nاختر ما تريد:",
                                call.message.chat.id, call.message.message_id,
                                reply_markup=get_admin_commands_menu(), parse_mode="Markdown")
        elif call.data.startswith("remove_user_"):
            user_id = int(call.data.replace("remove_user_", ""))
            if user_id in authorized_users:
                authorized_users.remove(user_id)
                save_data()
                bot.answer_callback_query(call.id, f"✅ تم حذف المستخدم {user_id}")
                manage_users_secret(call)
            else:
                bot.answer_callback_query(call.id, "❌ المستخدم غير موجود")
    
    # معالجة أوامر التحكم بالبوت
    elif call.data in ["bot_start", "bot_stop", "bot_restart", "bot_status"]:
        handle_bot_control(call)
    
    # معالجة نظام الإحالة
    elif call.data == "referral_history":
        user_id = call.message.chat.id
        referrals = referral_system.get(user_id, [])
        
        if not referrals:
            bot.answer_callback_query(call.id, "📭 لا يوجد لديك إحالات بعد")
            return
        
        text = "📋 **سجل الإحالات:**\n\n"
        for i, ref in enumerate(referrals[-10:], 1):  # آخر 10 إحالات فقط
            text += f"{i}. 👤 مستخدم: `{ref['user_id']}`\n"
            text += f"   📅 التاريخ: {ref['date']}\n"
            text += f"   ⭐ النقاط: +{ref['points_earned']}\n\n"
        
        bot.send_message(user_id, text, parse_mode="Markdown")
        bot.answer_callback_query(call.id)
    
    elif call.data == "redeem_points":
        user_id = call.message.chat.id
        points = user_points.get(user_id, 0)
        
        if points < REFERRAL_POINTS:
            bot.answer_callback_query(call.id, f"❌ تحتاج إلى {REFERRAL_POINTS} نقاط على الأقل")
            return
        
        text = f"""🎁 **استبدال النقاط**

نقاطك الحالية: {points}

اختر ما تريد:
• {REFERRAL_POINTS} نقاط = رفع ملف إضافي
• {REFERRAL_POINTS*2} نقاط = رفع ملفين إضافيين
• {REFERRAL_POINTS*3} نقاط = رفع 3 ملفات إضافية"""
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton(f"🎫 رفع ملف واحد ({REFERRAL_POINTS} نقطة)", 
                                       callback_data="redeem_1_file"),
            types.InlineKeyboardButton(f"🎫 رفع ملفين ({REFERRAL_POINTS*2} نقطة)", 
                                       callback_data="redeem_2_files"),
            types.InlineKeyboardButton(f"🎫 رفع 3 ملفات ({REFERRAL_POINTS*3} نقطة)", 
                                       callback_data="redeem_3_files")
        )
        
        bot.edit_message_text(text, user_id, call.message.message_id,
                            reply_markup=markup, parse_mode="Markdown")
    
    elif call.data == "send_message":
        msg = bot.send_message(call.message.chat.id, "✉️ **أرسل رسالتك للمالك:**", parse_mode="Markdown")
        bot.register_next_step_handler(msg, forward_to_owner)
    
    # معالجة عمليات الملفات
    else:
        try:
            parts = call.data.split("_", 1)
            if len(parts) < 2:
                return
            
            action, item_id = parts[0], parts[1]
            
            if action == "run":
                if item_id in uploaded_files:
                    file_info = uploaded_files[item_id]
                    file_path = file_info['path']
                    
                    bot.edit_message_text(f"🚀 **جاري تشغيل:** `{file_info['name']}`", 
                                        call.message.chat.id, call.message.message_id, parse_mode="Markdown")
                    
                    try:
                        process = subprocess.Popen(
                            [sys.executable, file_path],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            stdin=subprocess.DEVNULL,
                            cwd=os.getcwd()
                        )
                        
                        time.sleep(2)
                        
                        if process.poll() is None:
                            bot_processes[file_info['name']] = {
                                'process': process,
                                'path': file_path,
                                'time': time.strftime('%Y-%m-%d %H:%M:%S'),
                                'pid': process.pid
                            }
                            
                            bot.send_message(call.message.chat.id,
                                           f"✅ **تم تشغيل الملف بنجاح!**\n\n"
                                           f"📁 **الملف:** `{file_info['name']}`\n"
                                           f"🆔 **PID:** `{process.pid}`\n"
                                           f"⏰ **وقت التشغيل:** `{time.strftime('%Y-%m-%d %H:%M:%S')}`",
                                           parse_mode="Markdown")
                        else:
                            stderr = process.stderr.read().decode('utf-8', errors='ignore')
                            bot.send_message(call.message.chat.id,
                                           f"❌ **فشل التشغيل!**\n\n`{stderr[:500]}`",
                                           parse_mode="Markdown")
                            
                    except Exception as e:
                        bot.send_message(call.message.chat.id, f"❌ **خطأ:** `{str(e)}`", parse_mode="Markdown")
            
            elif action == "stop":
                if item_id in bot_processes:
                    try:
                        process = bot_processes[item_id]['process']
                        process.terminate()
                        time.sleep(1)
                        if process.poll() is None:
                            process.kill()
                        
                        del bot_processes[item_id]
                        
                        bot.edit_message_text(f"✅ **تم إيقاف:** `{item_id}`", 
                                            call.message.chat.id, call.message.message_id, parse_mode="Markdown")
                    except Exception as e:
                        bot.edit_message_text(f"❌ **خطأ:** `{str(e)}`", 
                                            call.message.chat.id, call.message.message_id, parse_mode="Markdown")
            
            elif action == "restart":
                if item_id in bot_processes:
                    try:
                        old_process = bot_processes[item_id]['process']
                        old_process.terminate()
                        time.sleep(2)
                        
                        new_process = subprocess.Popen(
                            [sys.executable, bot_processes[item_id]['path']],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            stdin=subprocess.DEVNULL,
                            cwd=os.getcwd()
                        )
                        
                        bot_processes[item_id]['process'] = new_process
                        bot_processes[item_id]['time'] = time.strftime('%Y-%m-%d %H:%M:%S')
                        bot_processes[item_id]['pid'] = new_process.pid
                        
                        bot.edit_message_text(f"✅ **تم إعادة تشغيل:** `{item_id}`", 
                                            call.message.chat.id, call.message.message_id, parse_mode="Markdown")
                    except Exception as e:
                        bot.edit_message_text(f"❌ **خطأ:** `{str(e)}`", 
                                            call.message.chat.id, call.message.message_id, parse_mode="Markdown")
            
            elif action == "delete":
                if item_id in uploaded_files:
                    file_info = uploaded_files[item_id]
                    file_path = file_info['path']
                    
                    try:
                        if file_info['name'] in bot_processes:
                            bot_processes[file_info['name']]['process'].terminate()
                            time.sleep(1)
                            del bot_processes[file_info['name']]
                        
                        if os.path.exists(file_path):
                            os.remove(file_path)
                        
                        del uploaded_files[item_id]
                        save_data()
                        
                        bot.edit_message_text(f"✅ **تم حذف الملف:** `{file_info['name']}`", 
                                            call.message.chat.id, call.message.message_id, parse_mode="Markdown")
                    except Exception as e:
                        bot.edit_message_text(f"❌ **خطأ في الحذف:** `{str(e)}`", 
                                            call.message.chat.id, call.message.message_id, parse_mode="Markdown")
            
            elif action == "info":
                if item_id in uploaded_files:
                    file_info = uploaded_files[item_id]
                    info_text = f"""📝 **معلومات الملف:**

📁 **الاسم:** `{file_info['name']}`
📊 **الحجم:** `{file_info['size'] / 1024:.2f} KB`
📅 **تاريخ الرفع:** `{file_info['date']}`
📍 **المسار:** `{file_info['path']}`
👤 **الرافع:** {file_info.get('uploader', 'غير معروف')}"""
                    
                    if file_info['name'] in bot_processes:
                        info_text += f"\n🟢 **الحالة:** يعمل (PID: {bot_processes[file_info['name']]['pid']})"
                    else:
                        info_text += f"\n🔴 **الحالة:** متوقف"
                    
                    bot.edit_message_text(info_text, call.message.chat.id, call.message.message_id, parse_mode="Markdown")
            
            elif action == "manage":
                if item_id in uploaded_files:
                    file_info = uploaded_files[item_id]
                    markup = types.InlineKeyboardMarkup(row_width=2)
                    markup.add(
                        types.InlineKeyboardButton("🚀 تشغيل", callback_data=f"run_{item_id}"),
                        types.InlineKeyboardButton("⏹️ إيقاف", callback_data=f"stop_{file_info['name']}"),
                        types.InlineKeyboardButton("🔄 إعادة تشغيل", callback_data=f"restart_{file_info['name']}"),
                        types.InlineKeyboardButton("🗑️ حذف", callback_data=f"delete_{item_id}"),
                        types.InlineKeyboardButton("📝 معلومات", callback_data=f"info_{item_id}")
                    )
                    bot.edit_message_text(f"⚙️ **إدارة الملف:** `{file_info['name']}`", 
                                        call.message.chat.id, call.message.message_id, 
                                        reply_markup=markup, parse_mode="Markdown")
        except Exception as e:
            print(f"Error in callback: {e}")
            bot.answer_callback_query(call.id, "❌ حدث خطأ")

def bot_control_menu(call):
    """قائمة التحكم بالبوت الرئيسي"""
    if call.message.chat.id != OWNER_ID:
        bot.answer_callback_query(call.id, "❌ هذه الميزة غير متاحة لك")
        return
    
    status = "🟢 **شغال**" if bot_active else "🔴 **متوقف**"
    
    bot.edit_message_text(f"""🤖 **التحكم بالبوت الرئيسي**

📊 **حالة البوت الحالية:** {status}

اختر الإجراء المطلوب:""",
                        call.message.chat.id, call.message.message_id,
                        reply_markup=get_bot_control_menu(),
                        parse_mode="Markdown")

# ==================== بدء تشغيل البوت ====================
if __name__ == "__main__":
    import atexit
    atexit.register(cleanup)
    
    print("=" * 60)
    print("✅ بوت الاستضافة الذكي يعمل!")
    print("=" * 60)
    print(f"👤 Owner ID: {OWNER_ID}")
    print(f"🔑 Current Password: {MAIN_PASSWORD}")
    print(f"🤖 Bot Token: {BOT_TOKEN}")
    print(f"📁 Uploads Directory: {os.path.abspath(UPLOADS_DIR)}")
    print(f"📊 Total Files: {len(uploaded_files)}")
    print(f"👥 Authorized Users: {len(authorized_users)}")
    print(f"💰 Total Points: {sum(user_points.values())}")
    print(f"🔄 Total Referrals: {sum(len(refs) for refs in referral_system.values())}")
    print(f"🤖 Bot Status: {'🟢 شغال' if bot_active else '🔴 متوقف'}")
    print("=" * 60)
    print("⚡ في انتظار الأوامر...")
    print("=" * 60)
    
    monitor_thread = threading.Thread(target=monitor_processes, daemon=True)
    monitor_thread.start()
    
    try:
        bot.infinity_polling()
    except KeyboardInterrupt:
        print("\n🛑 تم إيقاف البوت الرئيسي")
        cleanup()
