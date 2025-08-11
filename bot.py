import os
from flask import Flask, request, jsonify
from pocketoptionapi.stable_api import PocketOption

# --- CONFIGURACIÓN ---
SSID = os.getenv("SSID")
app = Flask(__name__) # Inicia la aplicación web

# --- LÓGICA DEL WEBHOOK ---
@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Esta función se activa cuando TradingView envía una alerta a esta URL.
    """
    try:
        # 1. Recibir los datos de la alerta de TradingView
        data = request.json
        print(f"Alerta recibida: {data}")

        # 2. Extraer los datos importantes de la alerta
        #    IMPORTANTE: El formato exacto depende de cómo configures el
        #    mensaje de la alerta en TradingView.
        #    Ejemplo de mensaje en TradingView:
        #    {"asset": "EURUSD", "action": "call", "amount": 15, "expiration": 5}
        
        asset = data.get('asset')
        action = data.get('action') # "call" o "put"
        amount = int(data.get('amount'))
        expiration = int(data.get('expiration'))

        if not all([asset, action, amount, expiration]):
            return jsonify({'status': 'error', 'message': 'Faltan datos en la alerta'}), 400

        # 3. Conectar y ejecutar la operación
        api = PocketOption(SSID)
        api.connect()

        if api.check_connect():
            print(f"Ejecutando operación: {action.upper()} de ${amount} en {asset} por {expiration} min.")
            
            # Cambia a cuenta de práctica. ¡¡COMENTA ESTA LÍNEA PARA OPERAR EN REAL!!
            api.change_balance("PRACTICE") 
            
            success = api.buy(amount=amount, asset=asset, action=action, anaysis_time=expiration)
            
            if success:
                print("Operación abierta con éxito.")
                return jsonify({'status': 'ok', 'message': 'Operación abierta'}), 200
            else:
                print("Error al abrir la operación.")
                return jsonify({'status': 'error', 'message': 'No se pudo abrir la operación'}), 500
        else:
            return jsonify({'status': 'error', 'message': 'No se pudo conectar a Pocket Option'}), 500

    except Exception as e:
        print(f"Error procesando la alerta: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    # Render usa Gunicorn para ejecutar Flask, por lo que esta parte
    # se usa solo si ejecutas el bot en tu propia computadora.
    # No es necesario cambiar el comando de inicio en Render.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
    
    return df


def accelerator_oscillator(dataframe, fastPeriod=5, slowPeriod=34, smoothPeriod=5):
    ao = ta.SMA(dataframe["hl2"], timeperiod=fastPeriod) - ta.SMA(dataframe["hl2"], timeperiod=slowPeriod)
    ac = ta.SMA(ao, timeperiod=smoothPeriod)
    return ac


def DeMarker(dataframe, Period=14):
    dataframe['dem_high'] = dataframe['high'] - dataframe['high'].shift(1)
    dataframe['dem_low'] = dataframe['low'].shift(1) - dataframe['low']
    dataframe.loc[(dataframe['dem_high'] < 0), 'dem_high'] = 0
    dataframe.loc[(dataframe['dem_low'] < 0), 'dem_low'] = 0

    dem = ta.SMA(dataframe['dem_high'], Period) / (ta.SMA(dataframe['dem_high'], Period) + ta.SMA(dataframe['dem_low'], Period))
    return dem


def vortex_indicator(dataframe, Period=14):
    vm_plus = abs(dataframe['high'] - dataframe['low'].shift(1))
    vm_minus = abs(dataframe['low'] - dataframe['high'].shift(1))

    tr1 = dataframe['high'] - dataframe['low']
    tr2 = abs(dataframe['high'] - dataframe['close'].shift(1))
    tr3 = abs(dataframe['low'] - dataframe['close'].shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    sum_vm_plus = vm_plus.rolling(window=Period).sum()
    sum_vm_minus = vm_minus.rolling(window=Period).sum()
    sum_tr = tr.rolling(window=Period).sum()

    vi_plus = sum_vm_plus / sum_tr
    vi_minus = sum_vm_minus / sum_tr

    return vi_plus, vi_minus


def supertrend(df, multiplier, period):
    #df = dataframe.copy()

    df['TR'] = ta.TRANGE(df)
    df['ATR'] = ta.SMA(df['TR'], period)

    st = 'ST'
    stx = 'STX'

    # Compute basic upper and lower bands
    df['basic_ub'] = (df['high'] + df['low']) / 2 + multiplier * df['ATR']
    df['basic_lb'] = (df['high'] + df['low']) / 2 - multiplier * df['ATR']

    # Compute final upper and lower bands
    df['final_ub'] = 0.00
    df['final_lb'] = 0.00
    for i in range(period, len(df)):
        df['final_ub'].iat[i] = df['basic_ub'].iat[i] if df['basic_ub'].iat[i] < df['final_ub'].iat[i - 1] or df['close'].iat[i - 1] > df['final_ub'].iat[i - 1] else df['final_ub'].iat[i - 1]
        df['final_lb'].iat[i] = df['basic_lb'].iat[i] if df['basic_lb'].iat[i] > df['final_lb'].iat[i - 1] or df['close'].iat[i - 1] < df['final_lb'].iat[i - 1] else df['final_lb'].iat[i - 1]

    # Set the Supertrend value
    df[st] = 0.00
    for i in range(period, len(df)):
        df[st].iat[i] = df['final_ub'].iat[i] if df[st].iat[i - 1] == df['final_ub'].iat[i - 1] and df['close'].iat[i] <= df['final_ub'].iat[i] else \
                        df['final_lb'].iat[i] if df[st].iat[i - 1] == df['final_ub'].iat[i - 1] and df['close'].iat[i] >  df['final_ub'].iat[i] else \
                        df['final_lb'].iat[i] if df[st].iat[i - 1] == df['final_lb'].iat[i - 1] and df['close'].iat[i] >= df['final_lb'].iat[i] else \
                        df['final_ub'].iat[i] if df[st].iat[i - 1] == df['final_lb'].iat[i - 1] and df['close'].iat[i] <  df['final_lb'].iat[i] else 0.00
    # Mark the trend direction up/down
    df[stx] = np.where((df[st] > 0.00), np.where((df['close'] < df[st]), 'down',  'up'), np.NaN)

    # Remove basic and final bands from the columns
    df.drop(['basic_ub', 'basic_lb', 'final_ub', 'final_lb'], inplace=True, axis=1)

    df.fillna(0, inplace=True)

    return df


def strategie():
    for pair in global_value.pairs:
        if 'history' in global_value.pairs[pair]:
            history = []
            history.extend(global_value.pairs[pair]['history'])
            if 'dataframe' in global_value.pairs[pair]:
                df = make_df(global_value.pairs[pair]['dataframe'], history)
            else:
                df = make_df(None, history)

            # Strategy 9, period: 30
            heikinashi = qtpylib.heikinashi(df)
            df['open'] = heikinashi['open']
            df['close'] = heikinashi['close']
            df['high'] = heikinashi['high']
            df['low'] = heikinashi['low']
            df = supertrend(df, 1.3, 13)
            df['ma1'] = ta.EMA(df["close"], timeperiod=16)
            df['ma2'] = ta.EMA(df["close"], timeperiod=165)
            df['buy'], df['cross'] = 0, 0
            df.loc[(qtpylib.crossed_above(df['ST'], df['ma1'])), 'cross'] = 1
            df.loc[(qtpylib.crossed_below(df['ST'], df['ma1'])), 'cross'] = -1
            df.loc[(
                    (df['STX'] == "up") &
                    (df['ma1'] > df['ma2']) &
                    (df['cross'] == 1)
                ), 'buy'] = 1
            df.loc[(
                    (df['STX'] == "down") &
                    (df['ma1'] < df['ma2']) &
                    (df['cross'] == -1)
                ), 'buy'] = -1
            if df.loc[len(df)-1]['buy'] != 0:
                t = threading.Thread(target=buy2, args=(100, pair, "call" if df.loc[len(df)-1]['buy'] == 1 else "put", 60,))
                t.start()

            # Strategy 8, period: 15
            # df['ma1'] = ta.SMA(df["close"], timeperiod=7)
            # df['ma2'] = ta.SMA(df["close"], timeperiod=9)
            # df['ma3'] = ta.SMA(df["close"], timeperiod=14)
            # df['buy'], df['ma13c'], df['ma23c'] = 0, 0, 0
            # df.loc[(qtpylib.crossed_above(df['ma1'], df['ma3'])), 'ma13c'] = 1
            # df.loc[(qtpylib.crossed_below(df['ma1'], df['ma3'])), 'ma13c'] = -1
            # df.loc[(qtpylib.crossed_above(df['ma2'], df['ma3'])), 'ma23c'] = 1
            # df.loc[(qtpylib.crossed_below(df['ma2'], df['ma3'])), 'ma23c'] = -1
            # df.loc[(
            #         (df['ma23c'] == 1) &
            #         (
            #             (df['ma13c'] == 1) |
            #             (df['ma13c'].shift(1) == 1)
            #         )
            #     ), 'buy'] = 1
            # df.loc[(
            #         (df['ma23c'] == -1) &
            #         (
            #             (df['ma13c'] == -1) |
            #             (df['ma13c'].shift(1) == -1)
            #         )
            #     ), 'buy'] = -1
            # if df.loc[len(df)-1]['buy'] != 0:
            #     t = threading.Thread(target=buy2, args=(100, pair, "call" if df.loc[len(df)-1]['buy'] == 1 else "put", 60,))
            #     t.start()

            # Strategy 7, period: 60
            # df['exith'] = ta.WMA(2 * ta.WMA(df['high'], int(15 / 2)) - ta.WMA(df['high'], 15), round(math.sqrt(15)))
            # df['exitl'] = ta.WMA(2 * ta.WMA(df['low'], int(15 / 2)) - ta.WMA(df['low'], 15), round(math.sqrt(15)))
            # df['hlv3'], df['buy'] = 0, 0
            # df.loc[(df['close'] > df['exith']), 'hlv3'] = 1
            # df.loc[(df['close'] < df['exitl']), 'hlv3'] = -1
            # df.loc[((df['close'] < df['exith']) & (df['close'] > df['exitl'])), 'hlv3'] = df['hlv3'].shift(1)
            # df.loc[(df['hlv3'] < 0), 'sslexit'] = df['exith']
            # df.loc[(df['hlv3'] > 0), 'sslexit'] = df['exitl']
            # df.loc[(qtpylib.crossed_above(df['close'], df['sslexit'])), 'buy'] = -1
            # df.loc[(qtpylib.crossed_below(df['close'], df['sslexit'])), 'buy'] = 1
            # if df.loc[len(df)-1]['buy'] != 0:
            #     t = threading.Thread(target=buy2, args=(100, pair, "call" if df.loc[len(df)-1]['buy'] == 1 else "put", 60,))
            #     t.start()

            # # Strategy 6, period: 60
            # df['macd'], df['macdsignal'], df['macdhist'] = ta.MACD(df['close'], 10, 15, 5)
            # df['vip'], df['vim'] = vortex_indicator(df, 5)
            # df['vcross'], df['mcross'], df['buy'] = 0, 0, 0
            # df.loc[(qtpylib.crossed_above(df['macd'], df['macdsignal'])), 'mcross'] = 1
            # df.loc[(qtpylib.crossed_below(df['macd'], df['macdsignal'])), 'mcross'] = -1
            # df.loc[(qtpylib.crossed_above(df['vip'], df['vim'])), 'vcross'] = 1
            # df.loc[(qtpylib.crossed_above(df['vim'], df['vip'])), 'vcross'] = -1
            # df.loc[(
            #         (
            #             (df['mcross'] == 1) &
            #             (
            #                 (df['vcross'] == 1) |
            #                 (df['vcross'].shift(1) == 1)
            #             )
            #         ) |
            #         (
            #             (
            #                 (df['mcross'] == 1) |
            #                 (df['mcross'].shift(1) == 1)
            #             ) &
            #             (df['vcross'] == 1)
            #         )
            #     ), 'buy'] = 1
            # df.loc[(
            #         (
            #             (df['mcross'] == -1) &
            #             (
            #                 (df['vcross'] == -1) |
            #                 (df['vcross'].shift(1) == -1)
            #             )
            #         ) |
            #         (
            #             (
            #                 (df['mcross'] == -1) |
            #                 (df['mcross'].shift(1) == -1)
            #             ) &
            #             (df['vcross'] == -1)
            #         )
            #     ), 'buy'] = -1
            # if df.loc[len(df)-1]['buy'] != 0:
            #     t = threading.Thread(target=buy2, args=(100, pair, "call" if df.loc[len(df)-1]['buy'] == 1 else "put", 60,))
            #     t.start()

            # # Strategy 5, period: 120
            # heikinashi = qtpylib.heikinashi(df)
            # df['open'] = heikinashi['open']
            # df['close'] = heikinashi['close']
            # df['high'] = heikinashi['high']
            # df['low'] = heikinashi['low']
            # bollinger = qtpylib.bollinger_bands(qtpylib.typical_price(df), window=6, stds=1.3)
            # df['bb_low'] = bollinger['lower']
            # df['bb_mid'] = bollinger['mid']
            # df['bb_up'] = bollinger['upper']
            # df['macd'], df['macdsignal'], df['macdhist'] = ta.MACD(df['close'], 6, 19, 6)
            # df['macd_cross'], df['hist_cross'], df['buy'] = 0, 0, 0
            # df.loc[(
            #         (df['macd'].shift(1) < df['macdsignal'].shift(1)) &
            #         (df['macd'] > df['macdsignal'])
            #     ), 'macd_cross'] = 1
            # df.loc[(
            #         (df['macd'].shift(1) > df['macdsignal'].shift(1)) &
            #         (df['macd'] < df['macdsignal'])
            #     ), 'macd_cross'] = -1
            # df.loc[(
            #         (df['macdhist'].shift(1) < 0) &
            #         (df['macdhist'] > 0)
            #     ), 'hist_cross'] = 1
            # df.loc[(
            #         (df['macdhist'].shift(1) > 0) &
            #         (df['macdhist'] < 0)
            #     ), 'hist_cross'] = -1
            # df.loc[(
            #         (df['close'] > df['bb_up']) &
            #         (
            #             (df['macd_cross'] == 1) |
            #             (df['macd_cross'].shift(1) == 1) |
            #             (df['macd_cross'].shift(2) == 1)
            #         ) &
            #         (
            #             (df['hist_cross'] == 1) |
            #             (df['hist_cross'].shift(1) == 1) |
            #             (df['hist_cross'].shift(2) == 1)
            #         )
            #     ), 'buy'] = 1
            # df.loc[(
            #         (df['close'] < df['bb_low']) &
            #         (
            #             (df['macd_cross'] == -1) |
            #             (df['macd_cross'].shift(1) == -1) |
            #             (df['macd_cross'].shift(2) == -1)
            #         ) &
            #         (
            #             (df['hist_cross'] == -1) |
            #             (df['hist_cross'].shift(1) == -1) |
            #             (df['hist_cross'].shift(2) == -1)
            #         )
            #     ), 'buy'] = -1
            # if df.loc[len(df)-1]['buy'] != 0:
            #     t = threading.Thread(target=buy2, args=(100, pair, "call" if df.loc[len(df)-1]['buy'] == 1 else "put", 120,))
            #     t.start()

            # Strategy 4, period: 60
            # df['ma1'] = ta.SMA(df["close"], timeperiod=4)
            # df['ma2'] = ta.SMA(df["close"], timeperiod=45)
            # # df['ma1'] = ta.EMA(df["close"], timeperiod=8)
            # # df['ma2'] = ta.EMA(df["close"], timeperiod=21)
            # # df['willr'] = ta.WILLR(df, timeperiod=7)
            # df['buy'], df['ma_cross'] = 0, 0
            # df.loc[(qtpylib.crossed_above(df['ma1'], df['ma2'])), 'ma_cross'] = 1
            # df.loc[(qtpylib.crossed_below(df['ma1'], df['ma2'])), 'ma_cross'] = -1
            # df.loc[(
            #         (df['ma_cross'] == 1)
            #     ), 'buy'] = 1
            # df.loc[(
            #         (df['ma_cross'] == -1)
            #     ), 'buy'] = -1
            # if df.loc[len(df)-1]['buy'] != 0:
            #     t = threading.Thread(target=buy2, args=(100, pair, "call" if df.loc[len(df)-1]['buy'] == 1 else "put", 180,))
            #     t.start()

            # Strategy 3, period: 60
            # heikinashi = qtpylib.heikinashi(df)
            # df['ha_open'] = heikinashi['open']
            # df['ha_close'] = heikinashi['close']
            # df['ha_high'] = heikinashi['high']
            # df['ha_low'] = heikinashi['low']
            # df['ma1'] = ta.SMA(df["ha_close"], timeperiod=5)
            # df['ma2'] = ta.SMA(df["ha_close"], timeperiod=10)
            # df['macd'], df['macdsignal'], df['macdhist'] = ta.MACD(df['ha_close'], 8, 26, 9)
            # df['buy'], df['ma_cross'], df['macd_cross'] = 0, 0, 0
            # df.loc[(qtpylib.crossed_above(df['ma1'], df['ma2'])), 'ma_cross'] = 1
            # df.loc[(qtpylib.crossed_below(df['ma1'], df['ma2'])), 'ma_cross'] = -1
            # df.loc[(qtpylib.crossed_above(df['macd'], df['macdsignal'])), 'macd_cross'] = 1
            # df.loc[(qtpylib.crossed_below(df['macd'], df['macdsignal'])), 'macd_cross'] = -1
            # df.loc[(
            #         (
            #             (df['ma_cross'] == 1) &
            #             (
            #                 (df['macd_cross'] == 1) |
            #                 (df['macd_cross'].shift(1) == 1)
            #             ) &
            #             (df['macdhist'] > 0)
            #         ) |
            #         (
            #             (df['macd_cross'] == 1) &
            #             (
            #                 (df['ma_cross'] == 1) |
            #                 (df['ma_cross'].shift(1) == 1)
            #             ) &
            #             (df['macdhist'] > 0) &
            #             (df['macd'] < 0)
            #         )
            #     ), 'buy'] = 1
            # df.loc[(
            #         (
            #             (df['ma_cross'] == -1) &
            #             (
            #                 (df['macd_cross'] == -1) |
            #                 (df['macd_cross'].shift(1) == -1)
            #             ) &
            #             (df['macdhist'] < 0)
            #         ) |
            #         (
            #             (df['macd_cross'] == -1) &
            #             (
            #                 (df['ma_cross'] == -1) |
            #                 (df['ma_cross'].shift(1) == -1)
            #             ) &
            #             (df['macdhist'] < 0) &
            #             (df['macd'] > 0)
            #         )
            #     ), 'buy'] = -1
            # if df.loc[len(df)-1]['buy'] != 0:
            #     t = threading.Thread(target=buy, args=(100, pair, "call" if df.loc[len(df)-1]['buy'] == 1 else "put", 60,))
            #     t.start()

            # Strategy 1, period: 60
            # df['ma1'] = ta.SMA(df["close"], timeperiod=5)
            # df['ma2'] = ta.SMA(df["close"], timeperiod=13)
            # df['ma3'] = ta.SMA(df["close"], timeperiod=45)
            # df['rsi'] = ta.RSI(df["close"], timeperiod=5)
            # df['ma12_cross'], df['ma13_cross'], df['ma23_cross'] = 0, 0, 0
            # df['ma1_trend'], df['ma2_trend'], df['ma3_trend'] = 0, 0, 0
            # df.loc[(df['ma1'] > df['ma1'].shift(1)), 'ma1_trend'] = 1
            # df.loc[(df['ma1'] < df['ma1'].shift(1)), 'ma1_trend'] = -1
            # df.loc[(df['ma2'] > df['ma2'].shift(1)), 'ma2_trend'] = 1
            # df.loc[(df['ma2'] < df['ma2'].shift(1)), 'ma2_trend'] = -1
            # df.loc[(df['ma3'] > df['ma3'].shift(1)), 'ma3_trend'] = 1
            # df.loc[(df['ma3'] < df['ma3'].shift(1)), 'ma3_trend'] = -1
            # df.loc[(qtpylib.crossed_above(df['ma1'], df['ma2'])), 'ma12_cross'] = 1
            # df.loc[(qtpylib.crossed_below(df['ma1'], df['ma2'])), 'ma12_cross'] = -1
            # df.loc[(qtpylib.crossed_above(df['ma1'], df['ma3'])), 'ma13_cross'] = 1
            # df.loc[(qtpylib.crossed_below(df['ma1'], df['ma3'])), 'ma13_cross'] = -1
            # df.loc[(qtpylib.crossed_above(df['ma2'], df['ma3'])), 'ma23_cross'] = 1
            # df.loc[(qtpylib.crossed_below(df['ma2'], df['ma3'])), 'ma23_cross'] = -1
            # df['buy'] = 0
            # df.loc[(
            #         (
            #             (df['ma13_cross'] == -1) |
            #             (df['ma23_cross'] == -1)
            #         ) &
            #         (df['ma3_trend'] == -1) &
            #         (df['rsi'] <= 35)
            #     ), 'buy'] = 1
            # df.loc[(
            #         (
            #             (df['ma13_cross'] == 1) |
            #             (df['ma23_cross'] == 1)
            #         ) &
            #         (df['ma3_trend'] == 1) &
            #         (df['rsi'] >= 65)
            #     ), 'buy'] = -1
            # if df.loc[len(df)-1]['buy'] != 0:
            #     t = threading.Thread(target=buy, args=(100, pair, "call" if df.loc[len(df)-1]['buy'] == 1 else "put", 60,))
            #     t.start()

            # Strategy 2, period: 60
            # bollinger2 = qtpylib.bollinger_bands(qtpylib.typical_price(df), window=13, stds=2)
            # df['bb_low'] = bollinger2['lower']
            # df['bb_mid'] = bollinger2['mid']
            # df['bb_up'] = bollinger2['upper']
            # df['rsi1'] = ta.RSI(df["close"], timeperiod=5)
            # df['rsi2'] = ta.RSI(df["close"], timeperiod=20)
            # df['buy'] = 0
            # df.loc[(
            #         (df['close'] < df['bb_low']) &
            #         (df['rsi1'] <= 30) &
            #         (df['rsi2'] <= 50)
            #     ), 'buy'] = 1
            # df.loc[(
            #         (df['close'] > df['bb_up']) &
            #         (df['rsi1'] >= 70) &
            #         (df['rsi2'] >= 50)
            #     ), 'buy'] = -1
            # if df.loc[len(df)-1]['buy'] != 0:
            #     t = threading.Thread(target=buy, args=(100, pair, "call" if df.loc[len(df)-1]['buy'] == 1 else "put", 60,))
            #     t.start()
#
#           ====================================================================================================================
#           Indicators =========================================================================================================
#           ====================================================================================================================
#             # Heikinashi
#             heikinashi = qtpylib.heikinashi(df)
#             df['ha_open'] = heikinashi['open']
#             df['ha_close'] = heikinashi['close']
#             df['ha_high'] = heikinashi['high']
#             df['ha_low'] = heikinashi['low']
#
#             # Accelerator Oscillator Indicator
#             df['hl2'] = (df['high'] + df['low']) / 2
#             df['ac'] = accelerator_oscillator(df, 5, 34, 5)
#
#             # Aroon, Aroon Oscillator
#             df['aroondown'], df['aroonup'] = ta.AROON(df['high'], df['low'], timeperiod=25)
#
#             # DeMarker
#             df['dem'] = DeMarker(df, 14)
#
#             # MACD
#             df['macd'], df['macdsignal'], df['macdhist'] = ta.MACD(df['ha_close'], 8, 26, 9)
#
#             # Rate of Change
#             df['roc'] = ta.ROC(df, timeperiod=10)
#
#             # ADX
#             df['adx'] = ta.ADX(df, timeperiod=14)
#             df['plus_di'] = ta.PLUS_DI(df, timeperiod=14)
#             df['minus_di'] = ta.MINUS_DI(df, timeperiod=14)
#
#             # ATR - Average True Range
#             df['atr'] = ta.ATR(df, timeframe=14)
#
#             # Bollinger Bands
#             bollinger = qtpylib.bollinger_bands(qtpylib.typical_price(df), window=5, stds=1)
#             df['bb_low'] = bollinger['lower']
#             df['bb_mid'] = bollinger['mid']
#             df['bb_up'] = bollinger['upper']
#
#             # CCI - Commodity Channel Index
#             df['cci'] = ta.CCI(df, timeperiod=20)
#
#             # MOM - Momentum
#             df['mom'] = ta.MOM(df, timeperiod=10)
#
#             # SAR - Parabolic SAR
#             df['sar'] = ta.SAR(df, 0.02, 0.2)
#
#             # Moving Average
#             df['ema'] = ta.EMA(df, timeperiod=10)
#             df['sma'] = ta.SMA(df, timeperiod=10)
#             df['wma'] = ta.WMA(df, timeperiod=10)
#
#             # RSI - Relative Strength Index
#             df['rsi'] = ta.RSI(df["close"], timeperiod=14)
#
#             # Stochastic Oscillator
#             df['slowk'], df['slowd'] = ta.STOCH(df['high'], df['low'], df['close'], fastk_period=14, slowk_period=3, slowk_matype=0, slowd_period=3, slowd_matype=0)
#
#             # Williams' %R
#             df['willr'] = ta.WILLR(df, timeperiod=14)
#
#             # Keltner Channel
#             kc = qtpylib.keltner_channel(df, window=14, atrs=2)
#             df['kc_upper'] = kc['upper']
#             df['kc_lower'] = kc['lower']
#             df['kc_mid'] = kc['mid']
#
#             # Vortex
#             df['vip'], df['vim'] = vortex_indicator(df, 14)

def prepare_get_history():
    try:
        data = get_payout()
        if data: return True
        else: return False
    except:
        return False

def prepare():
    try:
        data = get_payout()
        if data:
            data = get_df()
            if data: return True
            else: return False
        else: return False
    except:
        return False


def wait(sleep=True):
    dt = int(datetime.now().timestamp()) - int(datetime.now().second)
    if period == 60:
        dt += 60
    elif period == 30:
        if datetime.now().second < 30: dt += 30
        else: dt += 60
        if not sleep: dt -= 30
    elif period == 15:
        if datetime.now().second >= 45: dt += 60
        elif datetime.now().second >= 30: dt += 45
        elif datetime.now().second >= 15: dt += 30
        else: dt += 15
        if not sleep: dt -= 15
    elif period == 10:
        if datetime.now().second >= 50: dt += 60
        elif datetime.now().second >= 40: dt += 50
        elif datetime.now().second >= 30: dt += 40
        elif datetime.now().second >= 20: dt += 30
        elif datetime.now().second >= 10: dt += 20
        else: dt += 10
        if not sleep: dt -= 10
    elif period == 5:
        if datetime.now().second >= 55: dt += 60
        elif datetime.now().second >= 50: dt += 55
        elif datetime.now().second >= 45: dt += 50
        elif datetime.now().second >= 40: dt += 45
        elif datetime.now().second >= 35: dt += 40
        elif datetime.now().second >= 30: dt += 35
        elif datetime.now().second >= 25: dt += 30
        elif datetime.now().second >= 20: dt += 25
        elif datetime.now().second >= 15: dt += 20
        elif datetime.now().second >= 10: dt += 15
        elif datetime.now().second >= 5: dt += 10
        else: dt += 5
        if not sleep: dt -= 5
    elif period == 120:
        dt = int(datetime(int(datetime.now().year), int(datetime.now().month), int(datetime.now().day), int(datetime.now().hour), int(math.floor(int(datetime.now().minute) / 2) * 2), 0).timestamp())
        dt += 120
    elif period == 180:
        dt = int(datetime(int(datetime.now().year), int(datetime.now().month), int(datetime.now().day), int(datetime.now().hour), int(math.floor(int(datetime.now().minute) / 3) * 3), 0).timestamp())
        dt += 180
    elif period == 300:
        dt = int(datetime(int(datetime.now().year), int(datetime.now().month), int(datetime.now().day), int(datetime.now().hour), int(math.floor(int(datetime.now().minute) / 5) * 5), 0).timestamp())
        dt += 300
    elif period == 600:
        dt = int(datetime(int(datetime.now().year), int(datetime.now().month), int(datetime.now().day), int(datetime.now().hour), int(math.floor(int(datetime.now().minute) / 10) * 10), 0).timestamp())
        dt += 600
    if sleep:
        global_value.logger('======== Sleeping %s Seconds ========' % str(dt - int(datetime.now().timestamp())), "INFO")
        return dt - int(datetime.now().timestamp())

    return dt


def start():
    while global_value.websocket_is_connected is False:
        time.sleep(0.1)
    time.sleep(2)
    saldo = api.get_balance()
    global_value.logger('Account Balance: %s' % str(saldo), "INFO")
    prep = prepare()
    if prep:
        while True:
            strategie()
            time.sleep(wait())


def start_get_history():
    while global_value.websocket_is_connected is False:
        time.sleep(0.1)
    time.sleep(2)
    saldo = api.get_balance()
    global_value.logger('Account Balance: %s' % str(saldo), "INFO")
    prep = prepare_get_history()
    if prep:
        i = 0
        for pair in global_value.pairs:
            i += 1
            global_value.logger('%s (%s/%s)' % (str(pair), str(i), str(len(global_value.pairs))), "INFO")
            if not global_value.check_cache(str(global_value.pairs[pair]["id"])):
                time_red = int(datetime.now().timestamp()) - 86400 * 7
                df = api.get_history(pair, period, end_time=time_red)


if __name__ == "__main__":
    start()
    end_counter = time.perf_counter()
    rund = math.ceil(end_counter - start_counter)
    # print(f'CPU-gebundene Task-Zeit: {rund} {end_counter - start_counter} Sekunden')
    global_value.logger("CPU-gebundene Task-Zeit: %s Sekunden" % str(int(end_counter - start_counter)), "INFO")

