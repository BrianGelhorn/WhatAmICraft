param(
    [switch]$Reset,
    [switch]$Down,
    [switch]$Logs
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$composeFile = Join-Path $root "compose.pre-main.yaml"
$runtime = Join-Path $root "staging/runtime/pre-main"
$project = "whatamicraft-pre-main"
$composeArgs = @("-p", $project, "--project-directory", $root, "-f", $composeFile)

function Invoke-Compose {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)
    & docker compose @composeArgs @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "docker compose failed with exit code $LASTEXITCODE"
    }
}

function Invoke-PrepareRuntime {
    $python = Get-Command py -ErrorAction SilentlyContinue
    if ($null -ne $python) {
        if ($Reset) { & py -3 (Join-Path $root "scripts/ci/prepare_staging.py") --runtime-root $runtime --reset }
        else { & py -3 (Join-Path $root "scripts/ci/prepare_staging.py") --runtime-root $runtime }
    } else {
        if ($Reset) { & python (Join-Path $root "scripts/ci/prepare_staging.py") --runtime-root $runtime --reset }
        else { & python (Join-Path $root "scripts/ci/prepare_staging.py") --runtime-root $runtime }
    }
    if ($LASTEXITCODE -ne 0) {
        throw "pre-main runtime preparation failed with exit code $LASTEXITCODE"
    }
}

if ($Down) {
    Invoke-Compose down --remove-orphans
    exit 0
}

if ($Logs) {
    Invoke-Compose logs --no-color --tail=200
    exit 0
}

$stateFile = Join-Path $runtime "data/quiz-copy-episodes.json"
if ($Reset -or -not (Test-Path $stateFile)) {
    Invoke-PrepareRuntime
}

Invoke-Compose config --quiet
Invoke-Compose up -d --build dashboard clues-api analytics-api backup-rollback monitor media

Write-Host "pre-main activo: http://127.0.0.1:8878"
Write-Host "media local:    http://127.0.0.1:8088"
Write-Host "para logs:      .\scripts\pre_main.ps1 -Logs"
Write-Host "para detener:   .\scripts\pre_main.ps1 -Down"
