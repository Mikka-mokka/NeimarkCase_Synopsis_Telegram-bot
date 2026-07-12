"""Обработка голосовых сообщений (voice) и аудиофайлов (audio)."""
import logging
import os
import uuid

from telegram import Update
from telegram.ext import ContextTypes

from config import TMP_DIR, MAX_VOICE_SIZE_MB
from services.transcriber import transcribe_audio
from services.summarizer import summarize_text
from utils.text_utils import reply_with_optional_markdown
from utils.rate_limiter import check_rate_limit

logger = logging.getLogger(__name__)


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    audio_obj = message.voice or message.audio

    if audio_obj is None:
        return

    wait_seconds = check_rate_limit(update.effective_user.id)
    if wait_seconds is not None:
        await message.reply_text(f"⏳ Слишком часто. Подожди ещё {wait_seconds:.0f} сек.")
        return

    max_bytes = MAX_VOICE_SIZE_MB * 1024 * 1024
    if audio_obj.file_size and audio_obj.file_size > max_bytes:
        await message.reply_text(
            f"Аудио слишком большое ({audio_obj.file_size / 1024 / 1024:.1f} МБ). "
            f"Максимум — {MAX_VOICE_SIZE_MB} МБ."
        )
        return


    os.makedirs(TMP_DIR, exist_ok=True)
    local_path = os.path.join(TMP_DIR, f"{uuid.uuid4().hex}.ogg")

    await message.reply_chat_action("typing")
    tg_file = await audio_obj.get_file()
    await tg_file.download_to_drive(local_path)

    try:
        await message.reply_text("🎙 Распознаю речь...")
        transcript = transcribe_audio(local_path)

        if not transcript.strip():
            await message.reply_text("Не удалось распознать речь в этом аудио.")
            return

        summary = summarize_text(transcript)
        await message.reply_text(f"🎧 Расшифровка:\n{transcript}")
        await reply_with_optional_markdown(message, f"📝 Конспект:\n\n{summary}")

    except Exception:
        logger.exception("Ошибка обработки аудио")
        await message.reply_text("Не получилось обработать аудио. Попробуй ещё раз.")
    finally:
        if os.path.exists(local_path):
            os.remove(local_path)
