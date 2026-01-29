"""
Kalshi trading bot that scans markets and places automated trades.
"""
import csv
import os
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from clients import KalshiHttpClient
import utils


class TradingBot:
    """Automated trading bot that scans markets and places orders."""
    
    def __init__(self, client: KalshiHttpClient, csv_file: str = "data/top_series.csv"):
        """Initialize the trading bot.
        
        Args:
            client: An authenticated KalshiHttpClient instance.
            csv_file: Path to the CSV file containing top series.
        """
        self.client = client
        self.csv_file = csv_file
    
    def run(
        self,
        days_until_close: int = 3,
        days_after_start: int = 1,
        min_probability: float = 0.90,
        max_probability: float = 0.99,
        require_liquidity: bool = False,
        throttle_probability: float = 0.0,
        trade_amount: float = 5.0,
        dry_run: bool = False
    ) -> List[Dict[str, Any]]:
        """Run the trading bot: scan markets, filter by criteria, and place orders.
        
        Args:
            days_until_close: Maximum days until market closes
            days_after_start: Minimum days since market opened
            min_probability: Minimum mid-market probability threshold
            max_probability: Maximum mid-market probability threshold
            require_liquidity: Whether to require open orders
            throttle_probability: Probability of skipping a matching market
            trade_amount: Amount to spend per trade in dollars
            dry_run: If True, only scan and print markets without placing trades
        
        Returns:
            List of matching markets with details.
        """
        self._print_config(
            days_until_close, days_after_start, min_probability, 
            max_probability, require_liquidity, throttle_probability, dry_run
        )
        
        if not self._check_balance_safe():
            return []
        
        series_tickers = self._load_series_from_csv()
        if not series_tickers:
            print("No series found in CSV file.")
            return []
        
        print(f"Loaded {len(series_tickers)} series from {self.csv_file}")
        print("Fetching markets for each series...")
        
        # Prepare criteria dictionary to pass around
        criteria = {
            'days_until_close': days_until_close,
            'days_after_start': days_after_start,
            'min_prob': min_probability,
            'max_prob': max_probability,
            'throttle': throttle_probability,
            'require_liquidity': require_liquidity,
            'trade_amount': trade_amount,
            'dry_run': dry_run,
            'max_close_ts': int((datetime.now() + timedelta(days=days_until_close)).timestamp())
        }
        
        all_matching_markets = []
        all_traded_markets = []
        
        for i, ticker in enumerate(series_tickers, 1):
            print(f"  [{i}/{len(series_tickers)}] Processing {ticker}...", end=" ")
            matched, traded = self._process_series(ticker, criteria)
            all_matching_markets.extend(matched)
            all_traded_markets.extend(traded)
            
            # Check if we should stop due to low balance
            if not criteria['dry_run'] and traded and not self._check_balance_safe():
                print("\nBalance dropped below $10. Stopping trading.")
                self._print_final_summary(all_matching_markets, all_traded_markets, criteria['dry_run'])
                return all_matching_markets
        
        self._print_final_summary(all_matching_markets, all_traded_markets, criteria['dry_run'])
        return all_matching_markets
    
    def _process_series(self, ticker: str, criteria: Dict[str, Any]) -> tuple[List, List]:
        """Process a single series ticker (pagination loop)."""
        matching = []
        traded = []
        matched_count = 0
        cursor = None
        
        try:
            while True:
                response = self.client.get_markets(
                    series_ticker=ticker,
                    status='open',
                    max_close_ts=criteria['max_close_ts'],
                    limit=1000,
                    cursor=cursor
                )
                markets = response.get('markets', [])
                if not markets:
                    break
                
                batch_match, batch_traded = self._process_market_batch(markets, criteria)
                matching.extend(batch_match)
                traded.extend(batch_traded)
                matched_count += len(batch_match)
                
                # Stop processing if balance is too low
                if batch_traded and not criteria['dry_run'] and not self._check_balance_safe():
                    break
                
                cursor = response.get('cursor')
                if not cursor:
                    break
            
            print(f"{matched_count} matched" if matched_count > 0 else "no markets")
            
        except Exception as e:
            print(f"error: {e}")
        
        return matching, traded
    
    def _process_market_batch(self, markets: List[Dict], criteria: Dict) -> tuple[List, List]:
        """Process a batch of markets from the API."""
        matching = []
        traded = []
        
        for market in markets:
            if criteria['throttle'] > 0 and random.random() < criteria['throttle']:
                continue
            
            # Parse into a clean structure first
            market_data = self._parse_market_data(market)
            
            # Filter based on criteria
            if not self._meets_criteria(market_data, criteria):
                continue
            
            matching.append(market_data)
            
            # Execute trade if not dry run
            if not criteria['dry_run']:
                success, order_details = self._place_trade_order(market_data, criteria['trade_amount'], criteria['require_liquidity'])
                if success:
                    market_data['order_details'] = order_details
                    traded.append(market_data)
        
        return matching, traded
    
    def _load_series_from_csv(self) -> List[str]:
        """Load series tickers from CSV file."""
        if not os.path.exists(self.csv_file):
            return []
        try:
            with open(self.csv_file, 'r') as f:
                return [row['Ticker'] for row in csv.DictReader(f) if row.get('Ticker')]
        except Exception as e:
            print(f"Error reading CSV: {e}")
            return []
    
    def _check_balance_safe(self) -> bool:
        """Check balance and return False if too low."""
        try:
            balance_cents = self.client.get_balance().get('balance', 0)
            balance_dollars = balance_cents / 100
            print(f"Current balance: ${balance_dollars:.2f}")
            if balance_dollars <= 10:
                print("Balance is $10 or less. Stopping.")
                return False
            return True
        except Exception as e:
            print(f"Error checking balance: {e}")
            return False
    
    def _parse_market_data(self, market: Dict[str, Any]) -> Dict[str, Any]:
        """Parse raw API market dict into a clean object with derived fields."""
        close_time = utils.parse_iso_timestamp(market.get('close_time', ''))
        open_time = utils.parse_iso_timestamp(market.get('open_time', ''))
        now = datetime.now(close_time.tzinfo)
        
        yes_prob, no_prob = utils.calculate_mid_probabilities(market)
        
        # Determine high side and capture ask prices
        yes_ask = float(market.get('yes_ask_dollars', 0))
        no_ask = float(market.get('no_ask_dollars', 0))
        
        if yes_prob >= no_prob:
            high_side = 'YES'
            high_prob = yes_prob
            ask_price = yes_ask
        else:
            high_side = 'NO'
            high_prob = no_prob
            ask_price = no_ask
        
        return {
            'ticker': market.get('ticker'),
            'title': market.get('title'),
            'status': market.get('status'),
            'market_type': market.get('market_type'),
            'open_time': open_time,
            'close_time': close_time,
            'days_since_opened': (now - open_time).total_seconds() / (24 * 3600),
            'days_remaining': (close_time - now).total_seconds() / (24 * 3600),
            'hours_until_close': (close_time - now).total_seconds() / 3600,
            'yes_probability': yes_prob,
            'no_probability': no_prob,
            'high_side': high_side,
            'high_probability': high_prob,
            'ask_price': ask_price,
            'volume': market.get('volume', 0),
            'open_interest': market.get('open_interest', 0),
        }
    
    def _meets_criteria(self, data: Dict[str, Any], criteria: Dict) -> bool:
        """Check if pre-parsed market data meets criteria."""
        if data['status'] != 'active' or data['market_type'] != 'binary':
            return False
        
        if data['days_remaining'] > criteria['days_until_close'] or data['days_remaining'] < 0:
            return False
        
        if data['days_since_opened'] < criteria['days_after_start']:
            return False
        
        if not (criteria['min_prob'] <= data['high_probability'] <= criteria['max_prob']):
            return False
        
        return True
    
    def _place_trade_order(self, market: Dict[str, Any], amount: float, require_liquidity: bool) -> tuple[bool, Dict[str, Any]]:
        """Place order using the ask price to ensure execution.
        
        Args:
            market: Market information dict
            amount: Amount to spend in dollars
            require_liquidity: Whether to check for liquidity before placing order
            
        Returns:
            Tuple of (success: bool, order_details: dict)
        """
        ticker = market['ticker']
        side = market['high_side'].lower()
        
        if require_liquidity and not self._has_liquidity(ticker):
            print(f"    ⊘ Skipping {ticker} - no liquidity")
            return False, {}
        
        # PRICING STRATEGY:
        # Pay the higher of (ask price) or (mid + 0.01), capped at 0.98
        # This ensures immediate fills while protecting against underpricing
        target_price = max(market['high_probability'] + 0.01, market['ask_price'])
        limit_price = min(target_price, 0.98)
        
        # Safety check: Don't buy if price is effectively 0
        if limit_price <= 0.01:
            return False, {}
        
        count = max(1, int(amount / limit_price))
        price_cents = int(limit_price * 100)
        
        print(f"    Placing ${amount:.2f} buy on {side.upper()} (count: {count}, price: {price_cents}¢)...")
        
        try:
            expiration = int(datetime.now().timestamp() + 300)  # 5 min expiry
            params = {
                'ticker': ticker,
                'action': 'buy',
                'side': side,
                'count': count,
                'type': 'limit',
                'expiration_ts': expiration
            }
            if side == 'yes':
                params['yes_price'] = price_cents
            else:
                params['no_price'] = price_cents
            
            resp = self.client.create_order(**params)
            order = resp.get('order', {})
            order_id = order.get('order_id', 'unknown')
            status = order.get('status', 'unknown')
            filled = order.get('fill_count', 0)
            print(f"    ✓ Order placed (ID: {order_id}, status: {status}, filled: {filled}/{count})")
            
            order_details = {
                'order_id': order_id,
                'status': status,
                'count': count,
                'filled': filled,
                'price': limit_price,
                'price_cents': price_cents,
                'side': side,
                'amount': amount
            }
            return True, order_details
        except Exception as e:
            print(f"    ✗ Error placing order: {e}")
            return False, {}
    
    def _has_liquidity(self, ticker: str) -> bool:
        """Check if a market has liquidity (open orders)."""
        try:
            book = self.client.get_market_orderbook(ticker, depth=1).get('orderbook', {})
            return bool(book.get('yes') or book.get('no'))
        except Exception:
            return False
    
    def _print_config(self, days_until_close, days_after_start, min_prob, max_prob, 
                     require_liquidity, throttle, dry_run):
        """Print scanning configuration."""
        print("Scanning markets with criteria:")
        print(f"  - Closing within {days_until_close} days")
        print(f"  - Open for at least {days_after_start} days")
        print(f"  - Probability: {min_prob:.0%} - {max_prob:.0%}")
        print(f"  - Liquidity required: {require_liquidity}")
        print(f"  - Throttle: {throttle:.0%}")
        print(f"  - Dry run: {dry_run}\n")
    
    def _print_final_summary(self, matches, trades, dry_run):
        """Print final summary of matched and traded markets."""
        count_m = len(matches)
        count_t = len(trades)
        print(f"\nFound {count_m} matches, traded {count_t}.")
        
        target_list = matches if dry_run else trades
        title = "MATCHING (DRY RUN)" if dry_run else "TRADED"
        
        if target_list:
            print(f"\n{'='*100}")
            print(f"{title} MARKETS:")
            print(f"{'='*100}")
            print_market_results(target_list)


