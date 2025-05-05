# backend/scripts/test_api.py
import requests
import json
import sys
from pprint import pprint

# Configuration
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1"
ACCESS_TOKEN = None

def print_response(response):
    print(f"Status Code: {response.status_code}")
    try:
        pprint(response.json())
    except:
        print(response.text)
    print("-" * 50)

def test_health():
    print("\n🔍 Testing Health Check")
    response = requests.get(f"{BASE_URL}/health")
    print_response(response)
    return response.status_code == 200

def register_user(email, password):
    print(f"\n🔍 Registering User: {email}")
    data = {
        "email": email,
        "username": email.split("@")[0],
        "full_name": "Test User",
        "password": password
    }
    response = requests.post(f"{API_URL}/users/", json=data)
    print_response(response)
    return response.status_code == 200

def login(email, password):
    print(f"\n🔍 Logging in as: {email}")
    data = {
        "email": email,
        "password": password
    }
    response = requests.post(f"{API_URL}/auth/login/email", json=data)
    print_response(response)
    
    if response.status_code == 200:
        global ACCESS_TOKEN
        ACCESS_TOKEN = response.json()["access_token"]
        return True
    return False

def get_user_profile():
    print("\n🔍 Getting User Profile")
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    response = requests.get(f"{API_URL}/auth/me", headers=headers)
    print_response(response)
    return response.status_code == 200

def create_account(account_type="checking"):
    print(f"\n🔍 Creating Account: {account_type}")
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    data = {
        "account_type": account_type,
        "currency": "USD"
    }
    response = requests.post(f"{API_URL}/accounts/", headers=headers, json=data)
    print_response(response)
    
    if response.status_code == 200:
        return response.json()["id"]
    return None

def list_accounts():
    print("\n🔍 Listing Accounts")
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    response = requests.get(f"{API_URL}/accounts/", headers=headers)
    print_response(response)
    
    if response.status_code == 200:
        return response.json()["items"]
    return []

def make_deposit(account_id, amount):
    print(f"\n🔍 Making Deposit: {amount} to account {account_id}")
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    data = {
        "account_id": account_id,
        "amount": amount,
        "currency": "USD",
        "description": "Test deposit"
    }
    response = requests.post(f"{API_URL}/transactions/deposit", headers=headers, json=data)
    print_response(response)
    return response.status_code == 200

def make_withdrawal(account_id, amount):
    print(f"\n🔍 Making Withdrawal: {amount} from account {account_id}")
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    data = {
        "account_id": account_id,
        "amount": amount,
        "currency": "USD",
        "description": "Test withdrawal"
    }
    response = requests.post(f"{API_URL}/transactions/withdrawal", headers=headers, json=data)
    print_response(response)
    return response.status_code == 200

def make_transfer(source_id, dest_id, amount):
    print(f"\n🔍 Making Transfer: {amount} from account {source_id} to {dest_id}")
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    data = {
        "source_account_id": source_id,
        "destination_account_id": dest_id,
        "amount": amount,
        "currency": "USD",
        "description": "Test transfer"
    }
    response = requests.post(f"{API_URL}/transactions/transfer", headers=headers, json=data)
    print_response(response)
    return response.status_code == 200

def make_payment(account_id, amount, recipient):
    print(f"\n🔍 Making Payment: {amount} to {recipient} from account {account_id}")
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    data = {
        "account_id": account_id,
        "amount": amount,
        "currency": "USD",
        "recipient": recipient,
        "description": "Test payment"
    }
    response = requests.post(f"{API_URL}/transactions/payment", headers=headers, json=data)
    print_response(response)
    return response.status_code == 200

def list_transactions(account_id=None):
    print("\n🔍 Listing Transactions")
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    url = f"{API_URL}/transactions/"
    if account_id:
        url += f"?account_id={account_id}"
    
    response = requests.get(url, headers=headers)
    print_response(response)
    
    if response.status_code == 200:
        return response.json()["items"]
    return []

def get_transaction_stats(account_id):
    print(f"\n🔍 Getting Transaction Stats for account {account_id}")
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    response = requests.get(f"{API_URL}/transactions/stats/{account_id}", headers=headers)
    print_response(response)
    return response.status_code == 200

def run_full_test():
    print("=" * 50)
    print("🏦 Banking System API Test")
    print("=" * 50)
    
    # Test health check
    if not test_health():
        print("❌ Health check failed! Is the server running?")
        return False
    
    # Register a new user
    email = "testuser@example.com"
    password = "TestPass123"
    
    # Try to register (might fail if user already exists)
    register_user(email, password)
    
    # Login
    if not login(email, password):
        print("❌ Login failed!")
        return False
    
    # Get user profile
    if not get_user_profile():
        print("❌ Failed to get user profile!")
        return False
    
    # Create accounts
    checking_id = create_account("checking")
    if not checking_id:
        print("❌ Failed to create checking account!")
        return False
    
    savings_id = create_account("savings")
    if not savings_id:
        print("❌ Failed to create savings account!")
        return False
    
    # List accounts
    accounts = list_accounts()
    if not accounts:
        print("❌ Failed to list accounts!")
        return False
    
    # Make deposit
    if not make_deposit(checking_id, 1000):
        print("❌ Failed to make deposit!")
        return False
    
    # Make withdrawal
    if not make_withdrawal(checking_id, 200):
        print("❌ Failed to make withdrawal!")
        return False
    
    # Make transfer
    if not make_transfer(checking_id, savings_id, 300):
        print("❌ Failed to make transfer!")
        return False
    
    # Make payment
    if not make_payment(checking_id, 150, "Electric Company"):
        print("❌ Failed to make payment!")
        return False
    
    # List transactions
    transactions = list_transactions(checking_id)
    if not transactions:
        print("❌ Failed to list transactions!")
        return False
    
    # Get transaction stats
    if not get_transaction_stats(checking_id):
        print("❌ Failed to get transaction stats!")
        return False
    
    print("\n✅ All tests passed successfully!")
    return True

if __name__ == "__main__":
    run_full_test()