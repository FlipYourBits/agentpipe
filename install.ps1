param(
    [string]$Branch = "main",
    [string]$Dir = ".",
    [switch]$Help
)

$ErrorActionPreference = "Stop"
$Repo = "https://github.com/FlipYourBits/codemonkeys.git"

if ($Help) {
    Write-Host "Usage: .\install.ps1 [-Branch <branch>] [-Dir <project-dir>]"
    Write-Host ""
    Write-Host "Install codemonkeys skills and agents into a project's .claude/ directory."
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Branch <branch>   Git branch to install from (default: main)"
    Write-Host "  -Dir <path>        Target project directory (default: current directory)"
    Write-Host "  -Help              Show this help message"
    exit 0
}

$TargetDir = (Resolve-Path $Dir).Path

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Error "git is required but not installed."
    exit 1
}

$Tmp = Join-Path ([System.IO.Path]::GetTempPath()) ("codemonkeys-" + [guid]::NewGuid().ToString("N").Substring(0, 8))

try {
    Write-Host "Fetching codemonkeys ($Branch)..."
    git clone --depth 1 --branch $Branch $Repo $Tmp 2>$null
    if ($LASTEXITCODE -ne 0) { throw "git clone failed" }

    $Src = Join-Path $Tmp ".claude"
    $Dest = Join-Path $TargetDir ".claude"

    foreach ($Sub in @("agents", "skills", "shared")) {
        $SubPath = Join-Path $Dest $Sub
        if (-not (Test-Path $SubPath)) { New-Item -ItemType Directory -Path $SubPath -Force | Out-Null }
    }

    Write-Host "Installing agents..."
    foreach ($Agent in @("codemonkeys-code-reviewer", "codemonkeys-code-editor", "codemonkeys-researcher", "codemonkeys-test-reviewer")) {
        $AgentSrc = Join-Path $Src "agents/$Agent"
        $AgentDest = Join-Path $Dest "agents/$Agent"
        if (Test-Path $AgentDest) { Remove-Item -Recurse -Force $AgentDest }
        Copy-Item -Recurse -Force $AgentSrc $AgentDest
    }

    Write-Host "Installing skills..."
    foreach ($Skill in @("codemonkeys-bugfix", "codemonkeys-code-review", "codemonkeys-feature", "codemonkeys-research", "codemonkeys-smart-commit", "codemonkeys-test-quality", "codemonkeys-visualize")) {
        $SkillSrc = Join-Path $Src "skills/$Skill"
        $SkillDest = Join-Path $Dest "skills/$Skill"
        if (Test-Path $SkillDest) { Remove-Item -Recurse -Force $SkillDest }
        Copy-Item -Recurse -Force $SkillSrc $SkillDest
    }

    Write-Host "Installing shared guidelines..."
    Get-ChildItem -Path (Join-Path $Src "shared") -Filter "*.md" | ForEach-Object {
        Copy-Item -Force $_.FullName (Join-Path $Dest "shared" $_.Name)
    }

    Write-Host ""
    Write-Host "Done. Installed to $Dest/"
    Write-Host ""
    Write-Host "Available skills:"
    Write-Host "  /codemonkeys-code-review"
    Write-Host "  /codemonkeys-bugfix"
    Write-Host "  /codemonkeys-feature"
    Write-Host "  /codemonkeys-research"
    Write-Host "  /codemonkeys-visualize"
    Write-Host "  /codemonkeys-test-quality"
    Write-Host "  /codemonkeys-smart-commit"
}
finally {
    if (Test-Path $Tmp) { Remove-Item -Recurse -Force $Tmp }
}
