import os
import json
from PyQt6.QtCore import Qt, pyqtSignal, QFileInfo, QSize
from PyQt6.QtGui import QIcon, QFont, QPixmap, QColor, QPainter, QKeySequence, QKeyEvent
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton,
    QListWidget, QListWidgetItem, QLineEdit, QLabel, QFileDialog, QMessageBox, QComboBox,
    QGroupBox, QSlider, QSpinBox
)
from styles import load_styles
from i18n import i18n, t
from utils import is_url, get_website_domain, fetch_favicon, resolve_shortcut, load_square_icon


try:
    from PyQt6.QtWidgets import QFileIconProvider
except ImportError:
    from PyQt6.QtGui import QFileIconProvider


class HotkeyKeySequenceWidget(QPushButton):
    """
    Button widget that captures a hotkey press when clicked.
    """
    hotkey_changed = pyqtSignal(str)

    def __init__(self, current_hotkey="alt+c", parent=None):
        super().__init__(parent)
        self.recording = False
        self.set_hotkey_text(current_hotkey)
        self.clicked.connect(self.start_recording)

    def set_hotkey_text(self, text):
        self.current_hotkey = text.strip().lower()
        display_text = self.current_hotkey.upper().replace("+", " + ")
        self.setText(t("hotkey_prompt", hotkey=display_text))

    def start_recording(self):
        self.recording = True
        self.setText(t("hotkey_recording"))
        self.setStyleSheet("background-color: #0067C0; color: white; font-weight: bold; border-radius: 6px; padding: 6px;")
        self.setFocus()

    def keyPressEvent(self, event: QKeyEvent):
        if not self.recording:
            super().keyPressEvent(event)
            return

        key = event.key()
        if key in (Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt, Qt.Key.Key_Meta):
            return  # Wait for full combination

        modifiers = event.modifiers()
        parts = []
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            parts.append("ctrl")
        if modifiers & Qt.KeyboardModifier.AltModifier:
            parts.append("alt")
        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            parts.append("shift")
        if modifiers & Qt.KeyboardModifier.MetaModifier:
            parts.append("win")

        key_seq = QKeySequence(key).toString().lower()
        if key_seq:
            parts.append(key_seq)

        hotkey_str = "+".join(parts)
        self.recording = False
        self.setStyleSheet("")
        self.set_hotkey_text(hotkey_str)
        self.hotkey_changed.emit(hotkey_str)

    def focusOutEvent(self, event):
        if self.recording:
            self.recording = False
            self.setStyleSheet("")
            self.set_hotkey_text(self.current_hotkey)
        super().focusOutEvent(event)


class SingleKeyRecorderWidget(QPushButton):
    key_changed = pyqtSignal(str)

    def __init__(self, current_key="", parent=None):
        super().__init__(parent)
        self.recording = False
        self.set_key_text(current_key)
        self.clicked.connect(self.start_recording)

    def set_key_text(self, text):
        self.current_key = text.strip().lower()
        if self.current_key:
            display_text = self.current_key.upper()
            self.setText(f" ⌨ {display_text}")
        else:
            self.setText(t("btn_bind_key"))

    def start_recording(self):
        self.recording = True
        self.setText(t("hotkey_recording"))
        self.setStyleSheet("background-color: #0067C0; color: white; font-weight: bold; border-radius: 6px; padding: 6px;")
        self.setFocus()

    def keyPressEvent(self, event: QKeyEvent):
        if not self.recording:
            super().keyPressEvent(event)
            return

        key = event.key()
        if key == Qt.Key.Key_Escape:
            self.recording = False
            self.setStyleSheet("")
            self.set_key_text("")
            self.key_changed.emit("")
            return

        key_seq = QKeySequence(key).toString().lower()
        if key_seq:
            self.current_key = key_seq
            self.recording = False
            self.setStyleSheet("")
            self.set_key_text(self.current_key)
            self.key_changed.emit(self.current_key)

    def focusOutEvent(self, event):
        if self.recording:
            self.recording = False
            self.setStyleSheet("")
            self.set_key_text(self.current_key)
        super().focusOutEvent(event)


