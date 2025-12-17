# Complete Setup Guide: Backend + Zero-Knowledge Proofs

This guide walks you through setting up the complete backend with zkproof functionality.

## Prerequisites

1. **Python 3.9+**
2. **Node.js 16+** (for zk-SNARKs, optional)
3. **Redis** (for Celery)
4. **PostgreSQL** (optional, SQLite works for development)
5. **Deployed Smart Contract** (with address and ABI)

## Step 1: Install Dependencies

### 1.1 Python Dependencies

```bash
cd BlockProof-Code/backend
pip install -r requirements.txt
```

### 1.2 Node.js Dependencies (Optional, for advanced zk-SNARKs)

```bash
# Install circom
npm install -g circom

# Install snarkjs
npm install -g snarkjs
```

## Step 2: Configure Environment

### 2.1 Create .env File

```bash
cp .env.example .env
```

### 2.2 Edit .env with Your Values

```bash
# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=sqlite:///db.sqlite3

# Blockchain
RPC_URL=https://sepolia.infura.io/v3/YOUR_INFURA_KEY
CONTRACT_ADDRESS=0x...  # Your deployed contract address
CHAIN_ID=11155111
PRIVATE_KEY=0x...  # For write operations

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Zero-Knowledge Proofs
ZKPROOF_ENABLED=True
ZKPROOF_CIRCUIT_PATH=./zkproof/circuits
ZKPROOF_ARTIFACTS_PATH=./zkproof/artifacts
```

## Step 3: Setup Database

### 3.1 Run Migrations

```bash
python manage.py migrate
```

This creates tables for:
- Credentials
- Institutions
- Blockchain events
- Zero-knowledge proofs
- Proof verifications
- Circuits

### 3.2 Create Superuser

```bash
python manage.py createsuperuser
```

## Step 4: Setup Contract ABI

### 4.1 Compile Contract

```bash
cd ../contracts
forge build
# or
npx hardhat compile
```

### 4.2 Extract ABI

**Foundry:**
```bash
cat out/BlockProofCredentialVault.sol/BlockProofCredentialVault.json | jq .abi > ../backend/blockchain/contract_abi.json
```

**Hardhat:**
```bash
cat artifacts/contracts/BlockProofCredentialVault.sol/BlockProofCredentialVault.json | jq .abi > ../backend/blockchain/contract_abi.json
```

## Step 5: Start Services

### 5.1 Start Redis

```bash
redis-server
```

### 5.2 Start Django Server

```bash
python manage.py runserver
```

### 5.3 Start Celery Worker (Terminal 2)

```bash
celery -A blockproof_backend worker -l info
```

### 5.4 Start Celery Beat (Terminal 3)

```bash
celery -A blockproof_backend beat -l info
```

## Step 6: Test the Backend

### 6.1 Health Check

```bash
curl http://localhost:8000/api/zkproof/status/
```

### 6.2 Test Credential Verification

```bash
curl http://localhost:8000/api/blockchain/status/1/
```

### 6.3 Test ZKProof Generation

```bash
curl -X POST http://localhost:8000/api/zkproof/proofs/generate/ \
  -H "Content-Type: application/json" \
  -d '{
    "credential_id": 1,
    "proof_type": "credential_validity"
  }'
```

## Step 7: API Endpoints

### Credentials
- `GET /api/credentials/` - List credentials
- `GET /api/credentials/{id}/` - Get credential
- `POST /api/credentials/issue/` - Issue credential
- `POST /api/credentials/{id}/revoke/` - Revoke credential

### Blockchain
- `POST /api/blockchain/verify/` - Verify fingerprint
- `GET /api/blockchain/status/{id}/` - Get credential status

### Zero-Knowledge Proofs
- `GET /api/zkproof/proofs/` - List proofs
- `POST /api/zkproof/proofs/generate/` - Generate proof
- `POST /api/zkproof/proofs/{id}/verify/` - Verify proof
- `POST /api/zkproof/proofs/verify_raw/` - Verify external proof
- `GET /api/zkproof/status/` - ZKProof service status

## Step 8: Using Zero-Knowledge Proofs

### 8.1 Generate a Proof

```python
import requests

response = requests.post('http://localhost:8000/api/zkproof/proofs/generate/', json={
    'credential_id': 1,
    'proof_type': 'credential_validity',
    'secret_data': {
        'gpa': 3.8,
        'ssn': '***-**-****'  # This won't be revealed
    }
})

proof = response.json()
print(f"Proof ID: {proof['id']}")
print(f"Public Inputs: {proof['public_inputs']}")
```

### 8.2 Verify a Proof

```python
response = requests.post(
    f'http://localhost:8000/api/zkproof/proofs/{proof_id}/verify/',
    json={
        'expected_fingerprint': '0x...'
    }
)

result = response.json()
print(f"Valid: {result['valid']}")
print(f"Verification Time: {result['verification_time']}s")
```

### 8.3 Privacy-Preserving Verification

The proof allows verification without revealing:
- Full credential details
- Secret data (GPA, SSN, etc.)
- Student wallet address (only hash)

But still proves:
- Credential is valid
- Credential is not revoked
- Credential matches fingerprint

## Troubleshooting

### Issue: "Contract not configured"
- Check `CONTRACT_ADDRESS` in `.env`
- Verify contract is deployed at that address

### Issue: "ZKProof not enabled"
- Check `ZKPROOF_ENABLED=True` in `.env`
- Restart Django server

### Issue: "Celery not working"
- Check Redis is running: `redis-cli ping`
- Check Celery worker logs
- Verify `CELERY_BROKER_URL` in `.env`

### Issue: "ABI not found"
- Extract ABI from compiled contract
- Place in `backend/blockchain/contract_abi.json`
- Restart Django server

## Next Steps

1. **Deploy to Production**: See `DEPLOYMENT.md`
2. **Add Authentication**: Implement JWT or session auth
3. **Advanced zk-SNARKs**: Set up Circom circuits for more powerful proofs
4. **IPFS Integration**: Store proofs on IPFS for decentralization
5. **Frontend Integration**: Connect React/Next.js frontend

## Architecture Overview

```
┌─────────────┐
│   Frontend  │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│      Django REST API                │
│  ┌──────────┐  ┌──────────┐        │
│  │Credentials│  │  ZKProof │        │
│  │   API    │  │   API    │        │
│  └──────────┘  └──────────┘        │
└──────┬──────────────────┬───────────┘
       │                  │
       ▼                  ▼
┌──────────────┐   ┌──────────────┐
│   Database   │   │ ZKProof      │
│              │   │ Service      │
│  - Credentials│   │              │
│  - ZKProofs  │   │ - Generate   │
│  - Events    │   │ - Verify     │
└──────┬───────┘   └──────────────┘
       │
       ▼
┌─────────────────────┐
│  Smart Contract     │
│  (Blockchain)       │
└─────────────────────┘
```

## Support

For issues or questions:
1. Check logs: `celery -A blockproof_backend worker -l debug`
2. Check Django logs in console
3. Verify all environment variables
4. Test RPC connection: `python manage.py shell` → `from blockchain.services import get_blockproof_service; s = get_blockproof_service(); s.w3.eth.block_number`










