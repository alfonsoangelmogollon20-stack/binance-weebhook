import os
import asyncio
from flask import Flask, request, jsonify
from pocketoptionapi.stable_api import PocketOption

# --- CONFIGURACIÓN ---
SSID = SSID = '42["auth",{"session":"gqep422ie95ar8uabq0q9nsdsf","isDemo":1,"uid":107695044,"platform":2,"isFastHistory":true,"isOptimized":true}]'
app = Flask(__name__)

# --- FUNCIÓN ASÍNCRONA PARA OPERAR ---
async def execute_trade_logic(data):
    print(f"DEBUG: Intentando conectar con el SSID completo: '{SSID}'")
    
    asset = data.get('asset')
    action = data.get('action')
    amount = int(data.get('amount'))
    expiration = int(data.get('expiration'))

    if not all([asset, action, amount, expiration]):
        raise ValueError("Faltan datos en la alerta.")

    # Conectamos usando el SSID y el argumento 'demo'
    api = PocketOption(ssid=SSID, demo=True) # Pon demo=False para cuenta real
    api.connect()

    if api.check_connect():
        print(f"Ejecutando operación: {action.upper()} de ${amount} en {asset} por {expiration} min.")
        success, _ = await api.buy(amount=amount, asset=asset, action=action, anaysis_time=expiration)
        if success:
            print("Operación abierta con éxito.")
            return {'status': 'ok', 'message': 'Operación abierta'}
        else:
            raise ConnectionError("La API no pudo abrir la operación.")
    else:
        raise ConnectionError("No se pudo conectar a Pocket Option.")

# --- WEBHOOK (PUERTA DE ENTRADA) ---
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
