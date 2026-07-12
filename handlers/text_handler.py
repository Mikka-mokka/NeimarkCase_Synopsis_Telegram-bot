"""Обработка обычных текстовых сообщений и пересланных сообщений."""
import logging

from telegram import Update
from telegram.ext import ContextTypes

from services.summarizer import summarize_text
from utils.text_utils import reply_with_optional_markdown
from utils.rate_limiter import check_rate_limit

logger = logging.getLogger(__name__)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Срабатывает на любое текстовое сообщение — как обычное, так и пересланное
    (Telegram присылает пересланный текст в том же поле message.text).
    """
    message = update.message

    wait_seconds = check_rate_limit(update.effective_user.id)
    if wait_seconds is not None:
        await message.reply_text(f"⏳ Слишком часто. Подожди ещё {wait_seconds:.0f} сек.")
        return

    text = message.text or ""

    if not text.strip():
        await message.reply_text("Не вижу текста в сообщении 🤔")
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
