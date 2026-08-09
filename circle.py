import sys
import os
import json
import math
import subprocess
import threading
import urllib.request
from urllib.parse import urlparse
from pynput import keyboard

from PyQt6.QtCore import Qt, QPointF, pyqtSignal, QObject, QPropertyAnimation, QEasingCurve, QFileInfo, pyqtProperty
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QCursor, QIcon, QAction, QPixmap, QKeySequence
from PyQt6.QtWidgets import QApplication, QWidget, QFileIconProvider, QSystemTrayIcon, QMenu, QMessageBox

from settings_gui import SettingsWindow
from styles import load_styles
from i18n import i18n, t
from utils import is_url, get_website_domain, fetch_favicon, resolve_shortcut, load_square_icon


def show_launch_error(cmd_str: str, err_detail: str = ""):
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Critical)
    msg.setWindowTitle(t("msg_error_title", "Ошибка"))
    msg_text = t("msg_launch_failed", cmd=cmd_str)
    if err_detail:
        msg_text += f"\n({err_detail})"
    msg.setText(msg_text)
    msg.exec()


def launch_app(command: str):
    """
    Launches an executable, document, shortcut, website URL, or protocol URI safely on Windows.
    Displays error popup to user if launching fails.
    """
    if not command:
        return
    command = command.strip()

    if command.lower().startswith("start "):
        command = command[6:].strip()

    expanded_cmd = os.path.expandvars(command)

    # Web URL or Protocol
    if is_url(expanded_cmd):
        url = expanded_cmd if (expanded_cmd.lower().startswith(("http://", "https://")) or ":" in expanded_cmd) else f"https://{expanded_cmd}"
        try:
            import webbrowser
            webbrowser.open(url, new=2, autoraise=True)
            return
        except Exception:
            try:
                os.startfile(url)
                return
            except Exception as e:
                show_launch_error(url, str(e))
                return

    # Direct file or executable path
    if os.path.exists(expanded_cmd):
        try:
            os.startfile(expanded_cmd)
            return
        except Exception as e:
            show_launch_error(expanded_cmd, str(e))
            return

    # System command fallback
    try:
        if sys.platform == "win32":
            os.startfile(expanded_cmd)
        else:
            subprocess.Popen(expanded_cmd, shell=True)
    except Exception as e:
        show_launch_error(command, str(e))


class TriggerSignal(QObject):
    show_signal = pyqtSignal()
    reload_config_signal = pyqtSignal()


class HotkeyManager:
    """
    Thread-safe manager for pynput global hotkey listener.
    """
    def __init__(self, trigger):
        self.trigger = trigger
        self.target_keys = set()
        self.current_keys = set()
        self.lock = threading.Lock()
        self.load_target_hotkey()

    def load_target_hotkey(self):
        hotkey_str = "alt+c"
        path = os.path.join("Config", "settings.json")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    hotkey_str = json.load(f).get("hotkey", "alt+c")
            except Exception:
                pass

        parts = [p.strip().lower() for p in hotkey_str.split("+") if p.strip()]
        new_target = set()
        for p in parts:
            if p in ('control', 'ctl'): new_target.add('ctrl')
            elif p in ('option', 'menu'): new_target.add('alt')
            elif p in ('super', 'meta', 'windows', 'cmd'): new_target.add('win')
            else: new_target.add(p)

        with self.lock:
            self.target_keys = new_target

    def normalize_key(self, key):
        if key is None:
            return None
        if isinstance(key, keyboard.Key):
            name = key.name
            if name in ('alt', 'alt_l', 'alt_r', 'alt_gr'): return 'alt'
            elif name in ('ctrl', 'ctrl_l', 'ctrl_r'): return 'ctrl'
            elif name in ('shift', 'shift_l', 'shift_r'): return 'shift'
            elif name in ('cmd', 'cmd_l', 'cmd_r', 'win'): return 'win'
            elif name == 'space': return 'space'
            else: return name.lower()
        elif hasattr(key, 'char') and key.char:
            return key.char.lower()
        elif hasattr(key, 'vk') and key.vk is not None:
            if 65 <= key.vk <= 90 or 48 <= key.vk <= 57:
                return chr(key.vk).lower()
        return str(key).lower()

    def on_press(self, key):
        k = self.normalize_key(key)
        if k:
            self.current_keys.add(k)

        with self.lock:
            if self.target_keys and self.target_keys.issubset(self.current_keys):
                self.trigger.show_signal.emit()

    def on_release(self, key):
        k = self.normalize_key(key)
        if k in self.current_keys:
            self.current_keys.remove(k)

    def start(self):
        with keyboard.Listener(on_press=self.on_press, on_release=self.on_release) as listener:
            listener.join()


