import os
from typing import Dict, Any
import json

from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError

# Загружаем переменные из .env файла
load_dotenv()


class Config(BaseModel):
    """Конфигурация бота с валидацией через pydantic."""

    BOT_TOKEN: str
    BOT_ADMINS: list
    DB_TYPE: str  # "mysql" или "postgres"
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    DB_HOST: str
    DB_PORT: int | None = None  # Опционально, если используется сокет
    DB_SOCKET: str | None = None  # Опционально для Unix-сокета
    ALLOWED_CHAT_ID: int  # ID чата, где работает бот
    LANGUAGE_SELECTION_TIMEOUT: int  # Таймаут выбора языка
    QUIZ_ANSWER_TIMEOUT: int  # Таймаут ответа на квиз
    MESSAGE_DELETE_DELAY_CORRECT: int  # Задержка удаления при правильном ответе
    MESSAGE_DELETE_DELAY_INCORRECT: int  # Задержка удаления при неправильном ответе
    MESSAGE_DELETE_DELAY_TIMEOUT: int  # Задержка удаления при таймауте квиза
    DEFAULT_MESSAGE_DELETE_DELAY: int  # Задержка удаления по умолчанию
    MUTE_DURATION: int  # Длительность мута
    UNBAN_DELAY: int  # Пауза перед анбаном
    DB_DELETE_DELAY: int  # Пауза перед удалением из БД
    CLEANUP_INTERVAL: int  # Интервал проверки истекших банов

    class Config:
        extra = "forbid"  # Запрещаем лишние поля


# Загружаем и валидируем конфигурацию
try:
    raw_env = {key: os.getenv(key) for key in Config.__annotations__}
    if raw_env.get("BOT_ADMINS"):
        raw_env["BOT_ADMINS"] = json.loads(raw_env["BOT_ADMINS"])

    config = Config(**raw_env)
except ValidationError as e:
    raise ValueError(f"Ошибка в конфигурации: {e}")


def load_json_config() -> Dict[str, Any]:
    """Загрузка данных из config.json с базовой валидацией."""
    with open("data/config.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    if not all(key in data for key in ["questions", "dialogs"]):
        raise ValueError("Отсутствуют обязательные ключи в config.json")
    return data


# Загружаем JSON-конфигурацию
json_config = load_json_config()
questions = json_config["questions"]
dialogs = json_config["dialogs"]
