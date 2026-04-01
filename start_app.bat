@echo off
echo Starting API Translation Workflow...

cd /d "%~dp0"

if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment .venv not found in the current directory!
    echo Please ensure the .venv folder exists.
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat

echo Checking for requirements...
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo Installing missing modules, please wait...
    pip install streamlit openai google-generativeai pandas -i https://pypi.tuna.tsinghua.edu.cn/simple
)

echo Starting Streamlit server...
streamlit run app.py

pause
