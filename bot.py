import html
import json
import logging
import os
import warnings

from database import add_balance, get_balance, get_user_id_by_input, init_db
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
from telegram.warnings import PTBUserWarning

warnings.filterwarnings("ignore", category=PTBUserWarning)
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = -1001234567890  # O'zingizning to'g'ri guruh ID-ingizni kiriting (-100 bilan boshlanadi)
ADMIN_ID = 8061937333

BANK_NAME, CARD_NUMBER, CARD_HOLDER = "Kapitalbank", "8600 0000 0000 0000", "F.I.SH"

WAIT_TOPUP_AMOUNT, WAIT_RECEIPT_PHOTO, WAIT_TARGET_USERNAME, WAIT_ADMIN_USER, WAIT_ADMIN_AMOUNT = range(5)

GIFTS_DB = {
    "item_heart_15": ("💝 Yurak (15 stars)", 15, 3500),
    "item_bear_15": ("🧸 Ayiqcha (15 stars)", 15, 3500),
    "item_rose_25": ("🌹 Atirgul (25 stars)", 25, 5500),
    "item_box_25": ("🎁 Sovg'a quti (25 stars)", 25, 5500),
    "item_bouquet_50": ("💐 Buket (50 stars)", 50, 11000),
    "item_cake_50": ("🎂 Tort (50 stars)", 50, 11000),
    "item_champagne_50": ("🍾 Shampan (50 stars)", 50, 11000),
    "item_rocket_50": ("🚀 Raketa (50 stars)", 50, 11000),
    "item_ring_100": ("💍 Uzuk (100 stars)", 100, 22000),
    "item_trophy_100": ("🏆 Kubok (100 stars)", 100, 22000),
    "item_diamond_100": ("💎 Olmos (100 stars)", 100, 22000),
}

CANCEL_KEYBOARD = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_action")]])

