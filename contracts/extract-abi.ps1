# PowerShell script to extract ABI from Hardhat artifacts
# Usage: .\extract-abi.ps1

$artifactPath = "artifacts/contracts/BlockProofCredentialVault.sol/BlockProofCredentialVault.json"
$outputPath = "../backend/blockchain/contract_abi.json"

if (Test-Path $artifactPath) {
    Write-Host "Extracting ABI from $artifactPath..."
    
    $json = Get-Content $artifactPath | ConvertFrom-Json
    $abi = $json.abi | ConvertTo-Json -Depth 100
    
    # Ensure output directory exists
    $outputDir = Split-Path $outputPath -Parent
    if (-not (Test-Path $outputDir)) {
        New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
    }
    
    $abi | Out-File -FilePath $outputPath -Encoding utf8
    
    Write-Host "✅ ABI extracted to $outputPath"
} else {
    Write-Host "❌ Error: Artifact not found at $artifactPath"
    Write-Host "Make sure you've compiled the contract first: npm run compile"
    exit 1
}














