# Quick Guide: Get Private Key from MetaMask

## ⚠️ IMPORTANT: Use a Test Wallet!

**Create a separate wallet for development** - don't use your main wallet!

## Steps:

### 1. Create New Account in MetaMask
- Open MetaMask
- Click account icon (top right)
- Click **"Create Account"** or **"Add Account"**
- Name it "BlockProof Dev"
- Click **"Create"**

### 2. Get Private Key
- Click **three dots (⋮)** next to account name
- Select **"Account details"**
- Click **"Show private key"**
- Enter your MetaMask password
- **Copy the private key** (starts with `0x`)

### 3. Save in .env File
```bash
# In contracts/.env
PRIVATE_KEY=0xYOUR_PRIVATE_KEY_HERE

# In backend/.env  
PRIVATE_KEY=0xYOUR_PRIVATE_KEY_HERE
```

### 4. Get Testnet ETH
- Go to https://sepoliafaucet.com/
- Connect your MetaMask wallet
- Request Sepolia ETH
- Wait a few minutes

## ✅ Done!

Now you can deploy your contract. See `GET_PRIVATE_KEY.md` for more details and security tips.













