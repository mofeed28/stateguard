param(
    [switch]$Live,
    [ValidateSet('bedrock', 'openai')][string]$Provider = 'bedrock',
    [string]$AwsProfile = 'stateguard',
    [string]$Region = 'us-east-1'
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$env:STATEGUARD_MODEL_PROVIDER = $Provider
$env:AWS_PROFILE = $AwsProfile
$env:AWS_REGION = $Region
$env:STATEGUARD_DB_PATH = Join-Path $projectRoot 'sandbox.sqlite3'
$env:STATEGUARD_USE_STRANDS_LLM = '0'
if ($Live) {
    if ($Provider -eq 'bedrock') {
    python scripts/check_aws.py --profile $AwsProfile --region $Region
    if ($LASTEXITCODE -eq 4) { throw 'AWS login works, but Nova Micro has zero inference allowance. Await AWS quota restoration; signing in again will not fix this.' }
    if ($LASTEXITCODE -ne 0) { throw 'AWS preflight failed. Review the diagnostic above before starting live mode.' }
    }
    $keyPath = Join-Path $projectRoot '.stateguard-live-key'
    if (-not (Test-Path -LiteralPath $keyPath)) {
        $demoKey = python -c 'import secrets; print(secrets.token_urlsafe(32))'
        Set-Content -LiteralPath $keyPath -Value $demoKey -NoNewline
    }
    $env:STATEGUARD_LIVE_DEMO_KEY = (Get-Content -LiteralPath $keyPath -Raw).Trim()
    $env:STATEGUARD_USE_STRANDS_LLM = '1'
    Write-Host 'Live mode enabled. Copy the local demo access key from .stateguard-live-key when the UI asks. The selected model provider must have available quota.'
}
python -m uvicorn stateguard.app:app --app-dir backend --host 127.0.0.1 --port 8787
