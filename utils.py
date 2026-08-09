import os
import subprocess
import urllib.request
from urllib.parse import urlparse
from PyQt6.QtGui import QIcon, QPixmap, QPainter
from PyQt6.QtCore import Qt


def load_square_icon(path: str) -> QIcon:
    """
    Trims transparent margins and pads image into a 1:1 square QIcon,
    making the logo graphic significantly larger and preventing stretching.
    """
    if not path or not os.path.exists(path):
        return QIcon()
    orig_pm = QPixmap(path)
    if orig_pm.isNull():
        return QIcon()

    img = orig_pm.toImage()
    w, h = img.width(), img.height()
    min_x, min_y, max_x, max_y = w, h, 0, 0
    found = False
    for y in range(h):
        for x in range(w):
            if img.pixelColor(x, y).alpha() > 10:
                if x < min_x: min_x = x
                if x > max_x: max_x = x
                if y < min_y: min_y = y
                if y > max_y: max_y = y
                found = True

    if found and (max_x >= min_x) and (max_y >= min_y):
        crop_w = max_x - min_x + 1
        crop_h = max_y - min_y + 1
        cropped_pm = orig_pm.copy(min_x, min_y, crop_w, crop_h)
    else:
        cropped_pm = orig_pm

    cw, ch = cropped_pm.width(), cropped_pm.height()
    side = max(cw, ch)
    sq_pm = QPixmap(side, side)
    sq_pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(sq_pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    x = (side - cw) // 2
    y = (side - ch) // 2
    p.drawPixmap(x, y, cropped_pm)
    p.end()

    return QIcon(sq_pm)


def resolve_shortcut(lnk_path: str) -> str:
    """
    Resolves a Windows .lnk shortcut to its original target file path.
    Strips the shortcut overlay emblem by returning the actual target executable/file.
    """
    if not lnk_path or not lnk_path.lower().endswith(".lnk") or not os.path.exists(lnk_path):
        return lnk_path

    try:
        import win32com.client
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(lnk_path)
        target = shortcut.TargetPath
        if target and os.path.exists(target):
            return target
    except Exception:
        pass

    try:
        cmd = f'powershell -NoProfile -ExecutionPolicy Bypass -Command "$s=(New-Object -COM WScript.Shell).CreateShortcut(\'{lnk_path}\'); $s.TargetPath"'
        res = subprocess.check_output(cmd, shell=True, text=True, timeout=2).strip()
        if res and os.path.exists(res):
            return res
    except Exception:
        pass

    return lnk_path


def is_url(cmd: str) -> bool:
    if not cmd:
        return False
    cmd = cmd.strip()
    if cmd.lower().startswith("start "):
        return False
    if cmd.lower().startswith(("http://", "https://", "www.")):
        return True
    if ":" in cmd and not os.path.exists(cmd) and not cmd[1:3] == ":\\":
        if " " not in cmd and not cmd.lower().startswith(("ms-", "shell:", "file:")):
            return True
        if cmd.lower().startswith(("http:", "https:")):
            return True
        return False
    if not os.path.exists(cmd) and "." in cmd and not os.path.isabs(cmd) and " " not in cmd:
        parts = cmd.split("/")[0].split(".")
        if len(parts) >= 2 and len(parts[-1]) >= 2:
            return True
    return False


def get_website_domain(cmd: str) -> str:
    cmd = cmd.strip()
    if not cmd.lower().startswith(("http://", "https://")):
        cmd = "https://" + cmd
    try:
        parsed = urlparse(cmd)
        return parsed.netloc or parsed.path.split('/')[0]
    except Exception:
        return ""


def fetch_favicon(cmd: str) -> str:
    domain = get_website_domain(cmd)
    if not domain:
        return ""

    favicons_dir = os.path.join("Config", "favicons")
    os.makedirs(favicons_dir, exist_ok=True)
    cache_path = os.path.join(favicons_dir, f"{domain}.png")

    if os.path.exists(cache_path) and os.path.getsize(cache_path) > 0:
        return cache_path

    favicon_url = f"https://www.google.com/s2/favicons?domain={domain}&sz=64"
    try:
        req = urllib.request.Request(
            favicon_url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = resp.read()
            if data and len(data) > 100:
                with open(cache_path, "wb") as f:
                    f.write(data)
                return cache_path
    except Exception as e:
        print(f"Favicon download error for {domain}: {e}")

    return ""
