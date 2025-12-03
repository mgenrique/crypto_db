"""
Real-time cryptocurrency price fetching service
"""

import requests
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class PriceService:
    """Service for fetching real-time cryptocurrency prices"""

    COINGECKO_API_URL = "https://api.coingecko.com/api/v3"

    # Mapping of common crypto symbols to CoinGecko IDs
    CRYPTO_ID_MAP = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "ADA": "cardano",
        "SOL": "solana",
        "DOT": "polkadot",
        "MATIC": "matic-network",
        "LINK": "chainlink",
        "XRP": "ripple",
        "USDT": "tether",
        "USDC": "usd-coin",
        "BNB": "binancecoin",
        "AVAX": "avalanche-2",
    }

    @staticmethod
    def get_current_price(cryptocurrency: str, fiat_currency: str = "EUR") -> Optional[float]:
        """
        Get current price of cryptocurrency in FIAT currency

        Args:
            cryptocurrency: Crypto symbol (BTC, ETH, etc.)
            fiat_currency: FIAT currency code (EUR, USD, etc.)

        Returns:
            Current price or None if not available
        """
        crypto_id = PriceService.CRYPTO_ID_MAP.get(cryptocurrency.upper())

        if not crypto_id:
            logger.warning(f"Cryptocurrency {cryptocurrency} not found in mapping")
            return None

        try:
            url = f"{PriceService.COINGECKO_API_URL}/simple/price"
            params = {"ids": crypto_id, "vs_currencies": fiat_currency.lower()}

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            price = data.get(crypto_id, {}).get(fiat_currency.lower())

            return float(price) if price else None

        except requests.RequestException as e:
            logger.error(f"Error fetching price for {cryptocurrency}: {e}")
            return None
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Error parsing price data: {e}")
            return None

    @staticmethod
    def get_multiple_prices(
        cryptocurrencies: list, fiat_currency: str = "EUR"
    ) -> Dict[str, Optional[float]]:
        """
        Get current prices for multiple cryptocurrencies

        Args:
            cryptocurrencies: List of crypto symbols
            fiat_currency: FIAT currency code

        Returns:
            Dictionary mapping symbols to prices
        """
        prices = {}

        # Map symbols to IDs
        crypto_ids = []
        id_to_symbol = {}

        for crypto in cryptocurrencies:
            crypto_upper = crypto.upper()
            crypto_id = PriceService.CRYPTO_ID_MAP.get(crypto_upper)
            if crypto_id:
                crypto_ids.append(crypto_id)
                id_to_symbol[crypto_id] = crypto_upper

        if not crypto_ids:
            return prices

        try:
            url = f"{PriceService.COINGECKO_API_URL}/simple/price"
            params = {"ids": ",".join(crypto_ids), "vs_currencies": fiat_currency.lower()}

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            for crypto_id, symbol in id_to_symbol.items():
                price = data.get(crypto_id, {}).get(fiat_currency.lower())
                prices[symbol] = float(price) if price else None

        except requests.RequestException as e:
            logger.error(f"Error fetching multiple prices: {e}")
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Error parsing price data: {e}")

        return prices


# Convenience function
def get_current_price(cryptocurrency: str, fiat_currency: str = "EUR") -> Optional[float]:
    """Get current price of cryptocurrency"""
    return PriceService.get_current_price(cryptocurrency, fiat_currency)
