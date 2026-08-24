<#
Run-develop-backend.ps1

Generated from: ai-specs/.commands/develop-backend.md

This script is a safe, interactive helper that performs the common steps
for implementing a backend ticket. It does NOT auto-commit or push without
explicit confirmation. Review the script before running and run with
`-WhatIf` or `-DryRun` to preview actions.
#>

param(
    [string]$Ticket,
    [switch]$DryRun
)

function Run-Cmd([string]$cmd) {
    if ($DryRun) { Write-Host "[dry-run] $cmd"; return }
    Write-Host "--> $cmd"
    iex $cmd
}

if (-not $Ticket) {
    $Ticket = Read-Host 'Enter ticket ID (e.g. SCRUM-1)'
}

if (-not $Ticket) { Write-Error 'Ticket ID is required'; exit 1 }

$branch = "feature/$Ticket"

Write-Host "Preparing to work on ticket: $Ticket" -ForegroundColor Cyan
Write-Host "Branch to create: $branch"

if ($DryRun) { Write-Host "Running in dry-run mode. No changes will be made." -ForegroundColor Yellow }

# 1. Create branch
Run-Cmd "git checkout -b $branch"

# 2. Run tests and build
Run-Cmd ".\gradlew.bat test"
Run-Cmd ".\gradlew.bat check"

# 3. Lint/type checks (if you have custom tasks, add them)
Run-Cmd ".\gradlew.bat checkstyleMain -q"  # optional - may fail if plugin absent

# 4. Show git status and interactively stage only relevant changes
Write-Host "\nGit status:"; Run-Cmd "git status --porcelain"

Write-Host "\nStage changes for commit. Use interactive staging to select only affected files.\n" -ForegroundColor Cyan
if (-not $DryRun) {
    Write-Host "Running: git add -p" -ForegroundColor Green
    & git add -p
} else {
    Write-Host "[dry-run] git add -p" -ForegroundColor Yellow
}

# 5. Commit
$suggest = "feat($Ticket): "
$msg = Read-Host "Commit message (suggested prefix: $suggest)"
if (-not $msg) { $msg = "$suggest implement backend changes" }

if ($DryRun) {
    Write-Host "[dry-run] git commit -m '$msg'"
} else {
    Run-Cmd "git commit -m '$msg'"
}

# 6. Push and create PR
if ($DryRun) {
    Write-Host "[dry-run] git push -u origin $branch"
} else {
    Run-Cmd "git push -u origin $branch"
}

if (Get-Command gh -ErrorAction SilentlyContinue) {
    $create = Read-Host 'Create a PR now using gh? (y/N)'
    if ($create -eq 'y' -or $create -eq 'Y') {
        if ($DryRun) { Write-Host "[dry-run] gh pr create --fill --title 'Implement $Ticket' --body 'Implements ticket $Ticket'" }
        else { Run-Cmd "gh pr create --fill --title 'Implement $Ticket' --body 'Implements ticket $Ticket'" }
    } else { Write-Host 'Skipped PR creation' }
} else {
    Write-Host "gh CLI not found. Create a PR with your Git provider or install gh." -ForegroundColor Yellow
}

Write-Host "Done. Review changes and update ticket references as needed." -ForegroundColor Green
