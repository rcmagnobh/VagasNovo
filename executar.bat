@echo off
chcp 65001 >nul
title Gestão de Vagas
cd /d "%~dp0"

set "PYTHON=python"
set "PIP_ARGS=--disable-pip-version-check -q"
set "URL_APP=http://localhost:8501"

echo ========================================
echo   Gestao de Vagas - Inicio automatico
echo ========================================
echo.

REM 1) Python instalado
where %PYTHON% >nul 2>&1
if errorlevel 1 (
    where py >nul 2>&1
    if errorlevel 1 (
        echo [ERRO] Python nao encontrado.
        echo Instale Python 3.10+ em https://www.python.org/downloads/
        echo Marque a opcao "Add Python to PATH" na instalacao.
        pause
        exit /b 1
    )
    set "PYTHON=py -3"
)

REM 2) Versao Python 3.10+
%PYTHON% -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python 3.10 ou superior e obrigatorio.
    pause
    exit /b 1
)

REM 3) pip disponivel
%PYTHON% -m pip --version >nul 2>&1
if errorlevel 1 (
    %PYTHON% -m ensurepip --upgrade >nul 2>&1
)

echo [1/6] Python OK
%PYTHON% --version

REM 4) Dependencias Python
if not exist "requirements.txt" (
    echo [ERRO] requirements.txt nao encontrado.
    pause
    exit /b 1
)

echo [2/6] Instalando bibliotecas (se necessario)...
%PYTHON% -m pip install %PIP_ARGS% --upgrade pip >nul 2>&1
%PYTHON% -m pip install %PIP_ARGS% -r requirements.txt
if errorlevel 1 (
    echo [ERRO] Falha ao instalar dependencias. Verifique a internet.
    pause
    exit /b 1
)

%PYTHON% -c "import streamlit, plotly, pandas, requests, bs4, lxml, playwright" >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Bibliotecas incompletas. Tentando reinstalar...
    %PYTHON% -m pip install -r requirements.txt
    if errorlevel 1 (
        pause
        exit /b 1
    )
)

echo [3/6] Bibliotecas OK

REM 5) Chromium do Playwright
echo [4/6] Verificando Chromium (Playwright)...
%PYTHON% -m playwright install chromium >nul 2>&1

REM 6) Banco de dados
echo [5/6] Preparando banco de dados...
%PYTHON% init_db.py >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Falha ao inicializar banco de dados.
    pause
    exit /b 1
)

echo [6/6] Subindo servidor...
echo.

REM Encerra instancia anterior na mesma porta (se existir)
for /f "tokens=5" %%p in ('netstat -ano 2^>nul ^| findstr ":8501" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%p >nul 2>&1
)

REM Inicia Streamlit em segundo plano
start /B "" %PYTHON% -m streamlit run app.py --server.headless true --browser.gatherUsageStats false

REM Aguarda servidor ficar pronto (ate 45 segundos)
set /a TENTATIVA=0
:AGUARDAR_SERVIDOR
set /a TENTATIVA+=1
if %TENTATIVA% GTR 45 (
    echo [ERRO] Servidor nao respondeu a tempo.
    call :ENCERRAR_SERVIDOR
    pause
    exit /b 1
)

powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri '%URL_APP%/_stcore/health' -UseBasicParsing -TimeoutSec 2; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
if errorlevel 1 (
    timeout /t 1 /nobreak >nul
    goto AGUARDAR_SERVIDOR
)

echo [OK] Servidor online.
echo [INFO] Abrindo navegador em %URL_APP% ...
start "" "%URL_APP%"

echo.
echo ========================================
echo   Gestao de Vagas em execucao
echo ========================================
echo.
echo URL: %URL_APP%
echo.
echo Pressione qualquer tecla para encerrar o sistema.
pause >nul

call :ENCERRAR_SERVIDOR
echo Sistema encerrado.
exit /b 0

:ENCERRAR_SERVIDOR
for /f "tokens=5" %%p in ('netstat -ano 2^>nul ^| findstr ":8501" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%p >nul 2>&1
)
exit /b 0
