# Description: Long running PowerShell script for stress testing and abort verification.
# Flags: stress

param(
    [string[]]$Args
)

Write-Host "Starting PowerShell Long Running Test..."

function Get-RandomString {
    param([int]$Length)
    $chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "
    $random = New-Object System.Random
    $result = new-object char[] $Length
    for ($i = 0; $i -lt $Length; $i++) {
        $result[$i] = $chars[$random.Next($chars.Length)]
    }
    return -join $result
}

if ($Args -contains "stress") {
    Write-Host "Running in STRESS mode..."
    $startTime = Get-Date
    
    $logLevels = @("INFO", "WARNING", "ERROR", "CRITICAL", "DEBUG")
    # Simple weighted random selection simulation
    
    for ($i = 1; $i -le 10000; $i++) {
        $rand = Get-Random -Minimum 0 -Maximum 100
        if ($rand -lt 70) { $level = "INFO"; $color = "White" }
        elseif ($rand -lt 85) { $level = "WARNING"; $color = "Yellow" }
        elseif ($rand -lt 95) { $level = "ERROR"; $color = "Red" }
        elseif ($rand -lt 97) { $level = "CRITICAL"; $color = "Red" }
        else { $level = "DEBUG"; $color = "Gray" }

        if ((Get-Random -Minimum 0 -Maximum 100) -lt 5) {
            $length = Get-Random -Minimum 1000 -Maximum 5000
            $msgType = "LONG_MSG"
        }
        else {
            $length = Get-Random -Minimum 20 -Maximum 100
            $msgType = "MSG"
        }

        $message = Get-RandomString -Length $length
        $logLine = "[$level] Line $i ($msgType): $message"

        if ($level -in @("ERROR", "CRITICAL") -and (Get-Random -Minimum 0 -Maximum 2) -eq 0) {
            # Write to stderr equivalent
            [Console]::Error.WriteLine($logLine)
        }
        else {
            Write-Host $logLine -ForegroundColor $color
        }

        if ($i % 1000 -eq 0) {
            Start-Sleep -Milliseconds 10
        }
    }

    $endTime = Get-Date
    $duration = ($endTime - $startTime).TotalSeconds
    Write-Host "Stress test completed in $duration seconds."

}
else {
    Write-Host "Running in NORMAL mode (use 'stress' flag for stress test)..."
    for ($i = 1; $i -le 100; $i++) {
        Write-Host "Processing item $i/100 - Simulating work..."
        Start-Sleep -Milliseconds 500
    }
}

Write-Host "Long Running Test Finished."
