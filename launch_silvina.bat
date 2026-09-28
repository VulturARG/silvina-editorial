@echo off
title Silvina Editorial Assistant
:: Mueve el directorio de trabajo a la ruta exacta donde esta este script
cd /d "%~dp0"

echo.
echo =====================================
echo   SILVINA EDITORIAL ASSISTANT
echo =====================================
echo.
echo Iniciando Silvina... Por favor espere.
echo El servidor web local se levantara en breve.
echo.
echo NO CIERRE ESTA VENTANA mientras usa Silvina.
echo Para cerrar Silvina: presione Ctrl+C aqui.
echo.

:: Activa el entorno virtual local de la carpeta
call .venv\Scripts\activate.bat

:: Arranca la aplicacion
python web_main.py

pause
