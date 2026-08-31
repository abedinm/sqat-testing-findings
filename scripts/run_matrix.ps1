<#
  Generic matrix runner: levels x routes x repeats, constant-VU runs.
  Used for Stage 3 (Arm A) and Stage 6 (scaled dataset arm).

  Records per-run summaries plus Node CPU consumption. Run 1 of each cell is kept on disk
  but flagged as a warm-up to be discarded at analysis time - discarding at analysis
  rather than at capture keeps the evidence.
#>
param(
    [int[]]$Levels = @(2, 8, 16),
    [string[]]$Routes = @("/services.html", "/api/content", "/sitemap.xml"),
    [int]$Repeats = 5,
    [string]$Duration = "180s",
    [string]$OutRoot = "results/matrix",
    [string]$Tag = "arma",
    [int]$Port = 8099
)

$ErrorActionPreference = "Continue"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$k6 = Join-Path $root "tools\k6-v2.2.0-windows-amd64\k6.exe"
$pidFile = Join-Path $root "data\server.pid"
$pid_ = [int](Get-Content $pidFile)

New-Item -ItemType Directory -Path $OutRoot -Force | Out-Null
$index = Join-Path $OutRoot "index.csv"
if (-not (Test-Path $index)) {
    "tag,route,vus,run,is_warmup,requests,rps,failed_rate,p50_ms,avg_ms,p90_ms,p95_ms,p99_ms,max_ms,node_cpu_s,wall_s,cores_used,status" |
        Set-Content $index -Encoding utf8
}

$total = $Levels.Count * $Routes.Count * $Repeats
$done = 0
$startedAt = Get-Date
Write-Host "MATRIX  tag=$Tag  levels=$($Levels -join ',')  routes=$($Routes -join ',')  repeats=$Repeats  duration=$Duration"
Write-Host "  total runs: $total"

foreach ($vus in $Levels) {
  foreach ($route in $Routes) {
    $slug = ($route -replace "[/\.\?=]", "_").Trim("_")
    for ($run = 1; $run -le $Repeats; $run++) {
      $done++
      $cell = "$OutRoot/${Tag}_${slug}_vus${vus}_run${run}"
      New-Item -ItemType Directory -Path $cell -Force | Out-Null
      $summary = "$cell/summary.json"

      if (Test-Path $summary) {
        Write-Host "  [$done/$total] SKIP (exists) $Tag $route vus=$vus run=$run"
        continue
      }

      Start-Sleep -Seconds 3
      $proc = Get-Process -Id $pid_ -ErrorAction SilentlyContinue
      if (-not $proc) {
        Write-Host "  SERVER GONE - aborting matrix" -ForegroundColor Red
        "$Tag,$route,$vus,$run,,,,,,,,,,,,,,SERVER_GONE" | Add-Content $index -Encoding utf8
        return
      }
      $cpuBefore = $proc.TotalProcessorTime.TotalSeconds
      $sw = [System.Diagnostics.Stopwatch]::StartNew()

      $env:BASE = "http://127.0.0.1:$Port"
      $env:ROUTE = $route
      $env:VUS = "$vus"
      $env:DURATION = $Duration
      $env:SUMMARY = $summary
      $env:LABEL = "${Tag}_${slug}_vus${vus}_run${run}"
      & $k6 run --no-color --quiet "$root\scripts\const_load.js" *> "$cell/k6.log"
      $k6exit = $LASTEXITCODE

      $sw.Stop()
      $wall = [math]::Round($sw.Elapsed.TotalSeconds, 3)
      $proc = Get-Process -Id $pid_ -ErrorAction SilentlyContinue
      $cpuUsed = if ($proc) { [math]::Round($proc.TotalProcessorTime.TotalSeconds - $cpuBefore, 3) } else { "" }
      $cores = if ($proc -and $wall -gt 0) { [math]::Round($cpuUsed / $wall, 4) } else { "" }
      $warm = if ($run -eq 1) { "true" } else { "false" }

      if (-not (Test-Path $summary)) {
        Write-Host "  [$done/$total] FAILED (no summary, k6 exit $k6exit) $route vus=$vus run=$run" -ForegroundColor Red
        "$Tag,$route,$vus,$run,$warm,,,,,,,,,,$cpuUsed,$wall,$cores,K6_FAILED_EXIT_$k6exit" | Add-Content $index -Encoding utf8
        continue
      }
      $s = Get-Content $summary -Raw | ConvertFrom-Json
      "$Tag,$route,$vus,$run,$warm,$($s.requests),$([math]::Round($s.rps,2)),$([math]::Round($s.failed_rate,6))," +
      "$([math]::Round($s.p50,4)),$([math]::Round($s.avg,4)),$([math]::Round($s.p90,4)),$([math]::Round($s.p95,4))," +
      "$([math]::Round($s.p99,4)),$([math]::Round($s.max,4)),$cpuUsed,$wall,$cores,OK" | Add-Content $index -Encoding utf8

      $eta = ""
      if ($done -gt 0) {
        $per = ((Get-Date) - $startedAt).TotalSeconds / $done
        $eta = " eta " + [math]::Round(($total - $done) * $per / 60.0, 1) + "m"
      }
      Write-Host ("  [{0}/{1}] {2,-16} vus={3,-3} run={4} p50={5,7:N2} p95={6,7:N2} p99={7,7:N2} rps={8,6:N0} fail={9:P2}{10}" -f `
        $done, $total, $route, $vus, $run, $s.p50, $s.p95, $s.p99, $s.rps, $s.failed_rate, $eta)
    }
  }
}
Write-Host "MATRIX $Tag COMPLETE - index at $index"
