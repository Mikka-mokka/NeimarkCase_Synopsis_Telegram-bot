"""
Распознавание речи из аудиофайлов (voice, audio) с помощью локальной модели
faster-whisper. Модель загружается один раз и переиспользуется между запросами
(чтобы не тратить время на повторную инициализацию).

Требует установленный ffmpeg в системе (для декодирования .ogg/.oga из Telegram)
"""
import logging
from functools import lru_cache

from config import WHISPER_MODEL_SIZE

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_model():
    """Ленивая инициализация модели — грузится только при первом реальном запросе"""
    from faster_whisper import WhisperModel

    logger.info("Загружаю модель Whisper (%s)...", WHISPER_MODEL_SIZE)
    # compute_type="int8" — для работы на обычном CPU без GPU
    return WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")


def transcribe_audio(path: str) -> str:
    """
    Транскрибирует аудиофайл в текст.
    Whisper сам определяет язык, но мы подсказываем "ru" как основной,
    т.к. бот ориентирован на русскоязычных пользователей
    """
    model = _get_model()
    segments, info = model.transcribe(path, language="ru", vad_filter=True)

    logger.info("Распознавание: язык=%s, вероятность=%.2f", info.language, info.language_probability)

    text = " ".join(segment.text.strip() for segment in segments)
    return text.strip()
