@echo off
setlocal
echo JEIA DXF Fase 2B - diagnostico experimental do FreeCAD existente
echo Nao e necessario executar como administrador.
echo Nao ha instalacao nem alteracao de politica do PowerShell.
powershell.exe -NoLogo -NoProfile -File "%~dp0Diagnostico_FreeCAD.ps1" %*
set "JEIA_DIAG_EXIT=%ERRORLEVEL%"
echo.
echo Codigo de saida: %JEIA_DIAG_EXIT%
echo Se o Windows bloquear o script, consulte README.md. Nenhuma politica sera alterada.
pause
exit /b %JEIA_DIAG_EXIT%
