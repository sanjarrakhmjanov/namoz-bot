from __future__ import annotations

import json
import os
from typing import Any


class I18n:
    def __init__(self, locales_dir: str) -> None:
        self._locales_dir = locales_dir
        self._data = self._load_locales()

    def _load_locales(self) -> dict[str, dict[str, str]]:
        data: dict[str, dict[str, str]] = {}
        for filename in os.listdir(self._locales_dir):
            if not filename.endswith(".json"):
                continue
            lang = filename.replace(".json", "")
            path = os.path.join(self._locales_dir, filename)
            with open(path, "r", encoding="utf-8") as f:
                data[lang] = json.load(f)
        return data

    def t(self, key: str, lang: str, **kwargs: Any) -> str:
        lang_data = self._data.get(lang) or self._data.get("en", {})
        text = lang_data.get(key, key)
        if kwargs:
            try:
                return text.format(**kwargs)
            except Exception:
                return text
        return text
