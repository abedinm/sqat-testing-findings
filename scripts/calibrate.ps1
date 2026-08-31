<#
  Stage 2 - calibration sweep.

  Runs short constant-VU loads at increasing concurrency and records p50/p95/p99,
  throughput, error rate, and - critically - how much CPU the Node process actually
  consumed during each run.

  The CPU measurement is what separates a real server knee from load-generator
  contention (threat T1). Node is single-threaded, so "cores used" approaching 1.0 means
  the SUT is genuinely saturated. If p99 climbs while cores_used is well below 1.0, the
  bottleneck is not the server.
#>
param(
    [string]$Route = "/services.html",
    [string]$Duration = "20s",
    [int[]]$Levels = @(1, 2, 4, 8, 16, 32, 64, 100, 150, 200),
    [string]$OutCsv = "results/calibration/sweep.csv",
    [int]$Port = 8099
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$k6 = Join-Path $root "tools\k6-v2.2.0-windows-amd64\k6.exe"
$pid_ = [int](Get-Content (Join-Path $root "data\server.pid"))

New-Item -ItemType Directory -Path (Split-Path $OutCsv) -Force | Out-Null
"vus,requests,rps,failed_rate,p50_ms,avg_ms,p90_ms,p95_ms,p99_ms,max_ms,node_cpu_s,wall_s,cores_used" |
    Set-Content $OutCsv -Encoding utf8

Write-Host ""
Write-Host "CALIBRATION SWEEP  route=$Route  duration=$Duration  server pid=$pid_"
Write-Host ("-" * 108)

foreach ($vus in $Levels) {
    $dir = "results/calibration/vus$vus"
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
    $summary = "$dir/summary.json"

    # settle so the previous run's queue drains and the event loop is idle
    Start-Sleep -Seconds 3

    $proc = Get-Process -Id $pid_ -ErrorAction SilentlyContinue
    if (-not $proc) { Write-Host "SERVER GONE before VUS=$vus - aborting sweep" -ForegroundColor Red; break }
    $cpuBefore = $proc.TotalProcessorTime.TotalSeconds
    $sw = [System.Diagnostics.Stopwatch]::StartNew()

    $env:BASE = "http://127.0.0.1:$Port"
    $env:ROUTE = $Route
    $env:VUS = "$vus"
    $env:DURATION = $Duration
    $env:SUMMARY = $summary
    $env:LABEL = "calib_vus$vus"
    & $k6 run --no-color --quiet $root\scripts\const_load.js 2>&1 | Where-Object { $_ -match "VUS=" } | ForEach-Object { Write-Host $_ }

    $sw.Stop()
    $proc = Get-Process -Id $pid_ -ErrorAction SilentlyContinue
    if (-not $proc) {
        Write-Host "  SERVER DIED during VUS=$vus" -ForegroundColor Red
        "$vus,,,,,,,,,,,$($sw.Elapsed.TotalSeconds),SERVER_DIED" | Add-Content $OutCsv -Encoding utf8
        break
    }
    $cpuAfter = $proc.TotalProcessorTime.TotalSeconds
    $cpuUsed = [math]::Round($cpuAfter - $cpuBefore, 3)
    $wall = [math]::Round($sw.Elapsed.TotalSeconds, 3)
    $cores = if ($wall -gt 0) { [math]::Round($cpuUsed / $wall, 4) } else { 0 }

    if (-not (Test-Path $summary)) {
        Write-Host "  NO SUMMARY for VUS=$vus - run failed" -ForegroundColor Red
        "$vus,,,,,,,,,,$cpuUsed,$wall,$cores" | Add-Content $OutCsv -Encoding utf8
        continue
    }
    $s = Get-Content $summary -Raw | ConvertFrom-Json
    $row = "$vus,$($s.requests),$([math]::Round($s.rps,2)),$([math]::Round($s.failed_rate,6))," +
           "$([math]::Round($s.p50,4)),$([math]::Round($s.avg,4)),$([math]::Round($s.p90,4))," +
           "$([math]::Round($s.p95,4)),$([math]::Round($s.p99,4)),$([math]::Round($s.max,4))," +
           "$cpuUsed,$wall,$cores"
    $row | Add-Content $OutCsv -Encoding utf8
    Write-Host ("        node cpu {0,7:N2}s over {1,6:N1}s wall  ->  cores_used {2,6:N3}" -f $cpuUsed, $wall, $cores)

    if ($s.failed_rate -gt 0.05) {
        Write-Host "  error rate above 5% at VUS=$vus - stopping sweep" -ForegroundColor Yellow
        break
    }
}

Write-Host ("-" * 108)
Write-Host "sweep written to $OutCsv"
