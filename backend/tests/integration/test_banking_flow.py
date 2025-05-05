# backend/tests/integration/test_banking_flow.py
import asyncio
import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import get_db, SessionLocal
from app.services import UserService, AccountService, TransactionService
from app.schemas.user import UserCreate
from app.schemas.account import AccountCreate
from app.schemas.transaction import DepositCreate, WithdrawalCreate, TransferCreate
from app.db.models.account import AccountType
from app.core.security import create_access_token

client = TestClient(app)

# Override the dependency to use test database
def override_get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="module")
def test_user(db: Session):
    # Create a test user
    user_in = UserCreate(
        email="test@example.com",
        username="testuser",
        password="Test1234",
        full_name="Test User"
    )
    
    # Check if user already exists
    from app.db.repositories import user_repository
    existing_user = user_repository.get_by_email(db, email=user_in.email)
    if existing_user:
        return existing_user
    
    # Create the user
    user = asyncio.run(UserService.create(db, user_in=user_in))
    return user

@pytest.fixture(scope="module")
def test_superuser(db: Session):
    # Create a test superuser
    user_in = UserCreate(
        email="admin@example.com",
        username="admin",
        password="Admin1234",
        full_name="Admin User"
    )
    
    # Check if user already exists
    from app.db.repositories import user_repository
    existing_user = user_repository.get_by_email(db, email=user_in.email)
    if existing_user:
        # Ensure it's a superuser
        if not existing_user.is_superuser:
            existing_user.is_superuser = True
            db.add(existing_user)
            db.commit()
        return existing_user
    
    # Create the user
    user = asyncio.run(UserService.create(db, user_in=user_in))
    
    # Make it a superuser
    user.is_superuser = True
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user

@pytest.fixture(scope="module")
def user_token(test_user):
    return create_access_token(subject=test_user.id)

@pytest.fixture(scope="module")
def admin_token(test_superuser):
    return create_access_token(subject=test_superuser.id)

@pytest.fixture(scope="module")
def auth_headers(user_token):
    return {"Authorization": f"Bearer {user_token}"}

@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}

@pytest.fixture(scope="module")
def test_account(db: Session, test_user):
    # Create a test account
    account_in = AccountCreate(
        account_type=AccountType.CHECKING,
        currency="USD",
        balance=0.0
    )
    
    # Create the account
    account = asyncio.run(AccountService.create(
        db, 
        obj_in=account_in, 
        user_id=test_user.id,
        current_user_id=test_user.id
    ))
    
    return account

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_login(test_user):
    response = client.post(
        "/api/v1/auth/login/email",
        json={"email": test_user.email, "password": "Test1234"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

def test_create_account(auth_headers):
    response = client.post(
        "/api/v1/accounts/",
        headers=auth_headers,
        json={"account_type": "savings", "currency": "USD"}
    )
    assert response.status_code == 200
    assert response.json()["account_type"] == "savings"
    assert response.json()["currency"] == "USD"
    assert response.json()["balance"] == 0.0

def test_deposit(auth_headers, test_account):
    response = client.post(
        "/api/v1/transactions/deposit",
        headers=auth_headers,
        json={
            "account_id": test_account.id,
            "amount": 1000.0,
            "currency": "USD",
            "description": "Initial deposit"
        }
    )
    assert response.status_code == 200
    assert response.json()["transaction_type"] == "deposit"
    assert response.json()["amount"] == 1000.0
    
    # Check account balance
    account_response = client.get(
        f"/api/v1/accounts/{test_account.id}",
        headers=auth_headers
    )
    assert account_response.status_code == 200
    assert account_response.json()["balance"] == 1000.0

def test_withdrawal(auth_headers, test_account):
    response = client.post(
        "/api/v1/transactions/withdrawal",
        headers=auth_headers,
        json={
            "account_id": test_account.id,
            "amount": 200.0,
            "currency": "USD",
            "description": "ATM withdrawal"
        }
    )
    assert response.status_code == 200
    assert response.json()["transaction_type"] == "withdrawal"
    assert response.json()["amount"] == 200.0
    
    # Check account balance
    account_response = client.get(
        f"/api/v1/accounts/{test_account.id}",
        headers=auth_headers
    )
    assert account_response.status_code == 200
    assert account_response.json()["balance"] == 800.0

def test_transfer(auth_headers, test_account, db):
    # Create a second account for transfer
    account_in = AccountCreate(
        account_type=AccountType.SAVINGS,
        currency="USD",
        balance=0.0
    )
    
    # Get user ID from test_account
    user_id = test_account.user_id
    
    # Create the second account
    second_account = asyncio.run(AccountService.create(
        db, 
        obj_in=account_in, 
        user_id=user_id,
        current_user_id=user_id
    ))
    
    # Perform the transfer
    response = client.post(
        "/api/v1/transactions/transfer",
        headers=auth_headers,
        json={
            "source_account_id": test_account.id,
            "destination_account_id": second_account.id,
            "amount": 300.0,
            "currency": "USD",
            "description": "Transfer to savings"
        }
    )
    assert response.status_code == 200
    assert response.json()["transaction_type"] == "transfer"
    assert response.json()["amount"] == 300.0
    
    # Check source account balance
    source_response = client.get(
        f"/api/v1/accounts/{test_account.id}",
        headers=auth_headers
    )
    assert source_response.status_code == 200
    assert source_response.json()["balance"] == 500.0
    
    # Check destination account balance
    dest_response = client.get(
        f"/api/v1/accounts/{second_account.id}",
        headers=auth_headers
    )
    assert dest_response.status_code == 200
    assert dest_response.json()["balance"] == 300.0

def test_payment(auth_headers, test_account):
    response = client.post(
        "/api/v1/transactions/payment",
        headers=auth_headers,
        json={
            "account_id": test_account.id,
            "amount": 150.0,
            "currency": "USD",
            "recipient": "Electric Company",
            "description": "Monthly utility bill"
        }
    )
    assert response.status_code == 200
    assert response.json()["transaction_type"] == "payment"
    assert response.json()["amount"] == 150.0
    
    # Check account balance
    account_response = client.get(
        f"/api/v1/accounts/{test_account.id}",
        headers=auth_headers
    )
    assert account_response.status_code == 200
    assert account_response.json()["balance"] == 350.0

def test_transaction_list(auth_headers, test_account):
    response = client.get(
        f"/api/v1/transactions/?account_id={test_account.id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    assert "items" in response.json()
    assert "total" in response.json()
    assert len(response.json()["items"]) >= 3  # At least deposit, withdrawal, and payment

def test_transaction_stats(auth_headers, test_account):
    response = client.get(
        f"/api/v1/transactions/stats/{test_account.id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    assert "total_inflow" in response.json()
    assert "total_outflow" in response.json()
    assert "net_flow" in response.json()
    assert "transaction_counts" in response.json()