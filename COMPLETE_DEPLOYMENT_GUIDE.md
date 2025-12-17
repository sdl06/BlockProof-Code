# Complete Deployment Guide: BlockProof Full Stack

## 🔍 Current Status

**❌ NOT Connected Yet** - The backend code is ready, but you need to:
1. Deploy the smart contract
2. Extract the contract ABI
3. Configure environment variables
4. Connect everything together

## 📋 Deployment Checklist

### Phase 1: Smart Contract Deployment
- [ ] Install Foundry or Hardhat
- [ ] Compile contract
- [ ] Deploy to testnet (Sepolia)
- [ ] Save contract address
- [ ] Extract contract ABI

### Phase 2: Backend Setup
- [ ] Install Python dependencies
- [ ] Configure environment variables
- [ ] Setup database
- [ ] Test blockchain connection

### Phase 3: Production Deployment
- [ ] Choose hosting platform
- [ ] Deploy backend
- [ ] Setup Celery workers
- [ ] Configure domain & SSL

---

## 🚀 Step-by-Step Deployment

## PART 1: Deploy Smart Contract

### Option A: Using Foundry (Recommended)

#### 1.1 Install Foundry
```bash
# Install Foundry
curl -L https://foundry.paradigm.xyz | bash
foundryup
```

#### 1.2 Setup Project
```bash
cd BlockProof-Code/contracts

# If not already a Foundry project
forge init --force
```

#### 1.3 Compile Contract
```bash
forge build
```

#### 1.4 Get Testnet ETH
- Go to https://sepoliafaucet.com/
- Request Sepolia ETH for your wallet
- You'll need ~0.1 ETH for deployment

#### 1.5 Deploy Contract
```bash
# Set environment variables
export RPC_URL="https://sepolia.infura.io/v3/YOUR_INFURA_KEY"
export PRIVATE_KEY="0xYOUR_PRIVATE_KEY"

# Deploy
forge create BlockProofCredentialVault \
  --rpc-url $RPC_URL \
  --private-key $PRIVATE_KEY \
  --constructor-args

# Save the contract address from output
# Example: Deployed to: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
```

#### 1.6 Extract ABI
```bash
# Extract ABI to backend
cat out/BlockProofCredentialVault.sol/BlockProofCredentialVault.json | jq .abi > ../backend/blockchain/contract_abi.json

# Verify ABI was created
ls -la ../backend/blockchain/contract_abi.json
```

### Option B: Using Hardhat

#### 1.1 Install Hardhat
```bash
cd BlockProof-Code/contracts
npm install --save-dev hardhat @nomicfoundation/hardhat-toolbox
npx hardhat init
```

#### 1.2 Configure hardhat.config.js
```javascript
require("@nomicfoundation/hardhat-toolbox");

module.exports = {
  solidity: "0.8.21",
  networks: {
    sepolia: {
      url: process.env.RPC_URL,
      accounts: [process.env.PRIVATE_KEY]
    }
  }
};
```

#### 1.3 Compile & Deploy
```bash
# Compile
npx hardhat compile

# Deploy
npx hardhat run scripts/deploy.js --network sepolia

# Save contract address from output
```

#### 1.4 Extract ABI
```bash
cat artifacts/contracts/BlockProofCredentialVault.sol/BlockProofCredentialVault.json | jq .abi > ../backend/blockchain/contract_abi.json
```

---

## PART 2: Setup Backend Locally

### 2.1 Install Dependencies
```bash
cd BlockProof-Code/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### 2.2 Get RPC Endpoint

**Option 1: Infura (Free Tier)**
1. Go to https://infura.io/
2. Sign up and create a project
3. Copy your API key
4. RPC URL: `https://sepolia.infura.io/v3/YOUR_KEY`

**Option 2: Alchemy (Free Tier)**
1. Go to https://www.alchemy.com/
2. Create app for Sepolia testnet
3. Copy API key
4. RPC URL: `https://eth-sepolia.g.alchemy.com/v2/YOUR_KEY`

**Option 3: Public RPC (Free, Slower)**
- `https://rpc.sepolia.org`

### 2.3 Configure Environment
```bash
# Copy example file
cp .env.example .env

# Edit .env file
nano .env  # or use your favorite editor
```

