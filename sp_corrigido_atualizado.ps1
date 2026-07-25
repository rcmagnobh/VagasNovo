# ================================================
# SCRIPT CORRIGIDO - BuscarVagas
# ================================================

Clear-Host

Write-Host @"
╔═══════════════════════════════════════════════╗
║                                               ║
║   🚀 UPLOAD PARA GITHUB - BuscarVagas         ║
║   📦 rcmagnobh/BuscarVagas                    ║
║                                               ║
╚═══════════════════════════════════════════════╝
"@ -ForegroundColor Magenta

Write-Host "`n📁 Pasta atual: $(Get-Location)" -ForegroundColor Cyan

# 1. Verifica e corrige o remote
Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
Write-Host "▶ CORRIGINDO REMOTE" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray

# Mostra remote atual
$remoteAtual = git remote get-url origin 2>$null
if ($remoteAtual) {
    Write-Host "📡 Remote atual: $remoteAtual" -ForegroundColor Gray
} else {
    Write-Host "📡 Nenhum remote configurado" -ForegroundColor Gray
}

# Remove remote antigo
Write-Host "`n🗑️  Removendo remote antigo..." -ForegroundColor Yellow
git remote remove origin 2>$null

# Adiciona remote correto
Write-Host "📦 Adicionando remote correto..." -ForegroundColor Yellow
git remote add origin https://github.com/rcmagnobh/BuscarVagas.git

# Verifica se configurou certo
$novoRemote = git remote get-url origin
Write-Host "✅ Remote configurado: $novoRemote" -ForegroundColor Green

# 2. Verifica se o repositório existe no GitHub
Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
Write-Host "▶ VERIFICANDO REPOSITÓRIO" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray

Write-Host "🔍 Verificando se o repositório existe..." -ForegroundColor Yellow
$repoExists = git ls-remote https://github.com/rcmagnobh/BuscarVagas.git 2>$null

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Repositório não encontrado ou sem permissão!" -ForegroundColor Red
    Write-Host ""
    Write-Host "🔧 SOLUÇÕES:" -ForegroundColor Yellow
    Write-Host "1. O repositório deve existir em: https://github.com/rcmagnobh/BuscarVagas" -ForegroundColor Gray
    Write-Host "2. Você precisa ter permissão de escrita no repositório" -ForegroundColor Gray
    Write-Host "3. Verifique se está logado no GitHub" -ForegroundColor Gray
    Write-Host ""
    Write-Host "📝 Para criar o repositório:" -ForegroundColor Cyan
    Write-Host "   Acesse: https://github.com/new" -ForegroundColor Gray
    Write-Host "   Nome: BuscarVagas" -ForegroundColor Gray
    Write-Host "   Descrição: Buscar Vagas" -ForegroundColor Gray
    Write-Host "   Público ou Privado" -ForegroundColor Gray
    Write-Host ""
    Read-Host "Pressione ENTER para continuar mesmo assim"
}

# 3. Verifica branch
Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
Write-Host "▶ VERIFICANDO BRANCH" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray

$branchAtual = git branch --show-current
if ($branchAtual) {
    Write-Host "🌿 Branch atual: $branchAtual" -ForegroundColor Cyan
} else {
    Write-Host "🌿 Nenhuma branch ativa" -ForegroundColor Gray
}

# 4. Adiciona todos os arquivos
Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
Write-Host "▶ ADICIONANDO ARQUIVOS" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray

# Conta arquivos
$totalArquivos = (Get-ChildItem -File -Recurse -Force | Where-Object { $_.FullName -notmatch "\\.git\\" }).Count
Write-Host "📄 Total de arquivos encontrados: $totalArquivos" -ForegroundColor Gray

git add .

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Arquivos adicionados!" -ForegroundColor Green
} else {
    Write-Host "❌ Erro ao adicionar arquivos!" -ForegroundColor Red
}

# 5. Verifica status
Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
Write-Host "▶ STATUS DOS ARQUIVOS" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
git status --short

# 6. Faz commit
Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
Write-Host "▶ REALIZANDO COMMIT" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray

$commitMsg = "Upload inicial - BuscarVagas - $(Get-Date -Format 'dd/MM/yyyy HH:mm')"
git commit -m $commitMsg

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Commit realizado!" -ForegroundColor Green
} else {
    Write-Host "⚠️  Nada para commitar ou erro no commit" -ForegroundColor Yellow
}

# 7. Faz push para o GitHub
Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
Write-Host "▶ ENVIANDO PARA O GITHUB" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray

Write-Host "📤 Enviando para: https://github.com/rcmagnobh/BuscarVagas.git" -ForegroundColor Cyan
Write-Host "🌿 Branch: main" -ForegroundColor Cyan
Write-Host ""

# Tenta push normal
git push -u origin main

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n⚠️  Push normal falhou. Tentando com --force..." -ForegroundColor Yellow
    git push -u origin main --force
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n✅ Push forçado concluído!" -ForegroundColor Green
    } else {
        Write-Host "`n❌ Erro ao fazer push!" -ForegroundColor Red
        Write-Host ""
        Write-Host "🔧 Verifique:" -ForegroundColor Yellow
        Write-Host "1. O repositório existe: https://github.com/rcmagnobh/BuscarVagas" -ForegroundColor Gray
        Write-Host "2. Você tem permissão de escrita" -ForegroundColor Gray
        Write-Host "3. Suas credenciais do GitHub estão corretas" -ForegroundColor Gray
    }
}

# 8. Resumo final
Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
Write-Host "▶ RESUMO FINAL" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray

Write-Host "📊 Informações:" -ForegroundColor Cyan
Write-Host "   Repositório: https://github.com/rcmagnobh/BuscarVagas" -ForegroundColor Gray
Write-Host "   Branch: main" -ForegroundColor Gray
Write-Host "   Commit: $commitMsg" -ForegroundColor Gray
Write-Host "   Arquivos: $totalArquivos" -ForegroundColor Gray

Read-Host "`nPressione ENTER para sair"