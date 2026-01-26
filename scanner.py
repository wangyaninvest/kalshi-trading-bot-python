"""
Market scanner for Kalshi prediction markets.
"""
import csv
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
from clients import KalshiHttpClient


class MarketScanner:
    """Scans Kalshi markets based on specific criteria."""
    
    def __init__(self, client: KalshiHttpClient, csv_file: str = "data/top_series.csv"):
        """Initialize the scanner.
        
        Args:
            client: An authenticated KalshiHttpClient instance.
            csv_file: Path to the CSV file containing top series.
        """
        self.client = client
        self.csv_file = csv_file
    
    def scan_markets(
        self,
        days_until_close: int = 3,
        days_after_start: int = 1,
        min_probability: float = 0.90,
        max_probability: float = 0.99,
        require_liquidity: bool = False
    ) -> List[Dict[str, Any]]:
        """Scan markets from top series and filter by criteria.
        
        Args:
            days_until_close: Maximum days until market closes (default: 3)
            days_after_start: Minimum days since market opened (default: 1)
            min_probability: Minimum mid-market probability threshold (default: 0.90)
            max_probability: Maximum mid-market probability threshold (default: 0.99)
            require_liquidity: Whether to require open orders (default: False)
        
        Returns:
            List of markets meeting the criteria with relevant details.
        """
        print(f"Scanning markets with criteria:")
        print(f"  - Closing within {days_until_close} days")
        print(f"  - Open for at least {days_after_start} days")
        print(f"  - Probability between {min_probability * 100}% and {max_probability * 100}%")
        print(f"  - Liquidity required: {require_liquidity}")
        print()
        
        # Read series tickers from CSV
        series_tickers = self._load_series_from_csv()
        if not series_tickers:
            print("No series found in CSV file.")
            return []
        
        print(f"Loaded {len(series_tickers)} series from {self.csv_file}")
        
        # Calculate the timestamp threshold
        target_time = datetime.now() + timedelta(days=days_until_close)
        max_close_ts = int(target_time.timestamp())
        
        # Fetch markets for each series
        print("Fetching markets for each series...")
        matching_markets = []
        
        for i, ticker in enumerate(series_tickers, 1):
            print(f"  [{i}/{len(series_tickers)}] Processing {ticker}...", end=" ")
            try:
                cursor = None
                series_markets = []
                
                # Paginate through all markets for this series
                while True:
                    response = self.client.get_markets(
                        series_ticker=ticker,
                        status='open',
                        max_close_ts=max_close_ts,
                        limit=1000,
                        cursor=cursor
                    )
                    markets = response.get('markets', [])
                    
                    if not markets:
                        break
                    
                    series_markets.extend(markets)
                    
                    cursor = response.get('cursor')
                    if not cursor:
                        break
                
                if not series_markets:
                    print("no markets")
                    continue
                
                # Filter markets by criteria
                matched = 0
                for market in series_markets:
                    if self._meets_criteria(
                        market,
                        days_until_close,
                        days_after_start,
                        min_probability,
                        max_probability,
                        require_liquidity
                    ):
                        matching_markets.append(self._format_market_info(market))
                        matched += 1
                
                print(f"{matched} matched" if matched > 0 else "no matches")
                
            except Exception as e:
                print(f"error: {e}")
                continue
        
        print(f"\nFound {len(matching_markets)} matching markets!")
        return matching_markets
    
    def _load_series_from_csv(self) -> List[str]:
        """Load series tickers from CSV file."""
        if not os.path.exists(self.csv_file):
            print(f"CSV file not found: {self.csv_file}")
            return []
        
        series_tickers = []
        try:
            with open(self.csv_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    ticker = row.get('Ticker')
                    if ticker:
                        series_tickers.append(ticker)
        except Exception as e:
            print(f"Error reading CSV file: {e}")
            return []
        
        return series_tickers
    
    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse ISO timestamp and handle microseconds with more than 6 digits.
        
        Args:
            timestamp_str: ISO format timestamp string
            
        Returns:
            Parsed datetime object
        """
        timestamp_str = timestamp_str.replace('Z', '+00:00')
        
        # Handle microseconds with more than 6 digits by truncating
        if '.' in timestamp_str and '+' in timestamp_str:
            parts = timestamp_str.split('.')
            microseconds_and_tz = parts[1].split('+')
            if len(microseconds_and_tz[0]) > 6:
                microseconds_and_tz[0] = microseconds_and_tz[0][:6]
            timestamp_str = f"{parts[0]}.{microseconds_and_tz[0]}+{microseconds_and_tz[1]}"
        
        return datetime.fromisoformat(timestamp_str)
    
    def _calculate_probabilities(self, market: Dict[str, Any]) -> tuple[float, float]:
        """Calculate mid-market probabilities for YES and NO sides.
        
        Args:
            market: Market data from API
            
        Returns:
            Tuple of (yes_probability, no_probability)
        """
        yes_bid = float(market.get('yes_bid_dollars', 0))
        yes_ask = float(market.get('yes_ask_dollars', 0))
        no_bid = float(market.get('no_bid_dollars', 0))
        no_ask = float(market.get('no_ask_dollars', 0))
        
        yes_prob = (yes_bid + yes_ask) / 2 if (yes_bid > 0 and yes_ask > 0) else 0
        no_prob = (no_bid + no_ask) / 2 if (no_bid > 0 and no_ask > 0) else 0
        
        return yes_prob, no_prob
    
    def _meets_criteria(
        self,
        market: Dict[str, Any],
        days_until_close: int,
        days_after_start: int,
        min_probability: float,
        max_probability: float,
        require_liquidity: bool
    ) -> bool:
        """Check if a market meets all criteria.
        
        Args:
            market: Market data from API
            days_until_close: Maximum days until close
            days_after_start: Minimum days since market opened
            min_probability: Minimum mid-market probability threshold
            max_probability: Maximum mid-market probability threshold
            require_liquidity: Whether to check for liquidity
        
        Returns:
            True if market meets all criteria, False otherwise.
        """
        # Check status is 'active'
        if market.get('status') != 'active':
            return False
        
        # Check market_type is 'binary'
        if market.get('market_type') != 'binary':
            return False
        
        try:
            # Check close time
            close_time = self._parse_timestamp(market.get('close_time', ''))
            now = datetime.now(close_time.tzinfo)
            days_remaining = (close_time - now).total_seconds() / (24 * 3600)
            
            if days_remaining > days_until_close or days_remaining < 0:
                return False
            
            # Check open time (days since market opened for trading)
            open_time = self._parse_timestamp(market.get('open_time', ''))
            days_since_opened = (now - open_time).total_seconds() / (24 * 3600)
            
            if days_since_opened < days_after_start:
                return False
        except Exception:
            # Skip markets with invalid timestamps
            return False
        
        # Calculate mid-market probabilities (average of bid and ask)
        yes_prob, no_prob = self._calculate_probabilities(market)
        
        # Check if highest probability is within the specified range
        max_prob = max(yes_prob, no_prob)
        if max_prob < min_probability or max_prob > max_probability:
            return False
        
        # Check liquidity if required
        if require_liquidity:
            ticker = market.get('ticker')
            if not self._has_liquidity(ticker):
                return False
        
        return True
    
    def _has_liquidity(self, ticker: str) -> bool:
        """Check if a market has liquidity (open orders)."""
        try:
            orderbook = self.client.get_market_orderbook(ticker, depth=1)
            
            # Check if there are any open orders on either side
            yes_orders = orderbook.get('orderbook', {}).get('yes', [])
            no_orders = orderbook.get('orderbook', {}).get('no', [])
            
            return len(yes_orders) > 0 or len(no_orders) > 0
        except Exception as e:
            print(f"Error checking liquidity for {ticker}: {e}")
            return False
    
    def _format_market_info(self, market: Dict[str, Any]) -> Dict[str, Any]:
        """Format market information for display."""
        close_time = self._parse_timestamp(market.get('close_time', ''))
        open_time = self._parse_timestamp(market.get('open_time', ''))
        now = datetime.now(close_time.tzinfo)
        hours_remaining = (close_time - now).total_seconds() / 3600
        days_since_opened = (now - open_time).total_seconds() / (24 * 3600)
        
        # Calculate mid-market probabilities
        yes_prob, no_prob = self._calculate_probabilities(market)
        
        # Determine which side has higher probability
        if yes_prob >= no_prob:
            high_side = 'YES'
            high_probability = yes_prob
        else:
            high_side = 'NO'
            high_probability = no_prob
        
        return {
            'ticker': market.get('ticker'),
            'title': market.get('title'),
            'open_time': open_time.strftime('%Y-%m-%d %H:%M:%S %Z'),
            'days_since_opened': round(days_since_opened, 1),
            'close_time': close_time.strftime('%Y-%m-%d %H:%M:%S %Z'),
            'hours_until_close': round(hours_remaining, 1),
            'yes_probability': round(yes_prob, 3),
            'no_probability': round(no_prob, 3),
            'high_side': high_side,
            'high_probability': round(high_probability, 3),
            'volume': market.get('volume', 0),
            'open_interest': market.get('open_interest', 0),
        }


def print_market_results(markets: List[Dict[str, Any]]) -> None:
    """Print market scan results in a readable format."""
    if not markets:
        print("No markets found matching criteria.")
        return
    
    print("\n" + "="*100)
    print(f"{'MATCHING MARKETS':^100}")
    print("="*100)
    
    for i, market in enumerate(markets, 1):
        print(f"\n{i}. {market['ticker']}")
        print(f"   Title: {market['title']}")
        print(f"   Open Time: {market['open_time']} ({market['days_since_opened']} days ago)")
        print(f"   Close Time: {market['close_time']} ({market['hours_until_close']} hours remaining)")
        print(f"   Probabilities: YES={market['yes_probability']:.1%}, NO={market['no_probability']:.1%}")
        print(f"   High Side: {market['high_side']} at {market['high_probability']:.1%}")
        print(f"   Volume: {market['volume']}, Open Interest: {market['open_interest']}")
    
    print("\n" + "="*100)
