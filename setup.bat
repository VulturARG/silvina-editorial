@echo off
echo Setting up virtual environment...
py -m venv .venv
if errorlevel 1 (
    echo ERROR: Failed to create .venv
    exit /b 1
)
echo Installing PyTorch (CPU build; see README for NVIDIA CUDA or AMD ROCm)...
.venv\Scripts\pip install torch --index-url https://download.pytorch.org/whl/cpu
if errorlevel 1 (
    echo ERROR: PyTorch install failed
    exit /b 1
)
echo Installing dependencies...
.venv\Scripts\pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: pip install failed
    exit /b 1
)
echo.
echo Setup complete. Activate with: .venv\Scripts\activate
echo Run tests with: .venv\Scripts\pytest tests\
exit /b 0
