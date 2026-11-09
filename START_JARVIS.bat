@echo off
cd /d "%~dp0"
title JARVIS - setup and start

where py >nul 2>nul
if errorlevel 1 goto nopython

if exist venv\Scripts\python.exe goto havevenv
echo [1/4] Creating the virtual environment...
py -3.12 -m venv venv 2>nul
if not exist venv\Scripts\python.exe py -m venv venv
if not exist venv\Scripts\python.exe goto venvfail

:havevenv
call venv\Scripts\activate.bat

echo [2/4] Installing packages. First time only, this can take a few minutes...
python -m pip install --upgrade pip >nul 2>nul
pip install -r requirements.txt
if errorlevel 1 goto installfail

if exist .env goto havekey
echo [3/4] Gemini key setup.
echo Get a free key from https://aistudio.google.com/apikey
set /p GEMINIKEY=Paste your Gemini API key here and press Enter: 
> .env echo GEMINI_API_KEY=%GEMINIKEY%

:havekey
if not exist voices mkdir voices
if exist voices\en_US-lessac-medium.onnx goto checkhindi
echo [4/4] Downloading the English voice. First time only, needs internet...
cd voices
python -m piper.download_voices en_US-lessac-medium
cd ..

:checkhindi
if exist voices\hi_IN-rohan-medium.onnx goto start
echo Downloading the Hindi voice. First time only...
cd voices
python -m piper.download_voices hi_IN-rohan-medium
cd ..

:start
echo.
echo Starting JARVIS...
python main.py
pause
goto end

:nopython
echo Python is not installed. Install Python 3.12 from python.org and tick "Add python.exe to PATH".
pause
goto end

:venvfail
echo Could not create the virtual environment. Make sure Python 3.12 is installed.
pause
goto end

:installfail
echo Package install failed. Copy the error above and send it to Claude.
pause
goto end

:end
