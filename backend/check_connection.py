#!/usr/bin/env python
"""
Script to check if backend is properly connected to blockchain.
Run this after setup to verify everything is working.
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blockproof_backend.settings')
django.setup()

from blockchain.services import get_blockproof_service
from django.conf import settings


def check_connection():
    """Check blockchain connection status."""
    print("=" * 60)
    print("BlockProof Backend Connection Check")
    print("=" * 60)
    print()
    
    # Check configuration
    print("1. Checking Configuration...")
    config = settings.BLOCKCHAIN_CONFIG
    print(f"   [OK] RPC URL: {config['RPC_URL'][:50]}...")
    print(f"   [OK] Contract Address: {config['CONTRACT_ADDRESS']}")
    print(f"   [OK] Chain ID: {config['CHAIN_ID']}")
    print()
    
    # Check service initialization
    print("2. Initializing Service...")
    try:
        service = get_blockproof_service()
        print("   [OK] Service initialized")
    except Exception as e:
        print(f"   [ERROR] Failed to initialize service: {e}")
        return False
    print()
    
    # Check Web3 connection
    print("3. Testing Web3 Connection...")
    try:
        block_number = service.w3.eth.block_number
        print(f"   [OK] Connected to blockchain")
        print(f"   [OK] Latest block: {block_number}")
    except Exception as e:
        print(f"   [ERROR] Failed to connect: {e}")
        return False
    print()
    
    # Check contract ABI
    print("4. Checking Contract ABI...")
    if service.contract_abi:
        print(f"   [OK] ABI loaded ({len(service.contract_abi)} functions/events)")
    else:
        print("   [ERROR] ABI not loaded")
        return False
    print()
    
    # Check contract instance
    print("5. Checking Contract Instance...")
    if service.contract:
        print("   [OK] Contract instance created")
        
        # Try to call a function
        try:
            credential_count = service.contract.functions.credentialCount().call()
            print(f"   [OK] Contract is callable")
            print(f"   [OK] Current credential count: {credential_count}")
        except Exception as e:
            print(f"   [WARNING] Contract call failed: {e}")
            print("   (This might be okay if contract is not deployed yet)")
    else:
        print("   [ERROR] Contract instance is None")
        print("   (Check CONTRACT_ADDRESS in .env)")
        return False
    print()
    
    # Check account (for write operations)
    print("6. Checking Account (for write operations)...")
    if service.account:
        print(f"   [OK] Account configured: {service.account.address}")
        try:
            balance = service.w3.eth.get_balance(service.account.address)
            balance_eth = balance / 10**18
            print(f"   [OK] Balance: {balance_eth:.4f} ETH")
            if balance_eth < 0.01:
                print("   [WARNING] Low balance, may not be able to send transactions")
        except Exception as e:
            print(f"   [WARNING] Could not check balance: {e}")
    else:
        print("   [WARNING] No account configured (write operations won't work)")
        print("   (Set PRIVATE_KEY in .env for write operations)")
    print()
    
    # Check ABI file
    print("7. Checking ABI File...")
    abi_path = os.path.join(os.path.dirname(__file__), 'blockchain', 'contract_abi.json')
    if os.path.exists(abi_path):
        file_size = os.path.getsize(abi_path)
        print(f"   [OK] ABI file exists ({file_size} bytes)")
    else:
        print("   [WARNING] ABI file not found (using fallback ABI)")
        print(f"   Expected at: {abi_path}")
    print()
    
    # Summary
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print("[OK] Backend is configured and ready")
    print("[OK] Blockchain connection is working")
    if service.contract:
        print("[OK] Contract is accessible")
    else:
        print("[ERROR] Contract not accessible - check CONTRACT_ADDRESS")
    if service.account:
        print("[OK] Write operations enabled")
    else:
        print("[WARNING] Write operations disabled - set PRIVATE_KEY to enable")
    print()
    print("Next steps:")
    print("1. Start Django: python manage.py runserver")
    print("2. Start Celery: celery -A blockproof_backend worker -l info")
    print("3. Start Beat: celery -A blockproof_backend beat -l info")
    print("4. Test API: curl http://localhost:8000/api/zkproof/status/")
    print()


if __name__ == '__main__':
    try:
        check_connection()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

