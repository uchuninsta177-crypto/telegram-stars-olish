import html
import json
import logging
import os

from database import add_balance, get_balance, init_db
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

# State'lar
(
    WAIT_ADD_USER,
    WAIT_ADD_AMOUNT,
    WAIT_REMOVE_USER,
    WAIT_REMOVE_AMOUNT,
    WAIT_TARGET_USERNAME,
    WAIT_TOPUP_AMOUNT,
    WAIT_RECEIPT_PHOTO,
) = range(7)

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

CANCEL_KEYBOARD = InlineKeyboardMarkup(
    [[InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_action")]]
)

async def send_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, text_prefix: str = ""):
    user = update.effective_user
    user_balance = get_balance(user.id)

    # WebApp URL va balans parametri
    web_app_url = f"https://uchuninsta177-crypto.github.io/telegram-stars-olish/?balance={user_balance}"

    keyboard = [
        [
            InlineKeyboardButton(
                "⭐️ Stars olish",
                web_app=WebAppInfo(url=web_app_url),
            )
        ],
        [InlineKeyboardButton("🎁 Gift olish", callback_data="show_gifts")],
        [InlineKeyboardButton("💳 Balans to'ldirish", callback_data="topup_balance")],
    ]

    if user.id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("⚙️ Admin Panel", callback_data="admin_panel")])

    msg_text = f"{text_prefix}Salom, <b>{html.escape(user.first_name)}</b>! 👋\n\n💳 <b>Balansingiz:</b> {user_balance:,} so'm\n\nKerakli xizmatni tanlang:"

    if update.callback_query:
        await update.callback_query.message.reply_text(
            msg_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            msg_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_balance(user.id, 0)
    await send_main_menu(update, context)

async def topup_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.message.reply_text(
        "💵 <b>To'lov miqdorini kiriting:</b>\n\n"
        "Minimal summa: <b>3,500 so'm</b>\n\n"
        "<i>(Faqat raqamda kiriting, masalan: 5000)</i>",
        parse_mode="HTML",
        reply_markup=CANCEL_KEYBOARD
    )
    return WAIT_TOPUP_AMOUNT

async def process_topup_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().replace(" ", "").replace(",", "")

    if not text.isdigit():
        await update.message.reply_text(
            "❌ <b>Iltimos, faqat raqam kiriting!</b>\n\nMasalan: 5000",
            parse_mode="HTML",
            reply_markup=CANCEL_KEYBOARD
        )
        return WAIT_TOPUP_AMOUNT

    amount = int(text)

    if amount < 3500:
        await update.message.reply_text(
            "❌ <b>Xatolik:</b> Minimal balans to'ldirish summasi <b>3,500 so'm</b>",
            parse_mode="HTML",
            reply_markup=CANCEL_KEYBOARD
        )
        return WAIT_TOPUP_AMOUNT

    context.user_data["topup_amount"] = amount

    await update.message.reply_text(
        f"💳 <b>Hisobni to'ldirish</b>\n\n"
        f"💰 <b>Summa:</b> {amount:,} so'm\n\n"
        f"🏦 <b>Bank:</b> {BANK_NAME}\n"
        f"💳 <b>Karta raqami:</b> <code>{CARD_NUMBER}</code>\n"
        f"👤 <b>Karta egasi:</b> {CARD_HOLDER}\n\n"
        f"📸 <b>To'lov qilib bo'lgach, to'lov cheki rasmini shu yerga yuboring:</b>\n\n"
        f"‼️ <i>Eslatma: 30 daqiqa ichida chek yubormasangiz pulingiz tushmay qolishi mumkin!</i>",
        parse_mode="HTML",
        reply_markup=CANCEL_KEYBOARD
    )
    return WAIT_RECEIPT_PHOTO

async def invalid_receipt_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❌ <b>Xatolik:</b> Iltimos, faqat rasm (chek) yuboring!",
        parse_mode="HTML",
        reply_markup=CANCEL_KEYBOARD
    )
    return WAIT_RECEIPT_PHOTO

