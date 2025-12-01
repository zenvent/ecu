@echo off
REM Description: Comprehensive test for Batch script features: Flags, Colors, Input.
REM Flags: dev, test, prod, input, error

echo Starting Batch Features Test...
echo Arguments: %*

REM --- Flags Test ---
echo %* | findstr /C:"dev" >nul
if %errorlevel%==0 echo [INFO] Running in DEV mode

echo %* | findstr /C:"test" >nul
if %errorlevel%==0 echo [INFO] Running in TEST mode

echo %* | findstr /C:"prod" >nul
if %errorlevel%==0 echo [INFO] Running in PROD mode

REM --- Colors Test ---
echo.
echo [INFO] This message contains 'INFO' and should be BLUE.
echo [WARNING] This message contains 'WARNING' and should be YELLOW.
echo [ERROR] This message contains 'ERROR' and should be RED.
echo This is a normal message.
echo.

REM --- Stderr Test ---
echo %* | findstr /C:"error" >nul
if %errorlevel%==0 (
    echo Testing stderr output... 1>&2
    echo This is written to stderr. 1>&2
)

REM --- Input Test ---
echo Checking for input flag...
echo %* | findstr /C:"input" >nul
if %errorlevel%==0 (
    echo Input requested. Please enter something:
    set /p user_input=
    echo You entered: "%user_input%"
) else (
    echo No input flag detected, skipping input test.
)

echo Batch Features Test Complete.
