"""
Конфигурация проекта.
Все чувствительные данные (токены, ключи API) берутся из переменных окружения
через файл .env (см. .env.example) — они никогда не хранятся в коде
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Токен телеграм-бота, выдаёт @BotFather
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Какой LLM-провайдер использовать для суммаризации: "openai", "anthropic" или "none"
# "none" включает локальный алгоритм (без обращения к внешним API)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "none").lower()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-latest")

# Размер модели Whisper для распознавания речи: tiny / base / small / medium
# Чем больше модель — тем точнее, но медленнее и тяжелее для CPU
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "small")

# Максимальная длина текста (в символах), которую бот примет за один раз
MAX_INPUT_CHARS = int(os.getenv("MAX_INPUT_CHARS", "60000"))

# Размер одного чанка текста при разбиении длинных документов (map-reduce суммаризация)
CHUNK_SIZE_CHARS = int(os.getenv("CHUNK_SIZE_CHARS", "4000"))

# Папка для временных файлов (аудио, документы)
TMP_DIR = os.getenv("TMP_DIR", "tmp_files")
