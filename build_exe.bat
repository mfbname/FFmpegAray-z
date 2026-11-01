@echo off
chcp 65001 >nul
echo [1/2] PyInstaller kuruluyor / Installing PyInstaller...
python -m pip install --upgrade pyinstaller
echo [2/2] EXE olusturuluyor / Building EXE...
python -m PyInstaller --onefile --windowed --clean --name FFmpegArayuz ffmpeg_arayuz.py
echo.
echo Hazir / Done:  dist\FFmpegArayuz.exe
echo ffmpeg.exe ve ffprobe.exe dosyalarini FFmpegArayuz.exe ile ayni klasore koyabilirsiniz.
pause