async def process_receipt_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_file_id = update.message.photo[-1].file_id
    user = update.effective_user
    amount = context.user_data.get("topup_amount", 0)

    user_username = f"@{user.username}" if user.username else "yo'q"

    admin_caption = (
        "💳 <b>Yangi Balans To'ldirish So'rovi!</b>\n\n"
        f"👤 <b>Foydalanuvchi:</b> {html.escape(user.full_name)}\n"
        f"🆔 <b>User ID:</b> <code>{user.id}</code>\n"
        f"🏷 <b>Username:</b> {html.escape(user_username)}\n"
        f"💰 <b>Kutilayotgan summa:</b> {amount:,} so'm"
    )

    try:
        await context.bot.send_photo(
            chat_id=GROUP_ID,
            photo=photo_file_id,
            caption=admin_caption,
            parse_mode="HTML"
        )
    except Exception as e:
        logging.error(f"Adminga rasm yuborishda xatolik: {e}")

    await update.message.reply_text(
        "✅ <b>To'lov cheki qabul qilindi!</b>\n\n"
        "Administrator chekni tekshirib chiqib, tez orada balansingizni to'ldirib beradi.",
        parse_mode="HTML"
    )

    await send_main_menu(update, context)
    context.user_data.clear()
    return ConversationHandler.END

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
    await query.edit_message_text("🎁 <b>Biror gift turini tanlang:</b>", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

async def select_gift_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    category = query.data
    category_items = {
        "cat_15": [InlineKeyboardButton("💝 Yurak", callback_data="item_heart_15"), InlineKeyboardButton("🧸 Ayiqcha", callback_data="item_bear_15")],
        "cat_25": [InlineKeyboardButton("🌹 Atirgul", callback_data="item_rose_25"), InlineKeyboardButton("🎁 Sovg'a quti", callback_data="item_box_25")],
        "cat_50": [InlineKeyboardButton("💐 Buket", callback_data="item_bouquet_50"), InlineKeyboardButton("🎂 Tort", callback_data="item_cake_50"), InlineKeyboardButton("🍾 Shampan", callback_data="item_champagne_50"), InlineKeyboardButton("🚀 Raketa", callback_data="item_rocket_50")],
        "cat_100": [InlineKeyboardButton("💍 Uzuk", callback_data="item_ring_100"), InlineKeyboardButton("🏆 Kubok", callback_data="item_trophy_100"), InlineKeyboardButton("💎 Olmos", callback_data="item_diamond_100")]
    }
    if category in category_items:
        buttons = [[btn] for btn in category_items[category]]
        buttons.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="show_gifts")])
        await query.edit_message_text("👇 <b>Biror giftni tanlang:</b>", reply_markup=InlineKeyboardMarkup(buttons), parse_mode="HTML")

