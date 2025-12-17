# Configure Your .env File

## Quick Setup

Edit `backend/.env` and add these values:

```bash
# Django
SECRET_KEY=your-secret-key-here-change-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (SQLite for development)
DATABASE_URL=sqlite:///db.sqlite3

# Blockchain - UPDATE THESE!
RPC_URL=https://sepolia.base.org
CHAIN_ID=84532
CONTRACT_ADDRESS=0x6bf6a80d84De12378Cc2196DFaEEF9812A3c71c9
PRIVATE_KEY=0xYOUR_PRIVATE_KEY_HERE

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Zero-Knowledge Proofs
ZKPROOF_ENABLED=True
```

## Important Values to Update

1. **RPC_URL**: `https://sepolia.base.org` (for Base Sepolia)
2. **CHAIN_ID**: `84532` (Base Sepolia)
3. **CONTRACT_ADDRESS**: `0x6bf6a80d84De12378Cc2196DFaEEF9812A3c71c9` (your deployed contract)
4. **PRIVATE_KEY**: Your test wallet's private key (starts with `0x`)

## After Updating

Run the connection check:
```bash
python check_connection.py
```

This will verify everything is working!










