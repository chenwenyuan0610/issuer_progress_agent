$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $repoRoot

$logPath = Join-Path $repoRoot "run_api.debug.log"
"$(Get-Date -Format o) starting api from $repoRoot" | Add-Content -LiteralPath $logPath
python -m uvicorn app.main:app --host 127.0.0.1 --port 8080
"$(Get-Date -Format o) api exited with code $LASTEXITCODE" | Add-Content -LiteralPath $logPath