async def show_gift_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    item_key = query.data
    if item_key in GIFTS_DB:
        gift_name, stars, price_som = GIFTS_DB[item_key]
        keyboard = [[InlineKeyboardButton("✅ Sotib olish", callback_data=f"buy_{item_key}")], [InlineKeyboardButton("⬅️ Orqaga", callback_data=f"cat_{stars}")]]
        await query.edit_message_text(
            f"🎁 <b>Siz tanlagan gift:</b> {gift_name}\n⭐️ <b>Narxi:</b> {price_som} so'm\n\nSotib olishni tasdiqlaysizmi?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )

async def ask_username_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    gift_key = query.data.replace("buy_", "")
    context.user_data["selected_gift_key"] = gift_key
    await query.message.reply_text(
        "✏️ Gift yuborilishi kerak bo'lgan Telegram Username (nikingiz)ni kiriting:\n\n<i>(Masalan: @username)</i>",
        parse_mode="HTML",
        reply_markup=CANCEL_KEYBOARD
    )
    return WAIT_TARGET_USERNAME

async def process_gift_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target_username = update.message.text.strip()
    if not target_username.startswith("@"):
        target_username = f"@{target_username}"

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
            f"❌ <b>Mablag' yetarli emas!</b>\n\n🎁 Gift narxi: {price_som:,} so'm\n💳 Sizning balansingiz: {user_balance:,} so'm",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        return ConversationHandler.END

    # Balansdan ayirish
    add_balance(user.id, -price_som)
    new_balance = get_balance(user.id)

    buyer_username = f"@{user.username}" if user.username else "No_Username"

    text = (
        f"🎁 <b>Yangi Gift Xarid Qilindi!</b>\n\n"
        f"👤 <b>Xaridor ID:</b> <code>{user.id}</code> ({html.escape(buyer_username)})\n"
        f"📩 <b>Qabul qiluvchi Username:</b> {html.escape(target_username)}\n"
        f"🎁 <b>Gift:</b> {gift_name}\n"
        f"💰 <b>Yechildi:</b> {price_som:,} so'm\n"
        f"💳 <b>Qolgan balansi:</b> {new_balance:,} so'm"
    )

    try:
        await context.bot.send_message(chat_id=GROUP_ID, text=text, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Guruhga xabar yuborishda xatolik: {e}")

    await update.message.reply_text(
        f"✅ <b>Buyurtmangiz qabul qilindi!</b>\n\n"
        f"📩 <b>Username:</b> {html.escape(target_username)}\n"
        f"🎁 <b>Gift:</b> {gift_name}\n"
        f"💰 <b>Yechilgan summa:</b> {price_som:,} so'm",
        parse_mode="HTML"
    )

    await send_main_menu(update, context)
    context.user_data.clear()
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
    user = update.effective_user
    data = json.loads(update.effective_message.web_app_data.data)
    total_price = int(data.get('total', 0))
    stars_count = data.get('stars', 0)
    target_user = data.get('username', user.username or "")
    if target_user and not target_user.startswith("@"):
        target_user = f"@{target_user}"

    user_balance = get_balance(user.id)

    if user_balance < total_price:
        await update.message.reply_text(
            f"❌ <b>Mablag' yetarli emas!</b>\n\n"
            f"⭐️ Buyurtma summasi: {total_price:,} so'm\n"
            f"💳 Balansingiz: {user_balance:,} so'm",
            parse_mode="HTML"
        )
        return

    add_balance(user.id, -total_price)
    new_balance = get_balance(user.id)

    buyer_username = f"@{user.username}" if user.username else "yo'q"

    text = (
        f"🛒 <b>Yangi Stars Buyurtmasi!</b>\n\n"
        f"👤 <b>Xaridor:</b> <code>{user.id}</code> ({html.escape(buyer_username)})\n"
        f"🎯 <b>Qabul qiluvchi:</b> {html.escape(target_user)}\n"
        f"⭐️ <b>Stars:</b> {stars_count}\n"
        f"💰 <b>Yechilgan summa:</b> {total_price:,} so'm\n"
        f"💳 <b>Qolgan balans:</b> {new_balance:,} so'm"
    )
    
    try:
        await context.bot.send_message(chat_id=GROUP_ID, text=text, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Guruhga Stars buyurtmasini yuborishda xatolik: {e}")

    await update.message.reply_text(
        f"✅ <b>Stars buyurtmasi qabul qilindi!</b>\n\n⭐️ Stars: {stars_count}\n💰 Summa: {total_price:,} so'm",
        parse_mode="HTML"
    )

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID: return
    keyboard = [
        [InlineKeyboardButton("➕ Balans qo'shish", callback_data="add_balance")],
        [InlineKeyboardButton("➖ Balans ayirish", callback_data="remove_balance")],
        [InlineKeyboardButton("⬅️ Bosh menyu", callback_data="back_to_main")]
    ]
    await query.edit_message_text("⚙️ Admin Panel\n\nKerakli bo'limni tanlang:", reply_markup=InlineKeyboardMarkup(keyboard))

async def add_balance_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID: return ConversationHandler.END
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
        await context.bot.send_message(chat_id=user_id, text=f"🎉 <b>Balansingiz to'ldirildi!</b>\n\n➕ <b>Qo'shildi:</b> {amount:,} so'm\n💳 <b>Jami balans:</b> {balance:,} so'm", parse_mode="HTML")
    except Exception: pass
    await update.message.reply_text(f"✅ Balans qo'shildi!\n\n👤 User ID: {user_id}\n➕ Qo'shildi: {amount:,} so'm\n💳 Yangi balans: {balance:,} so'm")
    return ConversationHandler.END

async def remove_balance_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID: return ConversationHandler.END
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
    await update.message.reply_text(f"✅ Balans ayirildi!\n\n👤 User ID: {user_id}\n➖ Ayirildi: {amount:,} so'm\n💳 Yangi balans: {balance:,} so'm")
    return ConversationHandler.END

if __name__ == "__main__":
    init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    common_fallbacks = [CallbackQueryHandler(cancel_action, pattern="^cancel_action$")]

    topup_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(topup_start, pattern="^topup_balance$")],
        states={
            WAIT_TOPUP_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_topup_amount)
            ],
            WAIT_RECEIPT_PHOTO: [
                MessageHandler(filters.PHOTO, process_receipt_photo),
                MessageHandler(filters.TEXT & ~filters.COMMAND, invalid_receipt_text),
            ],
        },
        fallbacks=common_fallbacks,
    )

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

    app.add_handler(
        ConversationHandler(
            entry_points=[CallbackQueryHandler(remove_balance_start, pattern="^remove_balance$")],
            states={
                WAIT_REMOVE_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_remove_user)],
                WAIT_REMOVE_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_remove_amount)],
            },
            fallbacks=common_fallbacks,
        )
    )

    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, webapp_data))

    print("🤖 Bot ishga tushdi...")
    app.run_polling()
