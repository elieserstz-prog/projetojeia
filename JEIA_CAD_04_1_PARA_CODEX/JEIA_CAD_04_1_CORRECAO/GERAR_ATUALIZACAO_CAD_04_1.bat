@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo ===========================================================
echo JEIA CAD 04.1 - INSTALAR FREECAD + COMPILAR ATUALIZACAO
 echo ===========================================================
py -3.12 --version || goto falha
call "INSTALAR_FREECAD_UMA_VEZ.bat" || goto falha
set "VENV=.venv_jeia_cad041"
if not exist "%VENV%\Scripts\python.exe" py -3.12 -m venv "%VENV%"
if not exist "%VENV%\Scripts\python.exe" goto falha
"%VENV%\Scripts\python.exe" -m pip install --disable-pip-version-check --only-binary=:all: "PyQt6==6.11.0" "PyQt6-Qt6==6.11.0" "PyQt6-WebEngine==6.11.0" "PyQt6-WebEngine-Qt6==6.11.2" "pyinstaller==6.22.0" "ezdxf==1.4.4" || goto falha
"%VENV%\Scripts\python.exe" -m pip check || goto falha
"%VENV%\Scripts\python.exe" -c "from PyQt6.QtWebEngineWidgets import QWebEngineView; import ezdxf; print('Qt + ezdxf carregados')" || goto falha
"%VENV%\Scripts\python.exe" OBTER_OPENCASCADE_OFICIAL.py || goto falha
"%VENV%\Scripts\python.exe" -m PyInstaller --noconfirm --clean --windowed --onedir --name JEIA_MOTORES_TESTE --collect-submodules ezdxf --exclude-module PySide6 --exclude-module PySide2 --exclude-module PyQt5 --exclude-module webview --exclude-module pythonnet --exclude-module clr --add-data "JEIA_original_preservado.html;." --add-data "jeia_shell.html;." --add-data "engines;engines" --add-data "vendor;vendor" JEIA_Windows.py || goto falha
if not exist "dist\JEIA_MOTORES_TESTE\JEIA_MOTORES_TESTE.exe" goto falha
if not exist "dist\JEIA_MOTORES_TESTE\_internal\vendor\occt\occt-import-js.wasm" goto falha
set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" (echo Inno Setup nao encontrado & goto falha)
if not exist "INSTALADOR_PRONTO" mkdir "INSTALADOR_PRONTO"
"%ISCC%" "JEIA_Atualizacao.iss" || goto falha
if not exist "INSTALADOR_PRONTO\JEIA_TECH_Industrial_ATUALIZACAO_CAD_04_1.exe" goto falha
echo.
echo SUCESSO: INSTALADOR_PRONTO\JEIA_TECH_Industrial_ATUALIZACAO_CAD_04_1.exe
echo Instale esta atualizacao com o JEIA fechado.
pause
exit /b 0
:falha
echo.
echo FALHA - NAO INSTALE ATUALIZACAO ANTIGA OU INCOMPLETA.
pause
exit /b 1
