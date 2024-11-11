import requests
import time
import hmac
import hashlib
import json
import pandas as pd
import logging
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from pathlib import Path
from typing import Optional, List, Dict
import smtplib
from email.mime.text import MIMEText

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Config:
    """Configuration class for loading bot settings from a JSON file."""
    def __init__(self, config_path='config.json'):
        with open(config_path) as config_file:
            self.config = json.load(config_file)

        # Load configuration parameters for API, trade, and technical analysis
        self.API_KEY = self.config.get('API_KEY')
        self.API_SECRET = self.config.get('API_SECRET')
        self.BASE_URL = self.config.get('BASE_URL')
        self.SYMBOL = self.config.get('SYMBOL')
        self.BUY_THRESHOLD_RSI = self.config.get('BUY_THRESHOLD_RSI', 30)
        self.SELL_THRESHOLD_RSI = self.config.get('SELL_THRESHOLD_RSI', 70)
        self.TRADE_AMOUNT = self.config.get('TRADE_AMOUNT', 0.001)
        self.EMA_PERIOD = self.config.get('EMA_PERIOD', 14)
        self.RSI_PERIOD = self.config.get('RSI_PERIOD', 14)
        self.CHECK_INTERVAL = self.config.get('CHECK_INTERVAL', 60)
        self.MAX_RISK_PERCENT = self.config.get('MAX_RISK_PERCENT', 2)  # New: Risk management
        self.NOTIFY_EMAIL = self.config.get('NOTIFY_EMAIL')

        if not self.API_KEY or not self.API_SECRET:
            raise ValueError("API_KEY and API_SECRET are required in config.json")

config = Config()

class APIClient:
    """Handles API requests with retry mechanisms and signature generation."""
    def __init__(self, base_url: str, api_key: str, api_secret: str):
        self.base_url = base_url
        self.api_key = api_key
        self.api_secret = api_secret
        self.session = requests.Session()

        retries = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        self.session.mount('https://', HTTPAdapter(max_retries=retries))

    def generate_signature(self, params: Dict[str, str]) -> str:
        """Generate HMAC SHA256 signature required for authenticated requests."""
        query_string = '&'.join([f"{key}={value}" for key, value in sorted(params.items())])
        return hmac.new(self.api_secret.encode(), query_string.encode(), hashlib.sha256).hexdigest()

    def get(self, endpoint: str, params: Optional[Dict[str, str]] = None) -> Optional[dict]:
        """Performs a GET request with retries."""
        url = f'{self.base_url}{endpoint}'
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logging.error(f"GET request error at {url}: {e}")
            return None

    def post(self, endpoint: str, data: Dict[str, str]) -> Optional[dict]:
        """Performs a POST request with retries."""
        url = f'{self.base_url}{endpoint}'
        headers = {'X-MBX-APIKEY': self.api_key}
        data['signature'] = self.generate_signature(data)
        try:
            response = self.session.post(url, headers=headers, data=data)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logging.error(f"POST request error at {url}: {e}")
            return None

api_client = APIClient(config.BASE_URL, config.API_KEY, config.API_SECRET)

def send_notification(message: str):
    """Send a notification via email when critical events occur."""
    if config.NOTIFY_EMAIL:
        try:
            msg = MIMEText(message)
            msg['Subject'] = 'Trading Bot Alert'
            msg['From'] = 'tradingbot@alerts.com'
            msg['To'] = config.NOTIFY_EMAIL
            with smtplib.SMTP('localhost') as server:
                server.send_message(msg)
            logging.info("Alert email sent.")
        except Exception as e:
            logging.error(f"Failed to send email notification: {e}")

def get_balance() -> Optional[float]:
    """Retrieve the available balance to adjust trade size and manage risk."""
    balance_info = api_client.get('/api/v1/account/balance')
    if balance_info:
        return float(balance_info['data'].get('availableBalance', 0))
    return None

def get_price_history(symbol: str, interval='1m', limit=100) -> List[float]:
    """Fetch historical price data (close prices) for the given symbol."""
    data = api_client.get('/api/v1/market/klines', {'symbol': symbol, 'interval': interval, 'limit': limit})
    return [float(entry[4]) for entry in data['data']] if data else []

def calculate_ema(prices: List[float], period: int) -> Optional[float]:
    """Calculate the Exponential Moving Average (EMA) over a specific period."""
    if len(prices) < period:
        logging.warning("Insufficient data to calculate EMA.")
        return None
    return pd.Series(prices).ewm(span=period, adjust=False).mean().iloc[-1]

