<#
  Phase 1 - close the two data gaps identified in the overnight report.

  C) Variance-injection arm: same expensive work, different distribution.
  D) Thicken the cells that were too thin to cite (scaled arm, unlimited /api/search).
#>
param([int]$Port = 8099, [int]$Vus = 8, [string]$Duration = "120s")

$ErrorActionPreference = "Continue"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$k6 = Join-Path $root "tools\k6-v2.2.0-windows-amd64\k6.exe"
$pidFile = Join-Path $root "data\server.pid"

function Restart-Sut([hashtable]$ExtraEnv = @{}, [string]$Tag = "p1") {
    if (Test-Path $pidFile) {
        $old = [int](Get-Content $pidFile)
        $q = Get-Process -Id $old -ErrorAction SilentlyContinue
        if ($q) { $q | Stop-Process -Force; Start-Sleep -Seconds 2 }
    }
    Remove-Item env:DISABLE_RATE_LIMIT -ErrorAction SilentlyContinue
    $env:PORT = "$Port"
    foreach ($k in $ExtraEnv.Keys) { Set-Item -Path "env:$k" -Value $ExtraEnv[$k] }
    $p = Start-Process node -ArgumentList "serve.mjs" -WorkingDirectory (Join-Path $root "sut") `
         -RedirectStandardOutput (Join-Path $root "data\server_$Tag.log") `
         -RedirectStandardError (Join-Path $root "data\server_$Tag.err") -NoNewWindow -PassThru
    $p.Id | Set-Content $pidFile
    for ($i = 0; $i -lt 30; $i++) {
        Start-Sleep -Milliseconds 500
        try { if ((Invoke-WebRequest "http://127.0.0.1:$Port/robots.txt" -UseBasicParsing -TimeoutSec 5).StatusCode -eq 200) { return $p } } catch { }
    }
    Write-Host "  SERVER HEALTH CHECK FAILED ($Tag)" -ForegroundColor Red
    return $null
}

# ============================================== ARM C : VARIANCE INJECTION
Write-Host ""; Write-Host "===== ARM C : VARIANCE INJECTION ====="
$mixes = @(
    @{ name = "uniform_cheap";  mix = "1:/robots.txt" },
    @{ name = "uniform_expensive"; mix = "1:/api/content" },
    @{ name = "mix_10pct";      mix = "90:/robots.txt,10:/api/content" },
    @{ name = "mix_1pct";       mix = "99:/robots.txt,1:/api/content" },
    @{ name = "mix_0p1pct";     mix = "999:/robots.txt,1:/api/content" }
)
$index = "results/mixed/index.csv"
New-Item -ItemType Directory -Path "results/mixed" -Force | Out-Null
if (-not (Test-Path $index)) {
    "name,mix,run,is_warmup,requests,rps,failed_rate,mean_ms,p50_ms,p95_ms,p99_ms,max_ms,p99_over_mean,status" |
        Set-Content $index -Encoding utf8
}

