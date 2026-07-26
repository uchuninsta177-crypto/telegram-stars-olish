from flask import Flask, request, jsonify
import sqlite3
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = "-1004457471821"

@app.route("/")
def home():
    return "Server ishlayapti!"

@app.route("/balance/<int:user_id>")
def get_user_balance(user_id):

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT balance FROM users WHERE user_id=?",
        (user_id,)
    )

    row = cursor.fetchone()

    conn.close()

    if row:
        return jsonify({
            "success": True,
            "balance": row[0]
        })

    return jsonify({
        "success": False,
        "balance": 0
    })

@app.route("/order", methods=["POST"])
def order():
    data = request.get_json()

    username = data.get("username")
    stars = data.get("stars")
    total = data.get("total")

    text = (
        "🛒 Yangi buyurtma\n\n"
        f"👤 Username: {username}\n"
        f"⭐️ Stars: {stars}\n"
        f"💰 Summa: {total:,} so'm"
    )

    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={
            "chat_id": CHAT_ID,
            "text": text
        }
    )

    return jsonify({
    "success": True,
    "message": "✅ Buyurtma qabul qilindi!                                                                     ⏳Starsingizni tez orada yetkazib beramiz!"
})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
