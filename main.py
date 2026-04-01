import requests
import json
import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ==================== CONFIG ====================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))
API_URL = "https://api.vectorxo.online/lookup"
# ================================================

USERS_FILE = "users.json"
USER_DETAILS_FILE = "user_details.json"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return set(json.load(f))
    return set()

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(list(users), f)

def load_user_details():
    if os.path.exists(USER_DETAILS_FILE):
        with open(USER_DETAILS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_user_details(details):
    with open(USER_DETAILS_FILE, 'w') as f:
        json.dump(details, f)

users = load_users()
user_details = load_user_details()

def is_admin(user_id):
    return user_id == ADMIN_ID

def save_user_info(user_id, username, first_name):
    user_details[str(user_id)] = {
        "username": username or "No username",
        "first_name": first_name or "Unknown",
        "user_id": user_id
    }
    save_user_details(user_details)

def format_result(data, mobile):
    if not data or len(data) == 0:
        return f"❌ No results found for {mobile}"
    
    text = f"🔍 Mobile Search Results\n"
    text += f"━━━━━━━━━━━━━━━━━━━━\n"
    text += f"💬 Query: {mobile}\n"
    text += f"📊 Total Found: {len(data)}\n"
    text += f"📄 Showing: {len(data)} results\n"
    text += f"━━━━━━━━━━━━━━━━━━━━\n\n"
    
    for i, item in enumerate(data, 1):
        text += f"📄 Result {i}:\n"
        text += f"📱 Number: {item.get('mobile', 'N/A')}\n"
        text += f"👤 Name: {item.get('name', 'N/A')}\n"
        text += f"👨‍👩‍👧‍👦 Father: {item.get('fname', 'N/A')}\n"
        text += f"📍 Address:\n{item.get('address', 'N/A')}\n"
        text += f"📞 Alt Number: {item.get('alt', 'N/A')}\n"
        text += f"📧 Email: {item.get('email', 'N/A')}\n"
        text += f"🛜 Circle: {item.get('circle', 'N/A')}\n"
        text += f"🆔 ID: {item.get('id', 'N/A')}\n"
        text += f"━━━━━━━━━━━━━━━━━━━━\n\n"
    
    text += f"📊 Total Results: {len(data)}\n"
    text += f"━━━━━━━━━━━━━━━━━━━━\n"
    text += f"👑 Made by: 𝐋𝐞𝐠𝐞𝐧𝐝"
    return text

def lookup_number(mobile):
    try:
        url = f"{API_URL}?key=vectorxo&mobile={mobile}"
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            return r.json()
        return None
    except:
        return None

def get_admin_keyboard():
    keyboard = [
        ["📊 Stats", "📢 Broadcast"],
        ["👥 Users List", "📈 Total Users"],
        ["❌ Close Panel"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

def get_user_keyboard():
    keyboard = [["🔍 Search Number"]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    first_name = update.effective_user.first_name
    
    users.add(user_id)
    save_users(users)
    save_user_info(user_id, username, first_name)
    
    text = f"🚀 Welcome {first_name}!\n\nSend any 10-digit mobile number\n\n🔍 I'll show you the details!"
    
    if is_admin(user_id):
        await update.message.reply_text(text, reply_markup=get_admin_keyboard())
    else:
        await update.message.reply_text(text, reply_markup=get_user_keyboard())

async def handle_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    first_name = update.effective_user.first_name
    text = update.message.text.strip()
    
    users.add(user_id)
    save_users(users)
    save_user_info(user_id, username, first_name)
    
    # ========== BROADCAST MODE ==========
    if is_admin(user_id) and context.user_data.get('broadcast_mode'):
        if text == "/cancel":
            context.user_data['broadcast_mode'] = False
            await update.message.reply_text("❌ Broadcast cancelled!", reply_markup=get_admin_keyboard())
            return
        
        await update.message.reply_text(f"⏳ Broadcasting to {len(users)} users...")
        success = 0
        failed = 0
        for uid in users:
            try:
                await context.bot.send_message(chat_id=uid, text=f"📢 Announcement\n━━━━━━━━━━\n\n{text}")
                success += 1
            except:
                failed += 1
        await update.message.reply_text(f"✅ Broadcast Complete!\n\n✅ Success: {success}\n❌ Failed: {failed}", reply_markup=get_admin_keyboard())
        context.user_data['broadcast_mode'] = False
        return
    
    # ========== ADMIN BUTTONS ==========
    if is_admin(user_id):
        if text == "📊 Stats":
            await update.message.reply_text(f"📊 Stats\n━━━━━━━━\n👥 Users: {len(users)}", reply_markup=get_admin_keyboard())
            return
        elif text == "📈 Total Users":
            await update.message.reply_text(f"📈 Total Users: {len(users)}", reply_markup=get_admin_keyboard())
            return
        elif text == "👥 Users List":
            if users:
                lines = []
                for uid in list(users)[:30]:
                    uid_str = str(uid)
                    if uid_str in user_details:
                        info = user_details[uid_str]
                        lines.append(f"ID: {uid}\nName: {info.get('first_name')}\nUsername: @{info.get('username')}")
                    else:
                        lines.append(f"ID: {uid}")
                result_text = "\n\n".join(lines)
                await update.message.reply_text(result_text[:4000], reply_markup=get_admin_keyboard())
            else:
                await update.message.reply_text("No users yet!", reply_markup=get_admin_keyboard())
            return
        elif text == "📢 Broadcast":
            await update.message.reply_text("📢 Send your broadcast message:", reply_markup=get_admin_keyboard())
            context.user_data['broadcast_mode'] = True
            return
        elif text == "❌ Close Panel":
            await update.message.reply_text("✅ Panel Closed!", reply_markup=get_user_keyboard())
            return
    
    # ========== SEARCH BUTTON ==========
    if text == "🔍 Search Number":
        context.user_data['waiting_for_number'] = True
        await update.message.reply_text("🔍 Enter 10-digit mobile number:\nExample: 9826658110")
        return
    
    # ========== WAITING FOR NUMBER ==========
    if context.user_data.get('waiting_for_number'):
        if text.isdigit() and len(text) >= 10:
            mobile = text[-10:]
            context.user_data['waiting_for_number'] = False
            await update.message.reply_text(f"⏳ Searching...")
            data = lookup_number(mobile)
            if data:
                await update.message.reply_text(format_result(data, mobile))
            else:
                await update.message.reply_text(f"❌ No results for {mobile}")
        else:
            await update.message.reply_text("❌ Send valid 10-digit number!")
        return
    
    # ========== DIRECT NUMBER SEARCH ==========
    if text.isdigit() and len(text) >= 10:
        mobile = text[-10:]
        await update.message.reply_text(f"⏳ Searching...")
        data = lookup_number(mobile)
        if data:
            await update.message.reply_text(format_result(data, mobile))
        else:
            await update.message.reply_text(f"❌ No results for {mobile}")
        return
    
    # ========== INVALID ==========
    if not is_admin(user_id):
        await update.message.reply_text("❌ Send 10-digit mobile number!", reply_markup=get_user_keyboard())

def main():
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN not set!")
        return
    if ADMIN_ID == 0:
        print("❌ ADMIN_ID not set!")
        return
    
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages))
    
    print("🤖 Bot is running on Railway!")
    app.run_polling()

if __name__ == "__main__":
    main()
