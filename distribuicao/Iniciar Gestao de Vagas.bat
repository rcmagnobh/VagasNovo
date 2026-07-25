@echo off
chcp 65001 >nul
title Gestao de Vagas
cd /d "%~dp0"

if not exist "_internal\" (
    echo.
    echo [ERRO] Pasta _internal nao encontrada nesta pasta.
    echo.
    echo Copie a pasta INTEIRA "distribuicao" para o outro computador.
    echo Nao envie apenas o arquivo GestaoVagas.exe.
    echo.
    pause
    exit /b 1
)

if not exist "GestaoVagas.exe" (
    echo.
    echo [ERRO] GestaoVagas.exe nao encontrado.
    echo.
    pause
    exit /b 1
)

echo ========================================
echo   Gestao de Vagas
echo ========================================
echo.
echo Iniciando o sistema...
echo O navegador abrira em: http://localhost:8501
echo.
echo IMPORTANTE: NAO FECHE esta janela enquanto usar o programa.
echo Para encerrar, feche esta janela apos terminar.
echo.

GestaoVagas.exe
set ERR=%ERRORLEVEL%

echo.
if not "%ERR%"=="0" (
    echo [ERRO] O sistema encerrou com codigo %ERR%.
    echo Verifique o arquivo gestao_vagas.log nesta pasta.
) else (
    echo Sistema encerrado normalmente.
)
echo.
pause
