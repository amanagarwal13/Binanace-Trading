from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
import json
from datetime import datetime
from config import Config
from binance_client import BinanceClient
from utils.logger import logger
import os
from dotenv import load_dotenv

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Add context processor for datetime
@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

# Initialize Binance client
binance_client = None
try:
    binance_client = BinanceClient(
        api_key=Config.API_KEY,
        api_secret=Config.API_SECRET,
        testnet=Config.TESTNET
    )
    logger.info("Binance client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Binance client: {str(e)}")


@app.route('/')
def index():
    """Render the main trading interface"""
    try:
        # Get account information
        account_info = {}
        market_data = []
        
        if binance_client:
            try:
                account_info = binance_client.get_account_info()
                market_data = binance_client.get_market_data()
            except Exception as e:
                logger.error(f"Error fetching data: {str(e)}")
                flash(f"Error fetching data: {str(e)}", "error")
        
        # Format market data for display
        formatted_market_data = []
        for item in market_data:
            symbol = item.get('symbol', '')
            price = float(item.get('lastPrice', 0))
            volume = float(item.get('volume', 0))
            price_change_percent = float(item.get('priceChangePercent', 0))
            
            formatted_market_data.append({
                'symbol': symbol,
                'price': f"${price:,.2f}",
                'volume': f"{volume:,.0f}",
                'price_change_percent': price_change_percent,
                'price_change_class': 'text-success' if price_change_percent >= 0 else 'text-danger',
                'price_change_arrow': '↑' if price_change_percent >= 0 else '↓',
            })
        
        # Get supported symbols and order types for the form
        symbols = Config.SUPPORTED_SYMBOLS
        order_types = Config.ORDER_TYPES
        
        return render_template(
            'index.html',
            account_info=account_info,
            market_data=formatted_market_data,
            symbols=symbols,
            order_types=order_types
        )
    
    except Exception as e:
        logger.error(f"Error rendering index page: {str(e)}")
        return render_template('error.html', error=str(e))


@app.route('/api/market-data')
def get_market_data():
    """API endpoint to get current market data"""
    try:
        if not binance_client:
            return jsonify({'error': 'Binance client not initialized'}), 500
        
        symbol = request.args.get('symbol')
        
        if symbol:
            # Get 24hr data for a specific symbol (fix: use get_market_data)
            data = binance_client.get_market_data([symbol])
            # Return single object for consistency with frontend expectations
            return jsonify(data[0] if data else {})
        else:
            # Get data for all supported symbols
            data = binance_client.get_market_data()
            return jsonify(data)
    
    except Exception as e:
        logger.error(f"Error getting market data: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/account')
def get_account():
    """API endpoint to get account information"""
    try:
        if not binance_client:
            return jsonify({'error': 'Binance client not initialized'}), 500
        
        account_info = binance_client.get_account_info()
        return jsonify(account_info)
    
    except Exception as e:
        logger.error(f"Error getting account info: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/orders', methods=['GET'])
def get_orders():
    """API endpoint to get order history"""
    try:
        if not binance_client:
            return jsonify({'error': 'Binance client not initialized'}), 500
        
        symbol = request.args.get('symbol')
        limit = request.args.get('limit', 50, type=int)
        
        orders = binance_client.get_order_history(symbol=symbol, limit=limit)
        return jsonify(orders)
    
    except Exception as e:
        logger.error(f"Error getting orders: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/open-orders', methods=['GET'])
def get_open_orders():
    """API endpoint to get open orders"""
    try:
        if not binance_client:
            return jsonify({'error': 'Binance client not initialized'}), 500
        
        symbol = request.args.get('symbol')
        
        open_orders = binance_client.get_open_orders(symbol=symbol)
        return jsonify(open_orders)
    
    except Exception as e:
        logger.error(f"Error getting open orders: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/place-order', methods=['POST'])
def place_order():
    """API endpoint to place an order"""
    try:
        if not binance_client:
            return jsonify({'error': 'Binance client not initialized'}), 500
        
        data = request.json
        
        # Extract order parameters
        symbol = data.get('symbol')
        side = data.get('side')
        order_type = data.get('order_type')
        quantity = float(data.get('quantity', 0))
        price = float(data.get('price', 0)) if data.get('price') else None
        stop_price = float(data.get('stop_price', 0)) if data.get('stop_price') else None
        
        # Validate required parameters
        if not all([symbol, side, order_type, quantity]):
            return jsonify({'error': 'Missing required parameters'}), 400
        
        # Place the order
        response = binance_client.place_order(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price
        )
        
        logger.info(f"Order placed successfully: {response}")
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error placing order: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/cancel-order', methods=['POST'])
def cancel_order():
    """API endpoint to cancel an order"""
    try:
        if not binance_client:
            return jsonify({'error': 'Binance client not initialized'}), 500
        
        data = request.json
        
        # Extract parameters
        symbol = data.get('symbol')
        order_id = data.get('order_id')
        
        # Validate required parameters
        if not all([symbol, order_id]):
            return jsonify({'error': 'Missing required parameters'}), 400
        
        # Cancel the order
        response = binance_client.cancel_order(
            symbol=symbol,
            order_id=order_id
        )
        
        logger.info(f"Order cancelled successfully: {response}")
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error cancelling order: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    return render_template('error.html', error='Page not found'), 404


@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    return render_template('error.html', error='Server error'), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)