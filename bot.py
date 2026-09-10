import html
import logging
import sqlite3
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# ==========================================
# 1. SOZLAMALAR
# ==========================================
BOT_TOKEN = "BOT_TOKENINGIZNI_SHU_YERGA_YOZING"
GROUP_ID = -1002345678901  # Guruhingiz ID-si (minus bilan)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# ==========================================
# 2. MA'LUMOTLAR BAZASI (SQLite)
# ==========================================
DB_NAME = "users_database.db"


def init_db():
    """Baza faylini va jadvalni yaratish (faylda saqlanadi, yo'qolib ketmaydi)"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            full_name TEXT,
            username TEXT,
            balance REAL DEFAULT 0.0
        )
    """
    )
    conn.commit()
    conn.close()


def get_user_balance(user_id: int, full_name: str, username: str) -> float:
    """Foydalanuvchi balansini olish. Agar yangi bo'lsa, bazaga qo'shadi."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()

    if row is None:
        # Yangi foydalanuvchini bazaga qo'shish (boshlang'ich balans: 0)
        cursor.execute(
            "INSERT INTO users (user_id, full_name, username, balance) VALUES (?, ?, ?, ?)",
            (user_id, full_name, username, 0.0),
        )
        conn.commit()
        balance = 0.0
    else:
        balance = row[0]

    conn.close()
    return balance


def update_user_balance(user_id: int, amount: float) -> float:
    """Balansni o'zgartirish (qo'shish yoki ayirish uchun)"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE users SET balance = balance + ? WHERE user_id = ?",
        (amount, user_id),
    )
    conn.commit()

    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    new_balance = cursor.fetchone()[0]

    conn.close()
    return new_balance


# Bazani ishga tushirish
init_db()


# ==========================================
# 3. HANDLERLAR VA MENULAR
# ==========================================


def main_menu_keyboard():
    """Asosiy menyu tugmalari"""
    keyboard = [
        [
            InlineKeyboardButton(
                "⭐ Stars xarid qilish", callback_data="buy_stars"
            )
        ],
        [
            InlineKeyboardButton(
                "💰 Mening balansim", callback_data="check_balance"
            )
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


# /start komandasi
async def start_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    user = update.effective_user
    balance = get_user_balance(
        user.id, user.full_name, user.username or "mavjud emas"
    )

    welcome_text = (
        f"Assalomu alaykum, <b>{html.escape(user.first_name)}</b>!\n\n"
        f"💵 Sizing joriy balansinigiz: <b>{balance:,.0f} so'm</b>\n\n"
        "Balansni to'ldirish uchun to'lov cheki (rasmi)ni botga yuboring.\n"
        "Xizmatlardan foydalanish uchun quyidagi tugmalardan birini tanlang:"
    )

    await update.message.reply_text(
        welcome_text, reply_markup=main_menu_keyboard(), parse_mode="HTML"
    )


# Tugmalar bosilganda ishlaydigan loyiha
async def button_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    query = update.callback_query
    await query.answer()

    user = query.from_user
    balance = get_user_balance(
        user.id, user.full_name, user.username or "mavjud emas"
    )

    # 1. Balansni ko'rish tugmasi
    if query.data == "check_balance":
        text = (
            f"👤 <b>Foydalanuvchi:</b> {html.escape(user.full_name)}\n"
            f"🆔 <b>ID:</b> <code>{user.id}</code>\n\n"
            f"💰 <b>Sizning balansingiz:</b> {balance:,.0f} so'm\n\n"
            "<i>Balans doimiy saqlanadi va faqat harid qilganingizda kamayadi.</i>"
        )
        keyboard = [[InlineKeyboardButton("🔙 Orqaga", callback_data="main_menu")]]
        await query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML"
        )

    # 2. Stars bo'limi (Aynan shu yerda ham balans ko'rsatiladi)
    elif query.data == "buy_stars":
        text = (
            f"⭐ <b>Telegram Stars sotib olish bo'limi</b>\n\n"
            f"💳 <b>Sizning balansingiz:</b> <code>{balance:,.0f} so'm</code>\n"
            "------------------------------------\n"
            "Kerakli paketni tanlang:\n\n"
            "1️⃣ 50 Stars — 15,000 so'm\n"
            "2️⃣ 100 Stars — 30,000 so'm\n"
            "3️⃣ 250 Stars — 75,000 so'm"
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "⭐ 50 Stars (15 000 so'm)", callback_data="buy_star_50"
                )
            ],
            [
                InlineKeyboardButton(
                    "⭐ 100 Stars (30 000 so'm)", callback_data="buy_star_100"
                )
            ],
            [
                InlineKeyboardButton(
                    "⭐ 250 Stars (75 000 so'm)", callback_data="buy_star_250"
                )
            ],
            [InlineKeyboardButton("🔙 Orqaga", callback_data="main_menu")],
        ]
        await query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML"
        )

    # 3. Stars sotib olish jarayoni (Balansdan pul ayirish)
    elif query.data.startswith("buy_star_"):
        price_map = {
            "buy_star_50": (50, 15000),
            "buy_star_100": (100, 30000),
            "buy_star_250": (250, 75000),
        }

        stars_amount, price = price_map[query.data]

        if balance < price:
            # Pul yetmaslik xabari
            text = (
                f"❌ <b>Mablag' yetarli emas!</b>\n\n"
                f"Siz tanlagan paket: <b>{stars_amount} Stars ({price:,.0f} so'm)</b>\n"
                f"Sizning balansingiz: <b>{balance:,.0f} so'm</b>\n\n"
                "Iltimos, avval balansni to'ldiring (chek yuboring)."
            )
            keyboard = [
                [
                    InlineKeyboardButton(
                        "🔙 Stars bo'limiga qaytish", callback_data="buy_stars"
                    )
                ]
            ]
            await query.edit_message_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="HTML",
            )
        else:
            # Balans yetarli bo'lsa, pulni yechib olish
            new_balance = update_user_balance(user.id, -price)

            text = (
                f"✅ <b>Xarid muvaffaqiyatli amalga oshirildi!</b>\n\n"
                f"Sotib olindi: <b>{stars_amount} Stars</b>\n"
                f"Yechildi: <b>{price:,.0f} so'm</b>\n"
                f"Qolgan balansingiz: <b>{new_balance:,.0f} so'm</b>\n\n"
                "⭐ Stars tez orada hisobingizga o'tkaziladi!"
            )
            keyboard = [
                [
                    InlineKeyboardButton(
                        "🔙 Asosiy menyu", callback_data="main_menu"
                    )
                ]
            ]
            await query.edit_message_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="HTML",
            )

            # Admin guruhiga bildirishnoma yuborish
            admin_msg = (
                f"🛒 <b>Yangi Stars Xaridi!</b>\n\n"
                f"👤 <b>Xaridor:</b> {html.escape(user.full_name)}\n"
                f"🆔 <b>ID:</b> <code>{user.id}</code>\n"
                f"⭐ <b>Miqdori:</b> {stars_amount} Stars\n"
                f"💵 <b>To'langan summa:</b> {price:,.0f} so'm"
            )
            await context.bot.send_message(
                chat_id=GROUP_ID, text=admin_msg, parse_mode="HTML"
            )

    # 4. Asosiy menyuga qaytish
    elif query.data == "main_menu":
        welcome_text = (
            f"Assalomu alaykum, <b>{html.escape(user.first_name)}</b>!\n\n"
            f"💵 Sizing joriy balansingiz: <b>{balance:,.0f} so'm</b>\n\n"
            "Kerakli bo'limni tanlang:"
        )
        await query.edit_message_text(
            welcome_text, reply_markup=main_menu_keyboard(), parse_mode="HTML"
        )


