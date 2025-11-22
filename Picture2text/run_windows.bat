
@echo off
REM Simple double-clickable launcher for Windows.
REM This runs the system Python to start `ocr2md.py`.

SET script_dir=%~dp0

python "%script_dir%ocr2md.py"

pause
