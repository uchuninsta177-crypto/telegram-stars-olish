import os
import sqlite3
from flask import Flask, jsonify, request
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = "-1004457471821"
DB_PATH = "bot.db"  # Bazangiz fayli nomi (bot.db)


@app.route("/")
def home():
    return "Server ishlayapti!"


@app.route("/balance/<int:user_id>")
def get_user_balance(user_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT balance FROM users WHERE user_id=?", (user_id,)
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            return jsonify({"success": True, "balance": row[0]})

        return jsonify({"success": False, "balance": 0})
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "balance": 0})


@app.route("/order", methods=["POST"])
def order():
    try:
        data = request.get_json() or {}

        username = data.get("username", "Ko'rsatilmadi")
        stars = data.get("stars", 0)
        total = int(data.get("total", 0))

        text = (
            "🛒 <b>Yangi buyurtma (Web Server orqali)</b>\n\n"
            f"👤 <b>Username:</b> {username}\n"
            f"⭐️ <b>Stars:</b> {stars}\n"
            f"💰 <b>Summa:</b> {total:,} so'm"
        )

        if BOT_TOKEN:
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={
                    "chat_id": CHAT_ID,
                    "text": text,
                    "parse_mode": "HTML",
                },
            )

        return jsonify({
            "success": True,
            "message": "✅ Buyurtma qabul qilindi!\n⏳ Starsingizni tez orada yetkazib beramiz!",
        })
    except Exception as e:
        return jsonify(
            {"success": False, "message": f"Xatolik yuz berdi: {str(e)}"}
        ), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)