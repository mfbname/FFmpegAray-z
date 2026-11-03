#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FFmpeg Arayüzü / FFmpeg GUI
===========================
Bilgisayarınızda kurulu ffmpeg / ffprobe için grafik arayüz.
A graphical interface for the ffmpeg / ffprobe installed on your computer.

Çalıştırma / Run:
    python ffmpeg_arayuz.py

Gereksinimler / Requirements:
    - Python 3.8+ (Tkinter dahil / included; Linux: sudo apt install python3-tk)
    - ffmpeg ve ffprobe (PATH içinde, programın yanındaki klasörde ya da
      "Gelişmiş / Advanced" sekmesinde gösterilen yolda)
"""

import json
import os
import queue
import re
import shlex
import shutil
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# --------------------------------------------------------------------------
# Çeviriler / Translations   (anahtar: (Türkçe, English))
# --------------------------------------------------------------------------

S = {
    "title": ("FFmpeg Arayüzü", "FFmpeg GUI"),
    "lang": ("Dil / Language:", "Dil / Language:"),
    "theme": ("Tema:", "Theme:"),
    "tok_theme_auto": ("Otomatik (sistem)", "Auto (system)"),
    "tok_theme_light": ("Açık", "Light"),
    "tok_theme_dark": ("Koyu", "Dark"),
    "file": ("Video dosyası:", "Video file:"),
    "browse": ("Gözat…", "Browse…"),
    "info_frame": ("Video Bilgileri", "Video Information"),
    "col_prop": ("Özellik", "Property"),
    "col_val": ("Değer", "Value"),
    "settings_frame": ("Dönüştürme Ayarları", "Conversion Settings"),
    # sekmeler
    "tab_video": ("Video", "Video"),
    "tab_image": ("Görüntü", "Image"),
    "tab_audio": ("Ses", "Audio"),
    "tab_time": ("Süre & Hız", "Time & Speed"),
    "tab_gpu": ("GPU", "GPU"),
    "tab_adv": ("Gelişmiş", "Advanced"),
    # ortak değerler
    "tok_orig": ("Orijinal", "Original"),
    "tok_default": ("Varsayılan", "Default"),
    "tok_custom": ("Özel", "Custom"),
    "tok_crf": ("Kalite (CRF)", "Quality (CRF)"),
    "tok_abr": ("Bit hızı (ABR)", "Bitrate (ABR)"),
    "tok_rot_none": ("Yok", "None"),
    "tok_rot_cw": ("90° saat yönünde", "90° clockwise"),
    "tok_rot_ccw": ("90° saat yönünün tersine", "90° counter-clockwise"),
    "tok_rot_180": ("180°", "180°"),
    "tok_sub_remove": ("Kaldır", "Remove"),
    "tok_sub_copy": ("Kopyala (tüm altyazılar)", "Copy (all subtitles)"),
    "tok_off": ("Kapalı (yalnızca CPU)", "Off (CPU only)"),
    "tok_auto": ("Otomatik (çalışan GPU'yu kullan)", "Auto (use a working GPU)"),
    "v_copy": ("Orijinal (kopyala, yeniden kodlama yok)", "Original (copy, no re-encode)"),
    "v_none": ("Videoyu kaldır", "Remove video"),
    "a_copy": ("Orijinal (kopyala)", "Original (copy)"),
    "a_none": ("Sesi kaldır", "Remove audio"),
    # video sekmesi
    "container": ("Konteyner (çıktı biçimi)", "Container (output format)"),
    "vcodec": ("Video codec", "Video codec"),
    "rate_mode": ("Kodlama modu", "Encoding mode"),
    "quality": ("Kalite değeri", "Quality value"),
    "quality_hint": ("düşük = daha iyi kalite, büyük dosya (x264/x265: 18–28)",
                     "lower = better quality, bigger file (x264/x265: 18–28)"),
    "vbitrate": ("Video bit hızı", "Video bitrate"),
    "vbitrate_hint": ("örn. 2500k veya 5M", "e.g. 2500k or 5M"),
    "maxrate": ("Maks. bit hızı", "Max bitrate"),
    "bufsize": ("Tampon boyutu", "Buffer size"),
    "optional": ("isteğe bağlı", "optional"),
    "preset": ("Hız / Preset", "Speed / Preset"),
    "preset_hint": ("yavaş = daha küçük dosya", "slower = smaller file"),
    "tune": ("Tune", "Tune"),
    "profile": ("Profil", "Profile"),
    "pix_fmt": ("Piksel formatı", "Pixel format"),
    "copy_hint": ("Kopyalama modunda video yeniden kodlanmaz; çözünürlük, fps ve görüntü filtreleri uygulanmaz.",
                  "In copy mode the video is not re-encoded; resolution, fps and image filters are not applied."),
    "none_hint": ("Çıktıda video akışı olmayacak.", "The output will have no video stream."),
    # görüntü sekmesi
    "resolution": ("Çözünürlük", "Resolution"),
    "res_hint": ("yükseklik esas alınır, en-boy oranı korunur", "height-based, aspect ratio is kept"),
    "custom_res": ("Özel (G x Y)", "Custom (W x H)"),
    "auto_blank": ("  (boş = otomatik)", "  (blank = auto)"),
    "algo": ("Ölçekleme algoritması", "Scaling algorithm"),
    "fps": ("Kare hızı (fps)", "Frame rate (fps)"),
    "aspect": ("En-boy oranı", "Aspect ratio"),
    "crop": ("Kırpma (crop)", "Crop"),
    "crop_hint": ("G ve Y doluysa uygulanır", "applied when W and H are filled"),
    "cw": ("G:", "W:"), "ch": ("Yük.:", "H:"), "cx": ("X:", "X:"), "cy": ("Y konum:", "Y pos:"),
    "rotate": ("Döndür", "Rotate"),
    "flip": ("Çevirme", "Flip"),
    "hflip": ("Yatay çevir", "Flip horizontal"),
    "vflip": ("Dikey çevir", "Flip vertical"),
    "brightness": ("Parlaklık", "Brightness"),
    "brightness_hint": ("-1 … 1 (varsayılan 0)", "-1 … 1 (default 0)"),
    "contrast": ("Kontrast", "Contrast"),
    "saturation": ("Doygunluk", "Saturation"),
    "saturation_hint": ("0 = siyah-beyaz, varsayılan 1", "0 = black & white, default 1"),
    "gamma": ("Gamma", "Gamma"),
    "default1": ("varsayılan 1", "default 1"),
    "effects": ("Efektler", "Effects"),
    "deint": ("Deinterlace", "Deinterlace"),
    "denoise": ("Gürültü azalt", "Denoise"),
    "sharpen": ("Keskinleştir", "Sharpen"),
    "gray": ("Siyah-beyaz", "Black & white"),
    # ses sekmesi
    "acodec": ("Ses codec", "Audio codec"),
    "abitrate": ("Ses bit hızı", "Audio bitrate"),
    "abitrate_hint": ("kayıpsız codec'lerde kullanılmaz", "not used with lossless codecs"),
    "arate": ("Örnekleme hızı (Hz)", "Sample rate (Hz)"),
    "achan": ("Kanal sayısı", "Channels"),
    "volume": ("Ses seviyesi (dB)", "Volume (dB)"),
    "volume_hint": ("0 = değişiklik yok", "0 = no change"),
    "normalize": ("Normalleştirme", "Normalization"),
    "loudnorm": ("Sesi normalleştir (loudnorm)", "Normalize audio (loudnorm)"),
    "audio_note": ("Not: 'Orijinal (kopyala)' seçiliyken ses filtreleri uygulanmaz.",
                   "Note: audio filters are not applied when 'Original (copy)' is selected."),
    # süre sekmesi
    "start": ("Başlangıç", "Start"),
    "start_hint": ("SS:DD:ss veya saniye (boş = baştan)", "HH:MM:SS or seconds (blank = from start)"),
    "end": ("Bitiş", "End"),
    "end_hint": ("boş = sonuna kadar", "blank = until the end"),
    "speed": ("Oynatma hızı", "Playback speed"),
    "speed_hint": ("1 = normal, 2 = iki kat hızlı", "1 = normal, 2 = twice as fast"),
    # GPU sekmesi
    "gpu_mode": ("GPU hızlandırma", "GPU acceleration"),
    "gpu_decode": ("Videoyu GPU ile çöz (decode)", "Decode video on the GPU"),
    "gpu_decode_row": ("Çözme", "Decoding"),
    "gpu_fallback": ("GPU hata verirse otomatik olarak CPU ile tekrar dene",
                     "If the GPU fails, automatically retry with the CPU"),
    "gpu_fallback_row": ("Güvenlik", "Safety"),
    "gpu_detect": ("GPU'yu algıla / test et", "Detect / test GPU"),
    "gpu_unknown": ("Henüz test edilmedi.", "Not tested yet."),
    "gpu_testing": ("GPU'lar test ediliyor…", "Testing GPUs…"),
    "gpu_ok": ("kullanılabilir", "available"),
    "gpu_no": ("kullanılamıyor", "not available"),
    "gpu_auto_pick": ("Otomatik modda kullanılacak: {0}", "Auto mode will use: {0}"),
    "gpu_auto_none": ("Otomatik modda kullanılabilir GPU yok, CPU kullanılacak.",
                      "No usable GPU for Auto mode, the CPU will be used."),
    "gpu_info": (
        "GPU ile kodlama genellikle CPU'dan 3–10 kat hızlıdır. Dezavantajı: aynı kalitede dosya biraz daha "
        "büyük olabilir. Seçili codec H.264, H.265 veya AV1 ise uygun GPU kodlayıcısına otomatik çevrilir "
        "(örn. libx264 → h264_nvenc). VP9, ProRes gibi codec'ler CPU'da kalır.",
        "GPU encoding is usually 3–10x faster than the CPU. Downside: at the same quality the file can be "
        "somewhat larger. If the selected codec is H.264, H.265 or AV1 it is switched to the matching GPU "
        "encoder automatically (e.g. libx264 → h264_nvenc). Codecs like VP9 or ProRes stay on the CPU."),
    "gpu_req": (
        "Gereksinimler: güncel ekran kartı sürücüsü ve GPU kodlayıcılarını içeren bir ffmpeg derlemesi "
        "(örn. gyan.dev 'full' veya BtbN derlemeleri).",
        "Requirements: an up-to-date graphics driver and an ffmpeg build that includes GPU encoders "
        "(e.g. the gyan.dev 'full' or BtbN builds)."),
    "eff_cpu": ("Kodlayıcı: {0} (CPU)", "Encoder: {0} (CPU)"),
    "eff_gpu": ("Kodlayıcı: {0} → GPU ({1})", "Encoder: {0} → GPU ({1})"),
    "eff_dec": (" + GPU ile çözme", " + GPU decoding"),
    "eff_none": ("Video yeniden kodlanmıyor.", "Video is not re-encoded."),
    # gelişmiş sekme
    "subs": ("Altyazılar", "Subtitles"),
    "options": ("Seçenekler", "Options"),
    "map_all": ("Tüm akışları dahil et (-map 0)", "Include all streams (-map 0)"),
    "strip_meta": ("Metadata'yı sil", "Strip metadata"),
    "faststart": ("Web için hızlı başlatma (faststart, mp4/mov/m4a)",
                  "Fast start for web (faststart, mp4/mov/m4a)"),
    "threads": ("İş parçacığı sayısı", "Thread count"),
    "threads_hint": ("0 = otomatik", "0 = auto"),
    "extra": ("Ek ffmpeg parametreleri", "Extra ffmpeg arguments"),
    "ffmpeg_path": ("ffmpeg yolu", "ffmpeg path"),
    "ffprobe_path": ("ffprobe yolu", "ffprobe path"),
    # alt kısım
    "out_file": ("Çıktı dosyası:", "Output file:"),
    "save_as": ("Farklı kaydet…", "Save as…"),
    "cmd_frame": ("Oluşturulan ffmpeg komutu", "Generated ffmpeg command"),
    "run": ("▶  Dönüştür", "▶  Convert"),
    "cancel": ("■  İptal", "■  Cancel"),
    "copy_cmd": ("Komutu kopyala", "Copy command"),
    "open_dir": ("Çıktı klasörünü aç", "Open output folder"),
    # durum / mesajlar
    "ready": ("Hazır", "Ready"),
    "starting": ("Başlatılıyor…", "Starting…"),
    "cmd_copied": ("Komut panoya kopyalandı.", "Command copied to clipboard."),
    "cancelled": ("İptal edildi.", "Cancelled."),
    "done": ("✔ Tamamlandı.", "✔ Done."),
    "failed": ("Hata (çıkış kodu {0}). Günlüğe bakın.", "Error (exit code {0}). See the log."),
    "retry_cpu": ("GPU ile başarısız oldu, CPU ile yeniden deneniyor…", "GPU failed, retrying with the CPU…"),
    "pct": ("%{0:.1f}", "{0:.1f}%"),
    "speed_x": ("  |  hız {0:.2f}x", "  |  speed {0:.2f}x"),
    "left": ("  |  kalan ~{0}", "  |  ~{0} left"),
    "err": ("Hata", "Error"),
    "info": ("Bilgi", "Info"),
    "setting_err": ("Ayar hatası", "Setting error"),
    "pick_video_first": ("Önce bir video dosyası seçin.", "Select a video file first."),
    "pick_video_prev": ("Önce bir video seçin.", "Select a video first."),
    "ffmpeg_missing_t": ("ffmpeg bulunamadı", "ffmpeg not found"),
    "ffmpeg_missing": ("ffmpeg bulunamadı. 'Gelişmiş' sekmesinden yolunu belirtin veya ffmpeg'i programın yanına koyun.",
                       "ffmpeg was not found. Set its path in the 'Advanced' tab or put ffmpeg next to this program."),
    "ffprobe_missing": ("ffprobe çalıştırılamadı. 'Gelişmiş' sekmesinden yolunu belirtin.",
                        "ffprobe could not be run. Set its path in the 'Advanced' tab."),
    "ffprobe_err": ("ffprobe hatası", "ffprobe error"),
    "ffprobe_unread": ("Dosya okunamadı.", "The file could not be read."),
    "ffprobe_parse": ("ffprobe çıktısı çözümlenemedi.", "Could not parse the ffprobe output."),
    "file_nf": ("Dosya bulunamadı.", "File not found."),
    "pick_tool": ("Çalıştırılabilir dosyayı seçin", "Select the executable"),
    "pick_media": ("Video veya ses dosyası seç", "Select a video or audio file"),
    "media_files": ("Medya dosyaları", "Media files"),
    "all_files": ("Tüm dosyalar", "All files"),
    "out_dialog": ("Çıktı dosyası", "Output file"),
    "exists_t": ("Dosya var", "File exists"),
    "exists": ("'{0}' zaten var. Üzerine yazılsın mı?", "'{0}' already exists. Overwrite it?"),
    "e_noout": ("Çıktı dosyası belirtilmedi.", "No output file specified."),
    "e_same": ("Çıktı dosyası, girdi dosyasıyla aynı olamaz.", "The output file cannot be the same as the input."),
    "e_time": ("Geçersiz zaman değeri: '{0}' (örnek: 00:01:30 veya 90)",
               "Invalid time value: '{0}' (example: 00:01:30 or 90)"),
    "e_endstart": ("Bitiş zamanı, başlangıçtan büyük olmalı.", "End time must be greater than start time."),
    "e_num": ("'{0}' için geçerli bir sayı girin.", "Enter a valid number for '{0}'."),
    "e_speed": ("Oynatma hızı 0'dan büyük olmalı.", "Playback speed must be greater than 0."),
    "e_extra": ("Ek parametreler çözümlenemedi: {0}", "Could not parse extra arguments: {0}"),
    # bilgi paneli
    "g_general": ("Genel", "General"),
    "g_video": ("Video #{0}", "Video #{0}"),
    "g_audio": ("Ses #{0}", "Audio #{0}"),
    "g_sub": ("Altyazı #{0}", "Subtitle #{0}"),
    "g_other": ("{0} akışı", "{0} stream"),
    "i_filename": ("Dosya adı", "File name"),
    "i_size": ("Boyut", "Size"),
    "i_duration": ("Süre", "Duration"),
    "i_container": ("Konteyner", "Container"),
    "i_total_br": ("Toplam bit hızı", "Overall bitrate"),
    "i_nstreams": ("Akış sayısı", "Stream count"),
    "i_title": ("Başlık", "Title"),
    "i_codec": ("Codec", "Codec"),
    "i_profile": ("Profil", "Profile"),
    "i_res": ("Çözünürlük", "Resolution"),
    "i_dar": ("En-boy oranı", "Aspect ratio"),
    "i_fps_avg": ("Kare hızı (ort.)", "Frame rate (avg)"),
    "i_fps_base": ("Kare hızı (temel)", "Frame rate (base)"),
    "i_bitrate": ("Bit hızı", "Bitrate"),
    "i_pixfmt": ("Piksel formatı", "Pixel format"),
    "i_bitdepth": ("Bit derinliği", "Bit depth"),
    "i_cspace": ("Renk uzayı", "Color space"),
    "i_crange": ("Renk aralığı", "Color range"),
    "i_ctrans": ("Renk transferi", "Color transfer"),
    "i_scan": ("Tarama", "Scan type"),
    "i_frames": ("Kare sayısı", "Frame count"),
    "i_rotation": ("Döndürme", "Rotation"),
    "i_lang": ("Dil", "Language"),
    "i_srate": ("Örnekleme hızı", "Sample rate"),
    "i_channels": ("Kanal", "Channels"),
    "i_sfmt": ("Örnek formatı", "Sample format"),
}

COMMON_TOKENS = {"orig": "tok_orig", "default": "tok_default", "custom": "tok_custom"}

# --------------------------------------------------------------------------
# Sabitler
# --------------------------------------------------------------------------

VIDEO_CODECS = [
    ("libx264", "H.264 (libx264)"),
    ("libx265", "H.265 / HEVC (libx265)"),
    ("libvpx-vp9", "VP9 (libvpx-vp9)"),
    ("libvpx", "VP8 (libvpx)"),
    ("libsvtav1", "AV1 (libsvtav1)"),
    ("libaom-av1", "AV1 (libaom-av1)"),
    ("mpeg4", "MPEG-4 (mpeg4)"),
    ("prores_ks", "ProRes (prores_ks)"),
    ("copy", None),
    ("none", None),
]
AUDIO_CODECS = [
    ("aac", "AAC (aac)"),
    ("libmp3lame", "MP3 (libmp3lame)"),
    ("libopus", "Opus (libopus)"),
    ("libvorbis", "Vorbis (libvorbis)"),
    ("ac3", "AC3 (ac3)"),
    ("flac", "FLAC (flac)"),
    ("pcm_s16le", "WAV / PCM 16-bit (pcm_s16le)"),
    ("copy", None),
    ("none", None),
]
LOSSLESS_AUDIO = {"flac", "pcm_s16le", "copy", "none"}

CONTAINERS = ["mp4", "mkv", "mov", "webm", "avi", "flv", "ts", "gif",
              "mp3", "m4a", "aac", "ogg", "opus", "wav", "flac"]
AUDIO_ONLY = {"mp3", "m4a", "aac", "ogg", "opus", "wav", "flac"}

# Konteyner değişince önerilen codec'ler: ext -> (video, ses)
CONTAINER_DEFAULTS = {
    "mp4": ("libx264", "aac"), "mkv": ("libx264", "aac"), "mov": ("libx264", "aac"),
    "webm": ("libvpx-vp9", "libopus"),
    "mp3": (None, "libmp3lame"), "m4a": (None, "aac"), "aac": (None, "aac"),
    "ogg": (None, "libvorbis"), "opus": (None, "libopus"),
    "wav": (None, "pcm_s16le"), "flac": (None, "flac"),
}

X264_PRESETS = ["ultrafast", "superfast", "veryfast", "faster", "fast",
                "medium", "slow", "slower", "veryslow"]
PRESETS = {
    "libx264": ("-preset", X264_PRESETS),
    "libx265": ("-preset", X264_PRESETS),
    "libsvtav1": ("-preset", [str(i) for i in range(0, 14)]),
    "libvpx-vp9": ("-cpu-used", [str(i) for i in range(0, 9)]),
    "libvpx": ("-cpu-used", [str(i) for i in range(0, 9)]),
    "libaom-av1": ("-cpu-used", [str(i) for i in range(0, 9)]),
    # GPU kodlayıcıları (otomatik eşleme için)
    "h264_nvenc": ("-preset", [f"p{i}" for i in range(1, 8)]),
    "hevc_nvenc": ("-preset", [f"p{i}" for i in range(1, 8)]),
    "av1_nvenc": ("-preset", [f"p{i}" for i in range(1, 8)]),
    "h264_qsv": ("-preset", X264_PRESETS[2:]),
    "hevc_qsv": ("-preset", X264_PRESETS[2:]),
    "av1_qsv": ("-preset", X264_PRESETS[2:]),
    "h264_amf": ("-quality", ["speed", "balanced", "quality"]),
    "hevc_amf": ("-quality", ["speed", "balanced", "quality"]),
    "av1_amf": ("-quality", ["speed", "balanced", "quality"]),
}
TUNES = {
    "libx264": ["film", "animation", "grain", "stillimage", "fastdecode", "zerolatency"],
    "libx265": ["psnr", "ssim", "grain", "fastdecode", "zerolatency", "animation"],
}
PRORES = {"proxy": "0", "lt": "1", "standard": "2", "hq": "3", "4444": "4", "4444xq": "5"}
PROFILES = {
    "libx264": ["baseline", "main", "high"],
    "libx265": ["main", "main10"],
    "h264_nvenc": ["baseline", "main", "high"],
    "hevc_nvenc": ["main", "main10"],
    "prores_ks": list(PRORES.keys()),
}

PIX_FMTS = ["orig", "yuv420p", "yuv422p", "yuv444p", "yuv420p10le",
            "yuv422p10le", "nv12", "rgb24", "gray"]
RES_PRESETS = ["orig", "2160p", "1440p", "1080p", "720p", "480p", "360p", "240p", "custom"]
FPS_PRESETS = ["orig", "60", "50", "30", "29.97", "25", "24", "23.976", "15", "12", "10"]
ASPECTS = ["orig", "16:9", "4:3", "21:9", "1:1", "9:16"]
SCALE_ALGOS = ["default", "bicubic", "lanczos", "bilinear", "neighbor", "spline"]
ROTATIONS = ["none", "cw", "ccw", "180"]
ROT_TOKENS = {"none": "tok_rot_none", "cw": "tok_rot_cw", "ccw": "tok_rot_ccw", "180": "tok_rot_180"}
SUB_OPTIONS = ["default", "remove", "copy"]
SUB_TOKENS = {"default": "tok_default", "remove": "tok_sub_remove", "copy": "tok_sub_copy"}
AUDIO_BITRATES = ["default", "64k", "96k", "128k", "160k", "192k", "256k", "320k"]
SAMPLE_RATES = ["orig", "8000", "16000", "22050", "32000", "44100", "48000", "96000"]
CHANNELS = ["orig", "1", "2", "6"]
CHANNEL_LABELS = {"1": "1 (mono)", "2": "2 (stereo)", "6": "6 (5.1)"}

PROGRESS_KEYS = {"frame", "fps", "bitrate", "total_size", "out_time_us", "out_time_ms",
                 "out_time", "dup_frames", "drop_frames", "speed", "progress"}

# ---- GPU ------------------------------------------------------------------
VAAPI_DEVICE = "/dev/dri/renderD128"
GPU_NAMES = {
    "nvidia": "NVIDIA (NVENC / CUDA)",
    "qsv": "Intel (Quick Sync)",
    "amf": "AMD (AMF)",
    "vt": "Apple (VideoToolbox)",
    "vaapi": "VAAPI (Linux)",
}
GPU_ENCODERS = {
    "nvidia": {"h264": "h264_nvenc", "hevc": "hevc_nvenc", "av1": "av1_nvenc"},
    "qsv": {"h264": "h264_qsv", "hevc": "hevc_qsv", "av1": "av1_qsv"},
    "amf": {"h264": "h264_amf", "hevc": "hevc_amf", "av1": "av1_amf"},
    "vt": {"h264": "h264_videotoolbox", "hevc": "hevc_videotoolbox"},
    "vaapi": {"h264": "h264_vaapi", "hevc": "hevc_vaapi", "av1": "av1_vaapi"},
}
CODEC_FAMILY = {"libx264": "h264", "libx265": "hevc", "libsvtav1": "av1", "libaom-av1": "av1"}
GPU_MODES = ["off", "auto", "nvidia", "qsv", "amf", "vt", "vaapi"]


# --------------------------------------------------------------------------
# Yardımcı fonksiyonlar
# --------------------------------------------------------------------------

def app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def find_tool(name):
    """Önce programın yanında, sonra PATH içinde ara."""
    exe = name + (".exe" if os.name == "nt" else "")
    for d in (app_dir(), os.path.join(app_dir(), "ffmpeg", "bin"), getattr(sys, "_MEIPASS", None)):
        if d:
            c = os.path.join(d, exe)
            if os.path.isfile(c):
                return c
    return shutil.which(name) or name


def fmt_size(n):
    try:
        n = float(n)
    except (TypeError, ValueError):
        return None
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.2f} {unit}"
        n /= 1024


def fmt_duration(sec):
    try:
        sec = float(sec)
    except (TypeError, ValueError):
        return None
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = sec - h * 3600 - m * 60
    return f"{h:02d}:{m:02d}:{s:05.2f}"


def fmt_bitrate(bps):
    try:
        bps = float(bps)
    except (TypeError, ValueError):
        return None
    if bps >= 1_000_000:
        return f"{bps / 1_000_000:.2f} Mb/s"
    return f"{bps / 1000:.0f} kb/s"


def frac_to_float(s):
    try:
        if "/" in str(s):
            a, b = str(s).split("/")
            return float(a) / float(b) if float(b) else 0.0
        return float(s)
    except (TypeError, ValueError):
        return 0.0


def norm_rate(s):
    """'2500' -> '2500k'; '5M' -> '5M'."""
    s = s.strip()
    return s + "k" if s.isdigit() else s


def atempo_chain(speed):
    filters = []
    while speed > 2.0:
        filters.append("atempo=2.0")
        speed /= 2.0
    while speed < 0.5:
        filters.append("atempo=0.5")
        speed /= 0.5
    filters.append(f"atempo={speed:.4f}")
    return filters


def quality_args(codec, q):
    if codec in ("libx264", "libx265", "libsvtav1"):
        return ["-crf", q]
    if codec in ("libvpx-vp9", "libvpx", "libaom-av1"):
        return ["-crf", q, "-b:v", "0"]
    if codec.endswith("_nvenc"):
        return ["-rc", "vbr", "-cq", q, "-b:v", "0"]
    if codec.endswith("_qsv"):
        return ["-global_quality", q]
    if codec.endswith("_amf"):
        return ["-rc", "cqp", "-qp_i", q, "-qp_p", q, "-qp_b", q]
    if codec.endswith("_vaapi"):
        return ["-qp", q]
    if codec.endswith("_videotoolbox"):
        # VideoToolbox: 1-100, yüksek = daha iyi. CRF benzeri ölçeği tersine çevir.
        return ["-q:v", str(max(1, min(100, round(100 - float(q) * 2))))]
    if codec == "mpeg4":
        return ["-q:v", q]
    return []


def gpu_preset(preset, enc):
    """x264 preset adını GPU kodlayıcısının ölçeğine çevir."""
    order = X264_PRESETS
    if preset not in order:
        return None
    i = order.index(preset)
    if enc.endswith("_nvenc"):
        return ["p1", "p1", "p2", "p3", "p4", "p5", "p6", "p7", "p7"][i]
    if enc.endswith("_qsv"):
        return preset if preset in X264_PRESETS[2:] else "veryfast"
    if enc.endswith("_amf"):
        return "speed" if i <= 3 else ("balanced" if i <= 5 else "quality")
    return None


def hwaccel_args(backend):
    if backend == "nvidia":
        return ["-hwaccel", "cuda"]
    if backend == "qsv":
        return ["-hwaccel", "qsv"]
    if backend == "amf":
        return ["-hwaccel", "d3d11va"] if os.name == "nt" else []
    if backend == "vt":
        return ["-hwaccel", "videotoolbox"]
    if backend == "vaapi":
        return ["-hwaccel", "vaapi", "-hwaccel_device", VAAPI_DEVICE]
    return []


def gpu_order():
    if os.name == "nt":
        return ["nvidia", "amf", "qsv"]
    if sys.platform == "darwin":
        return ["vt"]
    return ["nvidia", "vaapi", "qsv"]


def gpu_test_cmd(ff, backend):
    base = [ff, "-hide_banner", "-loglevel", "error", "-y"]
    src = ["-f", "lavfi", "-i", "color=c=black:s=640x360:r=30", "-frames:v", "10"]
    if backend == "vaapi":
        return base + ["-vaapi_device", VAAPI_DEVICE] + src + [
            "-vf", "format=nv12,hwupload", "-c:v", "h264_vaapi", "-f", "null", "-"]
    return base + src + ["-c:v", GPU_ENCODERS[backend]["h264"], "-f", "null", "-"]


def cmd_to_str(cmd):
    if os.name == "nt":
        return subprocess.list2cmdline(cmd)
    return " ".join(shlex.quote(c) for c in cmd)


def no_window_flags():
    return subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0


THEME_TOKENS = {"auto": "tok_theme_auto", "light": "tok_theme_light", "dark": "tok_theme_dark"}

THEMES = {
    "light": dict(bg="#f0f0f0", fg="#1a1a1a", field="#ffffff", btn="#e1e1e1", btn_hover="#d2d2d2",
                  border="#b0b0b0", sel="#3b82f6", sel_fg="#ffffff", dis="#9a9a9a", hint="#6b7280",
                  accent="#2563eb", warn="#b45309", trough="#dcdcdc", text_bg="#ffffff", tab="#e6e6e6"),
    "dark": dict(bg="#1f2023", fg="#e8e8e8", field="#2b2d31", btn="#35383d", btn_hover="#444850",
                 border="#4a4d52", sel="#2f6fdb", sel_fg="#ffffff", dis="#767b82", hint="#9aa0a8",
                 accent="#6cb0ff", warn="#f5a524", trough="#26282b", text_bg="#18191b", tab="#2a2c30"),
}


def config_path():
    if os.name == "nt":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        return os.path.join(base, "FFmpegArayuz", "config.json")
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
    return os.path.join(base, "ffmpeg_arayuz", "config.json")


def load_config():
    try:
        with open(config_path(), encoding="utf-8") as f:
            d = json.load(f)
            return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def save_config(update):
    try:
        cfg = load_config()
        cfg.update(update)
        path = config_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass


def _run_quiet(cmd):
    try:
        r = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True,
                           timeout=2, creationflags=no_window_flags())
        return (r.stdout or "").strip().lower()
    except Exception:
        return ""


def detect_system_theme():
    """İşletim sisteminin açık/koyu temasını döndürür: 'light' veya 'dark'."""
    try:
        if os.name == "nt":
            import winreg
            key = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key) as k:
                val, _ = winreg.QueryValueEx(k, "AppsUseLightTheme")
            return "light" if val else "dark"
        if sys.platform == "darwin":
            return "dark" if "dark" in _run_quiet(["defaults", "read", "-g", "AppleInterfaceStyle"]) else "light"
        # Linux (GNOME / GTK / KDE)
        scheme = _run_quiet(["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"])
        if "dark" in scheme:
            return "dark"
        if "light" in scheme:
            return "light"
        if "dark" in _run_quiet(["gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"]):
            return "dark"
        if "dark" in os.environ.get("GTK_THEME", "").lower():
            return "dark"
        kde = os.path.join(os.path.expanduser("~"), ".config", "kdeglobals")
        if os.path.isfile(kde):
            with open(kde, encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if line.strip().lower().startswith("colorscheme="):
                        return "dark" if "dark" in line.lower() else "light"
    except Exception:
        pass
    return "light"


class ValidationError(ValueError):
    """Kullanıcıya gösterilecek (zaten çevrilmiş) ayar hatası."""


# --------------------------------------------------------------------------
# Dil bağımsız değer saklayan combobox
# --------------------------------------------------------------------------

class CodeCombo(ttk.Combobox):
    """Ekranda çevrilmiş etiketi gösterir, değişkende dil bağımsız 'kod' tutar."""

    def __init__(self, parent, app, key, codes, labeler=None, editable=False,
                 width=30, on_change=None):
        super().__init__(parent, width=width, state="normal" if editable else "readonly")
        self.app = app
        self.var = app.vars[key]
        self.labeler = labeler or app.label
        self.editable = editable
        self.on_change = on_change
        self.set_codes(codes)
        self.bind("<<ComboboxSelected>>", self._on_select)
        if editable:
            self.bind("<KeyRelease>", self._on_text)
            self.bind("<FocusOut>", self._on_text)
            self.bind("<Return>", self._on_text)
        self._tid = self.var.trace_add("write", lambda *a: self._sync())
        self.bind("<Destroy>", self._on_destroy)
        self._sync()

    def set_codes(self, codes):
        self.codes = list(codes)
        self.configure(values=[self.labeler(c) for c in self.codes])
        self._sync()

    def _sync(self):
        try:
            label = self.labeler(self.var.get())
            if self.get() != label:
                self.set(label)
        except tk.TclError:
            pass

    def _on_select(self, _e=None):
        idx = self.current()
        if 0 <= idx < len(self.codes):
            self.var.set(self.codes[idx])
        if self.on_change:
            self.on_change()

    def _on_text(self, _e=None):
        txt = self.get().strip()
        rev = {self.labeler(c): c for c in self.codes}
        code = rev.get(txt, txt)
        if self.var.get() != code:
            self.var.set(code)

    def _on_destroy(self, e):
        if e.widget is self:
            try:
                self.var.trace_remove("write", self._tid)
            except Exception:
                pass


# --------------------------------------------------------------------------
# Uygulama
# --------------------------------------------------------------------------

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.lang = "tr"                      # her zaman Türkçe başlar
        self.title(self.t("title"))
        self.geometry("1240x940")
        self.minsize(1000, 740)

        self.style = ttk.Style(self)
        self.vars = {}
        self.current_theme = "light"
        self.lang_var = tk.StringVar(value="Türkçe")
        self.status = tk.StringVar()
        self.status_rec = ("ready", ())
        self.eff_var = tk.StringVar()
        self.gpu_status_var = tk.StringVar()

        self.input_path = None
        self.info_data = None
        self.duration = 0.0
        self.proc = None
        self.cancelled = False
        self.running = False
        self.force_cpu = False
        self.gpu_used = False
        self.run_gpu_used = False
        self.enc_info = None
        self.q = queue.Queue()
        self.expected_out = 0.0
        self.log_lines = []
        self._pct = 0.0
        self._cur_time = 0.0
        self._ready = False

        self.gpu_results = None
        self.gpu_auto = "off"
        self.gpu_testing = False

        saved_mode = load_config().get("theme_mode", "auto")
        self.var("theme_mode", saved_mode if saved_mode in ("auto", "light", "dark") else "auto")
        self.var("ffmpeg_path", find_tool("ffmpeg"))
        self.var("ffprobe_path", find_tool("ffprobe"))

        self._build_ui()
        self._ready = True
        self.set_status("ready")
        self.refresh_codec_lists()
        self.update_preview()
        self.start_gpu_detect()
        self.after(100, self._poll)
        self.after(3000, self._theme_tick)

        fp = self.g("ffmpeg_path")
        if not (shutil.which(fp) or os.path.isfile(fp)):
            messagebox.showwarning(self.t("ffmpeg_missing_t"), self.t("ffmpeg_missing"))

    # ------------------------------------------------------- çeviri / değişken
    def t(self, key, *args):
        txt = S[key][0 if self.lang == "tr" else 1]
        return txt.format(*args) if args else txt

    def mk_lab(self, mapping):
        return lambda c: self.t(mapping[c]) if c in mapping else c

    def label(self, code):
        return self.t(COMMON_TOKENS[code]) if code in COMMON_TOKENS else code

    def vlabel(self, code):
        d = dict(VIDEO_CODECS)
        if d.get(code):
            return d[code]
        return self.t({"copy": "v_copy", "none": "v_none"}[code]) if code in ("copy", "none") else code

    def alabel(self, code):
        d = dict(AUDIO_CODECS)
        if d.get(code):
            return d[code]
        return self.t({"copy": "a_copy", "none": "a_none"}[code]) if code in ("copy", "none") else code

    def gpulabel(self, code):
        if code == "off":
            return self.t("tok_off")
        if code == "auto":
            return self.t("tok_auto")
        return GPU_NAMES.get(code, code)

    def var(self, name, default="", kind="s"):
        if name in self.vars:
            return self.vars[name]
        cls = {"s": tk.StringVar, "b": tk.BooleanVar}[kind]
        v = cls(value=default)
        v.trace_add("write", lambda *a: self.update_preview())
        self.vars[name] = v
        return v

    def g(self, key):
        return str(self.vars[key].get()).strip()

    def num(self, key, label_key):
        try:
            return float(self.g(key).replace(",", "."))
        except ValueError:
            raise ValidationError(self.t("e_num", self.t(label_key)))

    def parse_time(self, s):
        s = (s or "").strip()
        if not s:
            return None
        try:
            parts = [float(p) for p in s.split(":")]
        except ValueError:
            raise ValidationError(self.t("e_time", s))
        t = 0.0
        for p in parts:
            t = t * 60 + p
        return t

    def set_status(self, key, *args):
        self.status_rec = (key, args)
        self.status.set(self.t(key, *args))

    def set_status_raw(self, text):
        self.status_rec = ("raw", (text,))
        self.status.set(text)

    # ------------------------------------------------------------------ UI
    def row(self, parent, label, widget, hint=None):
        r = parent.grid_size()[1]
        ttk.Label(parent, text=label).grid(row=r, column=0, sticky="w", padx=(0, 10), pady=3)
        widget.grid(row=r, column=1, sticky="ew", pady=3)
        if hint:
            ttk.Label(parent, text=hint, style="Hint.TLabel").grid(row=r, column=2, sticky="w", padx=8)
        return widget

    def cc(self, parent, key, default, codes, labeler=None, editable=False, width=30, on_change=None):
        self.var(key, default)
        return CodeCombo(parent, self, key, codes, labeler, editable, width, on_change)

    def entry(self, parent, key, default="", width=12):
        return ttk.Entry(parent, textvariable=self.var(key, default), width=width)

    def spin(self, parent, key, lo, hi, inc, default, width=10):
        return ttk.Spinbox(parent, textvariable=self.var(key, str(default)),
                           from_=lo, to=hi, increment=inc, width=width)

    def chk(self, parent, key, text, default=False):
        return ttk.Checkbutton(parent, text=text, variable=self.var(key, default, "b"))

    def tab(self, nb, key):
        f = ttk.Frame(nb, padding=12)
        f.columnconfigure(1, weight=1)
        nb.add(f, text=self.t(key))
        return f

    def _build_ui(self):
        mono = "Consolas" if os.name == "nt" else "monospace"

        top = ttk.Frame(self, padding=(10, 10, 10, 4))
        top.pack(fill="x")
        ttk.Label(top, text=self.t("file")).pack(side="left")
        e = ttk.Entry(top, textvariable=self.var("in_path", ""))
        e.pack(side="left", fill="x", expand=True, padx=8)
        e.bind("<Return>", lambda ev: self.load_file(self.g("in_path")))
        ttk.Button(top, text=self.t("browse"), command=self.browse_input).pack(side="left")
        ttk.Label(top, text=self.t("theme")).pack(side="left", padx=(20, 4))
        self.cc(top, "theme_mode", "auto", ["auto", "light", "dark"], labeler=self.mk_lab(THEME_TOKENS),
                width=16, on_change=self.on_theme_change).pack(side="left")
        ttk.Label(top, text=self.t("lang")).pack(side="left", padx=(14, 4))
        lc = ttk.Combobox(top, textvariable=self.lang_var, values=["Türkçe", "English"],
                          state="readonly", width=9)
        lc.pack(side="left")
        lc.bind("<<ComboboxSelected>>", self.on_lang)

        pw = ttk.PanedWindow(self, orient="horizontal")
        pw.pack(fill="both", expand=True, padx=10, pady=4)

        left = ttk.LabelFrame(pw, text=self.t("info_frame"), padding=6)
        self.tree = ttk.Treeview(left, columns=("value",), show="tree headings", height=20)
        self.tree.heading("#0", text=self.t("col_prop"))
        self.tree.heading("value", text=self.t("col_val"))
        self.tree.column("#0", width=160, stretch=False)
        self.tree.column("value", width=250)
        sb = ttk.Scrollbar(left, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="left", fill="y")
        pw.add(left, weight=1)

        right = ttk.LabelFrame(pw, text=self.t("settings_frame"), padding=6)
        nb = ttk.Notebook(right)
        nb.pack(fill="both", expand=True)
        pw.add(right, weight=2)

        self._build_video_tab(nb)
        self._build_image_tab(nb)
        self._build_audio_tab(nb)
        self._build_time_tab(nb)
        self._build_gpu_tab(nb)
        self._build_advanced_tab(nb)

        bottom = ttk.Frame(self, padding=(10, 4, 10, 10))
        bottom.pack(fill="x")

        orow = ttk.Frame(bottom)
        orow.pack(fill="x", pady=2)
        ttk.Label(orow, text=self.t("out_file")).pack(side="left")
        ttk.Entry(orow, textvariable=self.var("out_path", "")).pack(side="left", fill="x", expand=True, padx=8)
        ttk.Button(orow, text=self.t("save_as"), command=self.browse_output).pack(side="left")

        pf = ttk.LabelFrame(bottom, text=self.t("cmd_frame"), padding=4)
        pf.pack(fill="x", pady=4)
        self.preview = tk.Text(pf, height=4, wrap="word", state="disabled", font=(mono, 9))
        self.preview.pack(fill="x")
        ttk.Label(pf, textvariable=self.eff_var, style="Accent.TLabel").pack(anchor="w", pady=(4, 0))

        prow = ttk.Frame(bottom)
        prow.pack(fill="x", pady=2)
        self.progress = ttk.Progressbar(prow, mode="determinate", maximum=100)
        self.progress.pack(side="left", fill="x", expand=True)
        ttk.Label(prow, textvariable=self.status, width=52, anchor="w").pack(side="left", padx=8)

        lf = ttk.Frame(bottom)
        lf.pack(fill="x", pady=2)
        self.log = tk.Text(lf, height=5, wrap="word", state="disabled", font=(mono, 9))
        lsb = ttk.Scrollbar(lf, command=self.log.yview)
        self.log.configure(yscrollcommand=lsb.set)
        self.log.pack(side="left", fill="x", expand=True)
        lsb.pack(side="left", fill="y")

        brow = ttk.Frame(bottom)
        brow.pack(fill="x", pady=(6, 0))
        self.btn_run = ttk.Button(brow, text=self.t("run"), command=self.start)
        self.btn_run.pack(side="left")
        self.btn_cancel = ttk.Button(brow, text=self.t("cancel"), command=self.cancel, state="disabled")
        self.btn_cancel.pack(side="left", padx=6)
        ttk.Button(brow, text=self.t("copy_cmd"), command=self.copy_cmd).pack(side="left")
        ttk.Button(brow, text=self.t("open_dir"), command=self.open_out_dir).pack(side="left", padx=6)
        self.apply_theme()

    def _build_video_tab(self, nb):
        t = self.tab(nb, "tab_video")
        self.row(t, self.t("container"),
                 self.cc(t, "container", "mp4", CONTAINERS, on_change=self.on_container_change))
        self.row(t, self.t("vcodec"),
                 self.cc(t, "vcodec", "libx264", [c for c, _ in VIDEO_CODECS],
                         labeler=self.vlabel, width=40, on_change=self.on_vcodec_change))
        self.row(t, self.t("rate_mode"),
                 self.cc(t, "rate_mode", "crf", ["crf", "abr"],
                         labeler=self.mk_lab({"crf": "tok_crf", "abr": "tok_abr"}),
                         on_change=self.update_rate_state))
        self.w_crf = self.row(t, self.t("quality"), self.spin(t, "crf", 0, 63, 1, 23), self.t("quality_hint"))
        self.w_vbr = self.row(t, self.t("vbitrate"), self.entry(t, "vbitrate", "2500k"), self.t("vbitrate_hint"))
        self.w_maxrate = self.row(t, self.t("maxrate"), self.entry(t, "maxrate", ""), self.t("optional"))
        self.w_bufsize = self.row(t, self.t("bufsize"), self.entry(t, "bufsize", ""), self.t("optional"))
        self.cb_preset = self.row(t, self.t("preset"), self.cc(t, "preset", "default", ["default"]),
                                  self.t("preset_hint"))
        self.cb_tune = self.row(t, self.t("tune"), self.cc(t, "tune", "default", ["default"]))
        self.cb_profile = self.row(t, self.t("profile"), self.cc(t, "profile", "default", ["default"]))
        self.row(t, self.t("pix_fmt"), self.cc(t, "pix_fmt", "orig", PIX_FMTS, editable=True))
        self.copy_hint = ttk.Label(t, text="", style="Warn.TLabel", wraplength=440, justify="left")
        self.copy_hint.grid(row=t.grid_size()[1], column=0, columnspan=3, sticky="w", pady=(10, 0))
        self.update_rate_state()

    def _build_image_tab(self, nb):
        t = self.tab(nb, "tab_image")
        self.row(t, self.t("resolution"),
                 self.cc(t, "res", "orig", RES_PRESETS, on_change=self.update_res_state), self.t("res_hint"))
        f = ttk.Frame(t)
        self.res_w = ttk.Entry(f, textvariable=self.var("res_w", ""), width=8)
        self.res_h = ttk.Entry(f, textvariable=self.var("res_h", ""), width=8)
        self.res_w.pack(side="left")
        ttk.Label(f, text=" x ").pack(side="left")
        self.res_h.pack(side="left")
        ttk.Label(f, text=self.t("auto_blank"), style="Hint.TLabel").pack(side="left")
        self.row(t, self.t("custom_res"), f)
        self.update_res_state()

        self.row(t, self.t("algo"), self.cc(t, "algo", "default", SCALE_ALGOS))
        self.row(t, self.t("fps"), self.cc(t, "fps", "orig", FPS_PRESETS, editable=True))
        self.row(t, self.t("aspect"), self.cc(t, "aspect", "orig", ASPECTS, editable=True))

        f = ttk.Frame(t)
        for k, lk in (("crop_w", "cw"), ("crop_h", "ch"), ("crop_x", "cx"), ("crop_y", "cy")):
            ttk.Label(f, text=self.t(lk)).pack(side="left")
            ttk.Entry(f, textvariable=self.var(k, ""), width=6).pack(side="left", padx=(2, 8))
        self.row(t, self.t("crop"), f, self.t("crop_hint"))

        self.row(t, self.t("rotate"),
                 self.cc(t, "rotate", "none", ROTATIONS, labeler=self.mk_lab(ROT_TOKENS)))
        f = ttk.Frame(t)
        self.chk(f, "hflip", self.t("hflip")).pack(side="left")
        self.chk(f, "vflip", self.t("vflip")).pack(side="left", padx=12)
        self.row(t, self.t("flip"), f)

        self.row(t, self.t("brightness"), self.spin(t, "brightness", -1, 1, 0.05, 0), self.t("brightness_hint"))
        self.row(t, self.t("contrast"), self.spin(t, "contrast", 0, 4, 0.05, 1), self.t("default1"))
        self.row(t, self.t("saturation"), self.spin(t, "saturation", 0, 3, 0.05, 1), self.t("saturation_hint"))
        self.row(t, self.t("gamma"), self.spin(t, "gamma", 0.1, 10, 0.05, 1), self.t("default1"))

        f = ttk.Frame(t)
        self.chk(f, "deint", self.t("deint")).pack(side="left")
        self.chk(f, "denoise", self.t("denoise")).pack(side="left", padx=10)
        self.chk(f, "sharpen", self.t("sharpen")).pack(side="left")
        self.chk(f, "gray", self.t("gray")).pack(side="left", padx=10)
        self.row(t, self.t("effects"), f)

    def _build_audio_tab(self, nb):
        t = self.tab(nb, "tab_audio")
        self.row(t, self.t("acodec"),
                 self.cc(t, "acodec", "aac", [c for c, _ in AUDIO_CODECS], labeler=self.alabel, width=36))
        self.row(t, self.t("abitrate"), self.cc(t, "abitrate", "default", AUDIO_BITRATES, editable=True),
                 self.t("abitrate_hint"))
        self.row(t, self.t("arate"), self.cc(t, "arate", "orig", SAMPLE_RATES, editable=True))
        self.row(t, self.t("achan"),
                 self.cc(t, "achan", "orig", CHANNELS,
                         labeler=lambda c: CHANNEL_LABELS.get(c) or self.label(c)))
        self.row(t, self.t("volume"), self.spin(t, "volume", -60, 60, 1, 0), self.t("volume_hint"))
        f = ttk.Frame(t)
        self.chk(f, "loudnorm", self.t("loudnorm")).pack(side="left")
        self.row(t, self.t("normalize"), f)
        ttk.Label(t, text=self.t("audio_note"), style="Hint.TLabel").grid(
            row=t.grid_size()[1], column=0, columnspan=3, sticky="w", pady=(10, 0))

    def _build_time_tab(self, nb):
        t = self.tab(nb, "tab_time")
        self.row(t, self.t("start"), self.entry(t, "start", "", 14), self.t("start_hint"))
        self.row(t, self.t("end"), self.entry(t, "end", "", 14), self.t("end_hint"))
        self.row(t, self.t("speed"), self.spin(t, "speed", 0.25, 8, 0.25, 1), self.t("speed_hint"))

    def _build_gpu_tab(self, nb):
        t = self.tab(nb, "tab_gpu")
        self.row(t, self.t("gpu_mode"),
                 self.cc(t, "gpu_mode", "auto", GPU_MODES, labeler=self.gpulabel, width=38))
        f = ttk.Frame(t)
        self.chk(f, "gpu_decode", self.t("gpu_decode"), True).pack(anchor="w")
        self.row(t, self.t("gpu_decode_row"), f)
        f = ttk.Frame(t)
        self.chk(f, "gpu_fallback", self.t("gpu_fallback"), True).pack(anchor="w")
        self.row(t, self.t("gpu_fallback_row"), f)

        ttk.Button(t, text=self.t("gpu_detect"), command=self.start_gpu_detect).grid(
            row=t.grid_size()[1], column=0, columnspan=2, sticky="w", pady=(10, 4))
        ttk.Label(t, textvariable=self.gpu_status_var, justify="left").grid(
            row=t.grid_size()[1], column=0, columnspan=3, sticky="w", pady=4)
        ttk.Separator(t).grid(row=t.grid_size()[1], column=0, columnspan=3, sticky="ew", pady=8)
        ttk.Label(t, text=self.t("gpu_info"), wraplength=480, justify="left").grid(
            row=t.grid_size()[1], column=0, columnspan=3, sticky="w", pady=3)
        ttk.Label(t, text=self.t("gpu_req"), wraplength=480, justify="left", style="Hint.TLabel").grid(
            row=t.grid_size()[1], column=0, columnspan=3, sticky="w", pady=3)
        self.gpu_status_var.set(self.gpu_status_text())

    def _build_advanced_tab(self, nb):
        t = self.tab(nb, "tab_adv")
        self.row(t, self.t("subs"), self.cc(t, "subs", "default", SUB_OPTIONS, labeler=self.mk_lab(SUB_TOKENS)))
        f = ttk.Frame(t)
        self.chk(f, "map_all", self.t("map_all")).pack(anchor="w")
        self.chk(f, "strip_meta", self.t("strip_meta")).pack(anchor="w")
        self.chk(f, "faststart", self.t("faststart")).pack(anchor="w")
        self.row(t, self.t("options"), f)
        self.row(t, self.t("threads"), self.spin(t, "threads", 0, 64, 1, 0), self.t("threads_hint"))
        self.row(t, self.t("extra"), self.entry(t, "extra", "", 40), "-metadata title=\"...\"")

        ttk.Separator(t).grid(row=t.grid_size()[1], column=0, columnspan=3, sticky="ew", pady=10)

        for key, lk in (("ffmpeg_path", "ffmpeg_path"), ("ffprobe_path", "ffprobe_path")):
            f = ttk.Frame(t)
            ttk.Entry(f, textvariable=self.vars[key]).pack(side="left", fill="x", expand=True)
            ttk.Button(f, text="…", width=3, command=lambda k=key: self.pick_tool(k)).pack(side="left", padx=4)
            self.row(t, self.t(lk), f)

    # ----------------------------------------------------------------- tema
    def resolve_theme(self):
        mode = self.g("theme_mode")
        if mode == "auto":
            return detect_system_theme()
        return "dark" if mode == "dark" else "light"

    def on_theme_change(self):
        """Kullanıcı temayı elle seçti: tercihi kaydet ve uygula.
        'light'/'dark' seçiliyse sistem teması değişse bile sabit kalır."""
        save_config({"theme_mode": self.g("theme_mode")})
        self.apply_theme()

    def _theme_tick(self):
        # Yalnızca 'Otomatik' modda sistem temasını izler.
        try:
            if self.g("theme_mode") == "auto":
                cur = detect_system_theme()
                if cur != self.current_theme:
                    self.apply_theme(cur)
        except Exception:
            pass
        self.after(3000, self._theme_tick)

    def apply_theme(self, resolved=None):
        resolved = resolved or self.resolve_theme()
        self.current_theme = resolved
        p = THEMES[resolved]
        st = self.style
        native = os.name == "nt" and resolved == "light"
        try:
            st.theme_use("vista" if native else "clam")
        except tk.TclError:
            native = False
            st.theme_use("clam")
        self.configure(bg=p["bg"])
        if not native:
            self._style_clam(st, p)
        st.configure("Hint.TLabel", foreground=p["hint"])
        st.configure("Accent.TLabel", foreground=p["accent"])
        st.configure("Warn.TLabel", foreground=p["warn"])
        for name in ("preview", "log"):
            tw = getattr(self, name, None)
            if tw is not None and tw.winfo_exists():
                tw.configure(bg=p["text_bg"], fg=p["fg"], insertbackground=p["fg"],
                             selectbackground=p["sel"], selectforeground=p["sel_fg"],
                             highlightthickness=1, highlightbackground=p["border"],
                             highlightcolor=p["border"], relief="flat")
        self._style_popdowns(self, p)
        dark = resolved == "dark"
        self._titlebar(dark)
        self.after(80, lambda: self._titlebar(dark))

    def _style_clam(self, st, p):
        st.configure(".", background=p["bg"], foreground=p["fg"], fieldbackground=p["field"],
                     troughcolor=p["trough"], bordercolor=p["border"], lightcolor=p["border"],
                     darkcolor=p["border"], insertcolor=p["fg"], selectbackground=p["sel"],
                     selectforeground=p["sel_fg"], focuscolor=p["border"])
        st.map(".", foreground=[("disabled", p["dis"])])
        for name in ("TFrame", "TLabel"):
            st.configure(name, background=p["bg"])
        st.configure("TLabel", foreground=p["fg"])
        st.configure("TLabelframe", background=p["bg"], bordercolor=p["border"])
        st.configure("TLabelframe.Label", background=p["bg"], foreground=p["fg"])
        st.configure("TButton", background=p["btn"], foreground=p["fg"], bordercolor=p["border"],
                     lightcolor=p["btn"], darkcolor=p["btn"], padding=(10, 4), anchor="center")
        st.map("TButton",
               background=[("disabled", p["bg"]), ("pressed", p["border"]), ("active", p["btn_hover"])],
               foreground=[("disabled", p["dis"])])
        st.configure("TCheckbutton", background=p["bg"], foreground=p["fg"],
                     indicatorbackground=p["field"], indicatorforeground=p["fg"],
                     upperbordercolor=p["border"], lowerbordercolor=p["border"])
        st.map("TCheckbutton", background=[("active", p["bg"])],
               indicatorbackground=[("disabled", p["trough"]), ("pressed", p["btn_hover"])],
               foreground=[("disabled", p["dis"])])
        for name in ("TEntry", "TSpinbox", "TCombobox"):
            st.configure(name, fieldbackground=p["field"], foreground=p["fg"], insertcolor=p["fg"],
                         bordercolor=p["border"], lightcolor=p["border"], darkcolor=p["border"],
                         arrowcolor=p["fg"], background=p["btn"])
        st.map("TEntry", fieldbackground=[("disabled", p["trough"])], foreground=[("disabled", p["dis"])])
        st.map("TSpinbox", fieldbackground=[("disabled", p["trough"])], foreground=[("disabled", p["dis"])],
               background=[("active", p["btn_hover"])], arrowcolor=[("disabled", p["dis"])])
        st.map("TCombobox",
               fieldbackground=[("disabled", p["trough"]), ("readonly", p["field"])],
               foreground=[("disabled", p["dis"])],
               selectbackground=[("readonly", p["field"])], selectforeground=[("readonly", p["fg"])],
               background=[("active", p["btn_hover"]), ("pressed", p["btn_hover"])],
               arrowcolor=[("disabled", p["dis"])])
        st.configure("TNotebook", background=p["bg"], bordercolor=p["border"],
                     lightcolor=p["border"], darkcolor=p["border"])
        st.configure("TNotebook.Tab", background=p["tab"], foreground=p["fg"],
                     bordercolor=p["border"], lightcolor=p["border"], darkcolor=p["border"])
        st.map("TNotebook.Tab", background=[("selected", p["bg"]), ("active", p["btn_hover"])],
               foreground=[("disabled", p["dis"])])
        st.configure("Treeview", background=p["field"], fieldbackground=p["field"], foreground=p["fg"],
                     bordercolor=p["border"], lightcolor=p["field"], darkcolor=p["field"])
        st.map("Treeview", background=[("selected", p["sel"])], foreground=[("selected", p["sel_fg"])])
        st.configure("Treeview.Heading", background=p["btn"], foreground=p["fg"], bordercolor=p["border"],
                     lightcolor=p["btn"], darkcolor=p["btn"], relief="flat")
        st.map("Treeview.Heading", background=[("active", p["btn_hover"])])
        st.configure("TScrollbar", background=p["btn"], troughcolor=p["trough"], bordercolor=p["border"],
                     arrowcolor=p["fg"], lightcolor=p["btn"], darkcolor=p["btn"])
        st.map("TScrollbar", background=[("active", p["btn_hover"])])
        st.configure("TProgressbar", background=p["sel"], troughcolor=p["trough"], bordercolor=p["border"],
                     lightcolor=p["sel"], darkcolor=p["sel"])
        st.configure("TSeparator", background=p["border"])
        st.configure("TPanedwindow", background=p["bg"])

    def _style_popdowns(self, widget, p):
        """Combobox açılır listelerini (tk Listbox) temaya uydur."""
        for c in widget.winfo_children():
            if isinstance(c, ttk.Combobox):
                try:
                    pd = self.tk.eval(f"ttk::combobox::PopdownWindow {c}")
                    self.tk.eval(
                        f"{pd}.f.l configure -background {p['field']} -foreground {p['fg']} "
                        f"-selectbackground {p['sel']} -selectforeground {p['sel_fg']} "
                        f"-highlightthickness 0 -borderwidth 0")
                except tk.TclError:
                    pass
            self._style_popdowns(c, p)

    def _titlebar(self, dark):
        """Windows'ta başlık çubuğunu da koyu/açık yap."""
        if os.name != "nt":
            return
        try:
            import ctypes
            self.update_idletasks()
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            val = ctypes.c_int(1 if dark else 0)
            for attr in (20, 19):  # DWMWA_USE_IMMERSIVE_DARK_MODE (yeni / eski sürüm)
                if ctypes.windll.dwmapi.DwmSetWindowAttribute(
                        hwnd, attr, ctypes.byref(val), ctypes.sizeof(val)) == 0:
                    break
        except Exception:
            pass

    # ----------------------------------------------------- dil değiştirme
    def on_lang(self, _e=None):
        self.lang = "tr" if self.lang_var.get() == "Türkçe" else "en"
        self.after(10, self._rebuild)

    def _rebuild(self):
        self._ready = False
        self.title(self.t("title"))
        for w in self.winfo_children():
            w.destroy()
        self._build_ui()
        self._ready = True
        self.refresh_codec_lists()
        self.update_res_state()
        self.update_rate_state()
        if self.info_data:
            self.show_info(*self.info_data)
        key, args = self.status_rec
        if key == "raw":
            self.status.set(args[0])
        else:
            self.status.set(self.t(key, *args))
        self.progress["value"] = self._pct
        self.log.configure(state="normal")
        self.log.insert("1.0", "\n".join(self.log_lines) + ("\n" if self.log_lines else ""))
        self.log.see("end")
        self.log.configure(state="disabled")
        if self.running:
            self.btn_run.configure(state="disabled")
            self.btn_cancel.configure(state="normal")
        self.gpu_status_var.set(self.gpu_status_text())
        self.update_preview()

    # ------------------------------------------------------ durum güncelleme
    def update_rate_state(self):
        if not hasattr(self, "w_crf") or not self.w_crf.winfo_exists():
            return
        crf_mode = self.g("rate_mode") == "crf"
        self.w_crf.configure(state="normal" if crf_mode else "disabled")
        for w in (self.w_vbr, self.w_maxrate, self.w_bufsize):
            w.configure(state="disabled" if crf_mode else "normal")
        self.update_preview()

    def update_res_state(self):
        if not hasattr(self, "res_w") or not self.res_w.winfo_exists():
            return
        custom = self.g("res") == "custom"
        for w in (self.res_w, self.res_h):
            w.configure(state="normal" if custom else "disabled")
        self.update_preview()

    def refresh_codec_lists(self):
        codec = self.g("vcodec")
        _, presets = PRESETS.get(codec, (None, []))
        for cbw, vals in ((self.cb_preset, presets),
                          (self.cb_tune, TUNES.get(codec, [])),
                          (self.cb_profile, PROFILES.get(codec, []))):
            cbw.set_codes(["default"] + vals)
            cbw.configure(state="readonly" if vals else "disabled")
        if codec == "copy":
            self.copy_hint.configure(text=self.t("copy_hint"))
        elif codec == "none":
            self.copy_hint.configure(text=self.t("none_hint"))
        else:
            self.copy_hint.configure(text="")

    def on_vcodec_change(self):
        for key in ("preset", "tune", "profile"):
            self.vars[key].set("default")
        self.refresh_codec_lists()
        self.update_preview()

    def on_container_change(self):
        ext = self.g("container")
        v, a = CONTAINER_DEFAULTS.get(ext, (None, None))
        if v and (ext == "webm" or self.g("vcodec") == "none"):
            self.vars["vcodec"].set(v)
            self.on_vcodec_change()
        if a and (ext in AUDIO_ONLY or ext == "webm" or self.g("acodec") == "none"):
            self.vars["acodec"].set(a)
        out = self.g("out_path")
        if out:
            self.vars["out_path"].set(f"{os.path.splitext(out)[0]}.{ext}")
        self.update_preview()

    # ------------------------------------------------------------------ GPU
    def gpu_status_text(self):
        if self.gpu_testing:
            return self.t("gpu_testing")
        if self.gpu_results is None:
            return self.t("gpu_unknown")
        lines = []
        for b in gpu_order():
            ok = self.gpu_results.get(b, (False, ""))[0]
            lines.append(f"{'✔' if ok else '✘'} {GPU_NAMES[b]} — {self.t('gpu_ok' if ok else 'gpu_no')}")
        if self.gpu_auto != "off":
            lines.append(self.t("gpu_auto_pick", GPU_NAMES[self.gpu_auto]))
        else:
            lines.append(self.t("gpu_auto_none"))
        return "\n".join(lines)

    def start_gpu_detect(self):
        if self.gpu_testing:
            return
        self.gpu_testing = True
        self.gpu_status_var.set(self.t("gpu_testing"))
        ff = self.g("ffmpeg_path") or "ffmpeg"
        threading.Thread(target=self._gpu_worker, args=(ff,), daemon=True).start()

    def _gpu_worker(self, ff):
        res = {}
        for b in gpu_order():
            try:
                r = subprocess.run(gpu_test_cmd(ff, b), stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                   stderr=subprocess.PIPE, text=True, errors="replace", timeout=30,
                                   creationflags=no_window_flags())
                res[b] = (r.returncode == 0, (r.stderr or "").strip()[-300:])
            except Exception as e:  # noqa
                res[b] = (False, str(e))
        self.q.put(("gpu", res))

    def effective_gpu(self):
        if self.force_cpu:
            return "off"
        mode = self.g("gpu_mode")
        return self.gpu_auto if mode == "auto" else mode

    # ----------------------------------------------------------- dosya işleri
    def pick_tool(self, key):
        p = filedialog.askopenfilename(title=self.t("pick_tool"))
        if p:
            self.vars[key].set(p)

    def browse_input(self):
        p = filedialog.askopenfilename(
            title=self.t("pick_media"),
            filetypes=[(self.t("media_files"),
                        "*.mp4 *.mkv *.mov *.avi *.webm *.flv *.ts *.m4v *.wmv *.mpg *.mpeg "
                        "*.3gp *.mp3 *.wav *.flac *.m4a *.ogg *.opus *.aac *.gif"),
                       (self.t("all_files"), "*.*")])
        if p:
            self.vars["in_path"].set(p)
            self.load_file(p)

    def browse_output(self):
        ext = self.g("container")
        p = filedialog.asksaveasfilename(title=self.t("out_dialog"), defaultextension="." + ext,
                                         initialfile=os.path.basename(self.g("out_path")))
        if p:
            self.vars["out_path"].set(p)
            e = os.path.splitext(p)[1].lstrip(".").lower()
            if e in CONTAINERS:
                self.vars["container"].set(e)

    def open_out_dir(self):
        d = os.path.dirname(self.g("out_path")) or "."
        try:
            if os.name == "nt":
                os.startfile(d)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", d], stdin=subprocess.DEVNULL)
            else:
                subprocess.Popen(["xdg-open", d], stdin=subprocess.DEVNULL)
        except Exception as e:
            messagebox.showerror(self.t("err"), str(e))

    def load_file(self, path):
        path = path.strip().strip('"')
        if not os.path.isfile(path):
            messagebox.showerror(self.t("err"), self.t("file_nf"))
            return
        try:
            r = subprocess.run(
                [self.g("ffprobe_path"), "-v", "error", "-print_format", "json",
                 "-show_format", "-show_streams", path],
                stdin=subprocess.DEVNULL, capture_output=True, text=True, encoding="utf-8",
                errors="replace", creationflags=no_window_flags())
        except FileNotFoundError:
            messagebox.showerror(self.t("err"), self.t("ffprobe_missing"))
            return
        if r.returncode != 0:
            messagebox.showerror(self.t("ffprobe_err"), r.stderr or self.t("ffprobe_unread"))
            return
        try:
            data = json.loads(r.stdout)
        except json.JSONDecodeError:
            messagebox.showerror(self.t("err"), self.t("ffprobe_parse"))
            return

        self.input_path = path
        self.vars["in_path"].set(path)
        self.info_data = (data, path)
        self.show_info(data, path)

        ext = os.path.splitext(path)[1].lstrip(".").lower()
        cont = ext if ext in CONTAINERS else "mp4"
        self._ready = False
        self.vars["container"].set(cont)
        self.vars["out_path"].set(f"{os.path.splitext(path)[0]}_converted.{cont}")
        self._ready = True
        self.update_preview()

    def show_info(self, d, path):
        t = self.tree
        t.delete(*t.get_children())
        fmt = d.get("format", {})
        streams = d.get("streams", [])
        T = self.t

        def group(title):
            return t.insert("", "end", text=title, open=True)

        def add(parent, k, v):
            if v not in (None, "", "N/A"):
                t.insert(parent, "end", text=T(k), values=(v,))

        dur = fmt.get("duration")
        if not dur:
            for s in streams:
                if s.get("duration"):
                    dur = s["duration"]
                    break
        try:
            self.duration = float(dur)
        except (TypeError, ValueError):
            self.duration = 0.0

        g = group(T("g_general"))
        add(g, "i_filename", os.path.basename(path))
        add(g, "i_size", fmt_size(fmt.get("size")))
        add(g, "i_duration", fmt_duration(self.duration) if self.duration else None)
        add(g, "i_container", fmt.get("format_long_name") or fmt.get("format_name"))
        add(g, "i_total_br", fmt_bitrate(fmt.get("bit_rate")))
        add(g, "i_nstreams", fmt.get("nb_streams"))
        add(g, "i_title", fmt.get("tags", {}).get("title"))

        vi = ai = si = 0
        for s in streams:
            ct = s.get("codec_type")
            tags = s.get("tags", {}) or {}
            if ct == "video":
                if s.get("disposition", {}).get("attached_pic"):
                    continue
                vi += 1
                g = group(T("g_video", vi))
                add(g, "i_codec", s.get("codec_long_name") or s.get("codec_name"))
                add(g, "i_profile", s.get("profile"))
                if s.get("width"):
                    add(g, "i_res", f"{s['width']} x {s['height']}")
                add(g, "i_dar", s.get("display_aspect_ratio"))
                avg = frac_to_float(s.get("avg_frame_rate"))
                rr = frac_to_float(s.get("r_frame_rate"))
                if avg:
                    add(g, "i_fps_avg", f"{avg:.3f} fps")
                if rr and abs(rr - avg) > 0.01:
                    add(g, "i_fps_base", f"{rr:.3f} fps")
                add(g, "i_bitrate", fmt_bitrate(s.get("bit_rate") or tags.get("BPS")))
                add(g, "i_pixfmt", s.get("pix_fmt"))
                add(g, "i_bitdepth", s.get("bits_per_raw_sample"))
                add(g, "i_cspace", s.get("color_space"))
                add(g, "i_crange", s.get("color_range"))
                add(g, "i_ctrans", s.get("color_transfer"))
                add(g, "i_scan", s.get("field_order"))
                add(g, "i_frames", s.get("nb_frames"))
                rot = tags.get("rotate")
                for sd in s.get("side_data_list", []) or []:
                    if "rotation" in sd:
                        rot = sd["rotation"]
                add(g, "i_rotation", f"{rot}°" if rot is not None else None)
                add(g, "i_lang", tags.get("language"))
            elif ct == "audio":
                ai += 1
                g = group(T("g_audio", ai))
                add(g, "i_codec", s.get("codec_long_name") or s.get("codec_name"))
                add(g, "i_profile", s.get("profile"))
                if s.get("sample_rate"):
                    add(g, "i_srate", f"{s['sample_rate']} Hz")
                add(g, "i_channels", f"{s.get('channels')} ({s.get('channel_layout', '?')})")
                add(g, "i_bitrate", fmt_bitrate(s.get("bit_rate") or tags.get("BPS")))
                add(g, "i_sfmt", s.get("sample_fmt"))
                add(g, "i_lang", tags.get("language"))
            elif ct == "subtitle":
                si += 1
                g = group(T("g_sub", si))
                add(g, "i_codec", s.get("codec_name"))
                add(g, "i_lang", tags.get("language"))
                add(g, "i_title", tags.get("title"))
            else:
                g = group(T("g_other", ct or "?"))
                add(g, "i_codec", s.get("codec_name"))

    # ---------------------------------------------------------- komut üretimi
    def build_command(self, progress=False):
        self.enc_info = None
        self.gpu_used = False
        if not self.input_path:
            return None
        out = self.g("out_path")
        if not out:
            raise ValidationError(self.t("e_noout"))
        if os.path.abspath(out) == os.path.abspath(self.input_path):
            raise ValidationError(self.t("e_same"))

        g = self.g
        ext = os.path.splitext(out)[1].lstrip(".").lower()
        audio_only = ext in AUDIO_ONLY
        is_gif = ext == "gif"

        speed = self.num("speed", "speed")
        if speed <= 0:
            raise ValidationError(self.t("e_speed"))

        # ---- GPU kararı
        vcodec = g("vcodec")
        video_on = not (audio_only or vcodec == "none")
        reencode = video_on and vcodec != "copy" and not is_gif
        backend = self.effective_gpu() if reencode else "off"
        enc = vcodec
        if reencode and backend != "off":
            fam = CODEC_FAMILY.get(vcodec)
            enc = GPU_ENCODERS.get(backend, {}).get(fam, vcodec) if fam else vcodec
        enc_changed = enc != vcodec
        use_decode = reencode and backend != "off" and self.vars["gpu_decode"].get()
        vaapi_upload = enc_changed and backend == "vaapi"
        self.enc_info = (enc, backend, enc_changed, use_decode) if reencode else None
        self.gpu_used = enc_changed or bool(use_decode and hwaccel_args(backend))

        cmd = [g("ffmpeg_path") or "ffmpeg", "-hide_banner", "-y"]
        if progress:
            cmd += ["-progress", "pipe:1", "-nostats"]

        # ---- Giriş seçenekleri
        if use_decode:
            cmd += hwaccel_args(backend)
        if vaapi_upload:
            cmd += ["-vaapi_device", VAAPI_DEVICE]
        start = self.parse_time(g("start"))
        end = self.parse_time(g("end"))
        if start:
            cmd += ["-ss", g("start")]
        if end is not None:
            dur = end - (start or 0)
            if dur <= 0:
                raise ValidationError(self.t("e_endstart"))
            cmd += ["-t", f"{dur:.3f}"]
        cmd += ["-i", self.input_path]

        # ---- Akış seçimi
        subs = g("subs")
        if subs == "copy":
            cmd += ["-map", "0:v?", "-map", "0:a?", "-map", "0:s?"]
            cmd += ["-c:s", "mov_text" if ext in ("mp4", "mov", "m4a") else "copy"]
        elif subs == "remove":
            cmd += ["-sn"]
            if self.vars["map_all"].get():
                cmd += ["-map", "0", "-map", "-0:s"]
        elif self.vars["map_all"].get():
            cmd += ["-map", "0"]

        # ---- Video
        if not video_on:
            cmd.append("-vn")
        elif vcodec == "copy" and not is_gif:
            cmd += ["-c:v", "copy"]
        else:
            vf = self.video_filters(is_gif, speed, vaapi_upload)
            if not is_gif:
                cmd += ["-c:v", enc]
                if enc != "prores_ks":
                    if g("rate_mode") == "crf":
                        q = g("crf")
                        if not re.fullmatch(r"\d+(\.\d+)?", q):
                            raise ValidationError(self.t("e_num", self.t("quality")))
                        cmd += quality_args(enc, q)
                    else:
                        if g("vbitrate"):
                            cmd += ["-b:v", norm_rate(g("vbitrate"))]
                        if g("maxrate"):
                            cmd += ["-maxrate", norm_rate(g("maxrate"))]
                        if g("bufsize"):
                            cmd += ["-bufsize", norm_rate(g("bufsize"))]
                flag, _ = PRESETS.get(enc, (None, None))
                pr = g("preset")
                if flag and pr != "default":
                    if enc_changed:
                        pr = gpu_preset(pr, enc)
                    if pr:
                        cmd += [flag, pr]
                if enc in TUNES and g("tune") != "default":
                    cmd += ["-tune", g("tune")]
                prof = g("profile")
                if prof != "default" and prof in PROFILES.get(enc, []):
                    cmd += ["-profile:v", PRORES[prof] if enc == "prores_ks" else prof]
                if g("pix_fmt") not in ("orig", "") and not enc.endswith("_vaapi"):
                    cmd += ["-pix_fmt", g("pix_fmt")]
                if g("fps") not in ("orig", ""):
                    self.num("fps", "fps")
                    cmd += ["-r", g("fps")]
                if g("aspect") not in ("orig", ""):
                    cmd += ["-aspect", g("aspect")]
            else:
                cmd += ["-loop", "0"]
            if vf:
                cmd += ["-vf", vf]

        # ---- Ses
        acodec = g("acodec")
        if is_gif or acodec == "none":
            cmd.append("-an")
        elif acodec == "copy":
            cmd += ["-c:a", "copy"]
        else:
            cmd += ["-c:a", acodec]
            if acodec not in LOSSLESS_AUDIO and g("abitrate") not in ("default", ""):
                cmd += ["-b:a", norm_rate(g("abitrate"))]
            if g("arate") not in ("orig", ""):
                cmd += ["-ar", g("arate")]
            if g("achan") != "orig":
                cmd += ["-ac", g("achan")]
            af = []
            vol = self.num("volume", "volume")
            if abs(vol) > 1e-9:
                af.append(f"volume={vol:g}dB")
            if self.vars["loudnorm"].get():
                af.append("loudnorm")
            if abs(speed - 1.0) > 1e-9:
                af += atempo_chain(speed)
            if af:
                cmd += ["-af", ",".join(af)]

        # ---- Genel
        if self.vars["strip_meta"].get():
            cmd += ["-map_metadata", "-1"]
        if self.vars["faststart"].get() and ext in ("mp4", "mov", "m4a"):
            cmd += ["-movflags", "+faststart"]
        th = g("threads")
        if th and th != "0":
            cmd += ["-threads", th]
        if g("extra"):
            try:
                cmd += shlex.split(g("extra"), posix=(os.name != "nt"))
            except ValueError as e:
                raise ValidationError(self.t("e_extra", e))

        cmd.append(out)
        return cmd

    def video_filters(self, is_gif, speed, vaapi_upload=False):
        g = self.g
        f = []
        if self.vars["deint"].get():
            f.append("yadif")

        cw, ch = g("crop_w"), g("crop_h")
        if cw and ch:
            f.append(f"crop={cw}:{ch}:{g('crop_x') or 0}:{g('crop_y') or 0}")

        res = g("res")
        scale = None
        if res == "custom":
            w, h = g("res_w") or "-2", g("res_h") or "-2"
            if not (w == "-2" and h == "-2"):
                scale = f"scale={w}:{h}"
        elif res != "orig":
            scale = f"scale=-2:{res.rstrip('p')}"
        if scale:
            if g("algo") != "default":
                scale += f":flags={g('algo')}"
            f.append(scale)

        rot = g("rotate")
        if rot == "cw":
            f.append("transpose=1")
        elif rot == "ccw":
            f.append("transpose=2")
        elif rot == "180":
            f += ["hflip", "vflip"]
        if self.vars["hflip"].get():
            f.append("hflip")
        if self.vars["vflip"].get():
            f.append("vflip")

        eq = []
        b = self.num("brightness", "brightness")
        c = self.num("contrast", "contrast")
        s = self.num("saturation", "saturation")
        gm = self.num("gamma", "gamma")
        if abs(b) > 1e-9:
            eq.append(f"brightness={b:g}")
        if abs(c - 1) > 1e-9:
            eq.append(f"contrast={c:g}")
        if abs(s - 1) > 1e-9:
            eq.append(f"saturation={s:g}")
        if abs(gm - 1) > 1e-9:
            eq.append(f"gamma={gm:g}")
        if eq:
            f.append("eq=" + ":".join(eq))

        if self.vars["denoise"].get():
            f.append("hqdn3d")
        if self.vars["sharpen"].get():
            f.append("unsharp=5:5:1.0:5:5:0.0")
        if self.vars["gray"].get():
            f.append("hue=s=0")
        if abs(speed - 1.0) > 1e-9:
            f.append(f"setpts=PTS/{speed:g}")

        if is_gif:
            fps = g("fps") if g("fps") not in ("orig", "") else "15"
            f.append(f"fps={fps}")
            chain = ",".join(f)
            pal = "split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse"
            return (chain + "," + pal) if chain else pal
        if vaapi_upload:
            f.append("format=nv12,hwupload")
        return ",".join(f)

    # -------------------------------------------------------------- önizleme
    def update_preview(self, *_):
        if not self._ready or not hasattr(self, "preview") or not self.preview.winfo_exists():
            return
        eff = ""
        try:
            cmd = self.build_command()
            if cmd is None:
                txt = self.t("pick_video_prev")
            else:
                txt = cmd_to_str(cmd)
                if self.enc_info is None:
                    eff = self.t("eff_none")
                else:
                    enc, backend, changed, dec = self.enc_info
                    if self.gpu_used:
                        eff = self.t("eff_gpu", enc, GPU_NAMES.get(backend, backend)) if changed \
                            else self.t("eff_cpu", enc)
                        if dec and hwaccel_args(backend):
                            eff += self.t("eff_dec")
                    else:
                        eff = self.t("eff_cpu", enc)
        except ValidationError as e:
            txt = f"⚠ {e}"
        self.eff_var.set(eff)
        self.preview.configure(state="normal")
        self.preview.delete("1.0", "end")
        self.preview.insert("1.0", txt)
        self.preview.configure(state="disabled")

    def copy_cmd(self):
        try:
            cmd = self.build_command()
        except ValidationError as e:
            messagebox.showerror(self.t("err"), str(e))
            return
        if cmd:
            self.clipboard_clear()
            self.clipboard_append(cmd_to_str(cmd))
            self.set_status("cmd_copied")

    # ---------------------------------------------------------- çalıştırma
    def start(self):
        if self.running:
            return
        try:
            cmd = self.build_command()
        except ValidationError as e:
            messagebox.showerror(self.t("setting_err"), str(e))
            return
        if cmd is None:
            messagebox.showinfo(self.t("info"), self.t("pick_video_first"))
            return
        out = self.g("out_path")
        if os.path.exists(out) and not messagebox.askyesno(
                self.t("exists_t"), self.t("exists", os.path.basename(out))):
            return

        start = self.parse_time(self.g("start")) or 0.0
        end = self.parse_time(self.g("end"))
        total = (end if end is not None else self.duration) - start
        self.expected_out = max(total, 0) / max(self.num("speed", "speed"), 1e-6) if total > 0 else 0.0

        self.running = True
        self.cancelled = False
        self.force_cpu = False
        self.btn_run.configure(state="disabled")
        self.btn_cancel.configure(state="normal")
        self._pct = 0.0
        self._cur_time = 0.0
        self.progress["value"] = 0
        self.set_status("starting")
        self.log_lines = []
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")
        self._run_conversion()

    def _run_conversion(self):
        try:
            cmd = self.build_command(progress=True)
        except ValidationError as e:
            messagebox.showerror(self.t("setting_err"), str(e))
            self._finish()
            return
        self.run_gpu_used = self.gpu_used
        self._log("$ " + cmd_to_str([c for c in cmd if c not in ("-progress", "pipe:1", "-nostats")]))
        threading.Thread(target=self._worker, args=(cmd,), daemon=True).start()

    def _worker(self, cmd):
        try:
            self.proc = subprocess.Popen(
                cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace", creationflags=no_window_flags())
            for line in self.proc.stdout:
                self.q.put(("line", line.rstrip()))
            rc = self.proc.wait()
            self.q.put(("done", rc))
        except FileNotFoundError:
            self.q.put(("error", "ffmpeg_missing"))
        except Exception as e:  # noqa
            self.q.put(("error_raw", str(e)))

    def cancel(self):
        if self.proc and self.running:
            self.cancelled = True
            try:
                self.proc.terminate()
            except Exception:
                pass

    def _log(self, text):
        self.log_lines.append(text)
        if len(self.log_lines) > 2000:
            self.log_lines = self.log_lines[-1500:]
        self.log.configure(state="normal")
        self.log.insert("end", text + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _finish(self):
        self.running = False
        self.force_cpu = False
        self.btn_run.configure(state="normal")
        self.btn_cancel.configure(state="disabled")
        self.update_preview()

    def _poll(self):
        try:
            while True:
                kind, val = self.q.get_nowait()
                if kind == "line":
                    self._handle_line(val)
                elif kind == "gpu":
                    self.gpu_results = val
                    self.gpu_testing = False
                    self.gpu_auto = next((b for b in gpu_order() if val.get(b, (False,))[0]), "off")
                    self.gpu_status_var.set(self.gpu_status_text())
                    self.update_preview()
                elif kind == "done":
                    if self.cancelled:
                        self._finish()
                        self.set_status("cancelled")
                    elif val == 0:
                        self._finish()
                        self._pct = 100.0
                        self.progress["value"] = 100
                        self.set_status("done")
                    elif self.run_gpu_used and not self.force_cpu and self.vars["gpu_fallback"].get():
                        self.force_cpu = True
                        self._log(self.t("retry_cpu"))
                        self.set_status("retry_cpu")
                        self._pct = 0.0
                        self.progress["value"] = 0
                        self._run_conversion()
                    else:
                        self._finish()
                        self.set_status("failed", val)
                elif kind in ("error", "error_raw"):
                    self._finish()
                    self.set_status("err")
                    messagebox.showerror(self.t("err"), self.t(val) if kind == "error" else val)
        except queue.Empty:
            pass
        self.after(100, self._poll)

    def _handle_line(self, line):
        m = re.match(r"^([a-z_0-9]+)=(.*)$", line)
        if not (m and m.group(1) in PROGRESS_KEYS):
            self._log(line)
            return
        key, val = m.group(1), m.group(2)
        if key == "out_time_us":
            try:
                self._cur_time = int(val) / 1_000_000
            except ValueError:
                return
            if self.expected_out > 0:
                self._pct = min(100.0, self._cur_time / self.expected_out * 100)
                self.progress["value"] = self._pct
        elif key == "speed":
            try:
                sp = float(val.replace("x", ""))
            except ValueError:
                sp = None
            txt = self.t("pct", self._pct)
            if sp:
                txt += self.t("speed_x", sp)
                if self.expected_out > 0:
                    remain = max(self.expected_out - self._cur_time, 0) / sp
                    txt += self.t("left", fmt_duration(remain)[:8])
            self.set_status_raw(txt)


if __name__ == "__main__":
    if os.name == "nt":
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass
    App().mainloop()
