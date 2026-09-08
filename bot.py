import json
import os
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

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = -1004457471821
ADMIN_ID = 8061937333

WAIT_ADD_USER, WAIT_ADD_AMOUNT, WAIT_REMOVE_USER, WAIT_REMOVE_AMOUNT = range(4)

# Sovg'alar bazasi: (Gift nomi + stars ko'rinishi, Stars soni, So'm narxi)
GIFTS_DB = {
    "item_heart_15": ("💝 Yurak (15 stars)", 15, "3500"),
    "item_bear_15": ("🧸 Ayiqcha (15 stars)", 15, "3500"),
    "item_rose_25": ("🌹 Atirgul (25 stars)", 25, "5500"),
    "item_box_25": ("🎁 Sovg'a quti (25 stars)", 25, "5500"),
    "item_bouquet_50": ("💐 Buket (50 stars)", 50, "11000"),
    "item_cake_50": ("🎂 Tort (50 stars)", 50, "11000"),
    "item_champagne_50": ("🍾 Shampan (50 stars)", 50, "11000"),
    "item_rocket_50": ("🚀 Raketa (50 stars)", 50, "11000"),
    "item_ring_100": ("💍 Uzuk (100 stars)", 100, "22000"),
    "item_trophy_100": ("🏆 Kubok (100 stars)", 100, "22000"),
    "item_diamond_100": ("💎 Olmos (100 stars)", 100, "22000")
}


# /start handleri
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
                "🎁 Gift olish", callback_data="show_gifts"
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


# 1-BOSQICH: Gift kategoriyalarini ko'rsatish
async def show_gifts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("💝 🧸 (15 Stars)", callback_data="cat_15")],
        [InlineKeyboardButton("🌹 🎁 (25 Stars)", callback_data="cat_25")],
        [InlineKeyboardButton("💐 🎂 🍾 🚀 (50 Stars)", callback_data="cat_50")],
        [InlineKeyboardButton("💍 🏆 💎 (100 Stars)", callback_data="cat_100")],
        [InlineKeyboardButton("⬅️ Orqaga", callback_data="back_to_main")]
    ]

    await query.edit_message_text(
        "🎁 **Biror gift turini tanlang:**",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


# 2-BOSQICH: Kategoriya bosilganda ichidagi sovg'alarni chiqarish
async def select_gift_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    category = query.data

    category_items = {
        "cat_15": [
            InlineKeyboardButton("💝 Yurak", callback_data="item_heart_15"),
            InlineKeyboardButton("🧸 Ayiqcha", callback_data="item_bear_15")
        ],
        "cat_25": [
            InlineKeyboardButton("🌹 Atirgul", callback_data="item_rose_25"),
            InlineKeyboardButton("🎁 Sovg'a quti", callback_data="item_box_25")
        ],
        "cat_50": [
            InlineKeyboardButton("💐 Buket", callback_data="item_bouquet_50"),
            InlineKeyboardButton("🎂 Tort", callback_data="item_cake_50"),
            InlineKeyboardButton("🍾 Shampan", callback_data="item_champagne_50"),
            InlineKeyboardButton("🚀 Raketa", callback_data="item_rocket_50")
        ],
        "cat_100": [
            InlineKeyboardButton("💍 Uzuk", callback_data="item_ring_100"),
            InlineKeyboardButton("🏆 Kubok", callback_data="item_trophy_100"),
            InlineKeyboardButton("💎 Olmos", callback_data="item_diamond_100")
        ]
    }

    if category in category_items:
        buttons = [[btn] for btn in category_items[category]]
        buttons.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="show_gifts")])

        await query.edit_message_text(
            "👇 **Biror birini tanlang:**",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="Markdown"
        )


# 3-BOSQICH: Sovg'a tanlanganda tafsilotlarini va sotib olish tugmasini ko'rsatish
async def show_gift_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    item_key = query.data
    if item_key in GIFTS_DB:
        gift_name, stars, price_som = GIFTS_DB[item_key]

        cat_code = f"cat_{stars}"

        keyboard = [
            [InlineKeyboardButton("✅ Sotib olish", callback_data=f"buy_{item_key}")],
            [InlineKeyboardButton("⬅️ Orqaga", callback_data=cat_code)]
        ]

        await query.edit_message_text(
            f"🎁 **Siz tanlagan gift:** {gift_name}\n"
            f"⭐️ **Narxi:** {price_som} so'm\n\n"
            f"Sotib olishni tasdiqlaysizmi?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )


# 4-BOSQICH: Sotib olish tugmasi bosilganda
async def confirm_buy_gift(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    buy_key = query.data.replace("buy_", "")
    if buy_key in GIFTS_DB:
        gift_name, stars, price_som = GIFTS_DB[buy_key]
        user = query.from_user

        text = (
            "🎁 **Yangi Gift Buyurtma!**\n\n"
            f"👤 **Foydalanuvchi:** @{user.username or 'No_Username'}\n"
            f"🆔 **User ID:** `{user.id}`\n"
            f"🎁 **Gift:** {gift_name}\n"
            f"⭐️ **Narxi:** {price_som} so'm"
        )

        await context.bot.send_message(chat_id=GROUP_ID, text=text, parse_mode="Markdown")

        keyboard = [[InlineKeyboardButton("⬅️ Bosh menyuga qaytish", callback_data="back_to_main")]]

        await query.edit_message_text(
            f"✅ **Buyurtmangiz qabul qilindi!**\n\n"
            f"🎁 **Siz tanlagan gift:** {gift_name}\n"
            f"⭐️ **Narxi:** {price_som} so'm\n\n"
            f"Administrator tez orada siz bilan bog'lanadi.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )


# Bosh menyuga qaytish
async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user

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
                "🎁 Gift olish", callback_data="show_gifts"
            )
        ],
    ]

    if user.id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("⚙️ Admin Panel", callback_data="admin_panel")])

    await query.edit_message_text(
        f"Salom, {user.first_name}! 👋\n\nKerakli xizmatni tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# Stars WebApp ma'lumotlarini qabul qilish
async def webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = json.loads(update.effective_message.web_app_data.data)

    text = (
        "🛒 **Yangi Stars Buyurtmasi!**\n\n"
        f"👤 **Username:** @{data['username']}\n"
        f"⭐️ **Stars:** {data['stars']}\n"
        f"💰 **Jami:** {data['total']:,} so'm"
    )

    await context.bot.send_message(chat_id=GROUP_ID, text=text, parse_mode="Markdown")


# Admin panel
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    keyboard = [
        [InlineKeyboardButton("➕ Balans qo'shish", callback_data="add_balance")],
        [InlineKeyboardButton("➖ Balans ayirish", callback_data="remove_balance")],
    ]

    await query.edit_message_text(
        "⚙️ Admin Panel\n\nKerakli bo'limni tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# Balans qo'shish
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


# Balans ayirish
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
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(show_gifts, pattern="^show_gifts$"))
    app.add_handler(CallbackQueryHandler(select_gift_category, pattern="^cat_"))
    app.add_handler(CallbackQueryHandler(show_gift_details, pattern="^item_"))
    app.add_handler(CallbackQueryHandler(confirm_buy_gift, pattern="^buy_item_"))
    app.add_handler(CallbackQueryHandler(back_to_main, pattern="^back_to_main$"))
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
