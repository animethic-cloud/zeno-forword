import telebot
import re
import json
import os
import time
import requests
from telebot import types
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ============== ENVIRONMENT VARIABLES ==============
BOT_TOKEN = os.environ.get("BOT_TOKEN", "7634920543:AAE4RaPPd3TO26hURlyBauOsJ_zJEnLk9rY")
YOUR_USER_ID = int(os.environ.get("YOUR_USER_ID", "7406197326"))
TARGET_CHANNEL_ID = int(os.environ.get("TARGET_CHANNEL_ID", "-1003120043320"))
TARGET_CHANNEL_USERNAME = os.environ.get("TARGET_CHANNEL_USERNAME", "@animethic2")
YOUR_WEBSITE = os.environ.get("YOUR_WEBSITE", "www.animethic.xyz")
SETTINGS_FILE = "settings.json"
# ===================================================

# Default authorized users
DEFAULT_AUTHORIZED_USERS = [YOUR_USER_ID]

# ============== SETTINGS FUNCTIONS ==============
def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_settings(settings):
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

def save_settings_to_file():
    data = {
        'channel_username': TARGET_CHANNEL_USERNAME,
        'website': YOUR_WEBSITE,
        'replace_urls': REPLACE_URLS,
        'replace_mentions': REPLACE_MENTIONS,
        'add_credit': ADD_CREDIT,
        'authorized_users': AUTHORIZED_USERS
    }
    return save_settings(data)

# Load settings
settings = load_settings()

# Global variables
if settings:
    TARGET_CHANNEL_USERNAME = settings.get('channel_username', TARGET_CHANNEL_USERNAME)
    YOUR_WEBSITE = settings.get('website', YOUR_WEBSITE)
    REPLACE_URLS = settings.get('replace_urls', True)
    REPLACE_MENTIONS = settings.get('replace_mentions', True)
    ADD_CREDIT = settings.get('add_credit', True)
    AUTHORIZED_USERS = settings.get('authorized_users', DEFAULT_AUTHORIZED_USERS)
else:
    REPLACE_URLS = True
    REPLACE_MENTIONS = True
    ADD_CREDIT = True
    AUTHORIZED_USERS = DEFAULT_AUTHORIZED_USERS

# ============== CUSTOM SESSION ==============
session = requests.Session()
retry_strategy = Retry(
    total=5,
    backoff_factor=2,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET", "POST"]
)
adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=20, pool_maxsize=20)
session.mount("https://", adapter)
session.mount("http://", adapter)

# Bot initialization
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
bot.threaded = False
bot.session = session

# ============== HELPER FUNCTIONS ==============
def is_authorized(user_id):
    return user_id in AUTHORIZED_USERS

def edit_caption(original_caption):
    if original_caption is None:
        original_caption = ""
    
    edited = str(original_caption)
    
    if REPLACE_MENTIONS:
        edited = re.sub(r'@[a-zA-Z][a-zA-Z0-9_]{3,}', TARGET_CHANNEL_USERNAME, edited)
    
    if REPLACE_URLS:
        edited = re.sub(r'(https?://)?t\.me/[a-zA-Z][a-zA-Z0-9_]+', f'https://t.me/{TARGET_CHANNEL_USERNAME[1:]}', edited)
        edited = re.sub(r'https?://(?!t\.me)[^\s]+', f'https://{YOUR_WEBSITE}', edited)
    
    if ADD_CREDIT:
        if edited.strip():
            edited += f"\n\nProvided by {YOUR_WEBSITE}"
        else:
            edited = f"Provided by {YOUR_WEBSITE}"
    
    return edited

# ============== SETTINGS PANEL ==============
@bot.message_handler(commands=['settings'])
def settings_panel(message):
    if not is_authorized(message.from_user.id):
        bot.reply_to(message, "❌ Unauthorized")
        return
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    url_status = "✅" if REPLACE_URLS else "❌"
    mention_status = "✅" if REPLACE_MENTIONS else "❌"
    credit_status = "✅" if ADD_CREDIT else "❌"
    
    markup.add(
        types.InlineKeyboardButton(f"{url_status} URL Replace", callback_data="toggle_url"),
        types.InlineKeyboardButton(f"{mention_status} @Mention Replace", callback_data="toggle_mention"),
        types.InlineKeyboardButton(f"{credit_status} Add Credit", callback_data="toggle_credit"),
        types.InlineKeyboardButton("📊 Current Settings", callback_data="show_settings"),
        types.InlineKeyboardButton("✏️ Edit Channel", callback_data="edit_channel"),
        types.InlineKeyboardButton("🌐 Edit Website", callback_data="edit_website"),
        types.InlineKeyboardButton("👥 Manage Users", callback_data="manage_users")
    )
    
    text = f"""
⚙️ <b>Settings Panel</b>

📌 <b>Current Settings:</b>
• Channel: <code>{TARGET_CHANNEL_USERNAME}</code>
• Website: <code>{YOUR_WEBSITE}</code>
• Replace URLs: {url_status}
• Replace @Mentions: {mention_status}
• Add Credit: {credit_status}
• Authorized Users: <code>{len(AUTHORIZED_USERS)}</code>

Tap buttons to toggle or edit.
    """
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="HTML")

