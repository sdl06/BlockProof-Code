# Quick Start: Complete Backend with ZKProof

## 🚀 Fast Setup (5 minutes)

### 1. Install Dependencies
```bash
cd BlockProof-Code/backend
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
# Copy example env file
cp .env.example .env

# Edit .env and set:
# - RPC_URL (get from Infura/Alchemy)
# - CONTRACT_ADDRESS (your deployed contract)
# - PRIVATE_KEY (for write operations)
```

### 3. Setup Database
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 4. Extract Contract ABI
```bash
# After compiling contract
cat ../contracts/out/BlockProofCredentialVault.sol/BlockProofCredentialVault.json | jq .abi > blockchain/contract_abi.json
```

### 5. Start Services
```bash
# Terminal 1: Django
python manage.py runserver

# Terminal 2: Redis
redis-server

# Terminal 3: Celery Worker
celery -A blockproof_backend worker -l info

# Terminal 4: Celery Beat
celery -A blockproof_backend beat -l info
```

## ✅ Verify Setup

```bash
# Check ZKProof status
curl http://localhost:8000/api/zkproof/status/

# Should return:
# {"enabled": true, "status": "operational", ...}
```

## 🎯 Next Steps

1. **Generate a ZKProof**: `POST /api/zkproof/proofs/generate/`
2. **Verify a Proof**: `POST /api/zkproof/proofs/{id}/verify/`
3. **See Full Guide**: `SETUP_GUIDE.md`

## 📚 Key Features

✅ **Zero-Knowledge Proofs**: Privacy-preserving credential verification
✅ **Blockchain Integration**: Full smart contract interaction
✅ **Event Indexing**: Automatic blockchain sync
✅ **Cost Optimized**: Minimal RPC calls
✅ **REST API**: Complete API for all operations

## 🔧 Troubleshooting

- **Contract not found**: Check `CONTRACT_ADDRESS` in `.env`
- **ZKProof disabled**: Set `ZKPROOF_ENABLED=True` in `.env`
- **Celery not working**: Check Redis is running

See `SETUP_GUIDE.md` for detailed instructions.










