# Arquivo Compilado - VagasNovo

Este diretório contém o aplicativo compilado VagasNovo dividido em partes.

## Reconstruindo o arquivo

O arquivo original agas.rar foi dividido em 10 partes de ~50 MB para permitir o armazenamento no GitHub.

### Windows (PowerShell)
\\\powershell
# Concatenar as partes
$output = @()
Get-ChildItem *.part*.rar | Sort-Object {[int]($_.Name -replace '\D')} | ForEach-Object {
    $output += [System.IO.File]::ReadAllBytes($_.FullName)
}
[System.IO.File]::WriteAllBytes("vagas_completo.rar", $output)
\\\

### Linux/Mac
\\\ash
cat vagas.part*.rar > vagas_completo.rar
\\\

Após reconstruir, você poderá extrair o arquivo RAR normalmente.
