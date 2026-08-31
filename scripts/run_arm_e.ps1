<#
  Arm E - coordinated-omission control.

  Re-measures /api/content open-loop (constant-arrival-rate) at three offered rates
  bracketing the closed-loop throughput measured at the knee (~1,174 req/s), so the
  closed-loop percentiles from Stages 3/5/6/7 can be checked against an unbiased model.

  Waits for Phase 1 to finish first: only one load test may run at a time.
#>
param([int]$Port = 8099, [string]$Duration = "120s", [int]$Repeats = 3)

$ErrorActionPreference = "Continue"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$k6 = Join-Path $root "tools\k6-v2.2.0-windows-amd64\k6.exe"
$pidFile = Join-Path $root "data\server.pid"

# --- wait for Phase 1 to release the machine -------------------------------
$deadline = (Get-Date).AddMinutes(150)
while ((Get-Date) -lt $deadline) {
    $phase1Done = (Test-Path (Join-Path $root "data\phase1.log")) -and
                  ((Get-Content (Join-Path $root "data\phase1.log") -Raw) -match "PHASE 1 COMPLETE")
    if ($phase1Done) { break }
    Start-Sleep -Seconds 30
}
Write-Host "phase 1 released the machine at $(Get-Date -Format HH:mm:ss)"

function Restart-Sut([string]$Tag) {
    if (Test-Path $pidFile) {
        $old = [int](Get-Content $pidFile)
        $q = Get-Process -Id $old -ErrorAction SilentlyContinue
        if ($q) { $q | Stop-Process -Force; Start-Sleep -Seconds 2 }
    }
    Remove-Item env:DISABLE_RATE_LIMIT -ErrorAction SilentlyContinue
    $env:PORT = "$Port"
    $p = Start-Process node -ArgumentList "serve.mjs" -WorkingDirectory (Join-Path $root "sut") `
         -RedirectStandardOutput (Join-Path $root "data\server_$Tag.log") `
         -RedirectStandardError (Join-Path $root "data\server_$Tag.err") -NoNewWindow -PassThru
    $p.Id | Set-Content $pidFile
    for ($i = 0; $i -lt 30; $i++) {
        Start-Sleep -Milliseconds 500
        try { if ((Invoke-WebRequest "http://127.0.0.1:$Port/robots.txt" -UseBasicParsing -TimeoutSec 5).StatusCode -eq 200) { return $p } } catch { }
    }
    return $null
}

New-Item -ItemType Directory -Path "results/open" -Force | Out-Null
$index = "results/open/index.csv"
if (-not (Test-Path $index)) {
    "target_rate,run,is_warmup,requests,achieved_rps,dropped_iterations,failed_rate,mean_ms,p50_ms,p95_ms,p99_ms,max_ms,status" |
        Set-Content $index -Encoding utf8
}

Write-Host ""; Write-Host "===== ARM E : OPEN-LOOP CONTROL (/api/content) ====="
$p = Restart-Sut "arme"
if (-not $p) { Write-Host "server would not start - aborting Arm E" -ForegroundColor Red; exit 1 }

foreach ($rate in @(600, 1100, 1400)) {
    for ($run = 1; $run -le $Repeats; $run++) {
        $cell = "results/open/rate${rate}_run$run"
        New-Item -ItemType Directory -Path $cell -Force | Out-Null
        $summary = "$cell/summary.json"
        if (Test-Path $summary) { continue }
        Start-Sleep -Seconds 3
        $env:BASE = "http://127.0.0.1:$Port"; $env:ROUTE = "/api/content"
        $env:RATE = "$rate"; $env:DURATION = $Duration
        $env:SUMMARY = $summary; $env:LABEL = "open_rate${rate}_run$run"
        & $k6 run --no-color --quiet "$root\scripts\open_load.js" *> "$cell/k6.log"
        if (-not (Test-Path $summary)) {
            Write-Host "  FAILED rate=$rate run=$run" -ForegroundColor Red
            "$rate,$run,,,,,,,,,,,K6_FAILED" | Add-Content $index -Encoding utf8
            continue
        }
        $s = Get-Content $summary -Raw | ConvertFrom-Json
        $warm = if ($run -eq 1) { "true" } else { "false" }
        "$rate,$run,$warm,$($s.requests),$([math]::Round($s.rps,2)),$($s.dropped_iterations)," +
        "$([math]::Round($s.failed_rate,6)),$([math]::Round($s.avg,4)),$([math]::Round($s.p50,4))," +
        "$([math]::Round($s.p95,4)),$([math]::Round($s.p99,4)),$([math]::Round($s.max,4)),OK" |
            Add-Content $index -Encoding utf8
        Write-Host ("  rate={0,5}/s run{1} achieved={2,6:N0} dropped={3,7} mean={4,8:N3} p95={5,8:N3} p99={6,8:N3}" -f `
            $rate, $run, $s.rps, $s.dropped_iterations, $s.avg, $s.p95, $s.p99)
    }
}
Write-Host "===== ARM E COMPLETE ====="
"done $(Get-Date -Format o)" | Set-Content (Join-Path $root "data\arm_e.marker") -Encoding utf8
