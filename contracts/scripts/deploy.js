const hre = require("hardhat");

async function main() {
  console.log("Deploying BlockProofCredentialVault...");
  console.log("Network:", hre.network.name);
  
  // Get the contract factory
  const BlockProofCredentialVault = await hre.ethers.getContractFactory("BlockProofCredentialVault");
  
  // Deploy the contract
  console.log("Deploying contract...");
  const contract = await BlockProofCredentialVault.deploy();
  
  // Wait for deployment
  await contract.waitForDeployment();
  
  // Get the deployed address
  const address = await contract.getAddress();
  
  console.log("\n" + "=".repeat(60));
  console.log("✅ Contract deployed successfully!");
  console.log("=".repeat(60));
  console.log("Contract Address:", address);
  console.log("\n📋 Add this to your backend/.env file:");
  console.log(`CONTRACT_ADDRESS=${address}`);
  console.log("\n🔗 View on Etherscan:");
  if (hre.network.name === "sepolia") {
    console.log(`https://sepolia.etherscan.io/address/${address}`);
  }
  console.log("=".repeat(60));
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("\n❌ Deployment failed:");
    console.error(error);
    process.exit(1);
  });










