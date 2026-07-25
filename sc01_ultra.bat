@echo off
echo REMOVENDO ARQUIVOS GIGANTES...
cd vagas_novo

:: Remove do LFS
git lfs untrack "distribuicao/ms-playwright/chromium-1228/**"
git lfs untrack "distribuicao/ms-playwright/chromium_headless_shell-1228/**"
git lfs untrack "distribuicao/ms-playwright/firefox-1532/**"

:: Remove do Git
git rm -r --cached distribuicao/ms-playwright/chromium-1228/
git rm -r --cached distribuicao/ms-playwright/chromium_headless_shell-1228/
git rm -r --cached distribuicao/ms-playwright/firefox-1532/
git rm --cached distribuicao/ms-playwright/webkit-2311/WebCore.dll
git rm --cached dist/GestaoVagas/_internal/playwright/driver/node.exe

:: Cria .gitignore
echo distribuicao/ms-playwright/chromium-1228/ > .gitignore
echo distribuicao/ms-playwright/chromium_headless_shell-1228/ >> .gitignore
echo distribuicao/ms-playwright/firefox-1532/ >> .gitignore
echo distribuicao/ms-playwright/webkit-2311/WebCore.dll >> .gitignore
echo dist/GestaoVagas/_internal/playwright/driver/node.exe >> .gitignore

:: Commit e push
git add .
git commit -m "Removendo arquivos gigantes"
git push -u origin vagas_novo --force --no-verify

echo FINALIZADO!
pause