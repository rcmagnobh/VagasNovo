@echo off
echo ============================================================
echo    CORRIGINDO UPLOAD - Removendo arquivos grandes
echo ============================================================
echo.

cd vagas_novo

echo [1] Removendo arquivos grandes do stage...
git reset

echo [2] Removendo arquivos grandes do repositorio...
git rm -r --cached distribuicao/ms-playwright/ 2>nul
git rm -r --cached dist/GestaoVagas/_internal/playwright/ 2>nul

echo [3] Criando .gitignore para bloquear arquivos grandes...
echo # Arquivos grandes do Playwright > .gitignore
echo distribuicao/ms-playwright/ >> .gitignore
echo dist/GestaoVagas/_internal/playwright/ >> .gitignore
echo *.exe >> .gitignore
echo *.dll >> .gitignore
echo *.node >> .gitignore
echo node_modules/ >> .gitignore
echo .venv/ >> .gitignore
echo venv/ >> .gitignore
echo __pycache__/ >> .gitignore
echo *.pyc >> .gitignore

echo [4] Adicionando .gitignore...
git add .gitignore

echo [5] Adicionando arquivos restantes (excluindo os grandes)...
git add .

echo [6] Fazendo novo commit...
git commit -m "Upload sem arquivos grandes - %date% %time%"

echo [7] Forcando push...
git push -u origin vagas_novo --force

echo.
echo ============================================================
echo    PROCESSO FINALIZADO!
echo ============================================================
echo.
echo Arquivos grandes foram ignorados:
echo    - distribuicao/ms-playwright/
echo    - dist/GestaoVagas/_internal/playwright/
echo    - *.exe, *.dll, *.node
echo.
pause