$p = Restart-Sut @{} "armc"
if ($p) {
  foreach ($m in $mixes) {
    for ($run = 1; $run -le 4; $run++) {
      $cell = "results/mixed/$($m.name)_run$run"
      New-Item -ItemType Directory -Path $cell -Force | Out-Null
      $summary = "$cell/summary.json"
      if (Test-Path $summary) { continue }
      Start-Sleep -Seconds 3
      $env:BASE = "http://127.0.0.1:$Port"; $env:MIX = $m.mix
      $env:VUS = "$Vus"; $env:DURATION = $Duration
      $env:SUMMARY = $summary; $env:LABEL = "$($m.name)_run$run"
      # capture per-request data once per mix, for the distribution figure
      if ($run -eq 2) {
        & $k6 run --no-color --quiet --out "json=$cell/raw.json.gz" "$root\scripts\mixed_load.js" *> "$cell/k6.log"
      } else {
        & $k6 run --no-color --quiet "$root\scripts\mixed_load.js" *> "$cell/k6.log"
      }
      if (-not (Test-Path $summary)) {
        Write-Host "  FAILED $($m.name) run$run" -ForegroundColor Red
        "$($m.name),$($m.mix),$run,,,,,,,,,,,K6_FAILED" | Add-Content $index -Encoding utf8
        continue
      }
      $s = Get-Content $summary -Raw | ConvertFrom-Json
      $ratio = if ($s.avg) { [math]::Round($s.p99 / $s.avg, 4) } else { "" }
      $warm = if ($run -eq 1) { "true" } else { "false" }
      "$($m.name),$($m.mix),$run,$warm,$($s.requests),$([math]::Round($s.rps,2)),$([math]::Round($s.failed_rate,6))," +
      "$([math]::Round($s.avg,4)),$([math]::Round($s.p50,4)),$([math]::Round($s.p95,4)),$([math]::Round($s.p99,4))," +
      "$([math]::Round($s.max,4)),$ratio,OK" | Add-Content $index -Encoding utf8
      Write-Host ("  {0,-18} run{1} rps={2,6:N0} mean={3,8:N3} p50={4,8:N3} p99={5,8:N3} p99/mean={6,6:N2}" -f `
        $m.name, $run, $s.rps, $s.avg, $s.p50, $s.p99, $ratio)
    }
  }
}

# ================================= ARM D : THICKEN THIN CELLS
Write-Host ""; Write-Host "===== THICKENING THIN CELLS ====="

# D1 - unlimited /api/search, 4 more runs (previous arm had only 2 kept, high variance)
Write-Host "  -- /api/search, limiter disabled --"
$p = Restart-Sut @{ DISABLE_RATE_LIMIT = "true" } "search_extra"
if ($p) {
  New-Item -ItemType Directory -Path "results/armb/disabled" -Force | Out-Null
  for ($run = 4; $run -le 7; $run++) {
    $summary = "results/armb/disabled/run$run.json"
    if (Test-Path $summary) { continue }
    Start-Sleep -Seconds 3
    $env:BASE = "http://127.0.0.1:$Port"; $env:ROUTE = "/api/search?q=delta"
    $env:VUS = "$Vus"; $env:DURATION = $Duration
    $env:SUMMARY = $summary; $env:LABEL = "armb_disabled_run$run"
    & $k6 run --no-color --quiet "$root\scripts\const_load.js" *> "results/armb/disabled/k6_run$run.log"
    if (Test-Path $summary) {
      $s = Get-Content $summary -Raw | ConvertFrom-Json
      Write-Host ("    run{0} rps={1,6:N0} mean={2,8:N3} p99={3,8:N3}" -f $run, $s.rps, $s.avg, $s.p99)
    } else { Write-Host "    run$run FAILED" -ForegroundColor Red }
  }
}

# D2 - scaled arm, 2 more repeats at x1/x10/x100 (x1000 excluded: ~1 rps, prohibitively slow)
Write-Host "  -- scaled arm extra repeats --"
$dataDir = Join-Path $root "sut\data"
$base = Join-Path $dataDir "content.json.base"
foreach ($scale in @(1, 10, 100)) {
    $gen = Join-Path $dataDir "content.scaled$scale.json"
    if (-not (Test-Path $gen)) { Write-Host "    missing scaled x$scale - skipping" -ForegroundColor Yellow; continue }
    Copy-Item $gen (Join-Path $dataDir "content.json") -Force
    $p = Restart-Sut @{} "scaled_extra_x$scale"
    if (-not $p) { continue }
    & "$root\scripts\run_matrix.ps1" -Levels $Vus -Routes "/api/content" -Repeats 3 `
        -Duration $Duration -OutRoot "results/scaled_extra" -Tag "x$scale" -Port $Port
}
Copy-Item $base (Join-Path $dataDir "content.json") -Force
Write-Host "  baseline content.json restored"
Restart-Sut @{} "final" | Out-Null

Write-Host ""; Write-Host "===== PHASE 1 COMPLETE ====="
