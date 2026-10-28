from flask import Flask, jsonify

app = Flask(__name__)

ORDERS = [
    {"id": 1001, "product": "Keyboard", "quantity": 1, "status": "created"},
    {"id": 1002, "product": "Mouse", "quantity": 2, "status": "processing"},
]


@app.get("/")
def index():
    return jsonify(service="orders-service", orders=ORDERS)


@app.get("/health")
def health():
    return jsonify(status="ok", service="orders-service"), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
