@echo off
REM %~dp0 expands to the drive letter and path of the script.
set "SOURCE_FILE=%~dp0code.py"

REM Pico drive letter
set "TARGET_DRIVE=D:\"

if exist %TARGET_DRIVE% (
    copy /Y "%SOURCE_FILE%" "%TARGET_DRIVE%code.py"
    echo Successfully pushed %SOURCE_FILE% to %TARGET_DRIVE%code.py
) else (
    echo Error: Pico drive %TARGET_DRIVE% not found. Make sure your Pico is connected.
)