**Fill in these values:**
```bash
# Django
SECRET_KEY=generate-a-random-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (SQLite for development)
DATABASE_URL=sqlite:///db.sqlite3

# Blockchain - USE YOUR VALUES FROM PART 1
RPC_URL=https://sepolia.infura.io/v3/YOUR_INFURA_KEY
CONTRACT_ADDRESS=0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb  # Your deployed address
CHAIN_ID=11155111  # Sepolia testnet
PRIVATE_KEY=0xYOUR_PRIVATE_KEY  # For write operations

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Zero-Knowledge Proofs
ZKPROOF_ENABLED=True
```

### 2.4 Setup Database
```bash
# Run migrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser
```

### 2.5 Install Redis (for Celery)
```bash
# macOS
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# Windows
# Download from: https://github.com/microsoftarchive/redis/releases
# Or use WSL
```

### 2.6 Test Connection
```bash
# Start Django shell
python manage.py shell

# Test blockchain connection
>>> from blockchain.services import get_blockproof_service
>>> service = get_blockproof_service()
>>> service.w3.eth.block_number
# Should return a number (latest block)

>>> service.contract
# Should show contract instance (not None)

>>> service.contract.functions.credentialCount().call()
# Should return 0 (no credentials yet)
```

### 2.7 Start Services
```bash
# Terminal 1: Django
python manage.py runserver

# Terminal 2: Celery Worker
celery -A blockproof_backend worker -l info

# Terminal 3: Celery Beat
celery -A blockproof_backend beat -l info
```

### 2.8 Verify Everything Works
```bash
# Test API
curl http://localhost:8000/api/zkproof/status/

# Should return:
# {"enabled": true, "status": "operational", ...}

# Test blockchain connection
curl http://localhost:8000/api/blockchain/status/1/
```

---

## PART 3: Deploy to Production

### Option A: Railway (Easiest, ~$5-20/month)

#### 3.1 Install Railway CLI
```bash
npm i -g @railway/cli
railway login
```

#### 3.2 Initialize Project
```bash
cd BlockProof-Code/backend
railway init
railway link
```

#### 3.3 Add Services
1. Go to Railway dashboard
2. Add **PostgreSQL** service
3. Add **Redis** service
4. Your Django app is already added

#### 3.4 Set Environment Variables
```bash
# In Railway dashboard, go to Variables tab
# Or use CLI:
railway variables set SECRET_KEY=your-production-secret-key
railway variables set DEBUG=False
railway variables set ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
railway variables set RPC_URL=https://sepolia.infura.io/v3/YOUR_KEY
railway variables set CONTRACT_ADDRESS=0x...
railway variables set CHAIN_ID=11155111
railway variables set PRIVATE_KEY=0x...
railway variables set ZKPROOF_ENABLED=True

# Database URL is auto-set by Railway
# Celery URLs are auto-set by Railway
```

#### 3.5 Deploy
```bash
railway up
```

#### 3.6 Setup Celery Workers
1. In Railway dashboard, add new service
2. Name it "celery-worker"
3. Command: `celery -A blockproof_backend worker -l info`
4. Same environment variables

#### 3.7 Setup Celery Beat
1. Add another service "celery-beat"
2. Command: `celery -A blockproof_backend beat -l info`
3. Same environment variables

#### 3.8 Run Migrations
```bash
railway run python manage.py migrate
railway run python manage.py createsuperuser
```

### Option B: Render (Free Tier Available)

#### 3.1 Create Web Service
1. Go to https://render.com/
2. Connect GitHub repository
3. Create new Web Service
4. Settings:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn blockproof_backend.wsgi:application`
   - **Environment**: Python 3

#### 3.2 Add PostgreSQL
1. Create PostgreSQL database
2. Copy connection string to `DATABASE_URL`

#### 3.3 Add Redis
1. Create Redis instance
2. Copy URL to `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND`

#### 3.4 Set Environment Variables
In Render dashboard → Environment:
```
SECRET_KEY=...
DEBUG=False
ALLOWED_HOSTS=your-app.onrender.com
DATABASE_URL=postgresql://...
RPC_URL=...
CONTRACT_ADDRESS=...
CHAIN_ID=11155111
PRIVATE_KEY=...
CELERY_BROKER_URL=redis://...
CELERY_RESULT_BACKEND=redis://...
ZKPROOF_ENABLED=True
```

#### 3.5 Create Background Workers
1. Create Background Worker for Celery worker
2. Command: `celery -A blockproof_backend worker -l info`
3. Create another for Celery beat
4. Command: `celery -A blockproof_backend beat -l info`

### Option C: AWS/GCP (More Complex)

See `backend/DEPLOYMENT.md` for detailed AWS/GCP instructions.

---

## PART 4: Post-Deployment

### 4.1 Initial Data Sync
```bash
# Sync historical events from blockchain
python manage.py sync_events

