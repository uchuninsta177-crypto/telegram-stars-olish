from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app = Flask(__name__)

@app.route("/")
def home():
    return "Server ishlayapti!"

@app.route("/order", methods=["POST"])
def order():
    data = request.json

    print("Yangi buyurtma:", data)

    return jsonify({
        "success": True,
        "message": "Buyurtma qabul qilindi"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
