"""Обработка обычных текстовых сообщений и пересланных сообщений"""
import logging

from telegram import Update
from telegram.ext import ContextTypes

from services.summarizer import summarize_text
from utils.text_utils import split_for_telegram

logger = logging.getLogger(__name__)

"""
Асинхронная функция (сетевой запрос — момент, когда программа ничего не делает, а просто ждёт),
бот может параллельно обрабатывать другие сообщения от других пользователей, а не стоять в очереди
"""
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    message = update.message
    text = message.text or ""

    #пока ждём отправки сообщения, в статусе отоброжаем 'печатает...'
    await message.reply_chat_action("typing")
    try:
        summary = summarize_text(text)
    except Exception:
        logger.exception("Ошибка суммаризации текста")
        await message.reply_text("Не получилось составить конспект. Попробуй ещё раз.")
        return

    reply = f"📝 Конспект:\n\n{summary}"
    for part in split_for_telegram(reply):
        await message.reply_text(part)
