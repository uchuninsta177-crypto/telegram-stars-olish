import json
import logging
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

# Loggingni sozlash
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = -1004457471821
ADMIN_ID = 8061937333

# KARTA REKVIZITLARI
BANK_NAME = "Kapitalbank"
CARD_NUMBER = "8600 0000 0000 0000"
CARD_HOLDER = "F.I.SH"

# State'lar (Bosqichlar)
(
    WAIT_ADD_USER,
    WAIT_ADD_AMOUNT,
    WAIT_REMOVE_USER,
    WAIT_REMOVE_AMOUNT,
    WAIT_TARGET_USERNAME,
    WAIT_TOPUP_AMOUNT,
    WAIT_RECEIPT_CLICK,
    WAIT_RECEIPT_PHOTO,
) = range(8)

# Sovg'alar bazasi
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

# Universal bekor qilish tugmasi
CANCEL_KEYBOARD = InlineKeyboardMarkup(
    [[InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_action")]]
)


# Bosh menyu chiqaruvchi yordamchi funksiya
async def send_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, text_prefix: str = ""):
    user = update.effective_user
    user_balance = get_balance(user.id)

    keyboard = [
        [
            InlineKeyboardButton(
                "⭐️ Stars olish",
                web_app=WebAppInfo(
                    url="https://uchuninsta177-crypto.github.io/telegram-stars-olish/"
                ),
            )
        ],
        [InlineKeyboardButton("🎁 Gift olish", callback_data="show_gifts")],
        [InlineKeyboardButton("💳 Balans to'ldirish", callback_data="topup_balance")],
    ]

    if user.id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("⚙️ Admin Panel", callback_data="admin_panel")])

    msg_text = f"{text_prefix}Salom, {user.first_name}! 👋\n\n💳 **Balansingiz:** {user_balance:,} so'm\n\nKerakli xizmatni tanlang:"

    if update.callback_query:
        await update.callback_query.message.reply_text(
            msg_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            msg_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )


# Bekor qilish tugmasi bosilganda bosh sahifaga qaytarish
async def cancel_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    
    try:
        await query.message.delete()
    except Exception:
        pass

    await send_main_menu(update, context, text_prefix="❌ Amaliyot bekor qilindi.\n\n")
    return ConversationHandler.END


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

    await send_main_menu(update, context)


# 1-BOSQICH: Balans to'ldirish summasini so'rash
async def topup_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.message.reply_text(
        "💵 **To'lov miqdorini kiriting:**\n\n"
        "Minimal summa: **3,500 so'm**\n\n"
        "*(Faqat raqamda kiriting, masalan: 5000)*",
        parse_mode="Markdown",
        reply_markup=CANCEL_KEYBOARD
    )
    return WAIT_TOPUP_AMOUNT


# 2-BOSQICH: Summa tekshiriladi va Rekvizitlar ko'rsatiladi
async def process_topup_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().replace(" ", "").replace(",", "")

    if not text.isdigit():
        await update.message.reply_text(
            "❌ **Iltimos, faqat raqam kiriting!**\n\nMasalan: 5000",
            parse_mode="Markdown",
            reply_markup=CANCEL_KEYBOARD
        )
        return WAIT_TOPUP_AMOUNT

    amount = int(text)

    if amount < 3500:
        await update.message.reply_text(
            "❌ **Xatolik:** Minimal balans to'ldirish summasi **3,500 so'm**",
            parse_mode="Markdown",
            reply_markup=CANCEL_KEYBOARD
        )
        return WAIT_TOPUP_AMOUNT

    # Summani saqlaymiz
    context.user_data["topup_amount"] = amount

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🧾 Chek yuborish", callback_data="send_receipt")],
        [InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_action")]
    ])

    await update.message.reply_text(
        f"💳 **Hisobni to'ldirish**\n\n"
        f"💰 **Summa:** {amount:,} so'm\n\n"
        f"🏦 **Bank:** {BANK_NAME}\n"
        f"💳 **Karta raqami:** `{CARD_NUMBER}`\n"
        f"👤 **Karta egasi:** {CARD_HOLDER}\n\n"
        f"⏳ To'lov qilib bo'lgach **'Chek yuborish'** orqali chekni yuborishingiz mumkin.\n\n"
        f"‼️ *Eslatma: 30 daqiqa ichida chek yubormasangiz pulingiz tushmay qolishi mumkin!*",
        parse_mode="Markdown",
        reply_markup=keyboard
    )
    return WAIT_RECEIPT_CLICK


# 3-BOSQICH: 'Chek yuborish' tugmasi bosilganda
async def ask_for_receipt_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.message.reply_text(
        "📸 **To'lov chekining rasmini yuboring:**",
        reply_markup=CANCEL_KEYBOARD
    )
    return WAIT_RECEIPT_PHOTO


