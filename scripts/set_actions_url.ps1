param(
    [Parameter(Mandatory = $true)]
    [string] $Url
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$specPath = Join-Path $repoRoot "openapi-actions.yaml"
$normalizedUrl = $Url.Trim().TrimEnd("/")

if (-not $normalizedUrl.StartsWith("https://")) {
    throw "Custom GPT Actions require an https URL. Got: $Url"
}

$content = Get-Content -LiteralPath $specPath -Raw
$content = $content -replace "url: https://.*", "url: $normalizedUrl"
Set-Content -LiteralPath $specPath -Value $content -Encoding utf8

"Updated openapi-actions.yaml server URL to $normalizedUrl"
