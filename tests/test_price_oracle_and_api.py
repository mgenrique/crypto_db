import time
import json
from fastapi.testclient import TestClient
from decimal import Decimal

import src.database.manager as db_manager_mod
from src.database.manager import DatabaseManager
from src.database.models import Base, PriceMapping, PriceCache
from src.services import price_oracle


def _make_db_manager_inmemory():
    mgr = DatabaseManager("sqlite:///:memory:", echo=False)
    mgr.create_tables(Base)
    return mgr


class DummyResponse:
    def __init__(self, status_code=200, data=None):
        self.status_code = status_code
        self._data = data or {}

    def json(self):
        return self._data

    def raise_for_status(self):
        if not (200 <= self.status_code < 300):
            raise Exception(f"HTTP {self.status_code}")


def test_contract_resolution_and_price_fetch(monkeypatch):
    # Prepare in-memory DB and patch global manager
    mgr = _make_db_manager_inmemory()
    monkeypatch.setattr(db_manager_mod, "_db_manager", mgr)

    # Prepare timestamps
    when_ts = int(time.time()) - 3600  # one hour ago
    key_ms = when_ts * 1000

    # Prepare mocked requests.get behavior
    def mock_get(url, timeout=10, **kwargs):
        # contract lookup
        if url.startswith("https://api.coingecko.com/api/v3/coins/ethereum/contract/"):
            return DummyResponse(200, {"id": "mock-token"})

        # market_chart/range
        if "/market_chart/range" in url:
            # return prices list containing a point near when_ts
            prices = [[key_ms - 5000, 1.23], [key_ms, 1.5], [key_ms + 5000, 1.4]]
            return DummyResponse(200, {"prices": prices})

        # fallback history
        if "/history" in url:
            return DummyResponse(200, {"market_data": {"current_price": {"eur": 1.5}}})

        return DummyResponse(404, {})

    monkeypatch.setattr(price_oracle.requests, "get", mock_get)

    # Call get_price_at with a contract address (starts with 0x)
    contract_addr = "0x" + "a" * 40
    price = price_oracle.get_price_at(contract_addr, when_ts)

    # Assert we got the mocked price (nearest 1.5)
    assert price == 1.5

    # Check that PriceMapping row was created
    with mgr.session_context() as session:
        pm = session.query(PriceMapping).filter_by(contract_address=contract_addr.lower()).first()
        assert pm is not None
        assert pm.coingecko_id == "mock-token"


def test_price_mappings_api_crud(monkeypatch):
    # Setup in-memory DB
    mgr = _make_db_manager_inmemory()
    monkeypatch.setattr(db_manager_mod, "_db_manager", mgr)

    # Import app lazily and test endpoints
    from main import app

    client = TestClient(app)

    payload = {
        "symbol": "TEST",
        "network": "ethereum",
        "contract_address": "0xdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
        "coingecko_id": "test-token",
        "source": "manual",
    }

    # Create mapping
    resp = client.post("/v1/price-mappings/", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["coingecko_id"] == "test-token"
    mapping_id = data["id"]

    # Get by contract
    resp = client.get(f"/v1/price-mappings/by-contract/{payload['contract_address']}")
    assert resp.status_code == 200
    data = resp.json()
    assert data is not None
    assert data["coingecko_id"] == "test-token"

    # Update mapping
    update_payload = {"symbol": "TEST2", "coingecko_id": "test-token-2", "source": "manual"}
    resp = client.put(f"/v1/price-mappings/{mapping_id}", json=update_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["symbol"] == "TEST2"
    assert data["coingecko_id"] == "test-token-2"

    # Delete mapping
    resp = client.delete(f"/v1/price-mappings/{mapping_id}")
    assert resp.status_code == 200
    assert resp.json().get("ok") is True
