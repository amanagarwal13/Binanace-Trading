from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException
import time
import hmac
import hashlib
import requests
import json
from urllib.parse import urlencode
from config import Config
from utils.logger import logger

class BinanceClient:
    def __init__(self, api_key=None, api_secret=None, testnet=True):
        """Initialize the Binance client with API credentials"""
        self.api_key = api_key or Config.API_KEY
        self.api_secret = api_secret or Config.API_SECRET
        self.testnet = testnet
        self.base_url = "https://testnet.binancefuture.com" if testnet else "https://fapi.binance.com"
        
        if not self.api_key or not self.api_secret:
            logger.error("API key and secret are required")
            raise ValueError("API key and secret are required")
        
        # Initialize the Binance python client
        try:
            self.client = Client(self.api_key, self.api_secret, testnet=self.testnet)
            logger.info("Binance client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Binance client: {str(e)}")
            raise
    
    def _get_timestamp(self):
        """Get current timestamp in milliseconds"""
        return int(time.time() * 1000)
    
    def _generate_signature(self, query_string):
        """Generate HMAC-SHA256 signature for API request"""
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _make_request(self, method, endpoint, params=None):
        """Make a request to the Binance API"""
        url = f"{self.base_url}{endpoint}"
        timestamp = self._get_timestamp()
        
        # Add timestamp to params
        if params is None:
            params = {}
        params['timestamp'] = timestamp
        
        # Generate query string and signature
        query_string = urlencode(params)
        signature = self._generate_signature(query_string)
        
        # Add signature to params
        params['signature'] = signature
        
        # Set up headers
        headers = {
            'X-MBX-APIKEY': self.api_key,
            'Content-Type': 'application/json'
        }
        
        # Log the request details (excluding API credentials)
        safe_params = {k: v for k, v in params.items() if k not in ['signature']}
        logger.info(f"Making {method} request to {endpoint} with params: {safe_params}")
        
        try:
            # Make the request
            if method == 'GET':
                response = requests.get(url, params=params, headers=headers)
            elif method == 'POST':
                # For POST requests, send data as form data
                response = requests.post(url, data=params, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, params=params, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            # Check if request was successful
            response.raise_for_status()
            
            # Log the response
            logger.info(f"Received response: {response.status_code}")
            logger.debug(f"Response content: {response.text}")
            
            return response.json()
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response content: {e.response.text}")
            raise
    
    def get_exchange_info(self):
        """Get exchange information"""
        try:
            endpoint = '/fapi/v1/exchangeInfo'
            return self._make_request('GET', endpoint)
        except Exception as e:
            logger.error(f"Failed to get exchange info: {str(e)}")
            raise
    
    def get_account_info(self):
        """Get account information"""
        try:
            endpoint = '/fapi/v2/account'
            return self._make_request('GET', endpoint)
        except Exception as e:
            logger.error(f"Failed to get account info: {str(e)}")
            raise
    
    def get_market_price(self, symbol):
        """Get current market price for a symbol"""
        try:
            endpoint = '/fapi/v1/ticker/price'
            params = {'symbol': symbol}
            return self._make_request('GET', endpoint, params)
        except Exception as e:
            logger.error(f"Failed to get market price for {symbol}: {str(e)}")
            raise
    
    def get_market_data(self, symbols=None):
        """Get market data for all supported symbols or specified ones"""
        try:
            endpoint = '/fapi/v1/ticker/24hr'
            symbols_to_fetch = symbols or Config.SUPPORTED_SYMBOLS
            result = []
            
            for symbol in symbols_to_fetch:
                params = {'symbol': symbol}
                data = self._make_request('GET', endpoint, params)
                result.append(data)
            
            return result
        except Exception as e:
            logger.error(f"Failed to get market data: {str(e)}")
            raise
    
    def place_order(self, symbol, side, order_type, quantity, price=None, stop_price=None):
        """
        Place an order on Binance Futures
        
        Args:
            symbol (str): Trading pair symbol e.g. 'BTCUSDT'
            side (str): 'BUY' or 'SELL'
            order_type (str): 'MARKET', 'LIMIT', 'STOP', 'STOP_MARKET', etc.
            quantity (float): Order quantity
            price (float, optional): Order price, required for LIMIT orders
            stop_price (float, optional): Stop price, required for STOP orders
        
        Returns:
            dict: Order response from Binance API
        """
        try:
            endpoint = '/fapi/v1/order'
            params = {
                'symbol': symbol,
                'side': side,
                'type': order_type,
                'quantity': str(quantity),  # Convert to string as required by API
            }
            
            # Add price for LIMIT orders
            if order_type == 'LIMIT':
                if price is None:
                    raise ValueError("Price is required for LIMIT orders")
                params['price'] = str(price)  # Convert to string
                params['timeInForce'] = 'GTC'  # Good Till Cancelled
            
            # Add price and stop price for STOP (Stop-Limit) orders
            if order_type == 'STOP':
                if stop_price is None or price is None:
                    raise ValueError("Both stop price and limit price are required for STOP orders")
                params['stopPrice'] = str(stop_price)
                params['price'] = str(price)
                params['timeInForce'] = 'GTC'
            
            # Add stop price for STOP_MARKET and similar orders
            if order_type in ['STOP_MARKET', 'TAKE_PROFIT', 'TAKE_PROFIT_MARKET']:
                if stop_price is None:
                    raise ValueError("Stop price is required for this order type")
                params['stopPrice'] = str(stop_price)
            
            # Make the API request
            return self._make_request('POST', endpoint, params)
        
        except Exception as e:
            logger.error(f"Failed to place {order_type} {side} order for {symbol}: {str(e)}")
            raise
    
    def get_open_orders(self, symbol=None):
        """Get all open orders for a symbol or all symbols"""
        try:
            endpoint = '/fapi/v1/openOrders'
            params = {}
            if symbol:
                params['symbol'] = symbol
            
            return self._make_request('GET', endpoint, params)
        except Exception as e:
            logger.error(f"Failed to get open orders: {str(e)}")
            raise
    
    def get_order_history(self, symbol=None, limit=50):
        """Get order history for a symbol or all symbols"""
        try:
            endpoint = '/fapi/v1/allOrders'
            params = {'limit': limit}
            if symbol:
                params['symbol'] = symbol
            
            return self._make_request('GET', endpoint, params)
        except Exception as e:
            logger.error(f"Failed to get order history: {str(e)}")
            raise
    
    def cancel_order(self, symbol, order_id=None, orig_client_order_id=None):
        """Cancel an open order"""
        try:
            endpoint = '/fapi/v1/order'
            params = {'symbol': symbol}
            
            if order_id:
                params['orderId'] = order_id
            elif orig_client_order_id:
                params['origClientOrderId'] = orig_client_order_id
            else:
                raise ValueError("Either order_id or orig_client_order_id must be provided")
            
            return self._make_request('DELETE', endpoint, params)
        except Exception as e:
            logger.error(f"Failed to cancel order for {symbol}: {str(e)}")
            raise
    
    def place_oco_order(self, symbol, side, quantity, price, stop_price, stop_limit_price):
        """
        Place a One-Cancels-the-Other (OCO) order
        
        This is a composite order type that combines a limit order with a stop limit order.
        When one order is executed, the other is automatically canceled.
        
        Args:
            symbol (str): Trading pair symbol e.g. 'BTCUSDT'
            side (str): 'BUY' or 'SELL'
            quantity (float): Order quantity
            price (float): Limit order price
            stop_price (float): Stop trigger price
            stop_limit_price (float): Stop limit price
        
        Returns:
            dict: Order response from Binance API
        """
        try:
            endpoint = '/fapi/v1/order/oco'
            params = {
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'price': price,
                'stopPrice': stop_price,
                'stopLimitPrice': stop_limit_price,
                'stopLimitTimeInForce': 'GTC'  # Good Till Cancelled
            }
            
            return self._make_request('POST', endpoint, params)
        except Exception as e:
            logger.error(f"Failed to place OCO order for {symbol}: {str(e)}")
            raise
    
    def place_twap_order(self, symbol, side, total_quantity, num_orders, duration_mins):
        """
        Implement a Time-Weighted Average Price (TWAP) order
        
        This executes multiple smaller orders over a specified time period
        to minimize market impact and achieve an average execution price.
        
        Args:
            symbol (str): Trading pair symbol e.g. 'BTCUSDT'
            side (str): 'BUY' or 'SELL'
            total_quantity (float): Total order quantity
            num_orders (int): Number of orders to split into
            duration_mins (int): Duration in minutes over which to execute
        
        Returns:
            list: List of order responses
        """
        try:
            # Calculate order size and time interval
            order_size = float(total_quantity) / num_orders
            interval_secs = (duration_mins * 60) / num_orders
            
            logger.info(f"Starting TWAP order: {side} {total_quantity} {symbol} "
                       f"split into {num_orders} orders over {duration_mins} minutes")
            
            # Initialize response list
            responses = []
            
            # Execute orders at calculated intervals
            for i in range(num_orders):
                response = self.place_order(
                    symbol=symbol,
                    side=side,
                    order_type='MARKET',
                    quantity=order_size
                )
                responses.append(response)
                
                logger.info(f"TWAP order {i+1}/{num_orders} placed successfully")
                
                # Sleep between orders (except the last one)
                if i < num_orders - 1:
                    time.sleep(interval_secs)
            
            logger.info(f"TWAP order completed: {num_orders} orders executed")
            return responses
            
        except Exception as e:
            logger.error(f"Failed to execute TWAP order for {symbol}: {str(e)}")
            raise