# Binance Trading Bot Web Application

## Overview
This project is a web-based trading bot for Binance Futures, built with Flask. It allows users to view market data, manage their Binance account, and place/cancel orders directly from a web interface. The application uses the official Binance API and supports both testnet and mainnet environments.

## Architecture
- **Flask Web Server**: Handles HTTP requests, serves HTML templates, and exposes RESTful API endpoints.
- **binance_client.py**: Encapsulates all interactions with the Binance API, including authentication, market data retrieval, and order management.
- **config.py**: Centralizes configuration, including API keys, supported trading pairs, and order types.
- **utils/logger.py**: Provides logging for debugging and audit purposes.
- **templates/**: Contains HTML templates for the web interface.
- **static/**: Contains static assets (CSS, JS) for the frontend.

## Main Files
- `app.py`: Main Flask application, defines routes and API endpoints.
- `binance_client.py`: Binance API wrapper class.
- `config.py`: Configuration settings.
- `wsgi.py`: Entry point for WSGI servers.

## Endpoints
### Web Interface
- `/` : Main trading dashboard (HTML page).

### API Endpoints
- `GET /api/market-data` : Get market data for all supported symbols or a specific symbol (via `?symbol=SYMBOL`).
- `GET /api/account` : Get Binance account information.
- `GET /api/orders` : Get order history (optionally filter by `symbol` and `limit`).
- `GET /api/open-orders` : Get all open orders (optionally filter by `symbol`).
- `POST /api/place-order` : Place a new order. Requires JSON body with `symbol`, `side`, `order_type`, `quantity`, and optionally `price` and `stop_price`.
- `POST /api/cancel-order` : Cancel an order. Requires JSON body with `symbol` and `order_id`.

## Order Types Usage in API

The `/api/place-order` endpoint supports the following order types (as defined in `config.py`):
- `MARKET`: Executes immediately at the current market price. Requires `symbol`, `side`, `order_type`, and `quantity`.
- `LIMIT`: Executes at a specified price or better. Requires `symbol`, `side`, `order_type`, `quantity`, and `price`.
- `STOP`: Stop-Limit order. Triggers a limit order when the stop price is reached. Requires `symbol`, `side`, `order_type`, `quantity`, `price`, and `stop_price`.
- `STOP_MARKET`: Stop-Market order. Triggers a market order when the stop price is reached. Requires `symbol`, `side`, `order_type`, `quantity`, and `stop_price`.

### Error Handling
- Custom error pages for 404 and 500 errors.

## Configuration
- Edit `config.py` to set API keys and other settings.
- Supported trading pairs and order types are defined in `config.py`.

## Logging
- Logs are written to `trading_bot.log` as configured in `config.py`.

## Running the App
1. Install dependencies: `pip install -r requirements.txt`
2. Run with: `python app.py` or use `wsgi.py` for production.