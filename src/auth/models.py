"""
Lightweight compatibility models
--------------------------------

To keep tests and some scripts working after switching to single-user
mode, this module provides minimal SQLAlchemy models for `users` and
`api_keys`. These are intentionally simple (no cross-table ForeignKey
constraints or ORM relationships) and exist only to satisfy imports and
to allow `auth_models.Base.metadata.create_all(engine)` in tests.

If you later remove tests that require these models, you can safely
delete this module or replace it with the single-user-only implementation.
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean
from src.database.base import Base
from src.utils.time import now_utc


class UserModel(Base):
	"""Minimal user model for compatibility in single-user deployments.

	Note: avoid adding relationships or ForeignKey constraints here to keep
	the schema independent of other tables.
	"""
	__tablename__ = "users"

	id = Column(Integer, primary_key=True)
	email = Column(String(255), unique=True, nullable=False, index=True)
	username = Column(String(100), unique=True, nullable=False, index=True)
	hashed_password = Column(String(255), nullable=False)
	is_active = Column(Boolean, default=True)
	is_admin = Column(Boolean, default=False)
	created_at = Column(DateTime, default=now_utc, nullable=False)


class APIKeyModel(Base):
	"""Minimal API key model for compatibility.

	Stores an owner id as an integer without enforcing a DB-level FK.
	"""
	__tablename__ = "api_keys"

	id = Column(Integer, primary_key=True)
	user_id = Column(Integer, nullable=False)
	key = Column(String(255), unique=True, nullable=False, index=True)
	secret = Column(String(255), nullable=False)
	name = Column(String(100), nullable=False)
	is_active = Column(Boolean, default=True)
	created_at = Column(DateTime, default=now_utc, nullable=False)