# ============== USER MANAGEMENT ==============
def manage_users_panel(chat_id, message_id=None):
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    markup.add(
        types.InlineKeyboardButton("➕ Add User", callback_data="add_user"),
        types.InlineKeyboardButton("➖ Remove User", callback_data="remove_user"),
        types.InlineKeyboardButton("📋 List Users", callback_data="list_users"),
        types.InlineKeyboardButton("🔙 Back to Settings", callback_data="back_to_settings")
    )
    
    text = f"""
👥 <b>User Management</b>

📊 <b>Authorized Users: {len(AUTHORIZED_USERS)}</b>

Select an option:
    """
    
    if message_id:
        try:
            bot.edit_message_text(text, chat_id, message_id, reply_markup=markup, parse_mode="HTML")
        except:
            bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")
    else:
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    global REPLACE_URLS, REPLACE_MENTIONS, ADD_CREDIT, TARGET_CHANNEL_USERNAME, YOUR_WEBSITE, AUTHORIZED_USERS
    
    if not is_authorized(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Unauthorized")
        return
    
    try:
        if call.data == "toggle_url":
            REPLACE_URLS = not REPLACE_URLS
            save_settings_to_file()
            bot.answer_callback_query(call.id, f"URL Replace: {'ON' if REPLACE_URLS else 'OFF'}")
            bot.delete_message(call.message.chat.id, call.message.message_id)
            settings_panel(call.message)
            
        elif call.data == "toggle_mention":
            REPLACE_MENTIONS = not REPLACE_MENTIONS
            save_settings_to_file()
            bot.answer_callback_query(call.id, f"@Mention Replace: {'ON' if REPLACE_MENTIONS else 'OFF'}")
            bot.delete_message(call.message.chat.id, call.message.message_id)
            settings_panel(call.message)
            
        elif call.data == "toggle_credit":
            ADD_CREDIT = not ADD_CREDIT
            save_settings_to_file()
            bot.answer_callback_query(call.id, f"Add Credit: {'ON' if ADD_CREDIT else 'OFF'}")
            bot.delete_message(call.message.chat.id, call.message.message_id)
            settings_panel(call.message)
            
        elif call.data == "show_settings":
            text = f"""
📊 <b>Current Configuration</b>

🔹 Channel: <code>{TARGET_CHANNEL_USERNAME}</code>
🔹 Channel ID: <code>{TARGET_CHANNEL_ID}</code>
🔹 Website: <code>{YOUR_WEBSITE}</code>
🔹 Replace URLs: {REPLACE_URLS}
🔹 Replace @Mentions: {REPLACE_MENTIONS}
🔹 Add Credit: {ADD_CREDIT}
🔹 Authorized Users: {len(AUTHORIZED_USERS)}
            """
            bot.send_message(call.message.chat.id, text, parse_mode="HTML")
            bot.answer_callback_query(call.id)
            
        elif call.data == "edit_channel":
            msg = bot.send_message(call.message.chat.id, "Send new channel username (e.g., @newchannel):")
            bot.register_next_step_handler(msg, update_channel)
            bot.answer_callback_query(call.id)
            
        elif call.data == "edit_website":
            msg = bot.send_message(call.message.chat.id, "Send new website (e.g., example.com):")
            bot.register_next_step_handler(msg, update_website)
            bot.answer_callback_query(call.id)
        
        elif call.data == "manage_users":
            manage_users_panel(call.message.chat.id, call.message.message_id)
            bot.answer_callback_query(call.id)
        
        elif call.data == "back_to_settings":
            bot.delete_message(call.message.chat.id, call.message.message_id)
            settings_panel(call.message)
            bot.answer_callback_query(call.id)
        
        elif call.data == "add_user":
            msg = bot.send_message(call.message.chat.id, "Send the Telegram User ID to authorize:")
            bot.register_next_step_handler(msg, add_authorized_user)
            bot.answer_callback_query(call.id)
        
        elif call.data == "remove_user":
            if len(AUTHORIZED_USERS) <= 1:
                bot.answer_callback_query(call.id, "❌ Cannot remove last user!", show_alert=True)
                return
            show_remove_user_list(call.message.chat.id)
            bot.answer_callback_query(call.id)
        
        elif call.data == "list_users":
            show_user_list(call.message.chat.id)
            bot.answer_callback_query(call.id)
        
        elif call.data.startswith("remove_"):
            user_id = int(call.data.replace("remove_", ""))
            if user_id in AUTHORIZED_USERS and user_id != YOUR_USER_ID:
                AUTHORIZED_USERS.remove(user_id)
                save_settings_to_file()
                bot.answer_callback_query(call.id, f"✅ User {user_id} removed!", show_alert=True)
                manage_users_panel(call.message.chat.id, call.message.message_id)
            else:
                bot.answer_callback_query(call.id, "❌ Cannot remove main admin!", show_alert=True)
    except Exception as e:
        bot.answer_callback_query(call.id, f"Error: {str(e)[:50]}")
        print(f"Callback error: {e}")

def add_authorized_user(message):
    if not is_authorized(message.from_user.id):
        return
    try:
        new_id = int(message.text.strip())
        if new_id not in AUTHORIZED_USERS:
            AUTHORIZED_USERS.append(new_id)
            save_settings_to_file()
            bot.reply_to(message, f"✅ User <code>{new_id}</code> authorized!", parse_mode="HTML")
        else:
            bot.reply_to(message, "❌ User already authorized!")
    except:
        bot.reply_to(message, "❌ Invalid ID! Please send a numeric ID.")

def show_remove_user_list(chat_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    for user_id in AUTHORIZED_USERS:
        if user_id != YOUR_USER_ID:
            markup.add(types.InlineKeyboardButton(f"❌ Remove {user_id}", callback_data=f"remove_{user_id}"))
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="manage_users"))
    bot.send_message(chat_id, "Select user to remove:", reply_markup=markup)

