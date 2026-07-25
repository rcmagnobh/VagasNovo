@echo off
echo INICIANDO UPLOAD...
echo.

cd vagas_novo
echo Entrou na pasta vagas_novo
echo.

git remote remove origin
git remote add origin https://github.com/rcmagnobh/BuscarVagas.git
echo Remote configurado
echo.

git branch -D vagas_novo
git push origin --delete vagas_novo
git checkout -b vagas_novo
echo Branch criada
echo.

git add --all
echo Arquivos adicionados
echo.

git commit -m "Upload completo - vagas_novo"
echo Commit realizado
echo.

git push -u origin vagas_novo --force
echo Push realizado
echo.

echo FINALIZADO!
pause