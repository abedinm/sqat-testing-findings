<#
  Stages 4, 5, 7 and 6 in sequence, unattended.

  Order is deliberate and differs from the brief's numbering: the soak (Stage 5) runs
  BEFORE the scaled-dataset arm (Stage 6) because the soak produces a headline
  deliverable (the degradation ratio) and the scaled arm is the one that can be trimmed
  if time runs out. Rationale recorded in docs/decision_log.md.

  Every stage restarts the server first, so each begins from a cold event loop, empty
  rate-limit state and a fresh heap.
#>
param(
    [int]$Port = 8099,
    [int]$KneeVus = 8,
    [switch]$SkipStress,
    [switch]$SkipSoak,
    [switch]$SkipArmB,
    [switch]$SkipScaled,
    [int]$SoakSeconds = 3600,
    [int[]]$Scales = @(1, 10, 100, 1000)
)

$ErrorActionPreference = "Continue"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$k6 = Join-Path $root "tools\k6-v2.2.0-windows-amd64\k6.exe"
$sut = Join-Path $root "sut"
$pidFile = Join-Path $root "data\server.pid"

function Stop-Sut {
    if (Test-Path $pidFile) {
        $old = [int](Get-Content $pidFile)
        $p = Get-Process -Id $old -ErrorAction SilentlyContinue
        if ($p) { $p | Stop-Process -Force; Start-Sleep -Seconds 2 }
    }
}

