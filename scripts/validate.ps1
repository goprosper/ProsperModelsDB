# Infrastructure Validation Script (PowerShell)
# Usage: .\scripts\validate.ps1 [environment]
# Example: .\scripts\validate.ps1 prod

param(
    [string]$Environment = "all"
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ValidateScript = Join-Path $ScriptDir "validate-infrastructure.py"

# Check if Python script exists
if (-not (Test-Path $ValidateScript)) {
    Write-Host "❌ Validation script not found: $ValidateScript" -ForegroundColor Red
    exit 1
}

# Check if Python is available
try {
    python --version | Out-Null
} catch {
    Write-Host "❌ Python is required but not installed" -ForegroundColor Red
    exit 1
}

# Check if boto3 is available
try {
    python -c "import boto3" 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "boto3 not found"
    }
} catch {
    Write-Host "❌ boto3 is required. Install with: pip install boto3" -ForegroundColor Red
    exit 1
}

# Run validation
if ($Environment -eq "all") {
    Write-Host "🔍 Validating all environments..." -ForegroundColor Cyan
    python $ValidateScript --all-environments
} else {
    Write-Host "🔍 Validating $Environment environment..." -ForegroundColor Cyan
    python $ValidateScript --environment $Environment
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Validation complete!" -ForegroundColor Green
} else {
    Write-Host "❌ Validation found issues!" -ForegroundColor Red
    exit $LASTEXITCODE
}