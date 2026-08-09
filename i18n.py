import os
import json


class I18n:
    def __init__(self, locales_dir="locales"):
        self.locales_dir = locales_dir
        self.current_lang = "ru"
        self.translations = {}
        self.available_languages = {}
        self.load_available_languages()
        self.set_language(self.current_lang)

    def load_available_languages(self):
        self.available_languages = {}
        if not os.path.exists(self.locales_dir):
            os.makedirs(self.locales_dir, exist_ok=True)

        for filename in os.listdir(self.locales_dir):
            if filename.endswith(".json"):
                lang_code = filename[:-5]
                filepath = os.path.join(self.locales_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        display_name = data.get("_language_name", lang_code.upper())
                        self.available_languages[lang_code] = display_name
                except Exception:
                    pass

        if not self.available_languages:
            self.available_languages = {"ru": "Русский", "en": "English"}

    def set_language(self, lang_code: str):
        if not lang_code:
            lang_code = "ru"
        lang_code = lang_code.lower()

        if lang_code not in self.available_languages:
            self.load_available_languages()

        filepath = os.path.join(self.locales_dir, f"{lang_code}.json")
        if not os.path.exists(filepath):
            filepath = os.path.join(self.locales_dir, "ru.json")

        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    self.translations = json.load(f)
                    self.current_lang = lang_code
                    return
            except Exception:
                pass

        self.translations = {}

    def t(self, key: str, default: str = None, **kwargs) -> str:
        text = self.translations.get(key, default if default is not None else key)
        if kwargs and isinstance(text, str):
            try:
                return text.format(**kwargs)
            except Exception:
                pass
        return text


# Global i18n instance
i18n = I18n()
t = i18n.t
