# Deploy Your Contract Now! 🚀

You have testnet tokens - let's deploy!

## Step 1: Get Your Private Key

1. In MetaMask, click **three dots (⋮)** next to your account name
2. Select **"Account details"**
3. Click **"Show private key"**
4. Enter your MetaMask password
5. **Copy the private key** (starts with `0x`)
6. **Save it somewhere safe** (you'll need it in a moment)

## Step 2: Configure Contracts

### Create .env file in contracts directory:

```bash
cd BlockProof-Code/contracts
```

Create `.env` file with:
```
RPC_URL=https://sepolia.base.org
PRIVATE_KEY=0xYOUR_PRIVATE_KEY_HERE
```

**Replace `YOUR_PRIVATE_KEY_HERE` with the private key you just copied!**

## Step 3: Install Dependencies

```bash
npm install
```

This will install Hardhat and all dependencies.

## Step 4: Compile Contract

```bash
npm run compile
```

You should see "Compiled successfully" message.

## Step 5: Deploy to Base Sepolia

```bash
npx hardhat run scripts/deploy.js --network baseSepolia
```

**This will:**
- Deploy your contract to Base Sepolia testnet
- Show you the contract address
- **Save the contract address!** You'll need it for the backend

## Step 6: Extract ABI

After deployment, extract the ABI for the backend:

**On Windows PowerShell:**
```powershell
.\extract-abi.ps1
```

**Or manually:**
```powershell
Get-Content artifacts/contracts/BlockProofCredentialVault.sol/BlockProofCredentialVault.json | ConvertFrom-Json | Select-Object -ExpandProperty abi | ConvertTo-Json -Depth 100 | Out-File -Encoding utf8 ../backend/blockchain/contract_abi.json
```

## Step 7: Configure Backend

1. Go to `backend` directory
2. Copy `.env.example` to `.env` (if not already done)
3. Edit `.env` and add:

```bash
RPC_URL=https://sepolia.base.org
CHAIN_ID=84532
CONTRACT_ADDRESS=0x...  # The address from Step 5
PRIVATE_KEY=0x...  # Your private key
```

## Step 8: Test Connection

```bash
cd ../backend
python check_connection.py
```

This will verify everything is connected correctly!

## ✅ You're Done!

Your contract is deployed and backend is configured. Next:
- Start Django server
- Start Celery workers
- Test the API

---

**Let's do it step by step!** 🚀













