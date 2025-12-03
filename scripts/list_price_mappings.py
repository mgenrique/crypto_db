import os
import sys

# Ensure project root is on sys.path so `from src...` imports work when the
# script is executed directly from `scripts/`.
root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root not in sys.path:
    sys.path.insert(0, root)

from src.database.manager import get_db_manager
from src.database.models import PriceMapping

dbm = get_db_manager()
with dbm.session_context() as s:
    rows = s.query(PriceMapping).order_by(PriceMapping.id).all()
    print("Total price_mappings rows:", len(rows))
    for r in rows:
        print(r.id, r.symbol, r.coingecko_id, r.network, r.source)
