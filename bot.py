import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import json

TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name

    keyboard = [
    [
        InlineKeyboardButton(
            "⭐ Stars olish",
            web_app=WebAppInfo(url="https://uchuninsta177-crypto.github.io/telegram-stars-olish/")
        )
    ],
    [
        InlineKeyboardButton(
            "💎 Premium olish",
            web_app=WebAppInfo(url="https://uchuninsta177-crypto.github.io/telegram-stars-olish/")
        )
    ]
]

    reply_markup = InlineKeyboardMarkup(keyboard)   
    await update.message.reply_text(
    f"Salom, {user}! 👋\n\nKerakli xizmatni tanlang:",
    reply_markup=reply_markup
)

async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Chat ID:", update.effective_chat.id)

async def webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):

    data = json.loads(update.effective_message.web_app_data.data)

    text = (
        "🛒 Yangi buyurtma\n\n"
        f"👤 Username: {data['username']}\n"
        f"⭐ Stars: {data['stars']}\n"
        f"💰 Jami: {data['total']:,} so'm"
    )

    await context.bot.send_message(
        chat_id=-1004457471821,
        text=text
    )
    
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.ALL, get_chat_id))

app.add_handler(
    
    MessageHandler(filters.StatusUpdate.WEB_APP_DATA, webapp_data)
)

print("Bot ishga tushdi...")

app.run_polling()