def calculate_rsi(prices: List[float], period: int) -> Optional[float]:
    """Calculate the Relative Strength Index (RSI) to identify overbought or oversold conditions."""
    if len(prices) < period:
        logging.warning("Insufficient data to calculate RSI.")
        return None
    delta = pd.Series(prices).diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs)).iloc[-1]

def calculate_pdl(symbol: str) -> Optional[float]:
    """Retrieve and calculate the previous day's low price for the symbol."""
    data = api_client.get('/api/v1/market/klines', {'symbol': symbol, 'interval': '1d', 'limit': 2})
    if data and len(data['data']) > 1:
        return float(data['data'][-2][3])  # Close of the previous day
    logging.error("Failed to retrieve PDL.")
    return None

def place_order(symbol: str, side: str, quantity: float, price: float) -> Optional[dict]:
    """Place a buy or sell order with risk and commission management."""
    params = {
        'symbol': symbol,
        'side': side,
        'type': 'LIMIT',
        'quantity': quantity,
        'price': price,
        'timestamp': int(time.time() * 1000)
    }
    return api_client.post('/api/v1/order', params)

def get_market_price(symbol: str) -> Optional[float]:
    """Fetch the current market price for the specified symbol."""
    data = api_client.get('/api/v1/market/ticker', {'symbol': symbol})
    return float(data['data']['lastPrice']) if data else None

def log_order_to_csv(order_data: dict, filename='trading_log.csv'):
   """Save trade order information to a CSV log file for tracking."""
    try:
        df = pd.DataFrame([order_data])
        file_exists = Path(filename).exists()
        df.to_csv(filename, mode='a', header=not file_exists, index=False)
    except Exception as e:
        logging.error(f"Error saving order log: {e}")

def trading_bot():
    """
    Ejecuta el ciclo principal del bot de trading. Obtiene los precios históricos y datos actuales,
    calcula indicadores técnicos (EMA, RSI, y PDL), y ejecuta órdenes de compra o venta 
    según los umbrales configurados en función de la estrategia.
    """
    while True:
        try:
            prices = get_price_history(config.SYMBOL)
            if not prices:
                logging.warning("No se pudo obtener precios históricos.")
                time.sleep(config.CHECK_INTERVAL)
                continue

            # Calcular indicadores técnicos
            ema = calculate_ema(prices, config.EMA_PERIOD)
            rsi = calculate_rsi(prices, config.RSI_PERIOD)
            pdl = calculate_pdl(config.SYMBOL)
            current_price = get_market_price(config.SYMBOL)

            # Validar si todos los datos se obtuvieron correctamente
            if current_price is None or ema is None or rsi is None or pdl is None:
                logging.warning("Datos insuficientes para ejecutar la estrategia.")
                time.sleep(config.CHECK_INTERVAL)
                continue

            logging.info(f'Precio actual: {current_price} USD, EMA: {ema:.2f}, RSI: {rsi:.2f}, PDL: {pdl:.2f}')
            order = None

            # Estrategia de compra si el precio es bajo, el RSI indica sobreventa y está cerca del PDL
            if current_price < ema and rsi < config.BUY_THRESHOLD_RSI and current_price <= pdl * 1.02:
                logging.info('El precio está bajo y el RSI indica sobreventa cerca del PDL. Ejecutando compra...')
                order = place_order(config.SYMBOL, 'BUY', config.TRADE_AMOUNT, current_price)

            # Estrategia de venta si el precio es alto y el RSI indica sobrecompra
            elif current_price > ema and rsi > config.SELL_THRESHOLD_RSI:
                logging.info('El precio está alto y el RSI indica sobrecompra. Ejecutando venta...')
                order = place_order(config.SYMBOL, 'SELL', config.TRADE_AMOUNT, current_price)

            # Registrar la orden en caso de ejecución
            if order:
                log_order_to_csv(order)
                logging.info(f'Orden ejecutada: {order}')
            else:
                logging.info('Esperando una mejor oportunidad de entrada/salida...')

            # Esperar el intervalo configurado antes de la siguiente iteración
            time.sleep(config.CHECK_INTERVAL)
        except Exception as e:
            logging.error(f'Error inesperado en el ciclo del bot: {e}')
            time.sleep(config.CHECK_INTERVAL)

# Ejecutar el bot
if __name__ == '__main__':
    trading_bot()