def show_user_list(chat_id):
    text = "👥 <b>Authorized Users:</b>\n\n"
    for i, user_id in enumerate(AUTHORIZED_USERS, 1):
        crown = " 👑" if user_id == YOUR_USER_ID else ""
        text += f"{i}. <code>{user_id}</code>{crown}\n"
    bot.send_message(chat_id, text, parse_mode="HTML")

def update_channel(message):
    global TARGET_CHANNEL_USERNAME
    if not is_authorized(message.from_user.id):
        return
    if not message.text.startswith('@'):
        bot.reply_to(message, "❌ Must start with @")
        return
    TARGET_CHANNEL_USERNAME = message.text.strip()
    save_settings_to_file()
    bot.reply_to(message, f"✅ Channel updated to {TARGET_CHANNEL_USERNAME}")

def update_website(message):
    global YOUR_WEBSITE
    if not is_authorized(message.from_user.id):
        return
    YOUR_WEBSITE = message.text.strip().replace('https://', '').replace('http://', '').split('/')[0]
    save_settings_to_file()
    bot.reply_to(message, f"✅ Website updated to {YOUR_WEBSITE}")

# ============== MEDIA HANDLERS ==============
@bot.message_handler(content_types=['video'])
def handle_video(message):
    if not is_authorized(message.from_user.id):
        bot.reply_to(message, "❌ Unauthorized")
        return
    
    new_caption = edit_caption(message.caption)
    try:
        bot.send_video(TARGET_CHANNEL_ID, message.video.file_id, caption=new_caption, parse_mode="HTML")
        bot.reply_to(message, "✅ Video posted to channel!")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

@bot.message_handler(content_types=['document'])
def handle_document(message):
    if not is_authorized(message.from_user.id):
        bot.reply_to(message, "❌ Unauthorized")
        return
    
    new_caption = edit_caption(message.caption)
    try:
        bot.send_document(TARGET_CHANNEL_ID, message.document.file_id, caption=new_caption, parse_mode="HTML")
        bot.reply_to(message, "✅ Document posted to channel!")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

@bot.message_handler(commands=['start', 'help'])
def start(message):
    if is_authorized(message.from_user.id):
        bot.reply_to(message, "👋 Bot is ready!\n/settings - Open control panel\nForward video/document to post.")
    else:
        bot.reply_to(message, "❌ Unauthorized")

# ============== WEB SERVER (Render Health Check) ==============
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'Bot is running!')
    
    def log_message(self, format, *args):
        pass

def run_health_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    print(f"🌐 Health check server running on port {port}")
    server.serve_forever()

# Start health server in background
threading.Thread(target=run_health_server, daemon=True).start()

# ============== INITIAL SAVE ==============
save_settings_to_file()

# ============== BOT START ==============
print("🤖 Bot is running on Render...")
print(f"Channel: {TARGET_CHANNEL_USERNAME}")
print(f"Website: {YOUR_WEBSITE}")
print(f"Authorized Users: {len(AUTHORIZED_USERS)}")

while True:
    try:
        print("🔄 Polling Telegram...")
        bot.infinity_polling(timeout=60, long_polling_timeout=30)
    except requests.exceptions.ReadTimeout:
        print("⏱️ Timeout - reconnecting in 5s...")
        time.sleep(5)
    except requests.exceptions.ConnectionError:
        print("🌐 Connection error - reconnecting in 10s...")
        time.sleep(10)
    except Exception as e:
        print(f"❌ Error: {e}")
        time.sleep(5)
