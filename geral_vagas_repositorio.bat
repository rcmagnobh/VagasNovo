@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ============================================================
:: SCRIPT BATCH - UPLOAD PARA GITHUB
:: ============================================================
:: Diretório: vagas_novo
:: Branch: vagas_novo
:: Repositório: https://github.com/rcmagnobh/BuscarVagas.git
:: ============================================================

set REPO_URL=https://github.com/rcmagnobh/BuscarVagas.git
set PASTA_ORIGEM=vagas_novo
set BRANCH_NOME=vagas_novo

echo ============================================================
echo    🚀 UPLOAD PARA GITHUB - BuscarVagas
echo    📂 Pasta: %PASTA_ORIGEM%
echo    🌿 Branch: %BRANCH_NOME%
echo ============================================================
echo.

:: 1. Verifica Git
echo [1] Verificando Git...
where git >nul 2>nul
if errorlevel 1 (
    echo ❌ Git nao encontrado!
    echo Instale em: https://git-scm.com/download/win
    pause
    exit /b 1
)
echo ✅ Git encontrado!
echo.

:: 2. Verifica pasta
echo [2] Verificando pasta %PASTA_ORIGEM%...
if not exist "%PASTA_ORIGEM%" (
    echo ❌ Pasta %PASTA_ORIGEM% nao encontrada!
    pause
    exit /b 1
)
cd "%PASTA_ORIGEM%"
echo ✅ Pasta encontrada: %cd%
echo.

:: 3. Lista arquivos
echo [3] Listando arquivos e pastas...
echo 📁 Pastas encontradas:
for /d /r . %%i in (*) do (
    echo    📂 %%~nxi
)
echo.
echo 📄 Contando arquivos...
set count=0
for /r . %%i in (*) do (
    set /a count+=1
)
echo Total de arquivos: %count%
echo.

:: 4. Inicializa Git
echo [4] Configurando repositorio Git...
if exist ".git" (
    echo Repositorio Git ja existe
) else (
    echo Inicializando Git...
    git init
    if errorlevel 1 (
        echo ❌ Erro ao inicializar Git!
        pause
        exit /b 1
    )
)

git remote remove origin 2>nul
git remote add origin %REPO_URL%
echo ✅ Remote configurado: %REPO_URL%
echo.

:: 5. Deleta branch existente
echo [5] Preparando branch %BRANCH_NOME%...

:: Deleta branch local
git branch -D %BRANCH_NOME% 2>nul
if errorlevel 1 (
    echo Branch local %BRANCH_NOME% nao existe
) else (
    echo ✅ Branch local deletada
)

:: Deleta branch remota
git push origin --delete %BRANCH_NOME% 2>nul
if errorlevel 1 (
    echo Branch remota %BRANCH_NOME% nao existe
) else (
    echo ✅ Branch remota deletada
)

:: Cria nova branch
git checkout -b %BRANCH_NOME%
if errorlevel 1 (
    echo ❌ Erro ao criar branch!
    pause
    exit /b 1
)
echo ✅ Branch %BRANCH_NOME% criada!
echo.

:: 6. Adiciona arquivos
echo [6] Adicionando TODOS os arquivos e subpastas...
echo Aguarde... Isso pode levar alguns segundos...

git add --all --verbose

if errorlevel 1 (
    echo ⚠️  Tentando git add . ...
    git add .
)

echo ✅ Arquivos adicionados!
echo.

:: 7. Verifica o que foi adicionado
echo [7] Verificando arquivos no stage...
git diff --cached --name-only
echo.

:: 8. Faz commit
echo [8] Realizando commit...
set COMMIT_MSG=Upload completo - Branch %BRANCH_NOME% - %date% %time%
git commit -m "%COMMIT_MSG%"

if errorlevel 1 (
    echo ❌ Erro ao fazer commit!
    pause
    exit /b 1
)
echo ✅ Commit realizado!
echo.

:: 9. Envia para GitHub
echo [9] Enviando para o GitHub...
echo Repositorio: %REPO_URL%
echo Branch: %BRANCH_NOME%
echo Total de arquivos: %count%
echo.

git push -u origin %BRANCH_NOME%

if errorlevel 1 (
    echo ⚠️  Push normal falhou. Tentando com --force...
    git push -u origin %BRANCH_NOME% --force
    
    if errorlevel 1 (
        echo.
        echo ❌ ERRO AO ENVIAR PARA O GITHUB!
        echo.
        echo Verifique:
        echo 1. Repositorio existe: https://github.com/rcmagnobh/BuscarVagas
        echo 2. Suas credenciais do GitHub
        echo 3. Use um token de acesso pessoal
        echo    https://github.com/settings/tokens
        echo.
        pause
        exit /b 1
    )
)

echo.
echo ============================================================
echo    ✅ SUCESSO! Upload concluido!
echo ============================================================
echo.
echo 📊 RESUMO:
echo    📦 Repositorio: rcmagnobh/BuscarVagas
echo    🌿 Branch: %BRANCH_NOME% (NOVA)
echo    📄 Arquivos enviados: %count%
echo    📁 Pastas: (todas as subpastas)
echo.
echo 🌐 Acesse: https://github.com/rcmagnobh/BuscarVagas/tree/%BRANCH_NOME%
echo.
pause