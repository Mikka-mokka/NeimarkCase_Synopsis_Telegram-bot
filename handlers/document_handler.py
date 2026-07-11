"""Обработка документов: .txt, .docx, .pdf"""
import logging
import os
import uuid

from telegram import Update
from telegram.ext import ContextTypes

from config import TMP_DIR, MAX_INPUT_CHARS
from services.extractors import extract_text
from services.summarizer import summarize_text
from utils.text_utils import split_for_telegram

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".txt", ".docx", ".pdf"}


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    document = message.document

    _, extension = os.path.splitext(document.file_name or "")  #узнаем расширение
    extension = extension.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        await message.reply_text(
            f"Формат {extension or '(без расширения)'} не поддерживается. "
            f"Пришли .txt, .docx или .pdf."
        )
        return

    os.makedirs(TMP_DIR, exist_ok=True) #Создаём папку для временных файлов, если её ещё нет
    local_path = os.path.join(TMP_DIR, f"{uuid.uuid4().hex}{extension}")    #Генерируем случайный уникальный идентификатор

    await message.reply_chat_action("typing")
    tg_file = await document.get_file() #запрашивает у Telegram служебную информацию о файле
    await tg_file.download_to_drive(local_path) #Скачиваем сам файл на диск бота по сгенерированному пути.

    try:
        text = extract_text(local_path, extension)

        if not text.strip():
            await message.reply_text(
                "Не удалось извлечь текст из файла. "
                "Если это скан PDF без текстового слоя — распознавание OCR пока не поддерживается."
            )
            return

        summary = summarize_text(text)
        reply = f"📄 Конспект файла «{document.file_name}»:\n\n{summary}"
        for part in split_for_telegram(reply):
            await message.reply_text(part)

    except Exception:
        logger.exception("Ошибка обработки документа")
        await message.reply_text("Не получилось обработать файл. Попробуй ещё раз.")
    finally:
        if os.path.exists(local_path):
            os.remove(local_path)