class CircleMenuWin11(QWidget):
    def __init__(self, trigger, hotkey_manager):
        super().__init__()
        self.trigger = trigger
        self.hotkey_manager = hotkey_manager

        self.trigger.show_signal.connect(self.show_at_cursor)
        self.trigger.reload_config_signal.connect(self.reload_config)

        self.hovered_index = -1  # -1: none, -2: center close button, >=0: app sector index
        self.radius_inner = 60
        self.radius_outer = 175
        self._anim_progress = 1.0
        self.animation_type = "expand"
        self.theme_mode = "dark"
        self.apps = []
        self.icons = []

        self.styles = load_styles()
        self.current_style_key = "fluent"
        self.icon_provider = QFileIconProvider()

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

        if os.path.exists(settings_path):
            try:
                with open(settings_path, "r", encoding="utf-8") as f:
                    st = json.load(f)
                    self.animation_type = st.get("animation", "expand")
                    self.current_style_key = st.get("style", "fluent")
                    self.theme_mode = st.get("theme_mode", "dark")
                    self.radius_inner = st.get("menu_radius_inner", 60)
                    self.radius_outer = st.get("menu_radius_outer", 175)
                    self.show_hotkeys = st.get("show_hotkeys", True)
                    lang = st.get("language", "ru")
                    i18n.set_language(lang)
            except Exception:
                pass

        if os.path.exists(apps_path):
            try:
                with open(apps_path, "r", encoding="utf-8") as f:
                    self.apps = json.load(f)
            except Exception:
                self.apps = []
        else:
            self.apps = [
                {"name": t("default_app_explorer"), "command": "explorer", "icon": "C:\\Windows\\explorer.exe"},
                {"name": t("default_app_notepad"), "command": "notepad", "icon": "C:\\Windows\\notepad.exe"},
                {"name": t("default_app_calc"), "command": "calc", "icon": "C:\\Windows\\System32\\calc.exe"},
                {"name": t("default_app_taskmgr"), "command": "taskmgr", "icon": "C:\\Windows\\System32\\Taskmgr.exe"}
            ]

        self.load_icons()

    def reload_config(self):
        self.load_configs()
        self.update_window_bounds()
        self.hotkey_manager.load_target_hotkey()
        if hasattr(self, "update_tray_ui") and callable(self.update_tray_ui):
            self.update_tray_ui()

    def load_icons(self):
        self.icons = []
        for app_info in self.apps:
            icon_path = app_info.get("icon", "")
            cmd = app_info.get("command", "")
            name = app_info.get("name", "")

            # Web URL Favicon Fetching
            if is_url(cmd) or (icon_path and is_url(icon_path)):
                web_target = cmd if is_url(cmd) else icon_path
                favicon_file = fetch_favicon(web_target)
                if favicon_file and os.path.exists(favicon_file):
                    icon_path = favicon_file

            target_file = icon_path if (icon_path and os.path.exists(icon_path)) else cmd
            clean_file = resolve_shortcut(target_file) if target_file else ""
            pixmap = None

            if clean_file and os.path.exists(clean_file):
                file_info = QFileInfo(clean_file)
                pixmap = self.icon_provider.icon(file_info).pixmap(32, 32)
                if pixmap.isNull() or clean_file.lower().endswith((".png", ".jpg", ".ico")):
                    pixmap = QPixmap(clean_file).scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

            # Check system apps if path missing
            if not pixmap or pixmap.isNull():
                system_cmd = cmd.strip()
                if system_cmd.lower() in ("explorer", "notepad", "calc", "taskmgr"):
                    sys_path = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "System32", f"{system_cmd}.exe")
                    if not os.path.exists(sys_path):
                        sys_path = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), f"{system_cmd}.exe")
                    if os.path.exists(sys_path):
                        pixmap = self.icon_provider.icon(QFileInfo(sys_path)).pixmap(32, 32)

            # Vector Monogram Fallback
            if not pixmap or pixmap.isNull():
                pixmap = QPixmap(32, 32)
                pixmap.fill(Qt.GlobalColor.transparent)
                p = QPainter(pixmap)
                p.setRenderHint(QPainter.RenderHint.Antialiasing)
                p.setBrush(QColor(0, 120, 212))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(0, 0, 32, 32)
                p.setPen(QColor(255, 255, 255))
                p.setFont(QFont("Roboto", 12, QFont.Weight.Bold))
                letter = name[0].upper() if name else "C"
                p.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, letter)
                p.end()

            self.icons.append(pixmap)

    def init_ui(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self.update_window_bounds()

    def update_window_bounds(self):
        padding = 30
        side = (self.radius_outer + padding) * 2
        self.resize(side, side)

    def init_animation(self):
        self.anim = QPropertyAnimation(self, b"anim_progress")
        self.anim.setDuration(220)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.anim_opacity = QPropertyAnimation(self, b"windowOpacity")
        self.anim_opacity.setDuration(180)
        self.anim_opacity.setEasingCurve(QEasingCurve.Type.OutCubic)

    def show_at_cursor(self):
        cursor_pos = QCursor.pos()
        self.move(cursor_pos.x() - self.width() // 2, cursor_pos.y() - self.height() // 2)

        self.show()
        self.raise_()
        self.activateWindow()

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

        if distance < self.radius_inner:
            self.hovered_index = -2  # Hovering center close button
        elif self.radius_inner <= distance <= (self.radius_outer + 15):
            angle = math.degrees(math.atan2(dy, dx)) + 90
            if angle < 0:
                angle += 360
            num_items = len(self.apps)
            if num_items > 0:
                self.hovered_index = int(angle // (360 / num_items)) % num_items
        else:
            self.hovered_index = -1

        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.hovered_index >= 0:
                command = self.apps[self.hovered_index].get("command", "")
                self.hide_animated()
                if command:
                    launch_app(command)
            else:
                self.hide_animated()
        elif event.button() == Qt.MouseButton.RightButton:
            if self.hovered_index >= 0:
                self.show_app_context_menu(self.hovered_index, event.globalPosition().toPoint())
            else:
                self.hide_animated()

    def show_app_context_menu(self, index: int, global_pos):
        if index < 0 or index >= len(self.apps):
            return

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #1E1E22;
                color: #FFFFFF;
                border: 1px solid #3E3E45;
                border-radius: 8px;
                padding: 6px;
                font-family: 'Roboto', 'Segoe UI', sans-serif;
                font-size: 13px;
                font-weight: 600;
            }
            QMenu::item {
                padding: 6px 16px 6px 12px;
                border-radius: 5px;
                color: #FFFFFF;
            }
            QMenu::item:selected {
                background-color: #0067C0;
                color: #FFFFFF;
            }
            QMenu::item:disabled {
                color: #777777;
            }
            QMenu::separator {
                height: 1px;
                background-color: #33333A;
                margin: 4px 6px;
            }
        """)

        num_apps = len(self.apps)

        act_up = QAction(t("ctx_move_up"), self)
        act_up.setEnabled(num_apps > 1)
        target_up = (index - 1) % num_apps if num_apps > 0 else 0
        act_up.triggered.connect(lambda: self.move_app_sector(index, target_up))
        menu.addAction(act_up)

        act_down = QAction(t("ctx_move_down"), self)
        act_down.setEnabled(num_apps > 1)
        target_down = (index + 1) % num_apps if num_apps > 0 else 0
        act_down.triggered.connect(lambda: self.move_app_sector(index, target_down))
        menu.addAction(act_down)

        menu.addSeparator()

        act_delete = QAction(t("ctx_delete"), self)
        act_delete.triggered.connect(lambda: self.delete_app_sector(index))
        menu.addAction(act_delete)

        menu.addSeparator()

        act_settings = QAction(t("ctx_settings"), self)
        act_settings.triggered.connect(lambda: open_settings_dialog(self.trigger, self))
        menu.addAction(act_settings)

        menu.exec(global_pos)

    def move_app_sector(self, from_idx: int, to_idx: int):
        if 0 <= from_idx < len(self.apps) and 0 <= to_idx < len(self.apps) and from_idx != to_idx:
            self.apps[from_idx], self.apps[to_idx] = self.apps[to_idx], self.apps[from_idx]
            self.save_apps_config()
            self.load_icons()
            self.update()

    def delete_app_sector(self, index: int):
        if 0 <= index < len(self.apps):
            del self.apps[index]
            self.save_apps_config()
            self.load_icons()
            self.hovered_index = -1
            self.update()

    def save_apps_config(self):
        config_dir = "Config"
        os.makedirs(config_dir, exist_ok=True)
        apps_path = os.path.join(config_dir, "apps.json")
        try:
            with open(apps_path, "w", encoding="utf-8") as f:
                json.dump(self.apps, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error saving apps.json: {e}")

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Escape, Qt.Key.Key_Alt):
            self.hide_animated()
            return

        key_text = event.text().strip().lower()
        key_name = QKeySequence(event.key()).toString().lower()

        if key_text or key_name:
            for app in self.apps:
                app_hk = app.get("hotkey", "").strip().lower()
                if app_hk and (key_text == app_hk or key_name == app_hk):
                    cmd = app.get("command", "")
                    self.hide_animated()
                    launch_app(cmd)
                    return

        super().keyPressEvent(event)

    def changeEvent(self, event):
        if event.type() == event.Type.ActivationChange and not self.isActiveWindow():
            if QApplication.activePopupWidget() is not None:
                return
            self.hide_animated()


def open_settings_dialog(trigger, menu_widget):
    dialog = SettingsWindow()
    dialog.config_changed.connect(menu_widget.reload_config)
    dialog.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    trigger = TriggerSignal()
    hotkey_mgr = HotkeyManager(trigger)
    menu = CircleMenuWin11(trigger, hotkey_mgr)

    logo_path = os.path.join(os.path.dirname(__file__), "circle.png")
    app_icon = load_square_icon(logo_path)
    if not app_icon.isNull():
        app.setWindowIcon(app_icon)
        tray_icon = QSystemTrayIcon(app_icon, app)
    else:
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

    action_settings = QAction(t("tray_settings"), app)
    action_settings.triggered.connect(lambda: open_settings_dialog(trigger, menu))

    action_quit = QAction(t("tray_quit"), app)
    action_quit.triggered.connect(app.quit)

    tray_menu.addAction(action_settings)
    tray_menu.addSeparator()
    tray_menu.addAction(action_quit)

    def refresh_tray_labels():
        action_settings.setText(t("tray_settings"))
        action_quit.setText(t("tray_quit"))
        tray_icon.setToolTip(t("tray_tooltip"))

    menu.update_tray_ui = refresh_tray_labels

    tray_icon.setContextMenu(tray_menu)
    tray_icon.setToolTip(t("tray_tooltip"))
    tray_icon.show()

    threading.Thread(target=hotkey_mgr.start, daemon=True).start()

    sys.exit(app.exec())