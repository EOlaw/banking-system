# backend/scripts/demo_data.py
import os
import sys
import json
from datetime import datetime
from decimal import Decimal

# Add parent directory to path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config.settings import settings
from app.db.session import Base
from app.db.models import User, Account, AccountType, Transaction, TransactionType
from app.db.repositories import UserRepository, AccountRepository, TransactionRepository

# Custom JSON encoder to handle decimals and dates
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# Create engine and tables
def setup_db():
    print(f"Setting up database at {settings.DATABASE_URL}")
    engine = create_engine(settings.DATABASE_URL)
    # Drop all tables (for demo purposes)
    Base.metadata.drop_all(bind=engine)
    # Create all tables
    Base.metadata.create_all(bind=engine)
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

# Create demo data and perform operations
def create_demo_data(db):
    print("\n--- Creating Demo Data ---")
    
    # Initialize repositories
    user_repo = UserRepository()
    account_repo = AccountRepository()
    transaction_repo = TransactionRepository()
    
    # Create users
    print("\n1. Creating Users:")
    alice = user_repo.create_user(
        db=db,
        email="alice@example.com",
        username="alice",
        password="password123",
        first_name="Alice",
        last_name="Smith"
    )
    print(f"Created user: {alice.username} (ID: {alice.id})")
    
    bob = user_repo.create_user(
        db=db,
        email="bob@example.com",
        username="bob",
        password="password123",
        first_name="Bob",
        last_name="Johnson"
    )
    print(f"Created user: {bob.username} (ID: {bob.id})")
    
    # Create accounts
    print("\n2. Creating Accounts:")
    alice_checking = account_repo.create_account(
        db=db,
        owner_id=alice.id,
        account_type=AccountType.CHECKING,
        initial_balance=1000.0
    )
    print(f"Created account: {alice_checking.account_number} for {alice.username} with balance ${alice_checking.balance}")
    
    alice_savings = account_repo.create_account(
        db=db,
        owner_id=alice.id,
        account_type=AccountType.SAVINGS,
        initial_balance=5000.0
    )
    print(f"Created account: {alice_savings.account_number} for {alice.username} with balance ${alice_savings.balance}")
    
    bob_checking = account_repo.create_account(
        db=db,
        owner_id=bob.id,
        account_type=AccountType.CHECKING,
        initial_balance=2000.0
    )
    print(f"Created account: {bob_checking.account_number} for {bob.username} with balance ${bob_checking.balance}")
    
    # Perform transactions
    print("\n3. Performing Transactions:")
    # Alice deposits money
    deposit = transaction_repo.create_deposit(
        db=db,
        account_id=alice_checking.id,
        amount=500.0,
        user_id=alice.id,
        description="Salary deposit"
    )
    print(f"Deposit: ${deposit.amount} to {alice_checking.account_number}, new balance: ${alice_checking.balance}")
    
    # Alice withdraws money
    withdrawal = transaction_repo.create_withdrawal(
        db=db,
        account_id=alice_checking.id,
        amount=200.0,
        user_id=alice.id,
        description="ATM withdrawal"
    )
    print(f"Withdrawal: ${withdrawal.amount} from {alice_checking.account_number}, new balance: ${alice_checking.balance}")
    
    # Alice transfers money to Bob
    transfer = transaction_repo.create_transfer(
        db=db,
        source_account_id=alice_checking.id,
        destination_account_id=bob_checking.id,
        amount=300.0,
        sender_id=alice.id,
        receiver_id=bob.id,
        description="Payment for dinner"
    )
    print(f"Transfer: ${transfer.amount} from {alice_checking.account_number} to {bob_checking.account_number}")
    print(f"Alice's new balance: ${alice_checking.balance}")
    print(f"Bob's new balance: ${bob_checking.balance}")
    
    # Return data for reporting
    return {
        "users": [alice, bob],
        "accounts": [alice_checking, alice_savings, bob_checking],
        "transactions": [deposit, withdrawal, transfer]
    }

