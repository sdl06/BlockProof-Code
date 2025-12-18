# How to Get Your Private Key from MetaMask

## ⚠️ SECURITY WARNING

**NEVER share your private key with anyone!**
- Your private key gives full control over your wallet
- Anyone with your private key can steal all your funds
- Only use it for development/testnet wallets
- **NEVER use your main wallet's private key**

## ✅ Safe Approach: Create a Separate Test Wallet

**Recommended**: Create a new MetaMask wallet specifically for development/testing.

### Step 1: Create New Account in MetaMask

1. Open MetaMask extension
2. Click the account icon (top right)
3. Click **"Create Account"** or **"Add Account"**
4. Name it something like "BlockProof Dev" or "Test Wallet"
5. Click **"Create"**

### Step 2: Export Private Key

1. Click the **three dots (⋮)** next to your account name
2. Select **"Account details"**
3. Click **"Show private key"**
4. Enter your MetaMask password
5. Click **"Show private key"** again
6. **Copy the private key** (it starts with `0x`)

### Step 3: Save Securely

- **DO NOT** save it in a file that gets committed to git
- **DO NOT** share it in screenshots or messages
- **DO** save it in your `.env` file (which should be in `.gitignore`)
- **DO** use a password manager for extra security

## 📝 Using the Private Key

### In Your .env File

```bash
# contracts/.env
PRIVATE_KEY=0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef

# backend/.env
PRIVATE_KEY=0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef
```

**Important**: Make sure `.env` is in your `.gitignore` file!

## 🔒 Security Best Practices

### ✅ DO:
- Use a separate wallet for development
- Keep private keys in `.env` files (not in code)
- Use testnet for development (Sepolia, Goerli)
- Never commit `.env` to git
- Use a password manager for production keys

### ❌ DON'T:
- Share your private key with anyone
- Commit private keys to git
- Use your main wallet's private key
- Post private keys in screenshots or messages
- Store private keys in plain text files in your repo

## 🧪 For Testing/Development

### Option 1: MetaMask Test Wallet (Recommended)
- Create a new account in MetaMask
- Use that account's private key
- Only fund it with testnet ETH

### Option 2: Generate New Wallet
You can also generate a new wallet programmatically:

```javascript
// In Node.js console
const { ethers } = require("ethers");
const wallet = ethers.Wallet.createRandom();
console.log("Address:", wallet.address);
console.log("Private Key:", wallet.privateKey);
```

**Then import this wallet into MetaMask:**
1. MetaMask → Import Account
2. Paste the private key
3. Name it "Generated Test Wallet"

## 🎯 Quick Checklist

- [ ] Created a separate test wallet in MetaMask
- [ ] Exported the private key
- [ ] Saved it in `.env` file (not committed to git)
- [ ] Got Sepolia testnet ETH for that wallet
- [ ] Verified `.env` is in `.gitignore`

## 🚨 If Your Private Key is Compromised

If you accidentally shared your private key:

1. **Immediately transfer all funds** to a new wallet
2. **Stop using that wallet** completely
3. **Create a new wallet** for future use
4. **Never reuse** the compromised wallet

## 📚 Additional Resources

- MetaMask Security: https://metamask.io/security/
- Testnet Faucets: https://sepoliafaucet.com/
- Ethereum Security: https://ethereum.org/en/security/

---

**Remember**: Your private key is like the password to your bank account. Treat it with extreme care!














