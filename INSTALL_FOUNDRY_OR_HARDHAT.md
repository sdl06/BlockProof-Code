# Installing Foundry or Hardhat

You have Node.js installed, so you can use either tool. **Hardhat is easier on Windows.**

## Option 1: Install Hardhat (Recommended for Windows) ⭐

### Step 1: Install Hardhat in your contracts directory
```bash
cd BlockProof-Code/contracts
npm install --save-dev hardhat @nomicfoundation/hardhat-toolbox
```

### Step 2: Initialize Hardhat
```bash
npx hardhat init
```

When prompted:
- Choose: **Create a JavaScript project**
- Yes to install dependencies
- Yes to add .gitignore

### Step 3: Create hardhat.config.js
Replace the contents of `hardhat.config.js` with:

```javascript
require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config();

module.exports = {
  solidity: {
    version: "0.8.21",
    settings: {
      optimizer: {
        enabled: true,
        runs: 200
      }
    }
  },
  networks: {
    sepolia: {
      url: process.env.RPC_URL || "https://rpc.sepolia.org",
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : []
    }
  },
  paths: {
    sources: "./",
    tests: "./test",
    cache: "./cache",
    artifacts: "./artifacts"
  }
};
```

### Step 4: Install dotenv (for environment variables)
```bash
npm install dotenv
```

### Step 5: Create .env file
```bash
# In contracts directory
echo RPC_URL=https://sepolia.infura.io/v3/YOUR_KEY > .env
echo PRIVATE_KEY=0xYOUR_PRIVATE_KEY >> .env
```

### Step 6: Compile Contract
```bash
npx hardhat compile
```

### Step 7: Create Deployment Script
Create `scripts/deploy.js`:

```javascript
const hre = require("hardhat");

async function main() {
  console.log("Deploying BlockProofCredentialVault...");
  
  const BlockProofCredentialVault = await hre.ethers.getContractFactory("BlockProofCredentialVault");
  const contract = await BlockProofCredentialVault.deploy();
  
  await contract.waitForDeployment();
  
  const address = await contract.getAddress();
  console.log("Contract deployed to:", address);
  console.log("\nSave this address for your .env file:");
  console.log(`CONTRACT_ADDRESS=${address}`);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
```

### Step 8: Deploy to Sepolia
```bash
npx hardhat run scripts/deploy.js --network sepolia
```

### Step 9: Extract ABI
```bash
# The ABI is automatically in artifacts/contracts/BlockProofCredentialVault.sol/BlockProofCredentialVault.json
# Copy it to backend
cat artifacts/contracts/BlockProofCredentialVault.sol/BlockProofCredentialVault.json | jq .abi > ../backend/blockchain/contract_abi.json
```

**On Windows PowerShell, use:**
```powershell
Get-Content artifacts/contracts/BlockProofCredentialVault.sol/BlockProofCredentialVault.json | ConvertFrom-Json | Select-Object -ExpandProperty abi | ConvertTo-Json -Depth 100 | Out-File -Encoding utf8 ../backend/blockchain/contract_abi.json
```

---

## Option 2: Install Foundry (More Advanced)

### Windows Installation

#### Method A: Using Git Bash or WSL (Recommended)

1. **Install Git for Windows** (if not installed): https://git-scm.com/download/win

2. **Open Git Bash** (not PowerShell)

3. **Install Foundry**:
```bash
curl -L https://foundry.paradigm.xyz | bash
```

4. **Restart terminal**, then run:
```bash
foundryup
```

5. **Verify installation**:
```bash
forge --version
cast --version
```

#### Method B: Using PowerShell (Alternative)

1. **Install Foundry using PowerShell**:
```powershell
# Download and run installer
irm https://github.com/foundry-rs/foundry/releases/latest/download/foundry_nightly_x86_64-pc-windows-msvc.tar.gz -OutFile foundry.tar.gz

# Extract (requires 7-Zip or similar)
# Then add to PATH
```

**Note**: Method A (Git Bash/WSL) is much easier!

### After Installation

1. **Initialize Foundry project** (if not already):
```bash
cd BlockProof-Code/contracts
forge init --force
```

2. **Compile**:
```bash
forge build
```

3. **Deploy**:
```bash
forge create BlockProofCredentialVault \
  --rpc-url $RPC_URL \
  --private-key $PRIVATE_KEY
```

4. **Extract ABI**:
```bash
cat out/BlockProofCredentialVault.sol/BlockProofCredentialVault.json | jq .abi > ../backend/blockchain/contract_abi.json
```

---

## Quick Comparison

| Feature | Hardhat | Foundry |
|---------|---------|---------|
| **Windows Support** | ✅ Excellent | ⚠️ Needs Git Bash/WSL |
| **Installation** | ✅ Easy (npm) | ⚠️ More complex |
| **Speed** | Good | ⚡ Very Fast |
| **Testing** | JavaScript | Solidity |
| **Recommended For** | Beginners, Windows | Advanced users |

---

## Recommendation

**Use Hardhat** since you're on Windows and already have Node.js installed. It's much easier to set up and works perfectly for your needs.

---

## Next Steps After Installation

1. **Get Sepolia ETH**:
   - Go to https://sepoliafaucet.com/
   - Request testnet ETH for your wallet

2. **Get RPC URL**:
   - Infura: https://infura.io/ (free tier)
   - Alchemy: https://www.alchemy.com/ (free tier)

3. **Deploy Contract** (using Hardhat or Foundry)

4. **Extract ABI** and place in `backend/blockchain/contract_abi.json`

5. **Configure Backend** (see `COMPLETE_DEPLOYMENT_GUIDE.md`)

---

## Troubleshooting

### Hardhat Issues
- **"Cannot find module"**: Run `npm install` in contracts directory
- **"Network not found"**: Check `hardhat.config.js` network configuration
- **"Insufficient funds"**: Get Sepolia ETH from faucet

### Foundry Issues (Windows)
- **"forge: command not found"**: Use Git Bash instead of PowerShell
- **Installation fails**: Try WSL (Windows Subsystem for Linux)
- **Path issues**: Add Foundry to your PATH environment variable

---

**Ready to proceed?** Choose Hardhat (easier) or Foundry (faster), then follow the deployment guide!