function Start-Sut([hashtable]$ExtraEnv = @{}, [string]$LogTag = "run") {
    Stop-Sut
    foreach ($k in @("DISABLE_RATE_LIMIT")) { Remove-Item "env:$k" -ErrorAction SilentlyContinue }
    $env:PORT = "$Port"
    foreach ($k in $ExtraEnv.Keys) { Set-Item -Path "env:$k" -Value $ExtraEnv[$k] }
    $out = Join-Path $root "data\server_$LogTag.log"
    $err = Join-Path $root "data\server_$LogTag.err"
    $p = Start-Process -FilePath "node" -ArgumentList "serve.mjs" -WorkingDirectory $sut `
         -RedirectStandardOutput $out -RedirectStandardError $err -NoNewWindow -PassThru
    $p.Id | Set-Content $pidFile
    # health gate - never proceed against a server that is not serving
    $ok = $false
    for ($i = 0; $i -lt 30; $i++) {
        Start-Sleep -Milliseconds 500
        try {
            $r = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/robots.txt" -UseBasicParsing -TimeoutSec 5
            if ($r.StatusCode -eq 200) { $ok = $true; break }
        } catch { }
    }
    if (-not $ok) { Write-Host "  SERVER FAILED HEALTH CHECK ($LogTag)" -ForegroundColor Red; return $null }
    Write-Host "  server up (pid $($p.Id)) $LogTag"
    return $p
}

function Sample-Proc([int]$procId, [string]$csv, [int]$seconds, [int]$every = 10) {
    "elapsed_s,rss_mb,cpu_s,handles,threads" | Set-Content $csv -Encoding utf8
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    while ($sw.Elapsed.TotalSeconds -lt $seconds) {
        $p = Get-Process -Id $procId -ErrorAction SilentlyContinue
        if (-not $p) { "$([math]::Round($sw.Elapsed.TotalSeconds,1)),,,,PROCESS_GONE" | Add-Content $csv; break }
        "$([math]::Round($sw.Elapsed.TotalSeconds,1)),$([math]::Round($p.WorkingSet64/1MB,2)),$([math]::Round($p.TotalProcessorTime.TotalSeconds,2)),$($p.HandleCount),$($p.Threads.Count)" |
            Add-Content $csv -Encoding utf8
        Start-Sleep -Seconds $every
    }
}

# ============================================================ STAGE 4 - STRESS
if (-not $SkipStress) {
    Write-Host ""; Write-Host "===== STAGE 4 : STRESS ====="
    $dir = "results/stress"; New-Item -ItemType Directory -Path $dir -Force | Out-Null
    $p = Start-Sut @{} "stress"
    if ($p) {
        $rssBefore = (Get-Process -Id $p.Id).WorkingSet64 / 1MB
        $job = Start-Job -ScriptBlock {
            param($procId, $csv, $secs)
            "elapsed_s,rss_mb,cpu_s,handles,threads" | Set-Content $csv -Encoding utf8
            $sw = [System.Diagnostics.Stopwatch]::StartNew()
            while ($sw.Elapsed.TotalSeconds -lt $secs) {
                $q = Get-Process -Id $procId -ErrorAction SilentlyContinue
                if (-not $q) { "$([math]::Round($sw.Elapsed.TotalSeconds,1)),,,,PROCESS_GONE" | Add-Content $csv; break }
                "$([math]::Round($sw.Elapsed.TotalSeconds,1)),$([math]::Round($q.WorkingSet64/1MB,2)),$([math]::Round($q.TotalProcessorTime.TotalSeconds,2)),$($q.HandleCount),$($q.Threads.Count)" | Add-Content $csv
                Start-Sleep -Seconds 2
            }
        } -ArgumentList $p.Id, (Join-Path $root "$dir\server_proc.csv"), 260

        $env:BASE = "http://127.0.0.1:$Port"; $env:ROUTE = "/services.html"
        $env:SUMMARY = "$dir/summary.json"; $env:LABEL = "stress"
        & $k6 run --no-color "$root\scripts\stress.js" *> "$dir/k6.log"
        $k6exit = $LASTEXITCODE
        Write-Host "  k6 exit: $k6exit"
        Wait-Job $job -Timeout 30 | Out-Null; Remove-Job $job -Force -ErrorAction SilentlyContinue

        $alive = $null -ne (Get-Process -Id $p.Id -ErrorAction SilentlyContinue)
        $rssAfter = if ($alive) { (Get-Process -Id $p.Id).WorkingSet64 / 1MB } else { $null }
        @{ server_survived = $alive; rss_before_mb = [math]::Round($rssBefore,2)
           rss_after_mb = if ($rssAfter) { [math]::Round($rssAfter,2) } else { $null }
           k6_exit = $k6exit } | ConvertTo-Json | Set-Content "$dir/server_state.json" -Encoding utf8
        Write-Host "  server survived: $alive"
    }
}

# ============================================================== STAGE 5 - SOAK
if (-not $SkipSoak) {
    Write-Host ""; Write-Host "===== STAGE 5 : SOAK ($SoakSeconds s at $KneeVus VUs) ====="
    $dir = "results/soak"; New-Item -ItemType Directory -Path $dir -Force | Out-Null
    $p = Start-Sut @{} "soak"
    if ($p) {
        $job = Start-Job -ScriptBlock {
            param($procId, $csv, $secs)
            "elapsed_s,rss_mb,cpu_s,handles,threads" | Set-Content $csv -Encoding utf8
            $sw = [System.Diagnostics.Stopwatch]::StartNew()
            while ($sw.Elapsed.TotalSeconds -lt $secs) {
                $q = Get-Process -Id $procId -ErrorAction SilentlyContinue
                if (-not $q) { "$([math]::Round($sw.Elapsed.TotalSeconds,1)),,,,PROCESS_GONE" | Add-Content $csv; break }
                "$([math]::Round($sw.Elapsed.TotalSeconds,1)),$([math]::Round($q.WorkingSet64/1MB,2)),$([math]::Round($q.TotalProcessorTime.TotalSeconds,2)),$($q.HandleCount),$($q.Threads.Count)" | Add-Content $csv
                Start-Sleep -Seconds 10
            }
        } -ArgumentList $p.Id, (Join-Path $root "$dir\server_proc.csv"), ($SoakSeconds + 30)

        $env:BASE = "http://127.0.0.1:$Port"; $env:ROUTE = "/api/content"
        $env:VUS = "$KneeVus"; $env:DURATION = "${SoakSeconds}s"
        $env:SUMMARY = "$dir/summary.json"; $env:LABEL = "soak"
        & $k6 run --no-color --quiet --out "json=$dir/raw.json.gz" "$root\scripts\const_load.js" *> "$dir/k6.log"
        Write-Host "  k6 exit: $LASTEXITCODE"
        Wait-Job $job -Timeout 60 | Out-Null; Remove-Job $job -Force -ErrorAction SilentlyContinue
        if (Test-Path "$dir/raw.json.gz") {
            Write-Host "  raw.json.gz $([math]::Round((Get-Item "$dir/raw.json.gz").Length/1MB,1)) MB"
        }
    }
}

# ========================================================= STAGE 7 - ARM B
if (-not $SkipArmB) {
    Write-Host ""; Write-Host "===== STAGE 7 : ARM B (rate limiter) ====="
    foreach ($mode in @("disabled", "enabled")) {
        $dir = "results/armb/$mode"; New-Item -ItemType Directory -Path $dir -Force | Out-Null
        $extra = @{}
        if ($mode -eq "disabled") { $extra = @{ DISABLE_RATE_LIMIT = "true" } }
        $p = Start-Sut $extra "armb_$mode"
        if (-not $p) { continue }
        for ($run = 1; $run -le 3; $run++) {
            $summary = "$dir/run$run.json"
            $env:BASE = "http://127.0.0.1:$Port"; $env:ROUTE = "/api/search?q=delta"
            $env:VUS = "$KneeVus"; $env:DURATION = "120s"
            $env:SUMMARY = $summary; $env:LABEL = "armb_${mode}_run$run"
            Start-Sleep -Seconds 3
            & $k6 run --no-color --quiet "$root\scripts\const_load.js" *> "$dir/k6_run$run.log"
            if (Test-Path $summary) {
                $s = Get-Content $summary -Raw | ConvertFrom-Json
                Write-Host ("  [{0}] run{1}  rps={2,6:N0}  mean={3,8:N3}  p50={4,8:N3}  p99={5,8:N3}  fail={6:P2}" -f `
                    $mode, $run, $s.rps, $s.avg, $s.p50, $s.p99, $s.failed_rate)
            } else { Write-Host "  [$mode] run$run FAILED" -ForegroundColor Red }
        }
    }
}