async def send_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, text_prefix: str = ""):
    user = update.effective_user
    add_balance(user.id, 0, user.username)
    user_balance = get_balance(user.id)

    web_app_url = f"https://uchuninsta177-crypto.github.io/telegram-stars-olish/?balance={user_balance}"
    keyboard = [
        [InlineKeyboardButton("⭐️ Stars olish", web_app=WebAppInfo(url=web_app_url))],
        [InlineKeyboardButton("🎁 Gift olish", callback_data="show_gifts")],
        [InlineKeyboardButton("💳 Balans to'ldirish", callback_data="topup_balance")],
    ]
    if user.id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("⚙️ Admin Panel", callback_data="admin_panel")])

    msg_text = (
        f"{text_prefix}Salom, <b>{html.escape(user.first_name)}</b>! 👋\n\n"
        f"💳 <b>Balansingiz:</b> {user_balance:,} so'm\n\nKerakli xizmatni tanlang:"
    )

    if update.callback_query:
        await update.callback_query.message.reply_text(msg_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
    else:
        await update.message.reply_text(msg_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

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
    context.user_data.clear()
    await send_main_menu(update, context)
    return ConversationHandler.END

# --- TOPUP FLOW ---
async def topup_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        "💵 <b>To'lov miqdorini kiriting:</b>\n\nMinimal summa: <b>3,500 so'm</b>\n\n<i>(Faqat raqamda kiriting, masalan: 5000)</i>",
        parse_mode="HTML", reply_markup=CANCEL_KEYBOARD
    )
    return WAIT_TOPUP_AMOUNT

async def process_topup_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().replace(" ", "").replace(",", "")
    if not text.isdigit() or int(text) < 3500:
        await update.message.reply_text("❌ <b>Xatolik:</b> Minimal summa <b>3,500 so'm</b> bo'lishi va faqat raqam kiritilishi kerak!", parse_mode="HTML", reply_markup=CANCEL_KEYBOARD)
        return WAIT_TOPUP_AMOUNT

    amount = int(text)
    context.user_data["topup_amount"] = amount
    await update.message.reply_text(
        f"💳 <b>Hisobni to'ldirish</b>\n\n💰 <b>Summa:</b> {amount:,} so'm\n🏦 <b>Bank:</b> {BANK_NAME}\n"
        f"💳 <b>Karta raqami:</b> <code>{CARD_NUMBER}</code>\n👤 <b>Karta egasi:</b> {CARD_HOLDER}\n\n"
        f"📸 <b>To'lov qilib bo'lgach, chek rasmini yuboring:</b>",
        parse_mode="HTML", reply_markup=CANCEL_KEYBOARD
    )
    return WAIT_RECEIPT_PHOTO

async def process_receipt_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    amount = context.user_data.get("topup_amount", 0)
    user_username = f"@{user.username}" if user.username else "yo'q"

    admin_caption = (
        f"💳 <b>Yangi Balans To'ldirish So'rovi!</b>\n\n👤 <b>Foydalanuvchi:</b> {html.escape(user.full_name)}\n"
        f"🆔 <b>User ID:</b> <code>{user.id}</code>\n🏷 <b>Username:</b> {html.escape(user_username)}\n💰 <b>Kutilayotgan summa:</b> {amount:,} so'm"
    )
    try:
        await context.bot.send_photo(chat_id=GROUP_ID, photo=update.message.photo[-1].file_id, caption=admin_caption, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Guruhga rasm yuborishda xatolik: {e}")

    await update.message.reply_text("✅ <b>To'lov cheki qabul qilindi!</b>\n\nTez orada balansingiz to'ldiriladi.", parse_mode="HTML")
    await send_main_menu(update, context)
    context.user_data.clear()
    return ConversationHandler.END

# --- GIFTS FLOW ---
async def show_gifts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("💝 🧸 (15 Stars)", callback_data="cat_15")],
        [InlineKeyboardButton("🌹 🎁 (25 Stars)", callback_data="cat_25")],
        [InlineKeyboardButton("💐 🎂 🍾 🚀 (50 Stars)", callback_data="cat_50")],
        [InlineKeyboardButton("💍 🏆 💎 (100 Stars)", callback_data="cat_100")],
        [InlineKeyboardButton("⬅️ Orqaga", callback_data="back_to_main")],
    ]
    await query.edit_message_text("🎁 <b>Biror gift turini tanlang:</b>", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

async def select_gift_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    category_items = {
        "cat_15": [("💝 Yurak", "item_heart_15"), ("🧸 Ayiqcha", "item_bear_15")],
        "cat_25": [("🌹 Atirgul", "item_rose_25"), ("🎁 Sovg'a quti", "item_box_25")],
        "cat_50": [("💐 Buket", "item_bouquet_50"), ("🎂 Tort", "item_cake_50"), ("🍾 Shampan", "item_champagne_50"), ("🚀 Raketa", "item_rocket_50")],
        "cat_100": [("💍 Uzuk", "item_ring_100"), ("🏆 Kubok", "item_trophy_100"), ("💎 Olmos", "item_diamond_100")],
    }
    if query.data in category_items:
        buttons = [[InlineKeyboardButton(name, callback_data=key)] for name, key in category_items[query.data]]
        buttons.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="show_gifts")])
        await query.edit_message_text("👇 <b>Biror giftni tanlang:</b>", reply_markup=InlineKeyboardMarkup(buttons), parse_mode="HTML")

