@echo off
setlocal

set "BASE_MODEL=hf.co/unsloth/gemma-4-26B-A4B-it-GGUF:UD-IQ4_XS"
set "MODEL_NAME=%~1"
if "%MODEL_NAME%"=="" set "MODEL_NAME=gemma4-26b-adapted"

where ollama >nul 2>&1
if errorlevel 1 (
    echo ERROR: ollama is not on PATH.
    exit /b 1
)

ollama show "%BASE_MODEL%" >nul 2>&1
if errorlevel 1 (
    echo Pulling base model %BASE_MODEL%...
    ollama pull "%BASE_MODEL%"
    if errorlevel 1 (
        echo ERROR: Failed to pull base model.
        exit /b 1
    )
) else (
    echo Base model %BASE_MODEL% is already installed, skipping pull.
)

echo Creating Ollama model "%MODEL_NAME%"...
ollama create %MODEL_NAME% -f "%~dp0..\src\infrastructure\resources\ollama\gemma4-26b-adapted.Modelfile"
if errorlevel 1 (
    echo ERROR: Failed to create model "%MODEL_NAME%".
    exit /b 1
)

echo Successfully created Ollama model "%MODEL_NAME%".
exit /b 0
