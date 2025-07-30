from flask import Flask, request
from binance.client import Client

API_KEY = "vFoo8iDlNkwe4X5S3znciN46TT6TOYSbrDH2TrMte6nMe22CLiYnkUvGFHAMLXw2"
API_SECRET = "lPIhxJaBkejBdlt501lYEPbCKraScMNLb6VW4BKrpGl5QobsCEij3Xpw9gEDJVtY"

client = Client(API_KEY, API_SECRET, testnet=True)
app = Flask(__name__)

SYMBOL = "BTCUSDT"
QUANTITY = 0.001

@app.route("/", methods=["POST"])
def webhook():
    data = request.json
    action = data.get("message")

    if action == "LONG":
        client.create_test_order(symbol=SYMBOL, side="BUY", type="MARKET", quantity=QUANTITY)
        return {"status": "long order sent"}, 200
    elif action == "SHORT":
        client.create_test_order(symbol=SYMBOL, side="SELL", type="MARKET", quantity=QUANTITY)
        return {"status": "short order sent"}, 200
    return {"status": "no action"}, 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
