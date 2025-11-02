import logging
from typing import Optional

from aiogram import types


LANGUAGE_MAP = {
    "ru": "ru",
    "be": "ru",
    "uk": "ru",
    "ky": "ru",
    "kk": "ru",
    "tg": "ru",
    "uz": "ru",
    "en": "en",
    "es": "en",
    "pt": "en",
    "de": "en",
    "fr": "en",
    "it": "en",
    "nl": "en",
    "pl": "en",
    "tr": "en",
    "ko": "en",
    "ja": "en",
    "zh": "zh",
}


def get_user_language(user: types.User) -> str:
    """
    Определяет язык пользователя из language_code.
    Возвращает 'ru', 'en' или 'zh', иначе 'en' как default.
    """
    if not user.language_code:
        return "en"

    lang_code = user.language_code.lower()
    language = LANGUAGE_MAP.get(lang_code, "en")

    logging.info(f"User {user.id} language detected: {lang_code} -> {language}")
    return language
