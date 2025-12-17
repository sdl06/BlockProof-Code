# Deployment Quick Reference

## 🔴 Current Status: NOT Connected

The backend code is ready, but you need to connect it to the blockchain.

## ⚡ Quick Start (5 Steps)

### 1. Deploy Contract
```bash
cd contracts
forge build
forge create BlockProofCredentialVault --rpc-url $RPC_URL --private-key $PRIVATE_KEY
# Save the contract address!
```

### 2. Extract ABI
```bash
cat out/BlockProofCredentialVault.sol/BlockProofCredentialVault.json | jq .abi > ../backend/blockchain/contract_abi.json
```

### 3. Configure Backend
```bash
cd ../backend
cp .env.example .env
# Edit .env with:
# - RPC_URL (from Infura/Alchemy)
# - CONTRACT_ADDRESS (from step 1)
# - PRIVATE_KEY (your wallet)
```

### 4. Setup & Test
```bash
pip install -r requirements.txt
python manage.py migrate
python check_connection.py  # Verify connection
```

### 5. Start Services
```bash
# Terminal 1
python manage.py runserver

# Terminal 2
redis-server

# Terminal 3
celery -A blockproof_backend worker -l info

# Terminal 4
celery -A blockproof_backend beat -l info
```

## ✅ Verify Connection

```bash
# Run connection check
python check_connection.py

# Test API
curl http://localhost:8000/api/zkproof/status/
```

## 📚 Full Guides

- **Complete Deployment**: `COMPLETE_DEPLOYMENT_GUIDE.md`
- **Backend Setup**: `backend/SETUP_GUIDE.md`
- **Connection Details**: `backend/CONTRACT_CONNECTION.md`

## 🚀 Production Deployment

See `COMPLETE_DEPLOYMENT_GUIDE.md` Part 3 for:
- Railway deployment
- Render deployment
- AWS/GCP deployment










