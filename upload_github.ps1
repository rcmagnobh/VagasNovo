# Script para subir a pasta GestaoVagas para o GitHub
# Autor: Script Automático
# Data: $(Get-Date -Format "dd/MM/yyyy")

Write-Host "🚀 Iniciando processo de upload da pasta GestaoVagas para o GitHub..." -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Yellow

# Configurações
$PASTA = "Vagas_Novo"
$BRANCH = "Busca_Vagas_240726"
$REPO_URL = "https://github.com/seu-usuario/Busca_Vagas_240726.git"  # ALTERE AQUI!

# Verifica se a pasta existe
if (-not (Test-Path $PASTA)) {
    Write-Host "❌ Erro: Pasta '$PASTA' não encontrada!" -ForegroundColor Red
    Write-Host "   Certifique-se de que a pasta está no diretório atual."
    exit 1
}

Write-Host "✅ Pasta '$PASTA' encontrada!" -ForegroundColor Green

# Função para verificar se o git está instalado
function Check-Git {
    try {
        $null = git --version
    } catch {
        Write-Host "❌ Git não está instalado!" -ForegroundColor Red
        Write-Host "   Instale o Git e tente novamente."
        Write-Host "   https://git-scm.com/downloads"
        exit 1
    }
}

# Entrar na pasta
Set-Location $PASTA
Write-Host "🏠 Diretório atual: $(Get-Location)" -ForegroundColor Gray

# Inicializa o Git se necessário
if (-not (Test-Path ".git")) {
    Write-Host "📁 Inicializando repositório Git..." -ForegroundColor Yellow
    git init
    Write-Host "✅ Repositório Git inicializado com sucesso!" -ForegroundColor Green
} else {
    Write-Host "⚠️  Este diretório já é um repositório Git!" -ForegroundColor Yellow
    $continuar = Read-Host "Deseja continuar com o repositório existente? (s/N)"
    if ($continuar -notmatch "[Ss]") {
        Write-Host "❌ Operação cancelada pelo usuário." -ForegroundColor Red
        exit 0
    }
}

# Configura o remote
Write-Host "🌐 Configurando remote..." -ForegroundColor Yellow
try {
    $null = git remote remove origin
} catch {
    # Ignora se não existir
}
git remote add origin $REPO_URL
Write-Host "✅ Remote configurado: $REPO_URL" -ForegroundColor Green

# Cria a branch
Write-Host "🌿 Criando branch '$BRANCH'..." -ForegroundColor Yellow
$branchExists = git branch --list $BRANCH
if ($branchExists) {
    Write-Host "   Branch '$BRANCH' já existe, mudando para ela..." -ForegroundColor Gray
    git checkout $BRANCH
} else {
    git checkout -b $BRANCH
}
Write-Host "✅ Branch '$BRANCH' criada/ativa!" -ForegroundColor Green

# Adiciona arquivos
Write-Host "📦 Adicionando arquivos da pasta '$PASTA'..." -ForegroundColor Yellow

# Remove .git da pasta se existir (para não conflitar)
if (Test-Path ".git") {
    Write-Host "⚠️  Removendo .git da pasta para não conflitar..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force ".git" -ErrorAction SilentlyContinue
}

git add .
Write-Host "✅ Arquivos adicionados com sucesso!" -ForegroundColor Green

# Faz commit
Write-Host "💾 Fazendo commit dos arquivos..." -ForegroundColor Yellow
$commitMsg = Read-Host "Digite a mensagem do commit (Enter para usar padrão)"
if ([string]::IsNullOrWhiteSpace($commitMsg)) {
    $commitMsg = "Upload inicial da pasta GestaoVagas - $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
}
git commit -m $commitMsg
Write-Host "✅ Commit realizado com sucesso!" -ForegroundColor Green

# Push para GitHub
Write-Host "⬆️  Enviando para o GitHub..." -ForegroundColor Yellow
Write-Host "   Branch: $BRANCH" -ForegroundColor Gray
Write-Host "   Repositório: $REPO_URL" -ForegroundColor Gray

# Verifica se a branch existe no remote
$remoteExists = git ls-remote --heads origin $BRANCH
if ($remoteExists) {
    Write-Host "   Branch '$BRANCH' já existe no remoto. Atualizando..." -ForegroundColor Yellow
    git push -u origin $BRANCH --force
} else {
    git push -u origin $BRANCH
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Upload concluído com sucesso!" -ForegroundColor Green
    Write-Host "🌐 Acesse: $REPO_URL" -ForegroundColor Cyan
    Write-Host "📂 Branch: $BRANCH" -ForegroundColor Cyan
} else {
    Write-Host "❌ Erro ao fazer push para o GitHub!" -ForegroundColor Red
    Write-Host "   Verifique suas credenciais e permissões."
    exit 1
}

Write-Host ""
Write-Host "✅ Processo concluído com sucesso!" -ForegroundColor Green
Write-Host "📊 Resumo:" -ForegroundColor Yellow
Write-Host "   - Pasta: $PASTA" -ForegroundColor Gray
Write-Host "   - Branch: $BRANCH" -ForegroundColor Gray
Write-Host "   - Repositório: $REPO_URL" -ForegroundColor Gray
Write-Host ""
Write-Host "📝 Para verificar o status: git status" -ForegroundColor Cyan
Write-Host "📝 Para ver commits: git log --oneline" -ForegroundColor Cyan