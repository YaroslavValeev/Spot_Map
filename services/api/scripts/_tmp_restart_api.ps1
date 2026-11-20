$conns = Get-NetTCPConnection -LocalPort 18080 -ErrorAction SilentlyContinue |
  Select-Object -ExpandProperty OwningProcess -Unique
foreach ($procId in $conns) {
  if ($procId) { Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue }
}
Start-Sleep -Seconds 2
Set-Location "f:\Проекты MyWave\NEW2026\Spot Map\services\api"
Start-Process -NoNewWindow -FilePath python -ArgumentList "-m","uvicorn","app.main:app","--host","127.0.0.1","--port","18080"
Start-Sleep -Seconds 4
try {
  (Invoke-WebRequest -Uri "http://127.0.0.1:18080/health" -UseBasicParsing -TimeoutSec 8).Content
} catch {
  "health_fail $($_.Exception.Message)"
}
