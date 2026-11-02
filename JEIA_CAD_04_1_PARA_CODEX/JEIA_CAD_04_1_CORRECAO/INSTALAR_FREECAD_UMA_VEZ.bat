@echo off
setlocal EnableExtensions
set "BIN="
for %%D in ("%ProgramFiles%\FreeCAD*\bin\FreeCADCmd.exe" "%LOCALAPPDATA%\Programs\FreeCAD*\bin\FreeCADCmd.exe") do if exist "%%~fD" set "BIN=%%~fD"
where FreeCADCmd.exe >nul 2>&1 && set "BIN=PATH"
if defined BIN (
 echo FreeCAD aparentemente instalado. A integracao fara uma verificacao real no JEIA.
 exit /b 0
)
where winget >nul 2>&1 || (
 echo ERRO: winget nao disponivel. Instale o FreeCAD oficial e execute novamente.
 exit /b 1
)
echo Instalando FreeCAD oficial via winget. Pode ser solicitada autorizacao do Windows.
winget install --id FreeCAD.FreeCAD --exact --version 1.1.3 --source winget --silent --accept-package-agreements --accept-source-agreements
if errorlevel 1 (
 echo ERRO na instalacao do FreeCAD. Verifique a conexao e execute novamente.
 exit /b 1
)
echo Instalacao solicitada com sucesso. Reinicie o JEIA depois da atualizacao.
exit /b 0
