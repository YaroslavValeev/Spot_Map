# Publish all approximate NEW-* pins to the public map (local/dev).
# Uses MODERATION_TOKEN from services/api/.env — do not commit secrets.

$ErrorActionPreference = "Stop"
$Api = "http://127.0.0.1:18080"
$Token = "local-dev-only-change-me"
$JsonPath = Join-Path $PSScriptRoot "..\..\..\data\imports\SpotMap_Research_Moscow_MO_2026-11-14\promote_targets_approx.json"
$JsonPath = (Resolve-Path $JsonPath).Path

$data = Get-Content -Raw -Encoding UTF8 $JsonPath | ConvertFrom-Json
Write-Host "Promoting $($data.count) candidates with publish=true ..."

$ok = 0
$fail = 0
foreach ($item in $data.items) {
  $body = @{
    latitude      = [double]$item.lat
    longitude     = [double]$item.lng
    evidence_note = "owner publish batch 2026-11-15 from approximate source GPS; legacy=$($item.legacy_row_id)"
    publish       = $true
  } | ConvertTo-Json -Compress

  $url = "$Api/v1/moderation/candidates/$($item.uuid)/promote-geo"
  try {
    $resp = Invoke-RestMethod -Method Post -Uri $url -ContentType "application/json" `
      -Headers @{ "X-SpotMap-Moderation-Token" = $Token } -Body $body
    Write-Host "OK $($item.legacy_row_id) spot=$($resp.spot_id)"
    $ok++
  } catch {
    Write-Host "FAIL $($item.legacy_row_id): $($_.Exception.Message)"
    $fail++
  }
}

Write-Host "Done ok=$ok fail=$fail"
Write-Host "Open map: $Api/"
