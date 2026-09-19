param([int]$Port = 8010)
$ErrorActionPreference = 'Stop'
$projectDir = $PSScriptRoot
$backendDir = Join-Path $projectDir 'backend'
$pythonExe = Join-Path $backendDir '.venv/Scripts/python.exe'
$webDir = Join-Path $projectDir 'build/web'
if (!(Test-Path (Join-Path $webDir 'index.html'))) {
  throw 'Chưa có build/web. Hãy build Flutter web trước khi chạy.'
}
if (!(Test-Path $pythonExe)) {
  python -m venv (Join-Path $backendDir '.venv')
  if ($LASTEXITCODE -ne 0) { throw 'Không tạo được môi trường Python.' }
}
& $pythonExe -c 'import fastapi,uvicorn,httpx,dotenv,PIL'
if ($LASTEXITCODE -ne 0) {
  & $pythonExe -m pip install -r (Join-Path $backendDir 'requirements.txt')
  if ($LASTEXITCODE -ne 0) { throw 'Không cài được thư viện backend.' }
}
$baseUrl = "http://127.0.0.1:$Port"
$active = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if (!$active) {
  $env:WEB_APP_DIR = $webDir
  $env:DATABASE_PATH = Join-Path $backendDir 'hanzi_go.db'
  Start-Process -FilePath $pythonExe -ArgumentList '-m','uvicorn','main:app','--host','127.0.0.1','--port',"$Port" -WorkingDirectory $backendDir -WindowStyle Hidden -RedirectStandardOutput (Join-Path $backendDir 'server.log') -RedirectStandardError (Join-Path $backendDir 'server-error.log') | Out-Null
}
$ready = $false
for ($attempt = 0; $attempt -lt 30; $attempt++) {
  try {
    $health = Invoke-RestMethod "$baseUrl/api/health" -TimeoutSec 2
    if ($health.product -eq 'HanziGo') { $ready = $true; break }
  } catch {}
  Start-Sleep -Milliseconds 500
}
if (!$ready) { throw 'Server chưa sẵn sàng. Xem backend/server-error.log.' }
Write-Host "HanziGo đang chạy: $baseUrl"
Start-Process "$baseUrl/update-app"
