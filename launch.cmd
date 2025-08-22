@echo off
call  "C:\Program Files\Python311\python.exe" --version
call  "C:\Program Files\Python311\python.exe" %4 %1 %2
if %errorLevel% neq 0 (
    echo Script encountered an error. Press any key to continue...
    pause
)