# Or via Django shell
python manage.py shell
>>> from blockchain.tasks import index_blockchain_events
>>> index_blockchain_events()
```

### 4.2 Test Production API
```bash
# Test health check
curl https://your-domain.com/api/zkproof/status/

# Test blockchain connection
curl https://your-domain.com/api/blockchain/status/1/
```

### 4.3 Setup Monitoring
- Monitor Celery workers
- Set up error alerts
- Track RPC usage
- Monitor database size

### 4.4 Setup Domain & SSL
- Railway/Render: Automatic SSL
- Custom domain: Add in dashboard
- Update `ALLOWED_HOSTS`

---

## 🔧 Troubleshooting

### Issue: "Contract not configured"
**Solution:**
- Check `CONTRACT_ADDRESS` in environment variables
- Verify contract is deployed at that address
- Test: `service.contract` should not be None

### Issue: "RPC errors"
**Solution:**
- Verify RPC URL is correct
- Check you're within free tier limits
- Try public RPC as fallback
- Test: `service.w3.eth.block_number` should return a number

### Issue: "ABI not found"
**Solution:**
- Extract ABI from compiled contract
- Place in `backend/blockchain/contract_abi.json`
- Or ensure fallback ABI works

### Issue: "Celery not working"
**Solution:**
- Check Redis is running
- Verify `CELERY_BROKER_URL` is correct
- Check Celery worker logs
- Test: `celery -A blockproof_backend inspect active`

### Issue: "Database errors"
**Solution:**
- Run migrations: `python manage.py migrate`
- Check database connection string
- Verify database exists and is accessible

---

## ✅ Verification Checklist

After deployment, verify:

- [ ] Django server is running
- [ ] Celery worker is running
- [ ] Celery beat is running
- [ ] Database migrations completed
- [ ] Contract ABI loaded successfully
- [ ] Blockchain connection works (`service.w3.eth.block_number`)
- [ ] Contract instance created (`service.contract` is not None)
- [ ] API endpoints respond
- [ ] Event indexer is syncing
- [ ] ZKProof service is enabled

---

## 🎯 Quick Test Commands

```bash
# Test blockchain connection
python manage.py shell
>>> from blockchain.services import get_blockproof_service
>>> s = get_blockproof_service()
>>> s.w3.eth.block_number  # Should return number
>>> s.contract.functions.credentialCount().call()  # Should return 0

# Test API
curl http://localhost:8000/api/zkproof/status/
curl http://localhost:8000/api/blockchain/status/1/

# Test event indexing
python manage.py sync_events
```

---

## 📊 Cost Estimates

### Development (Free)
- Testnet: Free
- Free RPC tier: 100k+ requests/day
- Local database: Free
- **Total: $0/month**

### Production (Railway/Render)
- App hosting: $5-10/month
- PostgreSQL: Included or $5/month
- Redis: $0-5/month (free tier available)
- RPC calls: Free (within tier)
- **Total: ~$5-20/month**

---

## 🚀 Next Steps After Deployment

1. **Test Credential Issuance**
   ```bash
   curl -X POST https://your-domain.com/api/credentials/issue/ \
     -H "Content-Type: application/json" \
     -d '{...}'
   ```

2. **Generate ZKProof**
   ```bash
   curl -X POST https://your-domain.com/api/zkproof/proofs/generate/ \
     -H "Content-Type: application/json" \
     -d '{"credential_id": 1, "proof_type": "credential_validity"}'
   ```

3. **Verify Proof**
   ```bash
   curl -X POST https://your-domain.com/api/zkproof/proofs/1/verify/
   ```

4. **Monitor Event Indexing**
   - Check Celery logs
   - Verify events are syncing
   - Check database for new credentials

---

## 📚 Additional Resources

- **Contract Connection**: `backend/CONTRACT_CONNECTION.md`
- **Setup Guide**: `backend/SETUP_GUIDE.md`
- **Cost Optimization**: `backend/COST_OPTIMIZATION.md`
- **Architecture**: `backend/ARCHITECTURE_SUMMARY.md`

---

**Status**: Ready to deploy! Follow the steps above to get your full stack running. 🚀










