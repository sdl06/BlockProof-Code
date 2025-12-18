# BlockProof Contracts

Smart contracts for the BlockProof credential verification system.

## Quick Start with Hardhat

### 1. Install Dependencies
```bash
npm install
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your RPC_URL and PRIVATE_KEY
```

### 3. Compile
```bash
npm run compile
```

### 4. Deploy to Sepolia
```bash
npm run deploy:sepolia
```

### 5. Extract ABI for Backend
```bash
# On Linux/Mac/Git Bash:
cat artifacts/contracts/BlockProofCredentialVault.sol/BlockProofCredentialVault.json | jq .abi > ../backend/blockchain/contract_abi.json

# On Windows PowerShell:
Get-Content artifacts/contracts/BlockProofCredentialVault.sol/BlockProofCredentialVault.json | ConvertFrom-Json | Select-Object -ExpandProperty abi | ConvertTo-Json -Depth 100 | Out-File -Encoding utf8 ../backend/blockchain/contract_abi.json
```

## Prerequisites

1. **Node.js** (v16+) - ✅ You have this
2. **Sepolia ETH** - Get from https://sepoliafaucet.com/
3. **RPC URL** - Get from Infura or Alchemy (free tier)

## Getting Sepolia ETH

1. Go to https://sepoliafaucet.com/
2. Connect your wallet (MetaMask)
3. Request testnet ETH
4. Wait a few minutes for it to arrive

## Getting RPC URL

### Option 1: Infura (Free)
1. Go to https://infura.io/
2. Sign up and create a project
3. Copy your API key
4. RPC URL: `https://sepolia.infura.io/v3/YOUR_KEY`

### Option 2: Alchemy (Free)
1. Go to https://www.alchemy.com/
2. Create app for Sepolia
3. Copy API key
4. RPC URL: `https://eth-sepolia.g.alchemy.com/v2/YOUR_KEY`

## Deployment Steps

1. **Install**: `npm install`
2. **Configure**: Edit `.env` with your RPC_URL and PRIVATE_KEY
3. **Compile**: `npm run compile`
4. **Deploy**: `npm run deploy:sepolia`
5. **Save Address**: Copy the contract address to backend `.env`
6. **Extract ABI**: Run the command above to copy ABI to backend

## Troubleshooting

- **"Cannot find module"**: Run `npm install`
- **"Insufficient funds"**: Get Sepolia ETH from faucet
- **"Network not found"**: Check `hardhat.config.js` and `.env`
- **"Private key invalid"**: Make sure it starts with `0x`

## Files

- `BlockProofCredentialVault.sol` - Main contract
- `hardhat.config.js` - Hardhat configuration
- `scripts/deploy.js` - Deployment script
- `.env` - Environment variables (not in git)














