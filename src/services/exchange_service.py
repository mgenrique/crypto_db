"""
Exchange Service
================

Service responsible for persisting exchange data (balances, trades,
deposits, withdrawals) into the database.
"""
from datetime import datetime, timezone
from src.utils.time import now_utc
from decimal import Decimal
import logging
from typing import Dict, List, Any, Optional

from src.database.manager import get_db_manager
from src.database.models import (
    ExchangeBalance, ExchangeTrade, ExchangeDeposit, ExchangeWithdrawal, ExchangeAccount
)
from src.services.price_oracle import get_price, get_price_fiat, get_price_at
from src.utils.config_loader import ConfigLoader
from src.utils.helpers import Converters

logger = logging.getLogger(__name__)


class ExchangeService:
    def __init__(self, db_manager=None):
        self.db_manager = db_manager or get_db_manager()

    def _upsert_price_mapping(self, session, contract_address: str, network: Optional[str] = None, symbol: Optional[str] = None, coingecko_id: Optional[str] = None):
        """Upsert a PriceMapping row for a contract+network. Expects an active session."""
        if not contract_address:
            return
        try:
            from src.database.models import PriceMapping
            ca = contract_address.lower()
            existing = session.query(PriceMapping).filter_by(contract_address=ca, network=network).first()
            if existing:
                changed = False
                if coingecko_id and existing.coingecko_id != coingecko_id:
                    existing.coingecko_id = coingecko_id
                    changed = True
                if symbol and not existing.symbol:
                    existing.symbol = symbol.upper()
                    changed = True
                if changed:
                    existing.source = existing.source or "detected"
            else:
                pm = PriceMapping(symbol=(symbol.upper() if symbol else None), network=network, contract_address=ca, coingecko_id=coingecko_id, source="detected")
                session.add(pm)
        except Exception:
            # Non-fatal: mapping upsert should not break exchange persistence
            logger.debug("Failed to upsert PriceMapping (non-fatal)")

    def persist_balances(self, exchange_account_id: int, balances: Dict[str, Dict[str, Any]]):
        """Persist exchange balances for the given exchange account.

        balances: { 'BTC': {'free': '0.1','locked':'0','total':'0.1'}, ... }
        """
        try:
            with self.db_manager.session_context() as session:
                # Ensure exchange account exists
                acct = session.query(ExchangeAccount).filter_by(id=exchange_account_id).first()
                if not acct:
                    raise ValueError(f"ExchangeAccount {exchange_account_id} not found")

                # Insert snapshot rows
                for asset, data in balances.items():
                    free = Decimal(data.get('free', '0'))
                    locked = Decimal(data.get('locked', '0'))
                    total = Decimal(data.get('total', str(free + locked)))
                    # If the exchange provided a contract address, persist mapping
                    contract = data.get('contract') or data.get('contractAddress') or data.get('tokenAddress')
                    network = data.get('network') or data.get('chain')
                    if contract:
                        try:
                            self._upsert_price_mapping(session, contract, network=network, symbol=asset)
                        except Exception:
                            pass
                    # attempt to obtain fiat valuation from the input when provided
                    cfg = ConfigLoader()
                    configured_fiat = cfg.get_fiat_currency()

                    total_usd = None
                    total_fiat = None

                    # Accept direct fiat value if provided and matches configured fiat
                    provided_total_fiat = data.get('total_fiat') or data.get('fiat_total')
                    provided_fiat_currency = data.get('fiat_currency')
                    if provided_total_fiat is not None:
                        try:
                            if not provided_fiat_currency or provided_fiat_currency.upper() == configured_fiat:
                                total_fiat = Decimal(str(provided_total_fiat))
                            else:
                                total_fiat = None
                        except Exception:
                            total_fiat = None

                    # If no provided fiat, compute via price oracle
                    if total_fiat is None:
                        try:
                            price_fiat = get_price_fiat(asset)
                            total_fiat = Decimal(price_fiat) * total if price_fiat is not None else None
                        except Exception:
                            total_fiat = None

                    try:
                        price_usd = get_price(asset, vs_currency='usd')
                        total_usd = Decimal(price_usd) * total if price_usd is not None else None
                    except Exception:
                        total_usd = None

                    eb = ExchangeBalance(
                        exchange_account_id=exchange_account_id,
                        asset=asset,
                        free=free,
                        locked=locked,
                        total=total,
                        total_usd=total_usd,
                        total_fiat=total_fiat,
                        created_at=now_utc()
                    )
                    session.add(eb)

                logger.info(f"Persisted {len(balances)} exchange balances for account {exchange_account_id}")
        except Exception as e:
            logger.error(f"Error persisting balances: {e}")
            raise

    def persist_trades(self, exchange_account_id: int, trades: List[Dict[str, Any]]):
        try:
            with self.db_manager.session_context() as session:
                acct = session.query(ExchangeAccount).filter_by(id=exchange_account_id).first()
                if not acct:
                    raise ValueError(f"ExchangeAccount {exchange_account_id} not found")

                for t in trades:
                    ts = None
                    if t.get('timestamp') is not None:
                        try:
                            if isinstance(t['timestamp'], int) or isinstance(t['timestamp'], float):
                                ts = Converters.parse_timestamp(int(t['timestamp']), unit='seconds')
                            else:
                                ts = datetime.fromisoformat(str(t['timestamp']))
                        except Exception:
                            ts = None
                    trade_id = str(t.get('id')) if t.get('id') is not None else None

                    # If trade_id is present, dedupe by (exchange_account_id, trade_id)
                    existing = None
                    if trade_id:
                        existing = session.query(ExchangeTrade).filter_by(
                            exchange_account_id=exchange_account_id,
                            trade_id=trade_id
                        ).first()

                    if existing:
                        # update mutable fields if changed
                        try:
                            if t.get('price'):
                                existing.price = Decimal(t.get('price'))
                            if t.get('qty'):
                                existing.qty = Decimal(t.get('qty'))
                            if t.get('commission'):
                                existing.commission = Decimal(t.get('commission'))
                        except Exception:
                            pass
                        existing.commission_asset = t.get('commissionAsset') or existing.commission_asset
                        existing.is_buyer = bool(t.get('is_buyer') or t.get('isBuyer') or existing.is_buyer)
                        existing.is_maker = bool(t.get('is_maker') or t.get('isMaker') or existing.is_maker)
                        # prefer provided timestamp if present; accept numeric epoch/millis as well
                        provided_ts = t.get('timestamp')
                        if provided_ts is not None:
                            try:
                                if isinstance(provided_ts, int) or isinstance(provided_ts, float):
                                    existing.timestamp = Converters.parse_timestamp(int(provided_ts), unit='seconds')
                                else:
                                    existing.timestamp = datetime.fromisoformat(str(provided_ts))
                            except Exception:
                                existing.timestamp = ts or existing.timestamp
                        else:
                            existing.timestamp = ts or existing.timestamp
                    else:
                        trade = ExchangeTrade(
                            exchange_account_id=exchange_account_id,
                            trade_id=trade_id,
                            symbol=t.get('symbol'),
                            price=Decimal(t.get('price')) if t.get('price') else None,
                            price_fiat=None,
                            qty=Decimal(t.get('qty')) if t.get('qty') else None,
                            commission=Decimal(t.get('commission')) if t.get('commission') else None,
                            commission_fiat=None,
                            commission_asset=t.get('commissionAsset'),
                            is_buyer=bool(t.get('is_buyer') or t.get('isBuyer')),
                            is_maker=bool(t.get('is_maker') or t.get('isMaker')),
                            timestamp=ts,
                            created_at=now_utc()
                        )
                        # attempt to compute or accept fiat valuations for the trade price and commission
                        ts_for_price = None
                        try:
                            ts_for_price = int(ts.timestamp()) if ts is not None else None
                        except Exception:
                            ts_for_price = None

                        # Prefer any fiat value provided by the exchange
                        configured_fiat = ConfigLoader().get_fiat_currency()
                        provided_price_fiat = t.get('price_fiat')
                        provided_price_fiat_currency = (t.get('price_fiat_currency') or t.get('fiat_currency'))
                        if provided_price_fiat is not None and (not provided_price_fiat_currency or provided_price_fiat_currency.upper() == configured_fiat):
                            try:
                                trade.price_fiat = Decimal(str(provided_price_fiat))
                            except Exception:
                                trade.price_fiat = None
                        else:
                            try:
                                sym = t.get('symbol') or (t.get('symbol') or '').split('/')[0]
                                if trade.price is not None and ts_for_price:
                                    p = get_price_at(sym, ts_for_price)
                                    trade.price_fiat = Decimal(p) if p is not None else None
                            except Exception:
                                trade.price_fiat = None

                        # Commission fiat: prefer provided
                        provided_commission_fiat = t.get('commission_fiat')
                        provided_commission_fiat_currency = t.get('commission_fiat_currency')
                        if provided_commission_fiat is not None and (not provided_commission_fiat_currency or provided_commission_fiat_currency.upper() == configured_fiat):
                            try:
                                trade.commission_fiat = Decimal(str(provided_commission_fiat))
                            except Exception:
                                trade.commission_fiat = None
                        else:
                            try:
                                if trade.commission is not None and trade.commission_asset and ts_for_price:
                                    c = get_price_at(trade.commission_asset, ts_for_price)
                                    trade.commission_fiat = (Decimal(c) * trade.commission) if c is not None else None
                            except Exception:
                                trade.commission_fiat = None
                        # If trade object has contract info, persist mapping
                        contract = t.get('contract') or t.get('contractAddress') or t.get('tokenAddress')
                        network = t.get('network') or t.get('chain')
                        if contract:
                            try:
                                self._upsert_price_mapping(session, contract, network=network, symbol=trade.symbol)
                            except Exception:
                                pass
                        session.add(trade)

                logger.info(f"Persisted {len(trades)} trades for account {exchange_account_id}")
        except Exception as e:
            logger.error(f"Error persisting trades: {e}")
            raise

    def persist_deposits(self, exchange_account_id: int, deposits: List[Dict[str, Any]]):
        try:
            with self.db_manager.session_context() as session:
                acct = session.query(ExchangeAccount).filter_by(id=exchange_account_id).first()
                if not acct:
                    raise ValueError(f"ExchangeAccount {exchange_account_id} not found")

                for d in deposits:
                    ts = None
                    if d.get('timestamp') is not None:
                        try:
                            if isinstance(d['timestamp'], int) or isinstance(d['timestamp'], float):
                                ts = Converters.parse_timestamp(int(d['timestamp']), unit='seconds')
                            else:
                                ts = datetime.fromisoformat(str(d['timestamp']))
                        except Exception:
                            ts = None
                    deposit_id = str(d.get('id')) if d.get('id') is not None else None
                    existing = None
                    if deposit_id:
                        existing = session.query(ExchangeDeposit).filter_by(
                            exchange_account_id=exchange_account_id,
                            deposit_id=deposit_id
                        ).first()

                    if existing:
                        # update status/txid if changed
                        existing.status = str(d.get('status')) if d.get('status') is not None else existing.status
                        existing.txid = d.get('txid') or d.get('txId') or existing.txid
                        existing.address = d.get('address') or existing.address
                        try:
                            if d.get('amount'):
                                existing.amount = Decimal(d.get('amount'))
                        except Exception:
                            pass
                        existing.timestamp = ts or existing.timestamp
                    else:
                        dep = ExchangeDeposit(
                            exchange_account_id=exchange_account_id,
                            deposit_id=deposit_id,
                            asset=d.get('coin') or d.get('asset') or d.get('currency'),
                            amount=Decimal(d.get('amount')) if d.get('amount') else None,
                            address=d.get('address'),
                            txid=d.get('txid') or d.get('txId'),
                            network=d.get('network'),
                            status=str(d.get('status')) if d.get('status') is not None else None,
                            timestamp=ts,
                            created_at=now_utc()
                        )
                        # Accept provided fiat amount if present, else compute via price oracle
                        cfg = ConfigLoader()
                        configured_fiat = cfg.get_fiat_currency()
                        provided_amount_fiat = d.get('amount_fiat') or d.get('fiat_amount')
                        provided_amount_fiat_currency = d.get('fiat_currency')
                        if provided_amount_fiat is not None and (not provided_amount_fiat_currency or provided_amount_fiat_currency.upper() == configured_fiat):
                            try:
                                dep.amount_fiat = Decimal(str(provided_amount_fiat))
                            except Exception:
                                dep.amount_fiat = None
                        else:
                            try:
                                # use deposit timestamp if available
                                if dep.amount is not None and dep.timestamp is not None:
                                    when = int(dep.timestamp.timestamp()) if hasattr(dep.timestamp, 'timestamp') else None
                                    if when:
                                        p = get_price_at(dep.asset, when)
                                        dep.amount_fiat = Decimal(p) * dep.amount if p is not None else None
                            except Exception:
                                pass

                        session.add(dep)

                        # If deposit includes token contract, persist mapping
                        d_contract = d.get('contract') or d.get('contractAddress') or d.get('tokenAddress')
                        d_network = d.get('network') or d.get('chain')
                        if d_contract:
                            try:
                                self._upsert_price_mapping(session, d_contract, network=d_network, symbol=dep.asset)
                            except Exception:
                                pass

                logger.info(f"Persisted {len(deposits)} deposits for account {exchange_account_id}")
        except Exception as e:
            logger.error(f"Error persisting deposits: {e}")
            raise

    def persist_withdrawals(self, exchange_account_id: int, withdrawals: List[Dict[str, Any]]):
        try:
            with self.db_manager.session_context() as session:
                acct = session.query(ExchangeAccount).filter_by(id=exchange_account_id).first()
                if not acct:
                    raise ValueError(f"ExchangeAccount {exchange_account_id} not found")

                for w in withdrawals:
                    ts = None
                    if w.get('timestamp') is not None:
                        try:
                            if isinstance(w['timestamp'], int) or isinstance(w['timestamp'], float):
                                ts = Converters.parse_timestamp(int(w['timestamp']), unit='seconds')
                            else:
                                ts = datetime.fromisoformat(str(w['timestamp']))
                        except Exception:
                            ts = None
                    withdrawal_id = str(w.get('id')) if w.get('id') is not None else None
                    existing = None
                    if withdrawal_id:
                        existing = session.query(ExchangeWithdrawal).filter_by(
                            exchange_account_id=exchange_account_id,
                            withdrawal_id=withdrawal_id
                        ).first()

                    if existing:
                        existing.status = str(w.get('status')) if w.get('status') is not None else existing.status
                        existing.txid = w.get('txid') or w.get('txId') or existing.txid
                        existing.address = w.get('address') or existing.address
                        try:
                            if w.get('amount'):
                                existing.amount = Decimal(w.get('amount'))
                        except Exception:
                            pass
                        existing.timestamp = ts or existing.timestamp
                    else:
                        wd = ExchangeWithdrawal(
                            exchange_account_id=exchange_account_id,
                            withdrawal_id=withdrawal_id,
                            asset=w.get('coin') or w.get('asset') or w.get('currency'),
                            amount=Decimal(w.get('amount')) if w.get('amount') else None,
                            address=w.get('address'),
                            txid=w.get('txid') or w.get('txId'),
                            network=w.get('network'),
                            status=str(w.get('status')) if w.get('status') is not None else None,
                            timestamp=ts,
                            created_at=now_utc()
                        )
                        # Accept provided fiat amount if present, else compute via price oracle
                        cfg = ConfigLoader()
                        configured_fiat = cfg.get_fiat_currency()
                        provided_amount_fiat = w.get('amount_fiat') or w.get('fiat_amount')
                        provided_amount_fiat_currency = w.get('fiat_currency')
                        if provided_amount_fiat is not None and (not provided_amount_fiat_currency or provided_amount_fiat_currency.upper() == configured_fiat):
                            try:
                                wd.amount_fiat = Decimal(str(provided_amount_fiat))
                            except Exception:
                                wd.amount_fiat = None
                        else:
                            try:
                                # use withdrawal timestamp if available
                                if wd.amount is not None and wd.timestamp is not None:
                                    when = int(wd.timestamp.timestamp()) if hasattr(wd.timestamp, 'timestamp') else None
                                    if when:
                                        p = get_price_at(wd.asset, when)
                                        wd.amount_fiat = Decimal(p) * wd.amount if p is not None else None
                            except Exception:
                                pass

                        session.add(wd)

                        # If withdrawal includes token contract, persist mapping
                        w_contract = w.get('contract') or w.get('contractAddress') or w.get('tokenAddress')
                        w_network = w.get('network') or w.get('chain')
                        if w_contract:
                            try:
                                self._upsert_price_mapping(session, w_contract, network=w_network, symbol=wd.asset)
                            except Exception:
                                pass

                logger.info(f"Persisted {len(withdrawals)} withdrawals for account {exchange_account_id}")
        except Exception as e:
            logger.error(f"Error persisting withdrawals: {e}")
            raise
