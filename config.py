import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or '123'
    API_KEY = "81e878117205d005e51c7fde7a61cb63e627c2674021b7853019764e5161b22d"
    API_SECRET = "e32ee9380b82c4fc6dfeac86591f0508e46d32d3c8eddafb0e394328fa1ff7d1"
    TESTNET = True
    BASE_URL = 'https://testnet.binancefuture.com'
    # Trading pairs to support
    SUPPORTED_SYMBOLS = [
        'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'DOGEUSDT',
        'XRPUSDT', 'DOTUSDT', 'LINKUSDT', 'LTCUSDT', 'BCHUSDT'
    ]
    # Order types
    ORDER_TYPES = ['MARKET', 'LIMIT', 'STOP', 'STOP_MARKET', 'TAKE_PROFIT', 'TAKE_PROFIT_MARKET']
    # Logging
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'trading_bot.log'