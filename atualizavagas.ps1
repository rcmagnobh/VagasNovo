# Salve como: criar_e_subir.ps1

$GITHUB_USER = "rcmagnobh"
$REPO_NAME = "GestaoVagas"
$REPO_URL = "https://github.com/$GITHUB_USER/$REPO_NAME.git"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SUBINDO PROJETO AO GITHUB" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar se o repositório existe
Write-Host "Verificando se o repositorio existe..." -ForegroundColor Yellow

# Usando GitHub CLI se disponível
$ghInstalled = Get-Command gh -ErrorAction SilentlyContinue

if ($ghInstalled) {
    Write-Host "GitHub CLI detectado. Verificando repositorio..." -ForegroundColor Green
    
    $repoExists = gh repo view $GITHUB_USER/$REPO_NAME 2>$null
    
    if (-not $repoExists) {
        Write-Host "Repositorio nao encontrado. Criando..." -ForegroundColor Yellow
        gh repo create $REPO_NAME --public --description "Projeto GestaoVagas"
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "ERRO ao criar repositorio. Criando manualmente..." -ForegroundColor Red
            Write-Host "Acesse: https://github.com/$GITHUB_USER" -ForegroundColor Cyan
            Write-Host "Clique em 'New' e crie: $REPO_NAME" -ForegroundColor Cyan
            Read-Host "Pressione Enter apos criar"
        }
    } else {
        Write-Host "Repositorio encontrado!" -ForegroundColor Green
    }
} else {
    Write-Host "GitHub CLI nao encontrado." -ForegroundColor Yellow
    Write-Host "Crie o repositorio manualmente:" -ForegroundColor Cyan
    Write-Host "1. Acesse: https://github.com/$GITHUB_USER" -ForegroundColor Cyan
    Write-Host "2. Clique em 'New' e crie: $REPO_NAME" -ForegroundColor Cyan
    Write-Host "3. Deixe DESMARCADO 'Initialize with README'" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Pressione Enter apos criar o repositorio"
}

# Configurar e fazer push
Write-Host ""
Write-Host "Configurando remote e enviando arquivos..." -ForegroundColor Yellow

# Remover remote existente
git remote remove origin 2>$null

# Adicionar remote
git remote add origin $REPO_URL

# Verificar se há alterações para commit
$status = git status --porcelain

if ($status) {
    Write-Host "Arquivos modificados encontrados. Commitando..." -ForegroundColor Yellow
    git add .
    git commit -m "Subindo projeto completo $REPO_NAME - $(Get-Date -Format 'dd/MM/yyyy HH:mm')"
} else {
    Write-Host "Nenhuma alteracao para commit." -ForegroundColor Yellow
}

# Fazer push
Write-Host "Enviando para o GitHub..." -ForegroundColor Yellow
git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  SUCESSO! PROJETO ENVIADO!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Acesse: $REPO_URL" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "  ERRO NO ENVIO" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Solucoes:" -ForegroundColor Yellow
    Write-Host "1. Verifique se o repositorio foi criado" -ForegroundColor Yellow
    Write-Host "2. Verifique suas credenciais" -ForegroundColor Yellow
    Write-Host "3. Tente: git push -u origin main --force" -ForegroundColor Yellow
}

Read-Host "`nPressione Enter para sair"