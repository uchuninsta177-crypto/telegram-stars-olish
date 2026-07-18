from flask import Flask, request, jsonify
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
    "message": "✅ Buyurtma qabul qilindi! Starsingiz tez orada yetkazib beramiz!"
})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
