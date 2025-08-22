@echo off
call "C:\Program Files\Python311\python.exe" -m pip install -r .\requirements.txt
call "C:\Program Files\Python311\python.exe" .\register.py 
if %errorLevel% neq 0 (
    echo Script encountered an error. Press any key to continue...
    pause
)
