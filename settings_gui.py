import os
import json
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QLineEdit, QLabel, QFileDialog, QMessageBox, QComboBox
)
from styles import load_styles

class SettingsWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки Circle")
        self.resize(550, 560)
        
        self.config_dir = "Config"
        self.apps_file = os.path.join(self.config_dir, "apps.json")
        self.settings_file = os.path.join(self.config_dir, "settings.json")
        
        self.apps = self.load_json(self.apps_file, [])
        self.settings = self.load_json(self.settings_file, {
            "hotkey": "alt+c", 
            "animation": "expand", 
            "style": "fluent",
            "theme_mode": "light"
        })

        self.available_styles = load_styles()
        self.init_ui()

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
        layout = QVBoxLayout()

        # Горячая клавиша
        hotkey_layout = QHBoxLayout()
        hotkey_layout.addWidget(QLabel("Горячая клавиша:"))
        self.hotkey_input = QLineEdit(self.settings.get("hotkey", "alt+c"))
        hotkey_layout.addWidget(self.hotkey_input)
        layout.addLayout(hotkey_layout)

        # Выбор стиля
        style_layout = QHBoxLayout()
        style_layout.addWidget(QLabel("Стиль оформления:"))
        self.style_combo = QComboBox()
        for style_key, style_obj in self.available_styles.items():
            self.style_combo.addItem(style_obj.name, style_key)
        
        current_style = self.settings.get("style", "fluent")
        idx_style = self.style_combo.findData(current_style)
        if idx_style >= 0:
            self.style_combo.setCurrentIndex(idx_style)
        style_layout.addWidget(self.style_combo)
        layout.addLayout(style_layout)

        # Тема (Светлая / Тёмная)
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("Режим темы:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Светлая (Light Mode)", "light")
        self.theme_combo.addItem("Тёмная (Dark Mode)", "dark")
        
        current_mode = self.settings.get("theme_mode", "light")
        idx_mode = self.theme_combo.findData(current_mode)
        if idx_mode >= 0:
            self.theme_combo.setCurrentIndex(idx_mode)
        theme_layout.addWidget(self.theme_combo)
        layout.addLayout(theme_layout)

        # Выбор анимации
        anim_layout = QHBoxLayout()
        anim_layout.addWidget(QLabel("Анимация появления:"))
        self.anim_combo = QComboBox()
        self.anim_combo.addItem("Открытие от курсора (Expand)", "expand")
        self.anim_combo.addItem("Плавное появление (Fade)", "fade")
        
        current_anim = self.settings.get("animation", "expand")
        idx_anim = self.anim_combo.findData(current_anim)
        if idx_anim >= 0:
            self.anim_combo.setCurrentIndex(idx_anim)
        anim_layout.addWidget(self.anim_combo)
        layout.addLayout(anim_layout)

        # Список приложений
        layout.addWidget(QLabel("Приложения в круге:"))
        self.apps_list = QListWidget()
        self.refresh_list()
        layout.addWidget(self.apps_list)

        form_layout = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Название")
        self.cmd_input = QLineEdit()
        self.cmd_input.setPlaceholderText("Команда / путь к exe")
        
        btn_browse = QPushButton("Обзор...")
        btn_browse.clicked.connect(self.browse_exe)

        form_layout.addWidget(self.name_input)
        form_layout.addWidget(self.cmd_input)
        form_layout.addWidget(btn_browse)
        layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        btn_add = QPushButton("Добавить приложение")
        btn_add.clicked.connect(self.add_app)
        
        btn_del = QPushButton("Удалить выбранное")
        btn_del.clicked.connect(self.delete_app)

        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_del)
        layout.addLayout(btn_layout)

        btn_save = QPushButton("Сохранить и применить")
        btn_save.setStyleSheet("background-color: #0067C0; color: white; font-weight: bold; padding: 8px;")
        btn_save.clicked.connect(self.save_all)
        layout.addWidget(btn_save)

        self.setLayout(layout)

    def refresh_list(self):
        self.apps_list.clear()
        for app in self.apps:
            self.apps_list.addItem(f"{app.get('name')} — [{app.get('command')}]")

    def browse_exe(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите программу", "", "Исполняемые файлы (*.exe);;Все файлы (*.*)")
        if file_path:
            self.cmd_input.setText(file_path)
            if not self.name_input.text():
                base_name = os.path.splitext(os.path.basename(file_path))[0].capitalize()
                self.name_input.setText(base_name)

    def add_app(self):
        name = self.name_input.text().strip()
        cmd = self.cmd_input.text().strip()

        if not name or not cmd:
            QMessageBox.warning(self, "Ошибка", "Заполните имя и команду/путь!")
            return

        self.apps.append({"name": name, "command": cmd, "icon": cmd if cmd.endswith(".exe") else ""})
        self.refresh_list()
        self.name_input.clear()
        self.cmd_input.clear()

    def delete_app(self):
        row = self.apps_list.currentRow()
        if row >= 0:
            del self.apps[row]
            self.refresh_list()

    def save_all(self):
        self.settings["hotkey"] = self.hotkey_input.text().strip().lower()
        self.settings["animation"] = self.anim_combo.currentData()
        self.settings["style"] = self.style_combo.currentData()
        self.settings["theme_mode"] = self.theme_combo.currentData()
        self.save_json(self.settings_file, self.settings)
        self.save_json(self.apps_file, self.apps)
        QMessageBox.information(self, "Успех", "Настройки сохранены!")
        self.accept()