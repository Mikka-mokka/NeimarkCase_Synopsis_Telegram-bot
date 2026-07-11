"""Обработка голосовых сообщений (voice) и аудиофайлов (audio)"""
import logging
import os
import uuid

from telegram import Update
from telegram.ext import ContextTypes

from config import TMP_DIR
from services.transcriber import transcribe_audio
from services.summarizer import summarize_text
from utils.text_utils import split_for_telegram

logger = logging.getLogger(__name__)


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    audio_obj = message.voice or message.audio

    if audio_obj is None:
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
        reply = (
            f"🎧 Расшифровка:\n{transcript}\n\n"
            f"📝 Конспект:\n\n{summary}"
        )
        for part in split_for_telegram(reply):
            await message.reply_text(part)

    except Exception:
        logger.exception("Ошибка обработки аудио")
        await message.reply_text("Не получилось обработать аудио. Попробуй ещё раз.")
    finally:
        if os.path.exists(local_path):
            os.remove(local_path)