# 4-BOSQICH: Matn yuborilganda beriladigan xatolik
async def invalid_receipt_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❌ **Xatolik:** Iltimos, faqat rasm (chek) yuboring!",
        reply_markup=CANCEL_KEYBOARD
    )
    return WAIT_RECEIPT_PHOTO


# 5-BOSQICH: Chek rasmi qabul qilindi -> Adminga yuboriladi
async def process_receipt_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Eng yuqori sifatli rasmni olish
    photo_file_id = update.message.photo[-1].file_id
    user = update.effective_user
    amount = context.user_data.get("topup_amount", 0)

    admin_caption = (
        "💳 **Yangi Balans To'ldirish So'rovi!**\n\n"
        f"👤 **Foydalanuvchi:** {user.full_name}\n"
        f"🆔 **User ID:** `{user.id}`\n"
        f"🏷 **Username:** @{user.username or 'yo_q'}\n"
        f"💰 **Kutilayotgan summa:** {amount:,} so'm"
    )

    # Adminga rasm (chek) va matnni birga yuborish
    await context.bot.send_photo(
        chat_id=GROUP_ID,
        photo=photo_file_id,
        caption=admin_caption,
        parse_mode="Markdown"
    )

    await update.message.reply_text(
        "✅ **To'lov cheki qabul qilindi!**\n\n"
        "Administrator chekni tekshirib chiqib, tez orada balansingizni to'ldirib beradi.",
        parse_mode="Markdown"
    )

    # Bosh sahifaga qaytarish
    await send_main_menu(update, context)
    context.user_data.clear()
    return ConversationHandler.END


# Gift va Menyular uchun handlerlar
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
            "👇 **Biror giftni tanlang:**",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="Markdown"
        )


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


async def ask_username_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    buy_key = query.data.replace("buy_", "")
    context.user_data["selected_gift_key"] = buy_key

    await query.message.reply_text(
        "✏️ Gift yuborilishi kerak bo'lgan Telegram Username (nikingiz)ni kiriting:\n\n"
        "*(Masalan: @username)*\n\n"
        "‼️ **Eslatma:** Username'ni to'g'ri kiritganingizga ishonch hosil qiling, aks holda pulingiz qaytarib berilmaydi!",
        parse_mode="Markdown",
        reply_markup=CANCEL_KEYBOARD
    )
    return WAIT_TARGET_USERNAME