async def show_gift_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data in GIFTS_DB:
        gift_name, stars, price_som = GIFTS_DB[query.data]
        keyboard = [
            [InlineKeyboardButton("✅ Sotib olish", callback_data=f"buy_{query.data}")],
            [InlineKeyboardButton("⬅️ Orqaga", callback_data=f"cat_{stars}")],
        ]
        await query.edit_message_text(f"🎁 <b>Gift:</b> {gift_name}\n⭐️ <b>Narxi:</b> {price_som:,} so'm\n\nSotib olishni tasdiqlaysizmi?", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

async def ask_username_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["selected_gift_key"] = query.data.replace("buy_", "")
    await query.message.reply_text("✏️ Telegram Username kiriting:\n<i>(Masalan: @username)</i>", parse_mode="HTML", reply_markup=CANCEL_KEYBOARD)
    return WAIT_TARGET_USERNAME

async def process_gift_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target_username = update.message.text.strip()
    if not target_username.startswith("@"):
        target_username = f"@{target_username}"

    user = update.effective_user
    buy_key = context.user_data.get("selected_gift_key")
    if not buy_key or buy_key not in GIFTS_DB:
        return ConversationHandler.END

    gift_name, _, price_som = GIFTS_DB[buy_key]
    user_balance = get_balance(user.id)

    if user_balance < price_som:
        keyboard = [[InlineKeyboardButton("💳 Balans to'ldirish", callback_data="topup_balance")]]
        await update.message.reply_text(f"❌ <b>Mablag' yetarli emas!</b>\n🎁 Narx: {price_som:,} so'm\n💳 Balans: {user_balance:,} so'm", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return ConversationHandler.END

    add_balance(user.id, -price_som, user.username)
    buyer_username = f"@{user.username}" if user.username else "No_Username"

    text = f"🎁 <b>Yangi Gift Xarid Qilindi!</b>\n\n👤 <b>Xaridor:</b> <code>{user.id}</code> ({buyer_username})\n📩 <b>Qabul qiluvchi:</b> {target_username}\n🎁 <b>Gift:</b> {gift_name}\n💰 <b>Yechildi:</b> {price_som:,} so'm"
    try:
        await context.bot.send_message(chat_id=GROUP_ID, text=text, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Guruhga yuborishda xatolik: {e}")

    await update.message.reply_text(f"✅ <b>Buyurtma qabul qilindi!</b>\n📩 {target_username}\n🎁 {gift_name}\n💰 {price_som:,} so'm", parse_mode="HTML")
    await send_main_menu(update, context)
    context.user_data.clear()
    return ConversationHandler.END

async def webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user, msg = update.effective_user, update.effective_message
    if not msg or not msg.web_app_data:
        return
    try:
        data = json.loads(msg.web_app_data.data)
        total_price, stars_count = int(data.get("total", 0)), int(data.get("stars", 0))
        target_user = str(data.get("username", user.username or "")).strip()
        if target_user and not target_user.startswith("@"):
            target_user = f"@{target_user}"

        if get_balance(user.id) < total_price or total_price <= 0:
            await msg.reply_text(f"❌ <b>Mablag' yetarli emas!</b>\n⭐️ Buyurtma: {total_price:,} so'm", parse_mode="HTML")
            return

        add_balance(user.id, -total_price, user.username)
        buyer_username = f"@{user.username}" if user.username else "yo'q"

        text = f"🛒 <b>Yangi Stars Buyurtmasi!</b>\n\n👤 <b>Xaridor ID:</b> <code>{user.id}</code> ({buyer_username})\n🎯 <b>Qabul qiluvchi:</b> {target_user}\n⭐️ <b>Stars:</b> {stars_count}\n💰 <b>Yechildi:</b> {total_price:,} so'm"
        try:
            await context.bot.send_message(chat_id=GROUP_ID, text=text, parse_mode="HTML")
        except Exception as e:
            logging.error(f"Guruhga Stars buyurtmasini yuborishda xatolik: {e}")

        await msg.reply_text(f"✅ <b>Stars buyurtmangiz qabul qilindi!</b>\n⭐️ Stars: <b>{stars_count}</b>\n💰 Yechilgan: <b>{total_price:,} so'm</b>", parse_mode="HTML")
    except Exception as e:
        logging.error(f"Web App ma'lumotida xatolik: {e}")

# --- ADMIN PANEL ---
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID:
        return
    keyboard = [
        [InlineKeyboardButton("➕ Balans qo'shish", callback_data="admin_add")],
        [InlineKeyboardButton("➖ Balans ayirish", callback_data="admin_remove")],
        [InlineKeyboardButton("⬅️ Bosh menyu", callback_data="back_to_main")],
    ]
    await query.edit_message_text("⚙️ Admin Panel\n\nKerakli bo'limni tanlang:", reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_start_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID:
        return ConversationHandler.END
    
    context.user_data["admin_mode"] = "add" if query.data == "admin_add" else "remove"
    await query.message.reply_text("👤 Foydalanuvchining <b>User ID</b> yoki <b>@username</b> ini yuboring:", reply_markup=CANCEL_KEYBOARD, parse_mode="HTML")
    return WAIT_ADMIN_USER

async def receive_admin_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target_id = get_user_id_by_input(update.message.text.strip())
    if not target_id:
        await update.message.reply_text("❌ Foydalanuvchi topilmadi!", reply_markup=CANCEL_KEYBOARD)
        return WAIT_ADMIN_USER

    context.user_data["target_user"] = target_id
    await update.message.reply_text(f"✅ Foydalanuvchi topildi (ID: <code>{target_id}</code>).\n\n💰 Summani yuboring:", parse_mode="HTML", reply_markup=CANCEL_KEYBOARD)
    return WAIT_ADMIN_AMOUNT

async def receive_admin_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❌ Faqat son kiriting.", reply_markup=CANCEL_KEYBOARD)
        return WAIT_ADMIN_AMOUNT

    user_id = context.user_data["target_user"]
    mode = context.user_data.get("admin_mode")
    final_amount = amount if mode == "add" else -amount

    add_balance(user_id, final_amount)
    new_balance = get_balance(user_id)

    if mode == "add":
        try:
            await context.bot.send_message(chat_id=user_id, text=f"🎉 <b>Balansingiz to'ldirildi!</b>\n➕ {amount:,} so'm\n💳 Balans: {new_balance:,} so'm", parse_mode="HTML")
        except Exception:
            pass

    action_text = "qo'shildi" if mode == "add" else "ayirildi"
    await update.message.reply_text(f"✅ Balans {action_text}!\n👤 User ID: <code>{user_id}</code>\n💳 Yangi balans: {new_balance:,} so'm", parse_mode="HTML")
    return ConversationHandler.END

if __name__ == "__main__":
    init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    common_fallbacks = [CommandHandler("start", start), CallbackQueryHandler(cancel_action, pattern="^cancel_action$")]

    app.add_handler(CommandHandler("start", start))
    
    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(topup_start, pattern="^topup_balance$")],
        states={
            WAIT_TOPUP_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_topup_amount)],
            WAIT_RECEIPT_PHOTO: [MessageHandler(filters.PHOTO, process_receipt_photo)],
        },
        fallbacks=common_fallbacks,
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(ask_username_start, pattern="^buy_")],
        states={WAIT_TARGET_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_gift_purchase)]},
        fallbacks=common_fallbacks,
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_start_action, pattern="^admin_(add|remove)$")],
        states={
            WAIT_ADMIN_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_admin_user)],
            WAIT_ADMIN_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_admin_amount)],
        },
        fallbacks=common_fallbacks,
    ))

    app.add_handler(CallbackQueryHandler(show_gifts, pattern="^show_gifts$"))
    app.add_handler(CallbackQueryHandler(select_gift_category, pattern="^cat_"))
    app.add_handler(CallbackQueryHandler(show_gift_details, pattern="^item_"))
    app.add_handler(CallbackQueryHandler(cancel_action, pattern="^back_to_main$"))
    app.add_handler(CallbackQueryHandler(admin_panel, pattern="^admin_panel$"))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, webapp_data))

    print("🤖 Bot ishga tushdi...")
    app.run_polling()
