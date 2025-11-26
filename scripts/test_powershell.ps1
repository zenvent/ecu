# Description: A test PowerShell script.
# Flags: Force, Recurse, WhatIf

param(
    [string[]]$Args
)

Write-Host "Starting PowerShell Script..."
Write-Host "Arguments: $Args"

if ($Args -contains "Force") {
    Write-Host "Force enabled" -ForegroundColor Red
}
if ($Args -contains "Recurse") {
    Write-Host "Recursive mode" -ForegroundColor Cyan
}
if ($Args -contains "WhatIf") {
    Write-Host "WhatIf mode - simulating..." -ForegroundColor Yellow
}

Start-Sleep -Seconds 2
Write-Host "Done."
