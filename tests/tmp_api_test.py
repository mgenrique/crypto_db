# Integration smoke test for auth + exchanges endpoints
import os, sys
# Ensure project root is on sys.path so `src` package is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.utils.config_loader import ConfigLoader
from src.database.manager import get_db_manager
from src.database import models as db_models
from src.auth import models as auth_models
from fastapi.testclient import TestClient
from main import app
import uuid

# Ensure YAML config loaded
# For single-user mode tests, set admin creds in env before ConfigLoader reads .env
import os
os.environ.setdefault('ADMIN_EMAIL', 'test+admin@example.com')
os.environ.setdefault('ADMIN_USERNAME', 'testadmin')
# For tests we can use a plain password (or set ADMIN_PASSWORD_HASH instead)
os.environ.setdefault('ADMIN_PASSWORD', 'Testpass123!')

used_admin = bool(os.environ.get('ADMIN_EMAIL'))

cfg = ConfigLoader()

# Initialize DB and create tables for both bases
dbm = get_db_manager()
engine = dbm.engine

print('Creating tables...')
auth_models.Base.metadata.create_all(engine)
db_models.Base.metadata.create_all(engine)
print('Tables created')

client = TestClient(app, base_url="http://localhost")

# Unique test user
email = f"test+{uuid.uuid4().hex[:6]}@example.com"
username = f"testuser_{uuid.uuid4().hex[:6]}"
password = "Testpass123!"

print('Registering user:', email)
if used_admin:
    # Single-user mode: perform login using ADMIN_* env variables
    login_email = os.environ.get('ADMIN_EMAIL')
    login_password = os.environ.get('ADMIN_PASSWORD')
    print('Single-user login as', login_email)
    r = client.post('/api/v1/auth/login', json={'email': login_email, 'password': login_password})
    print('Login status', r.status_code, r.text)
    if r.status_code != 200:
        raise SystemExit('Login failed')
else:
    r = client.post('/api/v1/auth/register', json={
        'email': email,
        'username': username,
        'password': password
    })
    print('Register status', r.status_code, r.text)
    if r.status_code not in (200, 201):
        raise SystemExit('Register failed')

if not used_admin:
    print('Logging in...')
    r = client.post('/api/v1/auth/login', json={'email': email, 'password': password})
    print('Login status', r.status_code, r.text)
    if r.status_code != 200:
        raise SystemExit('Login failed')

    data = r.json()
    access_token = data.get('access_token')
    headers = {'Authorization': f"Bearer {access_token}"}
else:
    # use token from earlier admin login
    data = r.json()
    access_token = data.get('access_token')
    headers = {'Authorization': f"Bearer {access_token}"}

# Create exchange account
print('Creating exchange account...')
r = client.post('/api/v1/exchanges', json={
    'name': 'binance',
    'api_key': 'sk_test_1234567890abcdef',
    'api_secret': 'ss_test_abcdef1234567890',
    'label': 'My Test Binance'
}, headers=headers)
print('Create exchange status', r.status_code, r.text)
if r.status_code != 201:
    raise SystemExit('Create exchange failed')
created = r.json()
acc_id = created.get('id')

# List exchanges
print('Listing exchanges...')
r = client.get('/api/v1/exchanges', headers=headers)
print('List status', r.status_code, r.text)

# Delete exchange
print('Deleting exchange id', acc_id)
r = client.delete(f'/api/v1/exchanges/{acc_id}', headers=headers)
print('Delete status', r.status_code, r.text)

print('Smoke test completed')
