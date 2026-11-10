@echo off
echo ==============================================
echo Menjalankan 3 Celery Worker di Jendela Terpisah
echo ==============================================

start "Worker: data_processing" /D "%~dp0" cmd /k ".venv\Scripts\python.exe -m celery -A celery_config worker --loglevel=info -P solo -n worker_dp@%%h -Q data_processing"

start "Worker: report_generation" /D "%~dp0" cmd /k ".venv\Scripts\python.exe -m celery -A celery_config worker --loglevel=info -P solo -n worker_rg@%%h -Q report_generation"

start "Worker: default" /D "%~dp0" cmd /k ".venv\Scripts\python.exe -m celery -A celery_config worker --loglevel=info -P solo -n worker_def@%%h -Q default"

echo.
echo Ketiga worker telah dijalankan di jendela cmd masing-masing.
echo Anda dapat menjalankan producer sekarang dengan:
echo   .venv\Scripts\activate
echo   python producer.py
echo.
pause
