import os
import asyncio
from flask import Flask, request, jsonify
from pocketoptionapi.stable_api import PocketOption

app = Flask(__name__)

ssid = """42["auth",{"sessionToken":"ef6650ab92e775a54c08a8f46df11b75","uid":"107695044","lang":"es","currentUrl":"cabinet/demo-quick-high-low","isChart":1}]"""
demo = True

async def execute_trade_logic(data):
    print(f"DEBUG: Intentando conectar con el SSID completo: '{ssid}'")

    asset = data.get('asset')
    action = data.get('action')
    amount = int(data.get('amount'))
    expiration = int(data.get('expiration'))

    if not asset or not action or not isinstance(amount, int) or not isinstance(expiration, int):
        raise ValueError("Faltan datos o son inválidos.")

    api = PocketOption(ssid, demo)
    api.connect()

    if api.check_connect():
        print(f"Ejecutando operación: {action.upper()} de ${amount} en {asset} por {expiration} min.")
        success, _ = await api.buy(amount=amount, asset=asset, action=action, analysis_time=expiration)
        if success:
            print("Operación abierta con éxito.")
            return {'status': 'ok', 'message': 'Operación abierta'}
        else:
            raise ConnectionError("La API no pudo abrir la operación.")
    else:
        raise ConnectionError("No se pudo conectar a Pocket Option.")

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        print(f"Alerta recibida: {data}")
        result = asyncio.run(execute_trade_logic(data))
        return jsonify(result), 200
    except Exception as e:
        print(f"Error procesando la alerta: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
