import os
import asyncio
from flask import Flask, request, jsonify
from pocketoptionapi.stable_api import PocketOption

# --- CONFIGURACIÓN ---
SSID = os.getenv("SSID")
app = Flask(__name__) # Inicia la aplicación web

# --- NUEVA FUNCIÓN ASÍNCRONA ---
async def execute_trade_logic(data):
    """
    Esta función asíncrona maneja la conexión y la operación con la API.
    """
    # --- LÍNEA DE DEPURACIÓN ---
    print(f"DEBUG: Intentando conectar con el SSID: '{SSID}'")
    # -------------------------

    print("Iniciando lógica de trade asíncrona...")
    asset = data.get('asset')
    # ... (el resto de la función sigue igual)

    """
    Esta función asíncrona maneja la conexión y la operación con la API.
    """
    print("Iniciando lógica de trade asíncrona...")
    asset = data.get('asset')
    action = data.get('action')
    amount = int(data.get('amount'))
    expiration = int(data.get('expiration'))

    if not all([asset, action, amount, expiration]):
        raise ValueError("Faltan datos en la alerta: asset, action, amount o expiration.")

    # Conectamos a la cuenta de práctica (o real si demo=False)
    api = PocketOption(ssid=SSID, demo=True)
    
    # Usamos 'await' porque connect() es una operación asíncrona
    api.connect()

    if api.check_connect():
        print(f"Ejecutando operación: {action.upper()} de ${amount} en {asset} por {expiration} min.")
        
        # Usamos 'await' porque buy() también es una operación asíncrona
        success, _ = await api.buy(amount=amount, asset=asset, action=action, anaysis_time=expiration)
        
        # Cerramos la conexión para liberar recursos
        

        if success:
            print("Operación abierta con éxito.")
            return {'status': 'ok', 'message': 'Operación abierta'}
        else:
            raise ConnectionError("La API no pudo abrir la operación.")
    else:
        
        raise ConnectionError("No se pudo conectar a Pocket Option.")


# --- WEBHOOK SÍNCRONO (Como antes) ---
@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Esta es la puerta de entrada síncrona que activa la lógica asíncrona.
    """
    try:
        data = request.json
        print(f"Alerta recibida: {data}")
        
        # Aquí está la magia: asyncio.run() ejecuta nuestra función asíncrona
        # y espera a que termine, devolviendo el resultado.
        result = asyncio.run(execute_trade_logic(data))
        
        return jsonify(result), 200

    except Exception as e:
        print(f"Error procesando la alerta: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
    