# ================================================= STAGE 6 - SCALED DATASET ARM
if (-not $SkipScaled) {
    Write-Host ""; Write-Host "===== STAGE 6 : SCALED DATASET ARM ====="
    $dataDir = Join-Path $sut "data"
    $base = Join-Path $dataDir "content.json.base"
    if (-not (Test-Path $base)) { Copy-Item (Join-Path $dataDir "content.json") $base -Force }

    foreach ($scale in $Scales) {
        Write-Host "  -- scale x$scale --"
        $gen = Join-Path $dataDir "content.scaled$scale.json"
        if (-not (Test-Path $gen)) {
            & python "$root\scripts\scale_dataset.py" --factor $scale --src $base --out "sut/data/content.scaled$scale.json" 2>&1 |
                Select-Object -Last 3 | ForEach-Object { Write-Host "    $_" }
        }
        if (-not (Test-Path $gen)) { Write-Host "    GENERATION FAILED - skipping scale x$scale" -ForegroundColor Red; continue }
        Copy-Item $gen (Join-Path $dataDir "content.json") -Force
        $p = Start-Sut @{} "scaled_x$scale"
        if (-not $p) { Write-Host "    server would not start at x$scale - skipping" -ForegroundColor Red; continue }

        & "$root\scripts\run_matrix.ps1" -Levels $KneeVus -Routes "/api/content","/services.html" `
            -Repeats 3 -Duration "120s" -OutRoot "results/scaled" -Tag "x$scale" -Port $Port
    }
    # restore the baseline dataset
    Copy-Item $base (Join-Path $dataDir "content.json") -Force
    Write-Host "  baseline content.json restored"
}

Write-Host ""
Write-Host "===== run_remaining.ps1 COMPLETE ====="
