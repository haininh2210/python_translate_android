# Kiểm tra Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python chưa được cài đặt. Đang tải Python..."
    Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.11.6/python-3.11.6-amd64.exe" -OutFile "$env:TEMP\\python-installer.exe"
    Start-Process -Wait -FilePath "$env:TEMP\\python-installer.exe" -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1"
    Remove-Item "$env:TEMP\\python-installer.exe"
    Write-Host "Đã cài đặt Python."
} else {
    Write-Host "Python đã được cài đặt."
}

# Cài pip nếu chưa có
python -m ensurepip

# Cài đặt các thư viện cần thiết
pip install --upgrade pip
pip install deep-translator beautifulsoup4

Write-Host "Đã cài đặt xong deep-translator và beautifulsoup4."