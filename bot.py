import json
import sqlite3

from database import add_balance, get_balance
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

TOKEN = ("BOT_TOKEN")
GROUP_ID = -1004457471821
ADMIN_ID = 8061937333

WAIT_ADD_USER, WAIT_ADD_AMOUNT, WAIT_REMOVE_USER, WAIT_REMOVE_AMOUNT = range(4)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        balance INTEGER DEFAULT 0
    )
    """)

    cursor.execute(
        """
        INSERT OR IGNORE INTO users(user_id, username)
        VALUES(?, ?)
        """,
        (user.id, user.username or ""),
    )

    conn.commit()
    conn.close()

    keyboard = [
        [
            InlineKeyboardButton(
                "⭐️ Stars olish",
                web_app=WebAppInfo(
                    url="https://uchuninsta177-crypto.github.io/telegram-stars-olish/"
                ),
            )
        ],
        [
            InlineKeyboardButton(
                "💎 Premium olish",
                web_app=WebAppInfo(
                    url="https://uchuninsta177-crypto.github.io/telegram-stars-olish/"
                ),
            )
        ],
    ]

    if user.id == ADMIN_ID:
        keyboard.append(
            [
                InlineKeyboardButton(
                    "⚙️ Admin Panel", callback_data="admin_panel"
                )
            ]
        )

    await update.message.reply_text(
        f"Salom, {user.first_name}! 👋\n\nKerakli xizmatni tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = json.loads(update.effective_message.web_app_data.data)

    text = (
        "🛒 Yangi buyurtma\n\n"
        f"👤 Username: {data['username']}\n"
        f"⭐️ Stars: {data['stars']}\n"
        f"💰 Jami: {data['total']:,} so'm"
    )

    await context.bot.send_message(chat_id=GROUP_ID, text=text)


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    keyboard = [
        [InlineKeyboardButton("➕ Balans qo'shish", callback_data="add_balance")],
        [InlineKeyboardButton("➖ Balans ayirish", callback_data="remove_balance")],
        [InlineKeyboardButton("📦 Buyurtmalar", callback_data="orders")],
    ]

    await query.edit_message_text(
        "⚙️ Admin Panel\n\nKerakli bo'limni tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def add_balance_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return ConversationHandler.END

    await query.message.reply_text("👤 User ID yuboring:")
    return WAIT_ADD_USER


async def receive_add_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["target_user"] = int(update.message.text)
    except ValueError:
        await update.message.reply_text("❌ Faqat User ID (son) yuboring.")
        return WAIT_ADD_USER

    await update.message.reply_text("💰 Qo'shiladigan summani yuboring:")
    return WAIT_ADD_AMOUNT


async def receive_add_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = int(update.message.text)
    except ValueError:
        await update.message.reply_text("❌ Faqat son kiriting.")
        return WAIT_ADD_AMOUNT

    user_id = context.user_data["target_user"]
    add_balance(user_id, amount)
    balance = get_balance(user_id)

    await update.message.reply_text(
        f"✅ Balans qo'shildi!\n\n"
        f"👤 User ID: {user_id}\n"
        f"➕ Qo'shildi: {amount:,} so'm\n"
        f"💳 Yangi balans: {balance:,} so'm"
    )

    return ConversationHandler.END


async def remove_balance_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return ConversationHandler.END

    await query.message.reply_text("👤 User ID yuboring:")
    return WAIT_REMOVE_USER


async def receive_remove_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["target_user"] = int(update.message.text)
    except ValueError:
        await update.message.reply_text("❌ Faqat User ID (son) yuboring.")
        return WAIT_REMOVE_USER

    await update.message.reply_text("💰 Ayiriladigan summani yuboring:")
    return WAIT_REMOVE_AMOUNT


async def receive_remove_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = int(update.message.text)
    except ValueError:
        await update.message.reply_text("❌ Faqat son kiriting.")
        return WAIT_REMOVE_AMOUNT

    user_id = context.user_data["target_user"]

    add_balance(user_id, -amount)
    balance = get_balance(user_id)

    await update.message.reply_text(
        f"✅ Balans ayirildi!\n\n"
        f"👤 User ID: {user_id}\n"
        f"➖ Ayirildi: {amount:,} so'm\n"
        f"💳 Yangi balans: {balance:,} so'm"
    )

    return ConversationHandler.END


if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(admin_panel, pattern="^admin_panel$"))

    app.add_handler(
        ConversationHandler(
            entry_points=[CallbackQueryHandler(add_balance_start, pattern="^add_balance$")],
            states={
                WAIT_ADD_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_add_user)],
                WAIT_ADD_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_add_amount)],
            },
            fallbacks=[],
        )
    )

    app.add_handler(
        ConversationHandler(
            entry_points=[CallbackQueryHandler(remove_balance_start, pattern="^remove_balance$")],
            states={
                WAIT_REMOVE_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_remove_user)],
                WAIT_REMOVE_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_remove_amount)],
            },
            fallbacks=[],
        )
    )

    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, webapp_data))

    print("🤖 Bot ishga tushdi...")
    app.run_polling()
