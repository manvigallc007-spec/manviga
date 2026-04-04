@echo off
REM YouTube Posting Pipeline — Windows Task Scheduler Batch Wrapper
REM Runs every 6 hours via Windows Task Scheduler
REM Last updated: 2026-03-29

setlocal enabledelayedexpansion

set "ProjectRoot=C:\Users\sport\Manviga\youtube-posting"
set "VenvActivate=C:\Users\sport\Manviga\.venv\Scripts\activate.bat"
set "PipelineScript=%ProjectRoot%\src\run_pipeline.py"
set "LogDir=%ProjectRoot%\logs"

REM Create log directory if it doesn't exist
if not exist "%LogDir%" mkdir "%LogDir%"

REM Create timestamp for log file
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c%%a%%b)
for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set mytime=%%a%%b)
set "SchedulerLog=%LogDir%\scheduler_%mydate%_%mytime%.log"

REM Log function
echo. >> "%SchedulerLog%"
echo [%date% %time%] ================================ >> "%SchedulerLog%"
echo [%date% %time%] YOUTUBE PIPELINE SCHEDULER START >> "%SchedulerLog%"
echo [%date% %time%] ================================ >> "%SchedulerLog%"
echo [%date% %time%] Project Root: %ProjectRoot% >> "%SchedulerLog%"
echo [%date% %time%] Pipeline Script: %PipelineScript% >> "%SchedulerLog%"

REM Activate virtual environment and run pipeline
echo [%date% %time%] Activating virtual environment... >> "%SchedulerLog%"
call "%VenvActivate%"

echo [%date% %time%] Running YouTube pipeline... >> "%SchedulerLog%"
cd /d "%ProjectRoot%"
python "%PipelineScript%" >> "%SchedulerLog%" 2>&1

if %ERRORLEVEL% equ 0 (
    echo [%date% %time%] ^✓ Pipeline completed successfully >> "%SchedulerLog%"
) else (
    echo [%date% %time%] ^✗ ERROR: Pipeline failed with exit code %ERRORLEVEL% >> "%SchedulerLog%"
)

echo [%date% %time%] ================================ >> "%SchedulerLog%"

endlocal