def print_market_results(markets: List[Dict[str, Any]]) -> None:
    """Print market scan results in a readable format."""
    if not markets:
        print("No markets found.")
        return
    
    for i, m in enumerate(markets, 1):
        print(f"\n{i}. {m['ticker']}")
        # Handle datetime objects for display
        start_str = m['open_time'].strftime('%Y-%m-%d') if isinstance(m['open_time'], datetime) else m['open_time']
        end_str = m['close_time'].strftime('%Y-%m-%d') if isinstance(m['close_time'], datetime) else m['close_time']
        
        print(f"   Title: {m['title']}")
        print(f"   Window: {start_str} to {end_str} ({m['hours_until_close']:.1f}h remaining)")
        print(f"   Probabilities: YES={m['yes_probability']:.1%}, NO={m['no_probability']:.1%}")
        print(f"   Target: {m['high_side']} @ ${m['ask_price']:.2f} (Mid: {m['high_probability']:.1%})")
        print(f"   Volume: {m['volume']}, Open Interest: {m['open_interest']}")
        
        # Display order details if present (for traded markets)
        if 'order_details' in m and m['order_details']:
            od = m['order_details']
            print(f"   Order: {od['side'].upper()} x{od['count']} @ {od['price_cents']}¢ (${od['amount']:.2f}) - ID: {od['order_id']}")
            print(f"   Status: {od['status']}, Filled: {od['filled']}/{od['count']}")
