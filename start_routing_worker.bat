@echo off
echo ========================================================
echo Menjalankan Celery Worker untuk Routing (Fanout & Topic)
echo ========================================================

start "Worker: Routing & Logs" /D "%~dp0" cmd /k ".venv\Scripts\python.exe -m celery -A celery_config worker --loglevel=info -P solo -Q fanout_queue_1,fanout_queue_2,error_logs_queue,all_logs_queue"

echo.
echo Worker routing telah dijalankan di jendela cmd baru.
echo Anda dapat menjalankan producer routing sekarang dengan:
echo   .venv\Scripts\activate
echo   python producer_routing.py
echo.
pause
