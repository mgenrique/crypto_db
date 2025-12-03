# Configuration Guide — Crypto Portfolio Tracker

This document explains the most important configuration options in `config/config.yaml` and how to set them for local development and production.

## Database

`config/config.yaml` (database section)

- `type`: `sqlite` (default for local dev) or `postgresql` for production.
- `path`: For SQLite, e.g. `./portfolio.db`.
- `url` / `connection_string`: Use for full DB URLs when not using `sqlite`.

Example (SQLite):

```yaml
database:
  type: sqlite
  path: ./portfolio.db
  timeout: 5
  echo: false
```

Example (Postgres):

```yaml
database:
  type: postgresql
  url: postgresql://dbuser:***@dbhost:5432/crypto_db
  pool_size: 10
  max_overflow: 5
  echo: false
```

> Notes:
> - The app no longer expects `DATABASE_URL` in `.env` as the single source of truth; prefer YAML for DB configuration.
> - If you use Postgres in production, add the connection URL to YAML (or a secrets manager) and avoid committing secrets to git.


## Security / Secret Management

`security.secret_key` is read from `config/config.yaml` but can be overridden by the `.env` `SECRET_KEY` environment variable.

For encryption of per-user API keys we currently derive a Fernet key from `secret_key`. For production you should provide a dedicated `ENCRYPTION_KEY` in your secrets manager and update `src/utils/crypto.py` to use it.

Example:

```yaml
security:
  secret_key: ${SECRET_KEY}
  access_token_expire_minutes: 30
  refresh_token_expire_days: 7
```


## Exchanges / Connectors

The `exchanges` section controls connector-level defaults (endpoints, rate limits) while `connectors` contains provider-level and sync controls.

Example `exchanges`:

```yaml
exchanges:
  binance:
    enabled: true
    base_url: https://api.binance.com
    ws_url: wss://stream.binance.com:9443
    rate_limit: 1200
```

Example `connectors` (provider keys and background sync):

```yaml
connectors:
  alchemy_api_key: ${ALCHEMY_API_KEY}
  infura_project_id: ${INFURA_PROJECT_ID}

  background_sync:
    enabled: true
    interval_seconds: 300
```

- `exchanges.<name>.enabled`: If false the app will avoid instantiating that exchange's connector.
- `connectors.background_sync.enabled`: When `true` the app will start the background sync loop at startup (FastAPI startup event).
- `connectors.background_sync.interval_seconds`: Poll interval in seconds (default: `300`).


## Per-user API keys

The application supports storing per-user exchange API keys via the UI/API. These keys are encrypted at rest using a Fernet key derived from `security.secret_key`.

To add an exchange account for a user, use the API endpoints (see API docs) or insert into the `exchange_accounts` table with `api_key_encrypted` and `api_secret_encrypted` set via `src.utils.crypto.encrypt_value()`.


## Background Sync

- Controlled by `connectors.background_sync`.
- The background sync iterates active `exchange_accounts`, decrypts credentials, initializes the connector (e.g., Binance), fetches balances/trades/deposits/withdrawals and persists them to DB using `ExchangeService`.
- The migration created for indexes/constraints skips altering existing SQLite tables to add UNIQUE constraints. The app enforces deduplication in `ExchangeService`.

Considerations:
- For production, run background sync on a dedicated worker (not in the API process) to avoid long-running tasks tying up the web server.
- Add rate-limits, exponential backoff, and circuit-breakers for robust behavior under API errors.


## Running locally

1. Copy `.env.example` to `.env` and set `SECRET_KEY` and any provider keys you want to test.

2. Start the app:

```bash
# development
uvicorn main:app --reload
```

3. To run migrations (preferred):

```bash
alembic upgrade head
```

4. To run the CCXT/Binance integration test (requires keys):

```bash
# Ensure BINANCE_API_KEY and BINANCE_API_SECRET are in .env or add per-user ExchangeAccount
python -m pytest tests/test_binance_integration.py -q
```


## Troubleshooting

- If tests that contact external services are skipped, check the environment variables or create a per-user `ExchangeAccount` in the DB with encrypted keys.
- If SQLite needs DB-level UNIQUE enforcement, see the `alembic/versions/0002_add_exchange_constraints.py` migration; for SQLite you may need to recreate tables to apply new UNIQUE constraints.


## Further Reading

- `config/config.yaml` — Primary runtime configuration
- `src/utils/config_loader.py` — Programmatic access to config
- `src/utils/crypto.py` — Encryption helpers
- `src/services/exchange_service.py` — Persistence/dedupe logic for exchange data

---

If you'd like, I can also add an example `docker-compose` service for running a worker-only background sync separated from the API process.

### Single-user authentication (ENV)

This project can run in "single-user" mode where authentication and API
keys are configured from environment variables instead of being persisted
in the database.

Set the following variables in your `.env` to enable single-user auth:

- `ADMIN_EMAIL` – admin email used to login (required for single-user mode)
- `ADMIN_USERNAME` – admin username (optional)
- `ADMIN_PASSWORD` – plain password (convenient for local testing)
- `ADMIN_PASSWORD_HASH` – preferred: bcrypt hash of the password (use instead of `ADMIN_PASSWORD`)
- `ADMIN_API_KEY` / `ADMIN_API_SECRET` – optional single API key pair
- `WALLET_SYNC_USER_ID` – integer owner id for imported wallets (default `0`)

Notes:

- If `ADMIN_PASSWORD_HASH` is set, the server will verify passwords against
  the hash. Otherwise `ADMIN_PASSWORD` will be compared in plaintext.
- For production, prefer `ADMIN_PASSWORD_HASH` and keep `.env` secure.
- To run tests that exercise DB registration, use `ALLOW_REGISTRATION=true` (opt-in).