async def process_gift_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target_username = update.message.text.strip()
    user = update.effective_user
    buy_key = context.user_data.get("selected_gift_key")

    if not buy_key or buy_key not in GIFTS_DB:
        await update.message.reply_text("❌ Xatolik yuz berdi. Qaytadan urinib ko'ring.")
        return ConversationHandler.END

    gift_name, stars, price_som_str = GIFTS_DB[buy_key]
    price_som = int(price_som_str.replace(",", "").replace(" ", ""))

    user_balance = get_balance(user.id)

    if user_balance < price_som:
        keyboard = [
            [InlineKeyboardButton("💳 Balans to'ldirish", callback_data="topup_balance")],
            [InlineKeyboardButton("🎁 Giftlar bo'limi", callback_data="show_gifts")]
        ]
        await update.message.reply_text(
            f"❌ **Mablag' yetarli emas!**\n\n"
            f"🎁 Gift narxi: {price_som:,} so'm\n"
            f"💳 Sizning balansingiz: {user_balance:,} so'm\n\n"
            f"Iltimos, balansingizni to'ldiring va qaytadan urinib ko'ring.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return ConversationHandler.END

    add_balance(user.id, -price_som)
    new_balance = get_balance(user.id)

    text = (
        "🎁 **Yangi Gift Xarid Qilindi!**\n\n"
        f"👤 **Xaridor ID:** `{user.id}` (@{user.username or 'No_Username'})\n"
        f"📩 **Qabul qiluvchi Username:** {target_username}\n"
        f"🎁 **Gift:** {gift_name}\n"
        f"💰 **Yechildi:** {price_som:,} so'm\n"
        f"💳 **Qolgan balansi:** {new_balance:,} so'm"
    )
    await context.bot.send_message(chat_id=GROUP_ID, text=text, parse_mode="Markdown")

    await update.message.reply_text(
        f"✅ **Buyurtmangiz qabul qilindi!**\n\n"
        f"📩 **Kiritilgan Username:** {target_username}\n"
        f"🎁 **Gift:** {gift_name}\n"
        f"💰 **Yechilgan summa:** {price_som:,} so'm\n"
        f"💳 **Qolgan balansingiz:** {new_balance:,} so'm\n\n"
        f"Administrator tez orada sovg'angizni yetkazib beradi.",
        parse_mode="Markdown"
    )

    await send_main_menu(update, context)
    return ConversationHandler.END


async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        await query.message.delete()
    except Exception:
        pass
    await send_main_menu(update, context)


async def webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = json.loads(update.effective_message.web_app_data.data)

    text = (
        "🛒 **Yangi Stars Buyurtmasi!**\n\n"
        f"👤 **Username:** @{data['username']}\n"
        f"⭐️ **Stars:** {data['stars']}\n"
        f"💰 **Jami:** {data['total']:,} so'm"
    )

    await context.bot.send_message(chat_id=GROUP_ID, text=text, parse_mode="Markdown")


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    keyboard = [
        [InlineKeyboardButton("➕ Balans qo'shish", callback_data="add_balance")],
        [InlineKeyboardButton("➖ Balans ayirish", callback_data="remove_balance")],
        [InlineKeyboardButton("⬅️ Bosh menyu", callback_data="back_to_main")],
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

    await query.message.reply_text("👤 User ID yuboring:", reply_markup=CANCEL_KEYBOARD)
    return WAIT_ADD_USER


async def receive_add_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["target_user"] = int(update.message.text)
    except ValueError:
        await update.message.reply_text("❌ Faqat User ID (son) yuboring.", reply_markup=CANCEL_KEYBOARD)
        return WAIT_ADD_USER

    await update.message.reply_text("💰 Qo'shiladigan summani yuboring:", reply_markup=CANCEL_KEYBOARD)
    return WAIT_ADD_AMOUNT


async def receive_add_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = int(update.message.text)
    except ValueError:
        await update.message.reply_text("❌ Faqat son kiriting.", reply_markup=CANCEL_KEYBOARD)
        return WAIT_ADD_AMOUNT

    user_id = context.user_data["target_user"]
    add_balance(user_id, amount)
    balance = get_balance(user_id)

    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"🎉 **Balansingiz to'ldirildi!**\n\n➕ **Qo'shildi:** {amount:,} so'm\n💳 **Jami balans:** {balance:,} so'm",
            parse_mode="Markdown"
        )
    except Exception:
        pass

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

    await query.message.reply_text("👤 User ID yuboring:", reply_markup=CANCEL_KEYBOARD)
    return WAIT_REMOVE_USER


async def receive_remove_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["target_user"] = int(update.message.text)
    except ValueError:
        await update.message.reply_text("❌ Faqat User ID (son) yuboring.", reply_markup=CANCEL_KEYBOARD)
        return WAIT_REMOVE_USER

    await update.message.reply_text("💰 Ayiriladigan summani yuboring:", reply_markup=CANCEL_KEYBOARD)
    return WAIT_REMOVE_AMOUNT


async def receive_remove_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = int(update.message.text)
    except ValueError:
        await update.message.reply_text("❌ Faqat son kiriting.", reply_markup=CANCEL_KEYBOARD)
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

    common_fallbacks = [CallbackQueryHandler(cancel_action, pattern="^cancel_action$")]

    # Balans to'ldirish va Chek tekshirish suhbati
    topup_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(topup_start, pattern="^topup_balance$")],
        states={
            WAIT_TOPUP_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_topup_amount)
            ],
            WAIT_RECEIPT_CLICK: [
                CallbackQueryHandler(ask_for_receipt_photo, pattern="^send_receipt$")
            ],
            WAIT_RECEIPT_PHOTO: [
                MessageHandler(filters.PHOTO, process_receipt_photo),
                MessageHandler(filters.TEXT & ~filters.COMMAND, invalid_receipt_text),
            ],
        },
        fallbacks=common_fallbacks,
    )

    # Gift xarid qilish suhbati
    buy_gift_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(ask_username_start, pattern="^buy_")],
        states={
            WAIT_TARGET_USERNAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_gift_purchase)
            ],
        },
        fallbacks=common_fallbacks,
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(topup_handler)
    app.add_handler(buy_gift_handler)
    app.add_handler(CallbackQueryHandler(show_gifts, pattern="^show_gifts$"))
    app.add_handler(CallbackQueryHandler(select_gift_category, pattern="^cat_"))
    app.add_handler(CallbackQueryHandler(show_gift_details, pattern="^item_"))
    app.add_handler(CallbackQueryHandler(back_to_main, pattern="^back_to_main$"))
    app.add_handler(CallbackQueryHandler(admin_panel, pattern="^admin_panel$"))

    # Admin: Add balance
    app.add_handler(
        ConversationHandler(
            entry_points=[CallbackQueryHandler(add_balance_start, pattern="^add_balance$")],
            states={
                WAIT_ADD_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_add_user)],
                WAIT_ADD_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_add_amount)],
            },
            fallbacks=common_fallbacks,
        )
    )

    # Admin: Remove balance
    app.add_handler(
        ConversationHandler(
            entry_points=[CallbackQueryHandler(remove_balance_start, pattern="^remove_balance$")],
            states={
                WAIT_REMOVE_USER: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, receive_remove_user)
                ],
                WAIT_REMOVE_AMOUNT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, receive_remove_amount)
                ],
            },
            fallbacks=common_fallbacks,
        )
    )

    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, webapp_data))

    print("🤖 Bot ishga tushdi...")
    app.run_polling()
