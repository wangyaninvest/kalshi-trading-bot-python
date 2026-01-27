import requests
import base64
import time
from typing import Any, Dict, Optional
from datetime import datetime, timedelta
from enum import Enum
import json

from requests.exceptions import HTTPError

from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.exceptions import InvalidSignature

import websockets

class Environment(Enum):
    DEMO = "demo"
    PROD = "prod"

class KalshiBaseClient:
    """Base client class for interacting with the Kalshi API."""
    def __init__(
        self,
        key_id: str,
        private_key: rsa.RSAPrivateKey,
        environment: Environment = Environment.DEMO,
    ):
        """Initializes the client with the provided API key and private key.

        Args:
            key_id (str): Your Kalshi API key ID.
            private_key (rsa.RSAPrivateKey): Your RSA private key.
            environment (Environment): The API environment to use (DEMO or PROD).
        """
        self.key_id = key_id
        self.private_key = private_key
        self.environment = environment
        self.last_api_call = datetime.now()

        if self.environment == Environment.DEMO:
            self.HTTP_BASE_URL = "https://demo-api.kalshi.co"
            self.WS_BASE_URL = "wss://demo-api.kalshi.co"
        elif self.environment == Environment.PROD:
            self.HTTP_BASE_URL = "https://api.elections.kalshi.com"
            self.WS_BASE_URL = "wss://api.elections.kalshi.com"
        else:
            raise ValueError("Invalid environment")

    def request_headers(self, method: str, path: str) -> Dict[str, Any]:
        """Generates the required authentication headers for API requests."""
        current_time_milliseconds = int(time.time() * 1000)
        timestamp_str = str(current_time_milliseconds)

        # Remove query params from path
        path_parts = path.split('?')

        msg_string = timestamp_str + method + path_parts[0]
        signature = self.sign_pss_text(msg_string)

        headers = {
            "Content-Type": "application/json",
            "KALSHI-ACCESS-KEY": self.key_id,
            "KALSHI-ACCESS-SIGNATURE": signature,
            "KALSHI-ACCESS-TIMESTAMP": timestamp_str,
        }
        return headers

    def sign_pss_text(self, text: str) -> str:
        """Signs the text using RSA-PSS and returns the base64 encoded signature."""
        message = text.encode('utf-8')
        try:
            signature = self.private_key.sign(
                message,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.DIGEST_LENGTH
                ),
                hashes.SHA256()
            )
            return base64.b64encode(signature).decode('utf-8')
        except InvalidSignature as e:
            raise ValueError("RSA sign PSS failed") from e

