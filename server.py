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
    data = request.json

    username = data.get("username")
    stars = data.get("stars")
    total = data.get("total")

    text = f"""🛒 Yangi buyurtma

👤 Username: {username}
⭐ Stars: {stars}
💰 Summa: {total:,} so'm
"""

    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={
            "chat_id": CHAT_ID,
            "text": text
        }
    )

    return jsonify({
        "success": True,
        "message": "Buyurtma qabul qilindi"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
