@echo off
echo ============================================================
echo    SOLUCAO DEFINITIVA - REMOVER ARQUIVOS GIGANTES
echo ============================================================
echo.

cd vagas_novo

echo [1] Removendo arquivos gigantes do LFS...
echo.

:: Remove os arquivos gigantes do tracking LFS
git lfs untrack "distribuicao/ms-playwright/chromium-1228/**"
git lfs untrack "distribuicao/ms-playwright/chromium_headless_shell-1228/**"
git lfs untrack "distribuicao/ms-playwright/firefox-1532/**"

echo [2] Removendo arquivos do controle de versao...
echo.

:: Remove os arquivos gigantes do Git
git rm -r --cached distribuicao/ms-playwright/chromium-1228/ 2>nul
git rm -r --cached distribuicao/ms-playwright/chromium_headless_shell-1228/ 2>nul
git rm -r --cached distribuicao/ms-playwright/firefox-1532/ 2>nul
git rm -r --cached dist/GestaoVagas/_internal/playwright/driver/node.exe 2>nul
git rm -r --cached distribuicao/ms-playwright/webkit-2311/WebCore.dll 2>nul

echo [3] Atualizando .gitattributes...
echo.

:: Cria .gitattributes correto
(
echo # Arquivos pequenos do Playwright (vai para LFS)
echo *.dll filter=lfs diff=lfs merge=lfs -text
echo *.exe filter=lfs diff=lfs merge=lfs -text
echo *.node filter=lfs diff=lfs merge=lfs -text
echo 
echo # Pastas que NAO vao para o Git (ignorar)
echo distribuicao/ms-playwright/chromium-1228/
echo distribuicao/ms-playwright/chromium_headless_shell-1228/
echo distribuicao/ms-playwright/firefox-1532/
echo dist/GestaoVagas/_internal/playwright/driver/node.exe
echo distribuicao/ms-playwright/webkit-2311/WebCore.dll
) > .gitattributes

echo [4] Adicionando .gitignore para bloquear arquivos gigantes...
echo.

(
echo # Arquivos gigantes do Playwright (nao enviar)
echo distribuicao/ms-playwright/chromium-1228/
echo distribuicao/ms-playwright/chromium_headless_shell-1228/
echo distribuicao/ms-playwright/firefox-1532/
echo distribuicao/ms-playwright/webkit-2311/WebCore.dll
echo dist/GestaoVagas/_internal/playwright/driver/node.exe
echo 
echo # Binarios grandes
echo *.dll
echo *.exe
echo *.node
echo 
echo # Dependencias
echo node_modules/
echo .venv/
echo venv/
echo __pycache__/
) > .gitignore

echo [5] Adicionando arquivos ao stage...
echo.

git add .gitattributes
git add .gitignore

echo [6] Fazendo commit final...
echo.

git commit -m "Removendo arquivos gigantes - %date% %time%"

echo [7] Forcando push para o GitHub...
echo.

git push -u origin vagas_novo --force

if errorlevel 1 (
    echo.
    echo ERRO! Tentando com --force --no-verify...
    git push -u origin vagas_novo --force --no-verify
)

echo.
echo ============================================================
echo    PROCESSO FINALIZADO!
echo ============================================================
echo.
echo Acesse: https://github.com/rcmagnobh/BuscarVagas/tree/vagas_novo
pause