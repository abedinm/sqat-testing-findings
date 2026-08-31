<#
  Watchdog: waits for the Stage 3 matrix to finish, then starts the remaining stages.
  Makes the overnight run self-continuing rather than dependent on being re-invoked.

  "Finished" = the matrix index has 45 data rows, OR no k6 process has been alive for
  three consecutive checks while the index has stopped growing (i.e. the runner died).
  Either way the remaining stages start, because they are independent of the matrix.
#>
param(
    [int]$TimeoutMinutes = 200,
    [int]$PollSeconds = 30
)

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$index = Join-Path $root "results\matrix\index.csv"
$marker = Join-Path $root "data\remaining_started.marker"

if (Test-Path $marker) { Write-Host "remaining stages already started - watchdog exiting"; exit 0 }

$deadline = (Get-Date).AddMinutes($TimeoutMinutes)
$lastCount = -1
$stalled = 0

while ((Get-Date) -lt $deadline) {
    $count = 0
    if (Test-Path $index) { $count = (Import-Csv $index | Measure-Object).Count }

    if ($count -ge 45) {
        Write-Host "matrix complete ($count rows) - starting remaining stages"
        break
    }

    $k6alive = (Get-Process k6 -ErrorAction SilentlyContinue | Measure-Object).Count -gt 0
    if ($count -eq $lastCount -and -not $k6alive) {
        $stalled++
        Write-Host "no progress and no k6 running (strike $stalled/3) at $count rows"
        if ($stalled -ge 3) {
            Write-Host "matrix appears to have stopped at $count/45 rows - continuing anyway"
            break
        }
    } else {
        $stalled = 0
    }
    $lastCount = $count
    Start-Sleep -Seconds $PollSeconds
}

"started $(Get-Date -Format o)" | Set-Content $marker -Encoding utf8
& "$root\scripts\run_remaining.ps1" *>> (Join-Path $root "data\stage4to7.log")
"finished $(Get-Date -Format o)" | Add-Content $marker -Encoding utf8
Write-Host "remaining stages complete"
