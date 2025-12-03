"""
Endpoints to manage per-user Exchange accounts (store encrypted API keys).

POST /api/v1/exchanges  -> create
GET  /api/v1/exchanges  -> list
DELETE /api/v1/exchanges/{id} -> delete (owner-only)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List
import logging

from src.auth.dependencies import get_current_user
from src.database.manager import get_db_manager
from src.database.models import ExchangeAccount
from src.utils.crypto import encrypt_value, decrypt_value

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["exchanges"])


class ExchangeCreateRequest(BaseModel):
    name: str = Field(..., description="Exchange name (binance/coinbase/kraken)")
    api_key: str = Field(..., description="Exchange API key")
    api_secret: str = Field(..., description="Exchange API secret")
    label: str = Field(None, description="Optional label for the account")


class ExchangeResponse(BaseModel):
    id: int
    exchange: str
    label: str | None
    is_active: bool
    created_at: str


@router.post("/exchanges", response_model=ExchangeResponse, status_code=201)
async def create_exchange(
    request: ExchangeCreateRequest,
    current_user: dict = Depends(get_current_user),
):
    dbm = get_db_manager()
    with dbm.session_context() as session:
        account = ExchangeAccount(
            user_id=current_user["user_id"],
            exchange=request.name.lower(),
            api_key_encrypted=encrypt_value(request.api_key),
            api_secret_encrypted=encrypt_value(request.api_secret),
            label=request.label,
            is_active=True,
        )
        session.add(account)
        session.flush()

        logger.info(f"Created exchange account {account.exchange} for user {current_user['user_id']}")

        return {
            "id": account.id,
            "exchange": account.exchange,
            "label": account.label,
            "is_active": account.is_active,
            "created_at": account.created_at.isoformat(),
        }


@router.get("/exchanges", response_model=dict)
async def list_exchanges(current_user: dict = Depends(get_current_user)):
    dbm = get_db_manager()
    with dbm.session_context() as session:
        rows = session.query(ExchangeAccount).filter_by(user_id=current_user["user_id"]).all()
        result = []
        for r in rows:
            # Mask api key for display
            dec = decrypt_value(r.api_key_encrypted)
            masked = None
            if dec:
                masked = dec[:4] + "..." + dec[-4:]

            result.append({
                "id": r.id,
                "exchange": r.exchange,
                "label": r.label,
                "api_key_masked": masked,
                "is_active": r.is_active,
                "created_at": r.created_at.isoformat(),
            })

        return {"exchanges": result}


@router.delete("/exchanges/{account_id}", status_code=204)
async def delete_exchange(account_id: int, current_user: dict = Depends(get_current_user)):
    dbm = get_db_manager()
    with dbm.session_context() as session:
        acc = session.query(ExchangeAccount).filter_by(id=account_id).first()
        if not acc:
            raise HTTPException(status_code=404, detail="Exchange account not found")
        if acc.user_id != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="Not allowed")

        session.delete(acc)
        logger.info(f"Deleted exchange account {account_id} for user {current_user['user_id']}")
        return None
