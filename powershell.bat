@echo off
setlocal enabledelayedexpansion
set "args=%*"
set "args=!args:-Command =!"
set "args=!args:\"="!"
for /f "tokens=* delims=" %%i in ("!args!") do set "clean_args=%%~i"
echo !clean_args! > C:\Users\itagr\.gemini\antigravity\scratch\Red-Social\run_cmd.bat
call C:\Users\itagr\.gemini\antigravity\scratch\Red-Social\run_cmd.bat