class SettingsWindow(QDialog):
    config_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_dir = "Config"
        self.apps_file = os.path.join(self.config_dir, "apps.json")
        self.settings_file = os.path.join(self.config_dir, "settings.json")

        self.apps = self.load_json(self.apps_file, [])
        self.settings = self.load_json(self.settings_file, {
            "hotkey": "alt+c",
            "animation": "expand",
            "style": "fluent",
            "theme_mode": "dark",
            "language": "ru",
            "menu_radius_inner": 60,
            "menu_radius_outer": 175
        })

        i18n.set_language(self.settings.get("language", "ru"))
        self.setWindowTitle(t("window_title"))
        self.resize(600, 680)
        self.setMinimumSize(540, 600)

        logo_path = os.path.join(os.path.dirname(__file__), "circle.png")
        icon = load_square_icon(logo_path)
        if not icon.isNull():
            self.setWindowIcon(icon)

        self.available_styles = load_styles()
        self.icon_provider = QFileIconProvider()
        self.init_ui()
        self.apply_theme_style()

    def load_json(self, path, default):
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return default

    def save_json(self, path, data):
        os.makedirs(self.config_dir, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(12)

        # --- Group 1: General Settings ---
        group_gen = QGroupBox(t("group_general"))
        gen_grid = QGridLayout()
        gen_grid.setHorizontalSpacing(14)
        gen_grid.setVerticalSpacing(10)

        # Row 0: Hotkey
        hk_lbl = QLabel(t("label_hotkey"))
        hk_lbl.setFont(QFont("Roboto", 9, QFont.Weight.Bold))
        self.hotkey_btn = HotkeyKeySequenceWidget(self.settings.get("hotkey", "alt+c"))
        gen_grid.addWidget(hk_lbl, 0, 0)
        gen_grid.addWidget(self.hotkey_btn, 0, 1, 1, 3)

        # Combos
        self.style_combo = QComboBox()
        for key, style_obj in self.available_styles.items():
            self.style_combo.addItem(style_obj.name, key)
        curr_style = self.settings.get("style", "fluent")
        idx_style = self.style_combo.findData(curr_style)
        if idx_style >= 0: self.style_combo.setCurrentIndex(idx_style)

        self.theme_combo = QComboBox()
        self.theme_combo.addItem(t("theme_dark"), "dark")
        self.theme_combo.addItem(t("theme_light"), "light")
        curr_theme = self.settings.get("theme_mode", "dark")
        idx_theme = self.theme_combo.findData(curr_theme)
        if idx_theme >= 0: self.theme_combo.setCurrentIndex(idx_theme)

        self.anim_combo = QComboBox()
        self.anim_combo.addItem(t("anim_expand"), "expand")
        self.anim_combo.addItem(t("anim_fade"), "fade")
        curr_anim = self.settings.get("animation", "expand")
        idx_anim = self.anim_combo.findData(curr_anim)
        if idx_anim >= 0: self.anim_combo.setCurrentIndex(idx_anim)

        self.lang_combo = QComboBox()
        for lang_code, display_name in i18n.available_languages.items():
            self.lang_combo.addItem(display_name, lang_code)
        curr_lang = self.settings.get("language", "ru")
        idx_lang = self.lang_combo.findData(curr_lang)
        if idx_lang >= 0: self.lang_combo.setCurrentIndex(idx_lang)

        self.chk_show_hotkeys = QCheckBox(t("label_show_hotkeys"))
        self.chk_show_hotkeys.setChecked(self.settings.get("show_hotkeys", True))

        # Row 1: Style & Theme
        gen_grid.addWidget(QLabel(t("label_style")), 1, 0)
        gen_grid.addWidget(self.style_combo, 1, 1)
        gen_grid.addWidget(QLabel(t("label_theme")), 1, 2)
        gen_grid.addWidget(self.theme_combo, 1, 3)

        # Row 2: Animation & Language
        gen_grid.addWidget(QLabel(t("label_anim")), 2, 0)
        gen_grid.addWidget(self.anim_combo, 2, 1)
        gen_grid.addWidget(QLabel(t("label_language")), 2, 2)
        gen_grid.addWidget(self.lang_combo, 2, 3)

        # Row 3: Show Hotkeys checkbox
        gen_grid.addWidget(self.chk_show_hotkeys, 3, 0, 1, 4)

        gen_grid.setColumnStretch(1, 1)
        gen_grid.setColumnStretch(3, 1)

        group_gen.setLayout(gen_grid)
        main_layout.addWidget(group_gen)

        # --- Group 2: Radius Controls ---
        group_rad = QGroupBox(t("group_radius"))
        rad_layout = QVBoxLayout()

        # Inner radius
        in_rad_layout = QHBoxLayout()
        in_rad_layout.addWidget(QLabel(t("label_inner_radius")))
        self.slider_inner = QSlider(Qt.Orientation.Horizontal)
        self.slider_inner.setRange(30, 100)
        self.slider_inner.setValue(self.settings.get("menu_radius_inner", 60))
        self.spin_inner = QSpinBox()
        self.spin_inner.setRange(30, 100)
        self.spin_inner.setSingleStep(1)
        self.spin_inner.setValue(self.slider_inner.value())
        self.slider_inner.valueChanged.connect(self.spin_inner.setValue)
        self.spin_inner.valueChanged.connect(self.slider_inner.setValue)
        in_rad_layout.addWidget(self.slider_inner)
        in_rad_layout.addWidget(self.spin_inner)
        rad_layout.addLayout(in_rad_layout)

        # Outer radius
        out_rad_layout = QHBoxLayout()
        out_rad_layout.addWidget(QLabel(t("label_outer_radius")))
        self.slider_outer = QSlider(Qt.Orientation.Horizontal)
        self.slider_outer.setRange(120, 260)
        self.slider_outer.setValue(self.settings.get("menu_radius_outer", 175))
        self.spin_outer = QSpinBox()
        self.spin_outer.setRange(120, 260)
        self.spin_outer.setSingleStep(1)
        self.spin_outer.setValue(self.slider_outer.value())
        self.slider_outer.valueChanged.connect(self.spin_outer.setValue)
        self.spin_outer.valueChanged.connect(self.slider_outer.setValue)
        out_rad_layout.addWidget(self.slider_outer)
        out_rad_layout.addWidget(self.spin_outer)
        rad_layout.addLayout(out_rad_layout)

        # Reset button for Radius
        btn_reset_rad = QPushButton(t("btn_reset_radius"))
        btn_reset_rad.clicked.connect(self.reset_radius_defaults)
        rad_layout.addWidget(btn_reset_rad)

        group_rad.setLayout(rad_layout)
        main_layout.addWidget(group_rad)

        # --- Group 3: App List ---
        group_apps = QGroupBox(t("group_apps"))
        apps_layout = QVBoxLayout()

        app_controls_layout = QHBoxLayout()
        self.apps_list = QListWidget()
        self.apps_list.setIconSize(QSize(24, 24))
        self.refresh_list()

        # Up / Down order buttons
        order_btn_layout = QVBoxLayout()
        btn_up = QPushButton("▲")
        btn_up.setToolTip("UP")
        btn_up.clicked.connect(self.move_app_up)
        btn_down = QPushButton("▼")
        btn_down.setToolTip("DOWN")
        btn_down.clicked.connect(self.move_app_down)
        order_btn_layout.addWidget(btn_up)
        order_btn_layout.addWidget(btn_down)
        order_btn_layout.addStretch()

        app_controls_layout.addWidget(self.apps_list, stretch=1)
        app_controls_layout.addLayout(order_btn_layout)
        apps_layout.addLayout(app_controls_layout)

        # Add app inputs
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(t("placeholder_app_name"))
        self.cmd_input = QLineEdit()
        self.cmd_input.setPlaceholderText(t("placeholder_app_cmd"))
        self.key_btn = SingleKeyRecorderWidget("")
        btn_browse = QPushButton(t("btn_browse"))
        btn_browse.clicked.connect(self.browse_exe)

        form_layout = QHBoxLayout()
        form_layout.addWidget(self.name_input, stretch=2)
        form_layout.addWidget(self.cmd_input, stretch=3)
        form_layout.addWidget(btn_browse)
        form_layout.addWidget(self.key_btn)

        apps_layout.addLayout(form_layout)

        # Action buttons
        btn_layout = QHBoxLayout()
        btn_add = QPushButton(t("btn_add_app"))
        btn_add.clicked.connect(self.add_app)

        btn_del = QPushButton(t("btn_delete_app"))
        btn_del.clicked.connect(self.delete_app)

        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_del)
        apps_layout.addLayout(btn_layout)

        group_apps.setLayout(apps_layout)
        main_layout.addWidget(group_apps, stretch=1)

        # Import / Export & Save Buttons
        bottom_layout = QHBoxLayout()

        btn_export = QPushButton(t("btn_export"))
        btn_export.clicked.connect(self.export_config)

        btn_import = QPushButton(t("btn_import"))
        btn_import.clicked.connect(self.import_config)

        btn_save = QPushButton(t("btn_save"))
        btn_save.setStyleSheet(
            "background-color: #0067C0; color: white; font-size: 13px; font-weight: bold; padding: 10px; border-radius: 6px;"
        )
        btn_save.clicked.connect(self.save_all)

        bottom_layout.addWidget(btn_export)
        bottom_layout.addWidget(btn_import)
        bottom_layout.addWidget(btn_save, stretch=1)

        main_layout.addLayout(bottom_layout)

        self.setLayout(main_layout)

    def reset_radius_defaults(self):
        self.slider_inner.setValue(60)
        self.spin_inner.setValue(60)
        self.slider_outer.setValue(180)
        self.spin_outer.setValue(180)

    def refresh_list(self):
        self.apps_list.clear()
        for app in self.apps:
            name = app.get("name", "")
            cmd = app.get("command", "")
            icon_path = app.get("icon", "")

            if is_url(cmd) or (icon_path and is_url(icon_path)):
                web_target = cmd if is_url(cmd) else icon_path
                favicon_file = fetch_favicon(web_target)
                if favicon_file and os.path.exists(favicon_file):
                    icon_path = favicon_file

            icon = QIcon()
            target_path = icon_path if (icon_path and os.path.exists(icon_path)) else cmd
            clean_path = resolve_shortcut(target_path) if target_path else ""
            if clean_path and os.path.exists(clean_path):
                if clean_path.lower().endswith((".png", ".jpg", ".ico")):
                    pm = QPixmap(clean_path).scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    icon = QIcon(pm)
                else:
                    icon = self.icon_provider.icon(QFileInfo(clean_path))

            if icon.isNull():
                # Generate placeholder monogram icon
                pm = QPixmap(24, 24)
                pm.fill(Qt.GlobalColor.transparent)
                p = QPainter(pm)
                p.setRenderHint(QPainter.RenderHint.Antialiasing)
                p.setBrush(QColor(0, 103, 192))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(0, 0, 24, 24)
                p.setPen(QColor(255, 255, 255))
                p.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                letter = name[0].upper() if name else "?"
                p.drawText(pm.rect(), Qt.AlignmentFlag.AlignCenter, letter)
                p.end()
                icon = QIcon(pm)

            hk = app.get("hotkey", "").strip().upper()
            hk_str = f"  (⌨ {hk})" if hk else ""
            item = QListWidgetItem(icon, f"{name}  —  [{cmd}]{hk_str}")
            self.apps_list.addItem(item)

    def browse_exe(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, t("file_dialog_app"), "", t("file_dialog_exe_filter")
        )
        if file_path:
            file_path = os.path.normpath(file_path)
            self.cmd_input.setText(file_path)
            if not self.name_input.text():
                base_name = os.path.splitext(os.path.basename(file_path))[0].capitalize()
                self.name_input.setText(base_name)

    def add_app(self):
        name = self.name_input.text().strip()
        cmd = self.cmd_input.text().strip()
        hotkey_val = self.key_btn.current_key

        if is_url(cmd):
            domain = get_website_domain(cmd)
            if not name and domain:
                name = domain.capitalize()
            if not cmd.lower().startswith(("http://", "https://")) and not ":" in cmd:
                cmd = "https://" + cmd

        if not name or not cmd:
            QMessageBox.warning(self, t("msg_error_title"), t("msg_fill_fields"))
            return

        icon_path = ""
        if is_url(cmd):
            favicon_file = fetch_favicon(cmd)
            if favicon_file and os.path.exists(favicon_file):
                icon_path = favicon_file
        elif os.path.exists(cmd) and cmd.lower().endswith((".exe", ".lnk", ".ico")):
            icon_path = cmd

        self.apps.append({"name": name, "command": cmd, "icon": icon_path, "hotkey": hotkey_val})
        self.refresh_list()
        self.name_input.clear()
        self.cmd_input.clear()
        self.key_btn.set_key_text("")

    def delete_app(self):
        row = self.apps_list.currentRow()
        if row >= 0:
            del self.apps[row]
            self.refresh_list()

    def move_app_up(self):
        row = self.apps_list.currentRow()
        n = len(self.apps)
        if n > 1 and row >= 0:
            target = (row - 1) % n
            self.apps[row], self.apps[target] = self.apps[target], self.apps[row]
            self.refresh_list()
            self.apps_list.setCurrentRow(target)

    def move_app_down(self):
        row = self.apps_list.currentRow()
        n = len(self.apps)
        if n > 1 and row >= 0:
            target = (row + 1) % n
            self.apps[row], self.apps[target] = self.apps[target], self.apps[row]
            self.refresh_list()
            self.apps_list.setCurrentRow(target)

    def save_all(self):
        self.settings["hotkey"] = self.hotkey_btn.current_hotkey
        self.settings["animation"] = self.anim_combo.currentData()
        self.settings["style"] = self.style_combo.currentData()
        self.settings["theme_mode"] = self.theme_combo.currentData()
        self.settings["language"] = self.lang_combo.currentData()
        self.settings["show_hotkeys"] = self.chk_show_hotkeys.isChecked()
        self.settings["menu_radius_inner"] = self.spin_inner.value()
        self.settings["menu_radius_outer"] = self.spin_outer.value()

        i18n.set_language(self.settings["language"])
        self.setWindowTitle(t("window_title"))
        self.save_json(self.settings_file, self.settings)
        self.save_json(self.apps_file, self.apps)

        self.config_changed.emit()
        QMessageBox.information(self, t("msg_saved_title"), t("msg_saved_text"))

    def export_config(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, t("btn_export"), "circle_backup.json", "JSON Files (*.json)"
        )
        if not file_path:
            return

        self.settings["hotkey"] = self.hotkey_btn.current_hotkey
        self.settings["animation"] = self.anim_combo.currentData()
        self.settings["style"] = self.style_combo.currentData()
        self.settings["theme_mode"] = self.theme_combo.currentData()
        self.settings["language"] = self.lang_combo.currentData()
        self.settings["show_hotkeys"] = self.chk_show_hotkeys.isChecked()
        self.settings["menu_radius_inner"] = self.spin_inner.value()
        self.settings["menu_radius_outer"] = self.spin_outer.value()

        export_data = {
            "version": "1.0",
            "settings": self.settings,
            "apps": self.apps
        }

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=4)
            QMessageBox.information(self, t("msg_saved_title"), t("msg_export_success", path=file_path))
        except Exception as e:
            QMessageBox.critical(self, t("msg_error_title"), t("msg_export_error", error=e))

    def import_config(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, t("btn_import"), "", "JSON Files (*.json)"
        )
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, dict) and "settings" in data and "apps" in data:
                self.settings = data["settings"]
                self.apps = data["apps"]
            elif isinstance(data, dict) and ("hotkey" in data or "style" in data):
                self.settings = data
            else:
                QMessageBox.warning(self, t("msg_error_title"), t("msg_import_invalid"))
                return

            self.hotkey_btn.set_hotkey_text(self.settings.get("hotkey", "alt+c"))

            curr_style = self.settings.get("style", "fluent")
            idx_style = self.style_combo.findData(curr_style)
            if idx_style >= 0: self.style_combo.setCurrentIndex(idx_style)

            curr_theme = self.settings.get("theme_mode", "dark")
            idx_theme = self.theme_combo.findData(curr_theme)
            if idx_theme >= 0: self.theme_combo.setCurrentIndex(idx_theme)

            curr_anim = self.settings.get("animation", "expand")
            idx_anim = self.anim_combo.findData(curr_anim)
            if idx_anim >= 0: self.anim_combo.setCurrentIndex(idx_anim)

            curr_lang = self.settings.get("language", "ru")
            idx_lang = self.lang_combo.findData(curr_lang)
            if idx_lang >= 0: self.lang_combo.setCurrentIndex(idx_lang)
            i18n.set_language(curr_lang)

            self.slider_inner.setValue(self.settings.get("menu_radius_inner", 60))
            self.slider_outer.setValue(self.settings.get("menu_radius_outer", 175))

            self.refresh_list()
            self.save_json(self.settings_file, self.settings)
            self.save_json(self.apps_file, self.apps)
            self.config_changed.emit()

            QMessageBox.information(self, t("msg_saved_title"), t("msg_import_success"))
        except Exception as e:
            QMessageBox.critical(self, t("msg_error_title"), t("msg_import_error", error=e))

    def apply_theme_style(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #202020;
                color: #FFFFFF;
                font-family: 'Roboto', 'Segoe UI', sans-serif;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #383838;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 12px;
                color: #E0E0E0;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 6px;
            }
            QLabel {
                color: #CCCCCC;
            }
            QLineEdit, QComboBox, QSpinBox {
                background-color: #2D2D2D;
                color: #FFFFFF;
                border: 1px solid #404040;
                border-radius: 5px;
                padding: 5px;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
                border: 1px solid #0067C0;
            }
            QListWidget {
                background-color: #2B2B2B;
                border: 1px solid #383838;
                border-radius: 6px;
                color: #FFFFFF;
                padding: 4px;
            }
            QListWidget::item {
                padding: 6px;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #0067C0;
                color: white;
            }
            QPushButton {
                background-color: #2D2D2D;
                color: #FFFFFF;
                border: 1px solid #404040;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #383838;
                border: 1px solid #505050;
            }
            QPushButton:pressed {
                background-color: #1F1F1F;
            }
        """)