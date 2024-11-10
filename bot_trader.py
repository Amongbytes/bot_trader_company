import requests
import time
import hmac
import hashlib
import json
import numpy as np
import pandas as pd

# Configuración
API_KEY = 'TU_API_KEY'
API_SECRET = 'TU_API_SECRET'
BASE_URL = 'https://api.bitflex.com'

# Parámetros de trading
SYMBOL = 'BTCUSDT'  # Par de trading
BUY_THRESHOLD_RSI = 30  # RSI para señal de compra
SELL_THRESHOLD_RSI = 70  # RSI para señal de venta
TRADE_AMOUNT = 0.001  # Cantidad de BTC a comprar/vender
EMA_PERIOD = 14  # Periodo de EMA
RSI_PERIOD = 14  # Periodo de RSI

# Función para generar la firma de la solicitud
def generate_signature(params, secret):
    query_string = '&'.join([f"{key}={value}" for key, value in sorted(params.items())])
    signature = hmac.new(secret.encode(), query_string.encode(), hashlib.sha256).hexdigest()
    return signature

# Función para obtener el historial de precios
def get_price_history(symbol, interval='1m', limit=100):
    url = f'{BASE_URL}/api/v1/market/klines?symbol={symbol}&interval={interval}&limit={limit}'
    response = requests.get(url)
    data = response.json()
    return [float(entry[4]) for entry in data['data']]  # Precio de cierre

# Función para calcular EMA
def calculate_ema(prices, period):
    return pd.Series(prices).ewm(span=period, adjust=False).mean().iloc[-1]

# Función para calcular RSI
def calculate_rsi(prices, period):
    delta = pd.Series(prices).diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs)).iloc[-1]

# Función para realizar una orden de compra/venta
def place_order(symbol, side, quantity):
    url = f'{BASE_URL}/api/v1/order'
    timestamp = int(time.time() * 1000)
    params = {
        'symbol': symbol,
        'side': side,
        'type': 'LIMIT',
        'quantity': quantity,
        'price': get_market_price(symbol),
        'timestamp': timestamp
    }
    signature = generate_signature(params, API_SECRET)
    headers = {
        'X-MBX-APIKEY': API_KEY
    }
    params['signature'] = signature
    response = requests.post(url, headers=headers, data=params)
    return response.json()

# Función para obtener el precio actual del mercado
def get_market_price(symbol):
    url = f'{BASE_URL}/api/v1/market/ticker?symbol={symbol}'
    response = requests.get(url)
    data = response.json()
    return float(data['data']['lastPrice'])

# Función principal del bot
def trading_bot():
    while True:
        try:
            # Obtener historial de precios y calcular indicadores técnicos
            prices = get_price_history(SYMBOL)
            ema = calculate_ema(prices, EMA_PERIOD)
            rsi = calculate_rsi(prices, RSI_PERIOD)
            current_price = get_market_price(SYMBOL)
            
            print(f'Precio actual: {current_price} USD, EMA: {ema}, RSI: {rsi}')

            # Estrategia de trading basada en EMA y RSI
            if current_price < ema and rsi < BUY_THRESHOLD_RSI:
                print('El precio está bajo y el RSI indica sobreventa. Comprando...')
                order = place_order(SYMBOL, 'BUY', TRADE_AMOUNT)
                print('Orden de compra ejecutada:', order)
            elif current_price > ema and rsi > SELL_THRESHOLD_RSI:
                print('El precio está alto y el RSI indica sobrecompra. Vendiendo...')
                order = place_order(SYMBOL, 'SELL', TRADE_AMOUNT)
                print('Orden de venta ejecutada:', order)
            else:
                print('Esperando una mejor oportunidad...')

            # Esperar antes de revisar nuevamente
            time.sleep(60)

        except Exception as e:
            print('Error:', e)
            time.sleep(60)

# Ejecutar el bot
if __name__ == '__main__':
    trading_bot()
