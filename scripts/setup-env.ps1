# scripts/setup-env.ps1
# 다른 컴퓨터에서 처음 실행할 때 .env.example → .env 복사
# 실행: .\scripts\setup-env.ps1

$services = @(
    "src/gateway",
    "src/orchestrator",
    "src/policy-engine",
    "src/tool-service",
    "src/rag-service",
    "src/context-service",
    "src/audit-service"
)

foreach ($svc in $services) {
    $example = "$svc/.env.example"
    $target  = "$svc/.env"

    if (-Not (Test-Path $example)) {
        Write-Warning "Not found: $example"
        continue
    }

    if (Test-Path $target) {
        Write-Host "[SKIP] $target already exists" -ForegroundColor Yellow
    } else {
        Copy-Item $example $target
        Write-Host "[OK]   $target created" -ForegroundColor Green
    }
}

# infra/.env
if (-Not (Test-Path "infra/.env")) {
    Copy-Item "infra/.env.example" "infra/.env"
    Write-Host "[OK]   infra/.env created" -ForegroundColor Green
} else {
    Write-Host "[SKIP] infra/.env already exists" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "⚠️  반드시 각 .env 파일에서 다음 값을 실제 값으로 교체하세요:" -ForegroundColor Cyan
Write-Host "  - JWT_SECRET_KEY"
Write-Host "  - SERVICE_SECRET"
Write-Host "  - OPENAI_API_KEY  (gateway, orchestrator)"
Write-Host "  - REDIS_PASSWORD  (infra/.env)"
Write-Host "  - POSTGRES_PASSWORD (infra/.env)"
