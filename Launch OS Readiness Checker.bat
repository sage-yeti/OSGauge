@echo off
cd /d "%~dp0"
where pythonw >nul 2>nul && (pythonw app.py & exit /b)
where pyw >nul 2>nul && (pyw -3 app.py & exit /b)
where python >nul 2>nul && (python app.py & exit /b)
where py >nul 2>nul && (py -3 app.py & exit /b)
echo Python 3.10 or newer is required. Download it from https://www.python.org/downloads/
pause
