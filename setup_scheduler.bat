@echo off
echo ===================================================
echo  ZERO-CONTEST STREAK BOT - DAILY SCHEDULER SETUP
echo ===================================================
echo.

set BOT_DIR=D:\daily bot
set TASK_NAME=ZeroContestStreakBot

echo Creating Daily Task '%TASK_NAME%' in Windows Task Scheduler...
schtasks /create /tn "%TASK_NAME%" /tr "python \"%BOT_DIR%\zero_contest_streak_bot.py\" --headless" /sc daily /st 09:00 /f /ru "%USERNAME%"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [SUCCESS] Daily task '%TASK_NAME%' scheduled to run every day at 09:00 AM!
    echo To view or modify the task, open Windows Task Scheduler (taskschd.msc).
) else (
    echo.
    echo [NOTE] Task creation returned exit code %ERRORLEVEL%. Run script as Administrator if needed.
)
echo.
pause
