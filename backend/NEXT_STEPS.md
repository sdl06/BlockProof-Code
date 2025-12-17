# Next Steps: Building Your BlockProof Backend

This document outlines the immediate next steps to get your Django backend running with the Solidity contract.

## Immediate Actions Required

### 1. Compile and Deploy Smart Contract

Before the Django backend can work, you need a deployed contract:

```bash
# Using Foundry (recommended)
cd BlockProof-Code/contracts
forge build
forge create BlockProofCredentialVault --rpc-url $RPC_URL --private-key $PRIVATE_KEY

# Or using Hardhat
npx hardhat compile
npx hardhat deploy --network sepolia
```

**Save the contract address** - you'll need it for `CONTRACT_ADDRESS` in `.env`.

### 2. Get Contract ABI

After compiling, extract the ABI:

**Foundry**:
```bash
cat out/BlockProofCredentialVault.sol/BlockProofCredentialVault.json | jq .abi > backend/blockchain/contract_abi.json
```

**Hardhat**:
```bash
cat artifacts/contracts/BlockProofCredentialVault.sol/BlockProofCredentialVault.json | jq .abi > backend/blockchain/contract_abi.json
```

Then update `backend/blockchain/services.py` to load from file:
```python
def _load_contract_abi(self) -> List[Dict]:
    import json
    abi_path = os.path.join(os.path.dirname(__file__), 'contract_abi.json')
    with open(abi_path) as f:
        return json.load(f)
```

### 3. Setup Environment

```bash
cd backend
cp .env.example .env
# Edit .env with your values:
# - RPC_URL (get from Infura/Alchemy)
# - CONTRACT_ADDRESS (from step 1)
# - PRIVATE_KEY (for write operations)
```

### 4. Install and Run

```bash
# Install dependencies
pip install -r requirements.txt

# Setup database
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run server
python manage.py runserver
```

### 5. Setup Celery (for event indexing)

In separate terminals:

```bash
# Terminal 1: Redis (if not running)
redis-server

# Terminal 2: Celery worker
celery -A blockproof_backend worker -l info

# Terminal 3: Celery beat (scheduler)
celery -A blockproof_backend beat -l info
```

### 6. Initial Event Sync

After deployment, sync historical events:

```bash
python manage.py sync_events
```

## Testing the Integration

### 1. Test Read Operations (Free)

```bash
# Get credential status
curl http://localhost:8000/api/blockchain/status/1/

# Verify fingerprint
curl -X POST http://localhost:8000/api/blockchain/verify/ \
  -H "Content-Type: application/json" \
  -d '{"credential_id": 1, "fingerprint": "0x..."}'
```

### 2. Test Write Operations (Costs Gas)

```bash
# Issue credential (requires private key in .env)
curl -X POST http://localhost:8000/api/credentials/issue/ \
  -H "Content-Type: application/json" \
  -d '{
    "institution_address": "0x...",
    "student_wallet": "0x...",
    "fingerprint": "0x...",
    "metadata_uri": "https://ipfs.io/...",
    "encrypted_payload_uri": "https://..."
  }'
```

## Cost Optimization Checklist

- [ ] Using testnet (Sepolia) for development
- [ ] Using free RPC tier (Infura/Alchemy)
- [ ] Event indexer running (minimizes RPC calls)
- [ ] Database caching enabled
- [ ] Monitoring RPC usage

## Development Workflow

1. **Local Development**:
   - Use SQLite (no setup needed)
   - Use Sepolia testnet (free)
   - Run Celery locally

2. **Testing**:
   - Test on testnet first
   - Verify event indexing works
   - Test all API endpoints

3. **Production**:
   - Deploy to Railway/Render
   - Use PostgreSQL
   - Use mainnet or L2 (Polygon/Arbitrum)
   - Set up monitoring

## Common Issues & Solutions

### Issue: "Contract not configured"
**Solution**: Set `CONTRACT_ADDRESS` in `.env`

### Issue: "RPC errors"
**Solution**: 
- Check RPC URL is correct
- Verify you're within free tier limits
- Try public RPC as fallback

### Issue: "Events not syncing"
**Solution**:
- Check Celery worker is running
- Check Celery beat is running
- Check Redis is running
- Run `python manage.py sync_events` manually

### Issue: "Database errors"
**Solution**:
- Run `python manage.py migrate`
- Check database connection in settings
- Verify database exists

## API Documentation

Once running, explore the API:

- **Admin**: http://localhost:8000/admin/
- **API Root**: http://localhost:8000/api/
- **Credentials**: http://localhost:8000/api/credentials/
- **Institutions**: http://localhost:8000/api/institutions/
- **Blockchain**: http://localhost:8000/api/blockchain/

## Next Features to Add

1. **Authentication**: Add JWT or session auth for API
2. **Rate Limiting**: Prevent abuse
3. **API Documentation**: Add Swagger/OpenAPI
4. **Webhooks**: Notify on credential events
5. **Analytics**: Track usage and costs
6. **Batch Operations**: Issue multiple credentials at once

## Resources

- [Django REST Framework Docs](https://www.django-rest-framework.org/)
- [Web3.py Docs](https://web3py.readthedocs.io/)
- [Celery Docs](https://docs.celeryproject.org/)
- [Cost Optimization Guide](./COST_OPTIMIZATION.md)
- [Deployment Guide](./DEPLOYMENT.md)

## Support

If you encounter issues:
1. Check logs: `celery -A blockproof_backend worker -l debug`
2. Check Django logs in console
3. Verify all environment variables are set
4. Test RPC connection: `python manage.py shell` → `from blockchain.services import get_blockproof_service; s = get_blockproof_service(); s.w3.eth.block_number`

