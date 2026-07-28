import sys
import os
import json
import math
import subprocess
import threading
from pynput import keyboard

from PyQt6.QtCore import Qt, QPointF, pyqtSignal, QObject, QPropertyAnimation, QEasingCurve, QFileInfo, pyqtProperty
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QCursor, QPainterPath, QIcon, QAction, QPixmap
from PyQt6.QtWidgets import QApplication, QWidget, QFileIconProvider, QSystemTrayIcon, QMenu

from settings_gui import SettingsWindow
from styles import load_styles

try:
    import pywinstyles
except ImportError:
    pywinstyles = None


class TriggerSignal(QObject):
    show_signal = pyqtSignal()


class CircleMenuWin11(QWidget):
    def __init__(self, trigger):
        super().__init__()
        self.trigger = trigger
        self.trigger.show_signal.connect(self.show_at_cursor)
        
        self.hovered_index = -1
        self.radius_inner = 60
        self.radius_outer = 175
        self._anim_progress = 1.0
        self.animation_type = "expand"
        self.theme_mode = "light"
        
        self.styles = load_styles()
        self.current_style_key = "fluent"

        self.load_configs()
        self.init_ui()
        self.init_animation()

    @pyqtProperty(float)
    def anim_progress(self):
        return self._anim_progress

    @anim_progress.setter
    def anim_progress(self, val):
        self._anim_progress = val
        self.update()

    def load_configs(self):
        config_dir = "Config"
        apps_path = os.path.join(config_dir, "apps.json")
        settings_path = os.path.join(config_dir, "settings.json")
        
        if os.path.exists(apps_path):
            try:
                with open(apps_path, "r", encoding="utf-8") as f:
                    self.apps = json.load(f)
            except Exception:
                self.apps = []
        else:
            self.apps = [{"name": "Проводник", "command": "explorer", "icon": "C:\\Windows\\explorer.exe"}]

        if os.path.exists(settings_path):
            try:
                with open(settings_path, "r", encoding="utf-8") as f:
                    st = json.load(f)
                    self.animation_type = st.get("animation", "expand")
                    self.current_style_key = st.get("style", "fluent")
                    self.theme_mode = st.get("theme_mode", "light")
            except Exception:
                self.animation_type = "expand"
                self.current_style_key = "fluent"
                self.theme_mode = "light"
            
        self.load_icons()

    def load_icons(self):
        icon_provider = QFileIconProvider()
        self.icons = []
        for app_info in self.apps:
            icon_path = app_info.get("icon", "")
            pixmap = None
            if icon_path and os.path.exists(icon_path):
                file_info = QFileInfo(icon_path)
                pixmap = icon_provider.icon(file_info).pixmap(32, 32)
            self.icons.append(pixmap)

    def init_ui(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(400, 400)
        self.setMouseTracking(True)

    def init_animation(self):
        self.anim = QPropertyAnimation(self, b"anim_progress")
        self.anim.setDuration(240)
        self.anim.setEasingCurve(QEasingCurve.Type.OutBack)

        self.anim_opacity = QPropertyAnimation(self, b"windowOpacity")
        self.anim_opacity.setDuration(200)
        self.anim_opacity.setEasingCurve(QEasingCurve.Type.OutCubic)

    def show_at_cursor(self):
        self.load_configs()
        cursor_pos = QCursor.pos()
        self.move(cursor_pos.x() - self.width() // 2, cursor_pos.y() - self.height() // 2)
        
        self.show()
        self.raise_()
        self.activateWindow()

        # Настоящее акриловое размытие Windows 11
        if pywinstyles:
            try:
                if self.current_style_key == "fluent":
                    pywinstyles.apply_style(self, "acrylic")
                else:
                    pywinstyles.apply_style(self, "transparent")
            except Exception:
                pass

        if self.animation_type == "fade":
            self.setWindowOpacity(0.0)
            self._anim_progress = 1.0
            self.anim_opacity.setStartValue(0.0)
            self.anim_opacity.setEndValue(1.0)
            self.anim_opacity.start()
        else:
            self.setWindowOpacity(1.0)
            self.anim.setStartValue(0.0)
            self.anim.setEndValue(1.0)
            self.anim.start()

    def hide_animated(self):
        self.hide()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.GlobalColor.transparent)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        

        center = QPointF(self.width() / 2, self.height() / 2)
        progress = self._anim_progress

        if self.animation_type == "expand":
            center_scale = min(1.0, progress / 0.4) if progress > 0 else 0
            sector_progress = max(0.0, (progress - 0.2) / 0.8)
        else:
            center_scale = 1.0
            sector_progress = 1.0

        style_obj = self.styles.get(self.current_style_key, self.styles.get("fluent"))
        if style_obj:
            style_obj.draw(painter, self, center, self.hovered_index, sector_progress, center_scale)

    def mouseMoveEvent(self, event):
        center = QPointF(self.width() / 2, self.height() / 2)
        dx = event.position().x() - center.x()
        dy = event.position().y() - center.y()
        distance = math.hypot(dx, dy)

        if self.radius_inner <= distance <= self.radius_outer:
            angle = math.degrees(math.atan2(dy, dx)) + 90
            if angle < 0:
                angle += 360
            num_items = len(self.apps)
            if num_items > 0:
                self.hovered_index = int(angle // (360 / num_items))
        else:
            self.hovered_index = -1

        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.hovered_index != -1:
            command = self.apps[self.hovered_index].get("command", "")
            if command:
                subprocess.Popen(command, shell=True)
            self.hide_animated()
        else:
            self.hide_animated()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.hide_animated()

    def changeEvent(self, event):
        if event.type() == event.Type.ActivationChange and not self.isActiveWindow():
            self.hide_animated()


def get_target_hotkey():
    path = os.path.join("Config", "settings.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f).get("hotkey", "alt+c")
        except Exception:
            pass
    return "alt+c"

def start_hotkey_listener(trigger):
    current_keys = set()
    
    def on_press(key):
        current_keys.add(key)
        target = get_target_hotkey()
        parts = target.split("+")
        
        req_alt = "alt" in parts
        req_space = "space" in parts
        req_char = next((p for p in parts if len(p) == 1), None)

        is_alt = any(k in current_keys for k in [keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r, keyboard.Key.alt_gr])
        is_space = keyboard.Key.space in current_keys
        
        is_char = False
        if req_char:
            try:
                if hasattr(key, 'char') and key.char and key.char.lower() == req_char:
                    is_char = True
                elif hasattr(key, 'vk') and key.vk == ord(req_char.upper()):
                    is_char = True
            except AttributeError:
                pass

        match = True
        if req_alt and not is_alt: match = False
        if req_space and not is_space: match = False
        if req_char and not is_char: match = False

        if match:
            trigger.show_signal.emit()

    def on_release(key):
        try: current_keys.remove(key)
        except KeyError: pass

    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    trigger = TriggerSignal()
    menu = CircleMenuWin11(trigger)

    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor(0, 103, 192))
    painter.setPen(QPen(QColor(255, 255, 255), 2))
    painter.drawEllipse(2, 2, 28, 28)
    painter.end()

    tray_icon = QSystemTrayIcon(QIcon(pixmap), app)
    tray_menu = QMenu()

    action_settings = QAction("Настройки...", app)
    action_settings.triggered.connect(lambda: SettingsWindow().exec())

    action_quit = QAction("Выход", app)
    action_quit.triggered.connect(app.quit)

    tray_menu.addAction(action_settings)
    tray_menu.addSeparator()
    tray_menu.addAction(action_quit)

    tray_icon.setContextMenu(tray_menu)
    tray_icon.show()

    threading.Thread(target=start_hotkey_listener, args=(trigger,), daemon=True).start()

    sys.exit(app.exec())