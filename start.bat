@echo off
cd /d "%~dp0"
echo ============================================================
echo   SISTEMA DE AUTOMATIZACION DE DROPSHIPPING
echo ============================================================
echo.

REM Verificar si existe el entorno virtual
if not exist "venv\" (
    echo [1/4] Creando entorno virtual...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: No se pudo crear el entorno virtual
        echo Asegurate de tener Python 3.11+ instalado
        pause
        exit /b 1
    )
    echo OK - Entorno virtual creado
    echo.
) else (
    echo [1/4] Entorno virtual ya existe - OK
    echo.
)

REM Activar entorno virtual
echo [2/4] Activando entorno virtual...
call venv\Scripts\activate.bat
echo OK - Entorno activado
echo.

REM Instalar dependencias
echo [3/4] Instalando dependencias...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo ERROR: No se pudieron instalar las dependencias
    pause
    exit /b 1
)
echo OK - Dependencias instaladas
echo.

REM Verificar configuracion
echo [4/4] Verificando configuracion del sistema...
python verify.py
if errorlevel 1 (
    echo.
    echo ERROR: El sistema tiene errores de configuracion
    pause
    exit /b 1
)
echo.

REM Verificar archivo .env
if not exist ".env" (
    echo ============================================================
    echo   ATENCION: Archivo .env no encontrado
    echo ============================================================
    echo.
    echo El sistema necesita un archivo .env con tus credenciales.
    echo.
    echo Pasos:
    echo   1. Copia .env.example a .env
    echo   2. Edita .env con tus credenciales reales
    echo   3. Ejecuta este script nuevamente
    echo.
    echo Comando rapido: copy .env.example .env
    echo.
    pause
    exit /b 1
)

REM Ejecutar sistema
echo ============================================================
echo   INICIANDO SISTEMA...
echo ============================================================
echo.
python main.py

echo.
echo ============================================================
echo   EJECUCION COMPLETADA
echo ============================================================
pause