class KalshiHttpClient(KalshiBaseClient):
    """Client for handling HTTP connections to the Kalshi API."""
    def __init__(
        self,
        key_id: str,
        private_key: rsa.RSAPrivateKey,
        environment: Environment = Environment.DEMO,
    ):
        super().__init__(key_id, private_key, environment)
        self.host = self.HTTP_BASE_URL
        self.exchange_url = "/trade-api/v2/exchange"
        self.markets_url = "/trade-api/v2/markets"
        self.portfolio_url = "/trade-api/v2/portfolio"

    def rate_limit(self) -> None:
        """Built-in rate limiter to prevent exceeding API rate limits."""
        THRESHOLD_IN_MILLISECONDS = 100
        now = datetime.now()
        threshold_in_microseconds = 1000 * THRESHOLD_IN_MILLISECONDS
        threshold_in_seconds = THRESHOLD_IN_MILLISECONDS / 1000
        if now - self.last_api_call < timedelta(microseconds=threshold_in_microseconds):
            time.sleep(threshold_in_seconds)
        self.last_api_call = datetime.now()

    def raise_if_bad_response(self, response: requests.Response) -> None:
        """Raises an HTTPError if the response status code indicates an error."""
        if response.status_code not in range(200, 299):
            response.raise_for_status()

    def post(self, path: str, body: dict) -> Any:
        """Performs an authenticated POST request to the Kalshi API."""
        self.rate_limit()
        response = requests.post(
            self.host + path,
            json=body,
            headers=self.request_headers("POST", path)
        )
        self.raise_if_bad_response(response)
        return response.json()

    def get(self, path: str, params: Dict[str, Any] = {}) -> Any:
        """Performs an authenticated GET request to the Kalshi API."""
        self.rate_limit()
        response = requests.get(
            self.host + path,
            headers=self.request_headers("GET", path),
            params=params
        )
        self.raise_if_bad_response(response)
        return response.json()

    def delete(self, path: str, params: Dict[str, Any] = {}) -> Any:
        """Performs an authenticated DELETE request to the Kalshi API."""
        self.rate_limit()
        response = requests.delete(
            self.host + path,
            headers=self.request_headers("DELETE", path),
            params=params
        )
        self.raise_if_bad_response(response)
        return response.json()

    def get_balance(self) -> Dict[str, Any]:
        """Retrieves the account balance."""
        return self.get(self.portfolio_url + '/balance')

    def create_order(
        self,
        ticker: str,
        action: str,
        side: str,
        count: int,
        type: str = "market",
        yes_price: Optional[int] = None,
        no_price: Optional[int] = None,
        yes_price_dollars: Optional[str] = None,
        no_price_dollars: Optional[str] = None,
        expiration_ts: Optional[int] = None,
        sell_position_floor: Optional[int] = None,
        buy_max_cost: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Creates an order for a specific market.
        
        Args:
            ticker: Market ticker symbol
            action: 'buy' or 'sell'
            side: 'yes' or 'no'
            count: Number of contracts
            type: Order type ('market' or 'limit')
            yes_price: Limit price for YES side (in cents)
            no_price: Limit price for NO side (in cents)
            yes_price_dollars: Limit price for YES side (in dollars, string format)
            no_price_dollars: Limit price for NO side (in dollars, string format)
            expiration_ts: Order expiration timestamp
            sell_position_floor: Minimum position to maintain when selling
            buy_max_cost: Maximum cost for buy orders (in cents)
            
        Returns:
            Order creation response
        """
        body = {
            'ticker': ticker,
            'action': action,
            'side': side,
            'count': count,
            'type': type,
        }
        
        # Add optional parameters
        if yes_price is not None:
            body['yes_price'] = yes_price
        if no_price is not None:
            body['no_price'] = no_price
        if yes_price_dollars is not None:
            body['yes_price_dollars'] = yes_price_dollars
        if no_price_dollars is not None:
            body['no_price_dollars'] = no_price_dollars
        if expiration_ts is not None:
            body['expiration_ts'] = expiration_ts
        if sell_position_floor is not None:
            body['sell_position_floor'] = sell_position_floor
        if buy_max_cost is not None:
            body['buy_max_cost'] = buy_max_cost
            
        return self.post(f"{self.portfolio_url}/orders", body)

    def get_exchange_status(self) -> Dict[str, Any]:
        """Retrieves the exchange status."""
        return self.get(self.exchange_url + "/status")

    def get_trades(
        self,
        ticker: Optional[str] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        max_ts: Optional[int] = None,
        min_ts: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Retrieves trades based on provided filters."""
        params = {
            'ticker': ticker,
            'limit': limit,
            'cursor': cursor,
            'max_ts': max_ts,
            'min_ts': min_ts,
        }
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        return self.get(self.markets_url + '/trades', params=params)

    def get_markets(
        self,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        event_ticker: Optional[str] = None,
        series_ticker: Optional[str] = None,
        min_created_ts: Optional[int] = None,
        max_created_ts: Optional[int] = None,
        max_close_ts: Optional[int] = None,
        min_close_ts: Optional[int] = None,
        status: Optional[str] = None,
        tickers: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Retrieves markets based on provided filters."""
        params = {
            'limit': limit,
            'cursor': cursor,
            'event_ticker': event_ticker,
            'series_ticker': series_ticker,
            'min_created_ts': min_created_ts,
            'max_created_ts': max_created_ts,
            'max_close_ts': max_close_ts,
            'min_close_ts': min_close_ts,
            'status': status,
            'tickers': tickers,
        }
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        return self.get(self.markets_url, params=params)

    def get_market(self, ticker: str) -> Dict[str, Any]:
        """Retrieves a single market by ticker."""
        return self.get(f"{self.markets_url}/{ticker}")

    def get_market_orderbook(self, ticker: str, depth: Optional[int] = None) -> Dict[str, Any]:
        """Retrieves the orderbook for a specific market."""
        params = {}
        if depth is not None:
            params['depth'] = depth
        return self.get(f"{self.markets_url}/{ticker}/orderbook", params=params)

    def get_series(
        self,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        category: Optional[str] = None,
        include_volume: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Retrieves all series."""
        params = {}
        if limit is not None:
            params['limit'] = limit
        if cursor is not None:
            params['cursor'] = cursor
        if category is not None:
            params['category'] = category
        if include_volume is not None:
            params['include_volume'] = include_volume
        return self.get("/trade-api/v2/series", params=params)

    def get_single_series(self, series_ticker: str) -> Dict[str, Any]:
        """Retrieves a single series by ticker."""
        return self.get(f"/trade-api/v2/series/{series_ticker}")

class KalshiWebSocketClient(KalshiBaseClient):
    """Client for handling WebSocket connections to the Kalshi API."""
    def __init__(
        self,
        key_id: str,
        private_key: rsa.RSAPrivateKey,
        environment: Environment = Environment.DEMO,
    ):
        super().__init__(key_id, private_key, environment)
        self.ws = None
        self.url_suffix = "/trade-api/ws/v2"
        self.message_id = 1  # Add counter for message IDs

    async def connect(self):
        """Establishes a WebSocket connection using authentication."""
        host = self.WS_BASE_URL + self.url_suffix
        auth_headers = self.request_headers("GET", self.url_suffix)
        async with websockets.connect(host, additional_headers=auth_headers) as websocket:
            self.ws = websocket
            await self.on_open()
            await self.handler()

    async def on_open(self):
        """Callback when WebSocket connection is opened."""
        print("WebSocket connection opened.")
        await self.subscribe_to_tickers()

    async def subscribe_to_tickers(self):
        """Subscribe to ticker updates for all markets."""
        subscription_message = {
            "id": self.message_id,
            "cmd": "subscribe",
            "params": {
                "channels": ["ticker"]
            }
        }
        await self.ws.send(json.dumps(subscription_message))
        self.message_id += 1

    async def handler(self):
        """Handle incoming messages."""
        try:
            async for message in self.ws:
                await self.on_message(message)
        except websockets.ConnectionClosed as e:
            await self.on_close(e.code, e.reason)
        except Exception as e:
            await self.on_error(e)

    async def on_message(self, message):
        """Callback for handling incoming messages."""
        print("Received message:", message)

    async def on_error(self, error):
        """Callback for handling errors."""
        print("WebSocket error:", error)

    async def on_close(self, close_status_code, close_msg):
        """Callback when WebSocket connection is closed."""
        print("WebSocket connection closed with code:", close_status_code, "and message:", close_msg)