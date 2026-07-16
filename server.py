from flask import Flask, request, jsonify

app = Flask(name)

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

if name == "main":
    app.run(host="0.0.0.0", port=5000)
