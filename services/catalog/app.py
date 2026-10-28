from flask import Flask, jsonify

app = Flask(__name__)

PRODUCTS = [
    {"id": 1, "name": "Keyboard", "price": 799},
    {"id": 2, "name": "Mouse", "price": 399},
]


@app.get("/")
def index():
    return jsonify(service="catalog-service", products=PRODUCTS)


@app.get("/health")
def health():
    return jsonify(status="ok", service="catalog-service"), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
