@echo off
chcp 65001 >nul
title Gestao de Vagas - Gerar Distribuicao
cd /d "%~dp0"

set "PYTHON=python"
where %PYTHON% >nul 2>&1
if errorlevel 1 (
    where py >nul 2>&1
    if errorlevel 1 (
        echo [ERRO] Python nao encontrado.
        pause
        exit /b 1
    )
    set "PYTHON=py -3"
)

echo Encerrando instancias anteriores do programa...
taskkill /F /IM GestaoVagas.exe >nul 2>&1
timeout /t 2 /nobreak >nul

echo ========================================
echo   Gestao de Vagas - Gerar Distribuicao
echo ========================================
echo.

echo [1/6] Instalando dependencias...
%PYTHON% -m pip install --disable-pip-version-check -q -r requirements.txt
if errorlevel 1 goto :erro

echo [2/6] Instalando navegador Playwright Chromium...
%PYTHON% -m playwright install chromium
if errorlevel 1 goto :erro

echo [3/6] Instalando PyInstaller...
%PYTHON% -m pip install --disable-pip-version-check -q pyinstaller>=6.0.0
if errorlevel 1 goto :erro

echo [4/6] Compilando executavel (aguarde, pode levar alguns minutos)...
%PYTHON% -m PyInstaller --noconfirm --clean gestao_vagas.spec
if errorlevel 1 goto :erro

if not exist "dist\GestaoVagasApp\GestaoVagas.exe" (
    echo [ERRO] Compilacao nao gerou dist\GestaoVagasApp\GestaoVagas.exe
    goto :erro
)

echo [5/6] Montando pasta distribuicao...
if exist "distribuicao" rmdir /s /q "distribuicao"
mkdir "distribuicao"

xcopy /E /I /Y /Q "dist\GestaoVagasApp\*" "distribuicao\" >nul
copy /Y "Iniciar Gestao de Vagas.bat" "distribuicao\" >nul
copy /Y "LEIA-ME-DISTRIBUICAO.txt" "distribuicao\LEIA-ME.txt" >nul

if exist "%LOCALAPPDATA%\ms-playwright" (
    echo Copiando navegador Chromium para distribuicao...
    xcopy /E /I /Y /Q "%LOCALAPPDATA%\ms-playwright" "distribuicao\ms-playwright\" >nul
) else (
    echo [AVISO] Pasta ms-playwright nao encontrada. Sites com JavaScript podem falhar.
)

echo [6/6] Verificando pacote...
if not exist "distribuicao\_internal\" goto :erro_pasta
if not exist "distribuicao\GestaoVagas.exe" goto :erro_pasta
if not exist "distribuicao\Iniciar Gestao de Vagas.bat" goto :erro_pasta
if not exist "distribuicao\_internal\plotly\validators\_validators.json" (
    echo [ERRO] Arquivo obrigatorio ausente: _internal\plotly\validators\_validators.json
    goto :erro_pasta
)
if not exist "distribuicao\ms-playwright\" (
    echo [AVISO] Pasta ms-playwright ausente. Catho, Indeed, Revelo, Coodesh e Upwork podem falhar.
)

echo.
echo ========================================
echo   Distribuicao criada com sucesso!
echo ========================================
echo.
echo Envie ao usuario a pasta:
echo   %CD%\distribuicao
echo.
echo O usuario deve executar:
echo   Iniciar Gestao de Vagas.bat
echo.
echo Compacte a pasta "distribuicao" em ZIP para enviar.
echo.
pause
exit /b 0

:erro_pasta
echo [ERRO] Pasta distribuicao incompleta.
pause
exit /b 1

:erro
echo [ERRO] Falha ao gerar distribuicao.
pause
exit /b 1
