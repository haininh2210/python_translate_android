@echo off
REM Kiểm tra Python
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Python chưa được cài đặt. Đang tải Python...
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.6/python-3.11.6-amd64.exe' -OutFile '%TEMP%\\python-installer.exe'"
    start /wait %TEMP%\python-installer.exe /quiet InstallAllUsers=1 PrependPath=1
    del %TEMP%\python-installer.exe
) else (
    echo Python đã được cài đặt.
)

REM Cài pip nếu chưa có
python -m ensurepip

REM Cài các thư viện cần thiết
python -m pip install --upgrade pip
python -m pip install deep-translator beautifulsoup4

echo Da cai dat xong deep-translator va beautifulsoup4.
pause