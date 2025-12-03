"""Admin routes for managing PriceMappings

Endpoints:
- GET /v1/price-mappings?symbol=ETH
- GET /v1/price-mappings/by-contract/{contract}
- POST /v1/price-mappings  (body: symbol, network, contract_address, coingecko_id, source)
- PUT /v1/price-mappings/{id}
- DELETE /v1/price-mappings/{id}

Requires admin/auth in production; for now endpoints are unprotected for convenience.
"""

from fastapi import APIRouter, HTTPException, Query, Path, Body
from typing import Optional, List
from pydantic import BaseModel, Field
from src.database.manager import get_db_manager
from src.database.models import PriceMapping
from src.utils.time import now_utc

router = APIRouter(prefix="/v1/price-mappings", tags=["price_mappings"])


class PriceMappingIn(BaseModel):
    symbol: Optional[str] = Field(None, description="Token symbol")
    network: Optional[str] = Field(None, description="Network name")
    contract_address: Optional[str] = Field(None, description="Contract address (lowercase)")
    coingecko_id: str = Field(..., description="CoinGecko id")
    source: Optional[str] = Field('manual')


class PriceMappingOut(BaseModel):
    id: int
    symbol: Optional[str]
    network: Optional[str]
    contract_address: Optional[str]
    coingecko_id: str
    source: Optional[str]
    created_at: Optional[str]


@router.get("/", response_model=List[PriceMappingOut])
def list_mappings(symbol: Optional[str] = Query(None)):
    dbm = get_db_manager()
    with dbm.session_context() as session:
        q = session.query(PriceMapping)
        if symbol:
            q = q.filter(PriceMapping.symbol == symbol.upper())
        results = q.order_by(PriceMapping.created_at.desc()).limit(200).all()
        return [PriceMappingOut(
            id=r.id,
            symbol=r.symbol,
            network=r.network,
            contract_address=r.contract_address,
            coingecko_id=r.coingecko_id,
            source=r.source,
            created_at=str(r.created_at)
        ) for r in results]


@router.get("/by-contract/{contract}", response_model=Optional[PriceMappingOut])
def get_by_contract(contract: str = Path(...)):
    dbm = get_db_manager()
    with dbm.session_context() as session:
        r = session.query(PriceMapping).filter_by(contract_address=contract.lower()).first()
        if not r:
            return None
        return PriceMappingOut(
            id=r.id,
            symbol=r.symbol,
            network=r.network,
            contract_address=r.contract_address,
            coingecko_id=r.coingecko_id,
            source=r.source,
            created_at=str(r.created_at)
        )


@router.post("/", response_model=PriceMappingOut)
def create_mapping(payload: PriceMappingIn = Body(...)):
    dbm = get_db_manager()
    with dbm.session_context() as session:
        pm = PriceMapping(
            symbol=(payload.symbol.upper() if payload.symbol else None),
            network=payload.network,
            contract_address=(payload.contract_address.lower() if payload.contract_address else None),
            coingecko_id=payload.coingecko_id,
            source=payload.source,
            created_at=now_utc()
        )
        session.add(pm)
        session.flush()
        return PriceMappingOut(
            id=pm.id,
            symbol=pm.symbol,
            network=pm.network,
            contract_address=pm.contract_address,
            coingecko_id=pm.coingecko_id,
            source=pm.source,
            created_at=str(pm.created_at)
        )


@router.put("/{mapping_id}", response_model=PriceMappingOut)
def update_mapping(mapping_id: int = Path(...), payload: PriceMappingIn = Body(...)):
    dbm = get_db_manager()
    with dbm.session_context() as session:
        pm = session.query(PriceMapping).filter_by(id=mapping_id).first()
        if not pm:
            raise HTTPException(status_code=404, detail="PriceMapping not found")
        if payload.symbol:
            pm.symbol = payload.symbol.upper()
        if payload.network:
            pm.network = payload.network
        if payload.contract_address:
            pm.contract_address = payload.contract_address.lower()
        pm.coingecko_id = payload.coingecko_id
        pm.source = payload.source
        session.add(pm)
        return PriceMappingOut(
            id=pm.id,
            symbol=pm.symbol,
            network=pm.network,
            contract_address=pm.contract_address,
            coingecko_id=pm.coingecko_id,
            source=pm.source,
            created_at=str(pm.created_at)
        )


@router.delete("/{mapping_id}")
def delete_mapping(mapping_id: int = Path(...)):
    dbm = get_db_manager()
    with dbm.session_context() as session:
        pm = session.query(PriceMapping).filter_by(id=mapping_id).first()
        if not pm:
            raise HTTPException(status_code=404, detail="PriceMapping not found")
        session.delete(pm)
    return {"ok": True}
