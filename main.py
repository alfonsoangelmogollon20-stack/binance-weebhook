from flask import Flask, request, render_template_string
from binance.client import Client

API_KEY = "vFoo8iDlNkwe4X5S3znciN46TT6TOYSbrDH2TrMte6nMe22CLiYnkUvGFHAMLXw2"
API_SECRET = "lPIhxJaBkejBdlt501lYEPbCKraScMNLb6VW4BKrpGl5QobsCEij3Xpw9gEDJVtY"

client = Client(API_KEY, API_SECRET, testnet=True)
app = Flask(__name__)

SYMBOL = "BTCUSDT"
QUANTITY = 0.0033  # Simula una inversión de ~200 USDT a BTC 60k

html_template = """
<!DOCTYPE html>
<html>
<head>
  <title>Panel de Órdenes</title>
  <style>
    body { font-family: Arial; background: #111; color: #fff; padding: 20px; }
    h2, h3 { color: #0f0; }
    .saldo { margin-bottom: 15px; padding: 10px; background: #222; border-radius: 5px; }
    table { width: 100%; border-collapse: collapse; margin-top: 20px; }
    th, td { border: 1px solid #555; padding: 8px; text-align: center; }
    th { background-color: #222; }
    tr:nth-child(even) { background-color: #1c1c1c; }
    .ganancia { color: lime; }
    .perdida { color: red; }
  </style>
</head>
<body>
  <h2>📊 Panel BTCUSDT (Testnet)</h2>
  <div class="saldo">
    <h3>💰 Saldos:</h3>
    <p><strong>USDT:</strong> {{ usdt_balance }} USDT</p>
    <p><strong>BTC:</strong> {{ btc_balance }} BTC</p>
    <p><strong>Precio Actual:</strong> {{ actual_price }} USDT</p>
  </div>

  <table>
    <thead>
      <tr>
        <th>Tipo</th>
        <th>Precio Entrada</th>
        <th>Cantidad</th>
        <th>Inversión (USDT)</th>
        <th>Estado</th>
        <th>Ganancia/Perdida</th>
        <th>%</th>
      </tr>
    </thead>
    <tbody>
      {% for orden in ordenes %}
      <tr>
        <td>{{ orden.side }}</td>
        <td>{{ orden.price }}</td>
        <td>{{ orden.executedQty }}</td>
        <td>{{ orden.inversion }}</td>
        <td>{{ orden.status }}</td>
        <td class="{{ 'ganancia' if orden.pnl >= 0 else 'perdida' }}">{{ orden.pnl }} USDT</td>
        <td class="{{ 'ganancia' if orden.porcentaje >= 0 else 'perdida' }}">{{ orden.porcentaje }}%</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</body>
</html>
"""

@app.route("/", methods=["POST"])
def webhook():
    data = request.json
    action = data.get("message")

    if action == "LONG":
        client.create_test_order(symbol=SYMBOL, side="BUY", type="MARKET", quantity=QUANTITY)
        print("✅ Orden LONG enviada")
        return {"status": "long order sent"}, 200

    elif action == "SHORT":
        client.create_test_order(symbol=SYMBOL, side="SELL", type="MARKET", quantity=QUANTITY)
        print("✅ Orden SHORT enviada")
        return {"status": "short order sent"}, 200

    return {"status": "no action"}, 400

@app.route("/panel")
def panel():
    actual_price = float(client.get_symbol_ticker(symbol=SYMBOL)["price"])
    orders = client.get_all_orders(symbol=SYMBOL)
    account = client.get_account()
    balances = {b["asset"]: float(b["free"]) for b in account["balances"]}
    usdt_balance = round(balances.get("USDT", 0), 2)
    btc_balance = round(balances.get("BTC", 0), 6)

    ordenes_visibles = []
    for o in orders:
        if o["status"] == "FILLED" and float(o["executedQty"]) > 0:
            price_entry = float(o["price"])
            qty = float(o["executedQty"])
            inversion = round(price_entry * qty, 2)
            ganancia = (actual_price - price_entry) * qty if o["side"] == "BUY" else (price_entry - actual_price) * qty
            porcentaje = (ganancia / inversion) * 100 if inversion > 0 else 0

            ordenes_visibles.append({
                "side": o["side"],
                "price": o["price"],
                "executedQty": o["executedQty"],
                "status": o["status"],
                "inversion": inversion,
                "pnl": round(ganancia, 2),
                "porcentaje": round(porcentaje, 2)
            })

    return render_template_string(html_template,
                                  ordenes=ordenes_visibles,
                                  actual_price=round(actual_price, 2),
                                  btc_balance=btc_balance,
                                  usdt_balance=usdt_balance)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
