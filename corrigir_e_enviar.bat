@echo off
echo ============================================
echo CORRIGINDO E ENVIANDO PARA O GITHUB
echo Repositorio: rcmagnobh/BuscarVagas
echo ============================================
echo.

echo [1] Verificando remote atual...
git remote -v
echo.

echo [2] Removendo remote incorreto...
git remote remove origin
echo.

echo [3] Adicionando remote correto...
git remote add origin https://github.com/rcmagnobh/BuscarVagas.git
echo.

echo [4] Verificando novo remote...
git remote -v
echo.

echo [5] Verificando branch atual...
git branch
echo.

echo [6] Adicionando todos os arquivos...
git add .
echo.

echo [7] Verificando se há mudancas...
git status
echo.

echo [8] Fazendo commit...
git commit -m "Upload inicial - BuscarVagas - %date% %time%"
echo.

echo [9] Enviando para o GitHub...
echo Repositorio: https://github.com/rcmagnobh/BuscarVagas.git
echo Branch: main
echo.

git push -u origin main

if errorlevel 1 (
    echo.
    echo Tentando com --force...
    git push -u origin main --force
)

echo.
echo ============================================
echo FINALIZADO!
echo ============================================
pause