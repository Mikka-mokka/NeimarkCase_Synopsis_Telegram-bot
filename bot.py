import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from config import TELEGRAM_BOT_TOKEN
from handlers.text_handler import handle_text
from handlers.document_handler import handle_document
from handlers.voice_handler import handle_voice

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

START_MESSAGE = (
    "Привет! Я делаю краткие конспекты 📝\n\n"
    "Пришли мне текст, голосовое сообщение или файл (.txt/.docx/.pdf) — "
    "и я верну структурированную выжимку ключевых идей.\n\n"
    "Все форматы и подробности — команда /help"
)

HELP_MESSAGE = (
    "Что я умею:\n\n"
    "📄 Файлы — пришли .txt, .docx или .pdf, верну конспект.\n"
    "🎙 Голосовые и аудио — пришли voice-сообщение или аудиофайл, "
    "сначала распознаю речь, потом сделаю конспект.\n"
    "💬 Текст — просто напиши или перешли сообщение.\n"
    "📨 Пересылка — переслай сообщение из любого чата, обработаю как обычный текст.\n\n"
    "Как выглядит конспект (только для режима LLM):\n"
    "• Основные идеи\n"
    "• Технические детали и практические нюансы\n"
    "• Риски и ограничения\n"
    "• Вывод\n\n"
    "Ограничения:\n"
    "- Максимум ~60000 символов текста за раз\n"
    "- Сканы PDF без текстового слоя не распознаются\n"
    "- Кружочки (video note) пока не поддерживаются\n\n"
    "Команды:\n"
    "/start — начать\n"
    "/help — эта справка\n"
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(START_MESSAGE)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP_MESSAGE)

#Глобальный обраточик ошибок
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Необработанная ошибка", exc_info=context.error)
    if isinstance(update, Update) and update.message:
        await update.message.reply_text(
            "Что-то пошло не так на моей стороне. Попробуй ещё раз чуть позже."
        )


def build_application() -> Application:
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError(
            "Не задан TELEGRAM_BOT_TOKEN. Создай файл .env на основе .env.example."
        )

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    #Какая функция вызывается для какого типа сообщения
    app.add_handler(CommandHandler("start", start)) #команда /start
    app.add_handler(CommandHandler("help", help_command)) #команда /help

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)) #текст и не команда - handle_text
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document)) #все документы - handle_document
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice)) #Голосовое или аудио - handle_voice

    app.add_error_handler(error_handler)
    return app


def main() -> None:
    app = build_application()
    logger.info("Бот запущен, жду сообщений...")
    app.run_polling(allowed_updates=Update.ALL_TYPES) #"есть новые сообщения?"


if __name__ == "__main__":
    main()
