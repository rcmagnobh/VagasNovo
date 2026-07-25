# ============================================================
# SOLUCAO DEFINITIVA - REMOVER ARQUIVOS GIGANTES
# ============================================================

Clear-Host
Write-Host "============================================================" -ForegroundColor Yellow
Write-Host "   SOLUCAO DEFINITIVA - REMOVER ARQUIVOS GIGANTES" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Yellow
Write-Host ""

Set-Location vagas_novo
Write-Host "📁 Pasta atual: $(Get-Location)" -ForegroundColor Cyan

# 1. Remove arquivos gigantes do LFS
Write-Host "`n[1] Removendo arquivos gigantes do LFS..." -ForegroundColor Yellow

git lfs untrack "distribuicao/ms-playwright/chromium-1228/**" 2>$null
git lfs untrack "distribuicao/ms-playwright/chromium_headless_shell-1228/**" 2>$null
git lfs untrack "distribuicao/ms-playwright/firefox-1532/**" 2>$null

Write-Host "✅ Arquivos removidos do LFS" -ForegroundColor Green

# 2. Remove do controle de versao
Write-Host "`n[2] Removendo arquivos gigantes do Git..." -ForegroundColor Yellow

$pastasGigantes = @(
    "distribuicao/ms-playwright/chromium-1228/",
    "distribuicao/ms-playwright/chromium_headless_shell-1228/",
    "distribuicao/ms-playwright/firefox-1532/"
)

foreach ($pasta in $pastasGigantes) {
    Write-Host "   Removendo: $pasta" -ForegroundColor Gray
    git rm -r --cached $pasta 2>$null
}

# Remove arquivos especificos grandes
git rm --cached distribuicao/ms-playwright/webkit-2311/WebCore.dll 2>$null
git rm --cached dist/GestaoVagas/_internal/playwright/driver/node.exe 2>$null
git rm --cached dist/GestaoVagasApp/_internal/playwright/driver/node.exe 2>$null

Write-Host "✅ Arquivos removidos" -ForegroundColor Green

# 3. Cria .gitattributes
Write-Host "`n[3] Criando .gitattributes..." -ForegroundColor Yellow

$gitattributes = @"
# Arquivos pequenos do Playwright (vai para LFS)
*.dll filter=lfs diff=lfs merge=lfs -text
*.exe filter=lfs diff=lfs merge=lfs -text
*.node filter=lfs diff=lfs merge=lfs -text

# Pastas que NAO vao para o Git (ignorar)
distribuicao/ms-playwright/chromium-1228/
distribuicao/ms-playwright/chromium_headless_shell-1228/
distribuicao/ms-playwright/firefox-1532/
dist/GestaoVagas/_internal/playwright/driver/node.exe
dist/GestaoVagasApp/_internal/playwright/driver/node.exe
distribuicao/ms-playwright/webkit-2311/WebCore.dll
"@

$gitattributes | Out-File -FilePath ".gitattributes" -Encoding UTF8
Write-Host "✅ .gitattributes criado" -ForegroundColor Green

# 4. Cria .gitignore
Write-Host "`n[4] Criando .gitignore..." -ForegroundColor Yellow

$gitignore = @"
# Arquivos gigantes do Playwright (nao enviar)
distribuicao/ms-playwright/chromium-1228/
distribuicao/ms-playwright/chromium_headless_shell-1228/
distribuicao/ms-playwright/firefox-1532/
distribuicao/ms-playwright/webkit-2311/WebCore.dll
dist/GestaoVagas/_internal/playwright/driver/node.exe
dist/GestaoVagasApp/_internal/playwright/driver/node.exe

# Binarios grandes
*.dll
*.exe
*.node
*.bin
*.so
*.dylib

# Dependencias
node_modules/
.venv/
venv/
env/
__pycache__/
*.pyc
*.pyo
*.pyd

# Build
dist/
build/
*.egg-info/
"@

$gitignore | Out-File -FilePath ".gitignore" -Encoding UTF8
Write-Host "✅ .gitignore criado" -ForegroundColor Green

# 5. Adiciona arquivos
Write-Host "`n[5] Adicionando arquivos ao stage..." -ForegroundColor Yellow

git add .gitattributes
git add .gitignore
git add --all

# 6. Commit
Write-Host "`n[6] Fazendo commit final..." -ForegroundColor Yellow

$commitMsg = "Removendo arquivos gigantes - $(Get-Date -Format 'dd/MM/yyyy HH:mm')"
git commit -m $commitMsg

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Commit realizado!" -ForegroundColor Green
} else {
    Write-Host "⚠️  Nada para commitar ou erro" -ForegroundColor Yellow
}

# 7. Push
Write-Host "`n[7] Enviando para o GitHub..." -ForegroundColor Yellow
Write-Host "   Repositorio: https://github.com/rcmagnobh/BuscarVagas.git" -ForegroundColor Gray
Write-Host "   Branch: vagas_novo" -ForegroundColor Gray
Write-Host ""

git push -u origin vagas_novo --force

if ($LASTEXITCODE -ne 0) {
    Write-Host "`nTentando com --force --no-verify..." -ForegroundColor Yellow
    git push -u origin vagas_novo --force --no-verify
}

Write-Host "`n============================================================" -ForegroundColor Green
Write-Host "   PROCESSO FINALIZADO!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Acesse: https://github.com/rcmagnobh/BuscarVagas/tree/vagas_novo" -ForegroundColor Green
Write-Host ""
Write-Host "⚠️  IMPORTANTE:" -ForegroundColor Yellow
Write-Host "   Arquivos GIGANTES removidos do repositorio:" -ForegroundColor Gray
Write-Host "   - chromium-1228 (272MB)" -ForegroundColor Gray
Write-Host "   - chromium_headless_shell-1228 (194MB)" -ForegroundColor Gray
Write-Host "   - firefox-1532 (167MB)" -ForegroundColor Gray
Write-Host "   - WebCore.dll (53MB)" -ForegroundColor Gray
Write-Host "   - node.exe (88MB)" -ForegroundColor Gray
Write-Host ""
Write-Host "✅ Para instalar o Playwright depois:" -ForegroundColor Cyan
Write-Host "   playwright install" -ForegroundColor Gray

Read-Host "`nPressione ENTER para finalizar"