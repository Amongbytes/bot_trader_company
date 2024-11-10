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
from typing import Optional, List

# Configuración de log
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Config:
    """Clase de configuración para cargar y manejar parámetros del bot desde un archivo JSON."""
    def __init__(self, config_path='config.json'):
        with open(config_path) as config_file:
            self.config = json.load(config_file)
        
        # Cargar configuraciones esenciales para API, trade y análisis técnico
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

        # Verificar claves API
        if not self.API_KEY or not self.API_SECRET:
            raise ValueError("API_KEY y API_SECRET son necesarios en config.json")

config = Config()

class APIClient:
    """Cliente de API con manejo de solicitudes GET/POST y firma de autenticación para la API."""
    def __init__(self, base_url: str, api_key: str, api_secret: str):
        self.base_url = base_url
        self.api_key = api_key
        self.api_secret = api_secret
        self.session = requests.Session()

        # Configuración de reintentos para evitar fallos por latencia
        retries = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        self.session.mount('https://', HTTPAdapter(max_retries=retries))

    def generate_signature(self, params: dict) -> str:
        """Genera una firma HMAC para la autenticación de la API."""
        query_string = '&'.join([f"{key}={value}" for key, value in sorted(params.items())])
        return hmac.new(self.api_secret.encode(), query_string.encode(), hashlib.sha256).hexdigest()
    
    def get(self, endpoint: str, params: Optional[dict] = None) -> Optional[dict]:
        """Realiza una solicitud GET a la API, con manejo de errores."""
        url = f'{self.base_url}{endpoint}'
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logging.error(f"Error en solicitud GET a {url}: {e}")
            return None
    
    def post(self, endpoint: str, data: dict) -> Optional[dict]:
        """Realiza una solicitud POST a la API con autenticación de firma."""
        url = f'{self.base_url}{endpoint}'
        headers = {'X-MBX-APIKEY': self.api_key}
        data['signature'] = self.generate_signature(data)
        try:
            response = self.session.post(url, headers=headers, data=data)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logging.error(f"Error en solicitud POST a {url}: {e}")
            return None

api_client = APIClient(config.BASE_URL, config.API_KEY, config.API_SECRET)

def get_price_history(symbol: str, interval='1m', limit=100) -> List[float]:
    """Obtiene el historial de precios de un símbolo específico y lo devuelve como lista de floats."""
    data = api_client.get('/api/v1/market/klines', {'symbol': symbol, 'interval': interval, 'limit': limit})
    return [float(entry[4]) for entry in data['data']] if data else []

def calculate_ema(prices: List[float], period: int) -> Optional[float]:
    """Calcula la media móvil exponencial (EMA) para los precios dados y el período especificado."""
    if len(prices) < period:
        logging.warning("Datos insuficientes para calcular la EMA.")
        return None
    return pd.Series(prices).ewm(span=period, adjust=False).mean().iloc[-1]

def calculate_rsi(prices: List[float], period: int) -> Optional[float]:
    """Calcula el Índice de Fuerza Relativa (RSI) de una lista de precios y un período especificado."""
    if len(prices) < period:
        logging.warning("Datos insuficientes para calcular el RSI.")
        return None
    delta = pd.Series(prices).diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs)).iloc[-1]

def calculate_pdl(symbol: str) -> Optional[float]:
    """Calcula el Precio de Cierre del Día Anterior (PDL) para un símbolo específico."""
    data = api_client.get('/api/v1/market/klines', {'symbol': symbol, 'interval': '1d', 'limit': 2})
    if data and len(data['data']) > 1:
        return float(data['data'][-2][3])  # Precio de cierre del día anterior
    logging.error("No se pudo obtener el PDL.")
    return None

def place_order(symbol: str, side: str, quantity: float, price: float) -> Optional[dict]:
    """Coloca una orden de compra o venta en la API con los parámetros especificados."""
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
    """Obtiene el precio actual de mercado para un símbolo específico."""
    data = api_client.get('/api/v1/market/ticker', {'symbol': symbol})
    return float(data['data']['lastPrice']) if data else None

def log_order_to_csv(order_data: dict, filename='trading_log.csv'):
    """Registra los datos de una orden en un archivo CSV para seguimiento de operaciones."""
    try:
        df = pd.DataFrame([order_data])
        file_exists = Path(filename).exists()
        df.to_csv(filename, mode='a', header=not file_exists, index=False)
    except Exception as e:
        logging.error(f"Error al guardar el registro de la orden: {e}")

def trading_bot():
    """Función principal del bot de trading para ejecutar la estrategia de trading en bucle."""
    while True:
        try:
            # Obtener precios históricos y calcular indicadores
            prices = get_price_history(config.SYMBOL)
            if not prices:
                time.sleep(config.CHECK_INTERVAL)
                continue

            ema = calculate_ema(prices, config.EMA_PERIOD)
            rsi = calculate_rsi(prices, config.RSI_PERIOD)
            pdl = calculate_pdl(config.SYMBOL)
            current_price = get_market_price(config.SYMBOL)

            if current_price is None or ema is None or rsi is None or pdl is None:
                time.sleep(config.CHECK_INTERVAL)
                continue

            logging.info(f'Precio actual: {current_price} USD, EMA: {ema:.2f}, RSI: {rsi:.2f}, PDL: {pdl:.2f}')
            order = None

            # Condiciones de compra/venta según los indicadores y niveles de PDL
            if current_price < ema and rsi < config.BUY_THRESHOLD_RSI and current_price <= pdl * 1.02:
                logging.info('El precio está bajo y el RSI indica sobreventa cerca del PDL. Comprando...')
                order = place_order(config.SYMBOL, 'BUY', config.TRADE_AMOUNT, current_price)
            elif current_price > ema and rsi > config.SELL_THRESHOLD_RSI:
                logging.info('El precio está alto y el RSI indica sobrecompra. Vendiendo...')
                order = place_order(config.SYMBOL, 'SELL', config.TRADE_AMOUNT, current_price)
                
            if order:
                log_order_to_csv(order)
                logging.info(f'Orden ejecutada: {order}')
            else:
                logging.info('Esperando una mejor oportunidad...')

            time.sleep(config.CHECK_INTERVAL)
        except Exception as e:
            logging.error(f'Error inesperado: {e}')
            time.sleep(config.CHECK_INTERVAL)

if __name__ == '__main__':
    trading_bot()
