@echo off
echo Setting up School Year Management Task...

REM Get the current directory
set "SCRIPT_DIR=%~dp0"

REM Create the task
schtasks /create /tn "SchoolYearManagement" /tr "python %SCRIPT_DIR%manage.py manage_school_year" /sc DAILY /st 00:00 /ru SYSTEM

echo Task created successfully!
echo The school year management will run daily at midnight.
echo You can modify the schedule using Windows Task Scheduler.
pause 