# Chek (rasm) kelganda ishlash
async def auto_handle_receipt(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    if update.effective_chat.type == "private":
        user = update.effective_user
        photo_id = update.message.photo[-1].file_id

        full_name_clean = html.escape(user.full_name)
        username_clean = (
            f"@{user.username}" if user.username else "mavjud emas"
        )

        admin_caption = (
            "💳 <b>Yangi To'lov Cheki Keldi!</b>\n\n"
            f"👤 <b>Foydalanuvchi:</b> {full_name_clean}\n"
            f"🆔 <b>User ID:</b> <code>{user.id}</code>\n"
            f"🏷 <b>Username:</b> {username_clean}\n\n"
            f"<i>Foydalanuvchi balansiga pul qo'shish uchun bazaga kiring yoki admin buyrug'ini ishlating.</i>"
        )

        try:
            await context.bot.send_photo(
                chat_id=GROUP_ID,
                photo=photo_id,
                caption=admin_caption,
                parse_mode="HTML",
            )
            await update.message.reply_text(
                "✅ <b>To'lov chekingiz qabul qilindi!</b>\n\n"
                "Administratorlar tekshirib, balansingizni to'ldiradi.",
                parse_mode="HTML",
            )
        except Exception as e:
            print(f"❌ Guruhga rasm yuborishda XATOLIK: {e}")


# Adminlar uchun foydalanuvchiga balans qo'shish komandasi (/addbalance ID SUMMA)
async def add_balance_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    # Faqat admin guruhida yoki belgilangan admin ishlatishi uchun
    try:
        args = context.args
        target_user_id = int(args[0])
        amount = float(args[1])

        new_bal = update_user_balance(target_user_id, amount)

        await update.message.reply_text(
            f"✅ Foydalanuvchi (ID: <code>{target_user_id}</code>) balansiga {amount:,.0f} so'm qo'shildi.\n"
            f"Yangi balans: <b>{new_bal:,.0f} so'm</b>",
            parse_mode="HTML",
        )

        # Foydalanuvchining o'ziga bildirishnoma yuborish
        await context.bot.send_message(
            chat_id=target_user_id,
            text=f"🎉 <b>Balansingiz to'ldirildi!</b>\n\nQo'shildi: <b>+{amount:,.0f} so'm</b>\nJoriy balans: <b>{new_bal:,.0f} so'm</b>",
            parse_mode="HTML",
        )
    except Exception as e:
        await update.message.reply_text(
            "❌ Buyruq xato kiritildi!\nMisol: <code>/addbalance 123456789 50000</code>",
            parse_mode="HTML",
        )


# ==========================================
# 4. ISHGA TUSHIRISH
# ==========================================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("addbalance", add_balance_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(
        MessageHandler(
            filters.PHOTO & filters.ChatType.PRIVATE, auto_handle_receipt
        )
    )

    print("🤖 Bot muvaffaqiyatli ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    main()
