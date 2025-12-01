# Description: Comprehensive test for PowerShell script features: Flags, Colors, Input.
# Flags: dev, test, prod, input, error

param(
    [string[]]$Args
)

Write-Host "Starting PowerShell Features Test..."
Write-Host "Arguments: $Args"

# --- Flags Test ---
if ($Args -contains "dev") {
    Write-Host "[INFO] Running in DEV mode" -ForegroundColor Cyan
}
if ($Args -contains "test") {
    Write-Host "[INFO] Running in TEST mode" -ForegroundColor Cyan
}
if ($Args -contains "prod") {
    Write-Host "[INFO] Running in PROD mode" -ForegroundColor Cyan
}

# --- Colors Test ---
Write-Host "[INFO] This is an info message (Cyan)" -ForegroundColor Cyan
Write-Host "[WARNING] This is a warning message (Yellow)" -ForegroundColor Yellow
Write-Host "[ERROR] This is an error message (Red)" -ForegroundColor Red
Write-Host "This is a normal message."

# --- Stderr Test ---
if ($Args -contains "error") {
    [Console]::Error.WriteLine("Testing stderr output...")
    [Console]::Error.WriteLine("This is written to stderr.")
}

# --- Input Test ---
if ($Args -contains "input") {
    $userInput = Read-Host "Input requested. Please enter something"
    Write-Host "You entered: $userInput"
}
else {
    Write-Host "No input flag detected, skipping input test."
}

Write-Host "PowerShell Features Test Complete."
