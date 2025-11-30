@echo off
REM Run the ClashArena MVP application on Windows

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Load environment variables
if exist "..\.env" (
    for /f "tokens=*" %%a in ('type ..\.env') do set %%a
)

REM Run the application
python main.py