# Generate real-time reports
def generate_reports(db, data):
    print("\n--- Generating Real-Time Reports ---")
    
    # User report
    print("\n1. User Account Summary:")
    for user in data["users"]:
        user_accounts = Account.query.filter_by(owner_id=user.id).all()
        total_balance = sum(account.balance for account in user_accounts)
        print(f"User: {user.first_name} {user.last_name} ({user.username})")
        print(f"Number of accounts: {len(user_accounts)}")
        print(f"Total balance across all accounts: ${total_balance:.2f}")
        print(f"Accounts:")
        for account in user_accounts:
            print(f"  - {account.account_type.value}: {account.account_number}, ${account.balance:.2f}")
        print()
    
    # Transaction report
    print("\n2. Recent Transactions Report:")
    all_transactions = Transaction.query.order_by(Transaction.created_at.desc()).limit(10).all()
    for txn in all_transactions:
        source = Account.query.get(txn.source_account_id).account_number if txn.source_account_id else "N/A"
        destination = Account.query.get(txn.destination_account_id).account_number if txn.destination_account_id else "N/A"
        print(f"Transaction: {txn.transaction_number}")
        print(f"Type: {txn.transaction_type.value}")
        print(f"Amount: ${txn.amount:.2f}")
        print(f"Status: {txn.status.value}")
        print(f"From: {source} - To: {destination}")
        print(f"Date: {txn.created_at}")
        print(f"Description: {txn.description}")
        print()
    
    # Account activity report
    print("\n3. Account Activity Report:")
    for account in data["accounts"]:
        print(f"Account: {account.account_number} ({account.account_type.value})")
        print(f"Current Balance: ${account.balance:.2f}")
        
        # Get account transactions
        account_transactions = Transaction.query.filter(
            (Transaction.source_account_id == account.id) | 
            (Transaction.destination_account_id == account.id)
        ).order_by(Transaction.created_at.desc()).all()
        
        print(f"Transaction Count: {len(account_transactions)}")
        if account_transactions:
            print(f"Last transaction: {account_transactions[0].created_at}")
            incoming = sum(t.amount for t in account_transactions if t.destination_account_id == account.id)
            outgoing = sum(t.amount for t in account_transactions if t.source_account_id == account.id)
            print(f"Total incoming: ${incoming:.2f}")
            print(f"Total outgoing: ${outgoing:.2f}")
        print()

# Export data to JSON (for API simulation)
def export_data_to_json(data):
    print("\n--- Exporting Data to JSON ---")
    
    # Convert data to dictionaries
    users = [{
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_active": user.is_active,
        "created_at": user.created_at,
    } for user in data["users"]]
    
    accounts = [{
        "id": account.id,
        "account_number": account.account_number,
        "account_type": account.account_type.value,
        "balance": account.balance,
        "currency": account.currency,
        "owner_id": account.owner_id,
        "created_at": account.created_at,
    } for account in data["accounts"]]
    
    transactions = [{
        "id": txn.id,
        "transaction_number": txn.transaction_number,
        "transaction_type": txn.transaction_type.value,
        "amount": txn.amount,
        "currency": txn.currency,
        "status": txn.status.value,
        "source_account_id": txn.source_account_id,
        "destination_account_id": txn.destination_account_id,
        "sender_id": txn.sender_id,
        "receiver_id": txn.receiver_id,
        "description": txn.description,
        "created_at": txn.created_at,
        "completed_at": txn.completed_at,
    } for txn in data["transactions"]]
    
    # Write to files
    os.makedirs("./data", exist_ok=True)
    
    with open("./data/users.json", "w") as f:
        json.dump(users, f, cls=CustomJSONEncoder, indent=2)
    
    with open("./data/accounts.json", "w") as f:
        json.dump(accounts, f, cls=CustomJSONEncoder, indent=2)
    
    with open("./data/transactions.json", "w") as f:
        json.dump(transactions, f, cls=CustomJSONEncoder, indent=2)
    
    print("Data exported to ./data/ directory")

# Main function
def main():
    try:
        db = setup_db()
        data = create_demo_data(db)
        generate_reports(db, data)
        export_data_to_json(data)
        print("\nDemo completed successfully!")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    main()