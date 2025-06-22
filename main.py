from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from flask import Flask
from threading import Thread
import requests
import os

# === In-memory data (clears on restart) ===
user_data = {}

# === API Endpoint ===
API_URL = "https://9e82a7cf-97bd-4238-b172-a7870d7aeba6-00-1db4jxtpvh62r.pike.replit.dev/attendance"

# === Flask Server to Keep Replit Alive ===
app = Flask('')

@app.route('/')
def home():
    return "✅ LNCTU Attendance Bot is running."

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# === Telegram Bot Handlers ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to LNCTU Attendance Bot!\n\n"
        "Use:\n"
        "`/set_username your_id`\n"
        "`/set_password your_pass`\n"
        "Then send `.` to get your attendance.",
        parse_mode="Markdown"
    )

async def set_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if context.args:
        user_data.setdefault(uid, {})['username'] = context.args[0]
        await update.message.reply_text("✅ Username saved.")
    else:
        await update.message.reply_text("⚠️ Usage: /set_username 11111531351")

async def set_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if context.args:
        user_data.setdefault(uid, {})['password'] = context.args[0]
        await update.message.reply_text("✅ Password saved.")
    else:
        await update.message.reply_text("⚠️ Usage: /set_password Ayush123")

async def handle_dot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    creds = user_data.get(uid)

    if not creds or 'username' not in creds or 'password' not in creds:
        await update.message.reply_text("⚠️ Please set both username and password first.")
        return

    await update.message.reply_text("⏳ Fetching attendance...")
    try:
        res = requests.get(API_URL, params={
            "username": creds["username"],
            "password": creds["password"]
        }, timeout=15)

        data = res.json()
        if data.get("success") and "data" in data:
            d = data["data"]
            msg = f"""📊 *LNCTU Attendance Summary*:

✅ *Present:* {d['attended_classes']}
❌ *Absent:* {d['absent']}
📘 *Total Classes:* {d['total_classes']}
📈 *Percentage:* {d['overall_percentage']}%
🕒 *Last Updated:* `{d['last_updated']}`"""
            await update.message.reply_text(msg, parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ API error:\n" + data.get("message", "Unknown issue."))

    except Exception as e:
        await update.message.reply_text(f"❌ Error:\n{str(e)}")

# === Main Entry Point ===
if __name__ == "__main__":
    keep_alive()  # Start the Flask server in the background

    # Get your bot token from environment (Replit secrets)
    TOKEN = os.environ.get("BOT_TOKEN") or "PASTE-YOUR-TOKEN-HERE"

    # Build the Telegram bot
    app_bot = ApplicationBuilder().token(TOKEN).build()

    # Add all your handlers
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("set_username", set_username))
    app_bot.add_handler(CommandHandler("set_password", set_password))
    app_bot.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^\.$'), handle_dot))

    print("✅ Bot running...")
    app_bot.run_polling()  # Start the bot polling (main thread)
