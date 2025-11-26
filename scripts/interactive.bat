@echo off
REM Description: A test batch script.
REM Flags: verbose, debug, force

echo Starting Batch Script...
echo Arguments: %*

if "%1"=="verbose" echo Verbose mode ON
if "%2"=="debug" echo Debug mode ON
if "%3"=="force" echo Force mode ON

echo Doing some work...
ping -n 3 127.0.0.1 >nul
echo Done.
