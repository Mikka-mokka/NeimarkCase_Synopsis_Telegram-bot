"""Обработка обычных текстовых сообщений и пересланных сообщений."""
import logging

from telegram import Update
from telegram.ext import ContextTypes

from config import MAX_INPUT_CHARS
from services.summarizer import summarize_text
from utils.text_utils import reply_with_optional_markdown

logger = logging.getLogger(__name__)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Срабатывает на любое текстовое сообщение — как обычное, так и пересланное
    (Telegram присылает пересланный текст в том же поле message.text).
    """
    message = update.message
    text = message.text or ""

    if not text.strip():
        await message.reply_text("Не вижу текста в сообщении 🤔")
        return

    if len(text) > MAX_INPUT_CHARS:
        await message.reply_text(
            f"Текст слишком длинный ({len(text)} символов). "
            f"Максимум — {MAX_INPUT_CHARS}. Пришли файлом (.txt/.docx/.pdf)."
        )
        return

    await message.reply_chat_action("typing")
    try:
        summary = summarize_text(text)
    except Exception:
        logger.exception("Ошибка суммаризации текста")
        await message.reply_text("Не получилось составить конспект. Попробуй ещё раз.")
        return

    reply = f"📝 Конспект:\n\n{summary}"
    await reply_with_optional_markdown(message, reply)
