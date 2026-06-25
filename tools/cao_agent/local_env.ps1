$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$ToolRoot = "D:\tools"
$GitRoot = Join-Path $ToolRoot "git"
$GitConfigDir = Join-Path $ToolRoot "gitconfig"
$CacheRoot = Join-Path $ToolRoot "cache"

$requiredPaths = @(
    (Join-Path $GitRoot "cmd\git.exe"),
    (Join-Path $GitRoot "bin\bash.exe"),
    (Join-Path $RepoRoot ".venv\Scripts\python.exe")
)

foreach ($path in $requiredPaths) {
    if (-not (Test-Path -LiteralPath $path)) {
        throw "Missing required local tool: $path"
    }
}

New-Item -ItemType Directory -Force -Path `
    $GitConfigDir, `
    (Join-Path $ToolRoot "home"), `
    (Join-Path $CacheRoot "pip"), `
    (Join-Path $CacheRoot "pytest"), `
    (Join-Path $CacheRoot "npm"), `
    (Join-Path $CacheRoot "uv"), `
    (Join-Path $RepoRoot ".cao_agent_context") `
    | Out-Null

$env:STOCK_BOT_REPO = $RepoRoot
$env:STOCK_BOT_TOOLS = $ToolRoot
$env:GIT_CONFIG_GLOBAL = Join-Path $GitConfigDir ".gitconfig"
$env:HOME = Join-Path $ToolRoot "home"
$env:USERPROFILE = $env:HOME
$env:PIP_CACHE_DIR = Join-Path $CacheRoot "pip"
$env:PYTEST_ADDOPTS = "-o cache_dir=$((Join-Path $CacheRoot "pytest") -replace "\\", "/")"
$env:NPM_CONFIG_CACHE = Join-Path $CacheRoot "npm"
$env:UV_CACHE_DIR = Join-Path $CacheRoot "uv"
$env:STOCK_BOT_AGENT_CONTEXT = Join-Path $RepoRoot ".cao_agent_context"

$prepend = @(
    (Join-Path $GitRoot "cmd"),
    (Join-Path $GitRoot "bin"),
    (Join-Path $GitRoot "usr\bin"),
    (Join-Path $RepoRoot ".venv\Scripts")
) -join ";"

$env:PATH = "$prepend;$env:PATH"

git config --global --add safe.directory ($RepoRoot -replace "\\", "/")
git config --global core.autocrlf false
git -C $RepoRoot config --local --replace-all core.autocrlf false

Write-Host "stock-bot local environment ready"
Write-Host "Repo: $RepoRoot"
Write-Host "Tools: $ToolRoot"
git --version
bash --version | Select-Object -First 1
python --version
