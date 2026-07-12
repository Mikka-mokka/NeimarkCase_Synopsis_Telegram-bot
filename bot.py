import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from handlers.text_handler import handle_text
from handlers.document_handler import handle_document
from handlers.voice_handler import handle_voice

from config import TELEGRAM_BOT_TOKEN, LLM_PROVIDER, OPENAI_MODEL, ANTHROPIC_MODEL, WHISPER_MODEL_SIZE

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
    "📨 Пересылка — переслай сообщение из любого чата, обработаю как обычное сообщение.\n\n"
    "Как выглядит конспект (в режиме LLM):\n"
    "Список ключевых мыслей связными предложениями, важные слова и цифры "
    "выделены жирным. Для длинных и многотемных текстов конспект сам "
    "разбивается на смысловые блоки с подзаголовками — их формулировки "
    "каждый раз подбираются под содержание конкретного текста, а не "
    "берутся из фиксированного шаблона. В конце — короткий общий вывод.\n\n"
    "⚠️ Если текст очень длинный (Telegram ограничивает одно сообщение "
    "~4096 символами) — лучше пришли его файлом .txt, а не вставляй в поле "
    "ввода напрямую. Иначе Telegram может сам разбить его на несколько "
    "отдельных сообщений при отправке, и я обработаю их как разные, "
    "не связанные друг с другом тексты — конспект получится неполным.\n\n"
    "Ограничения:\n"
    "- Максимум ~60000 символов текста за раз\n"
    "- Сканы PDF без текстового слоя не распознаются\n"
    "- Кружочки (video note) пока не поддерживаются\n"
    "- Не чаще одного сообщения в несколько секунд (защита от спама)\n\n"
    "Команды:\n"
    "/start — начать\n"
    "/help — эта справка\n"
    "/about — о проекте\n"
    "/mode — текущие настройки суммаризации"
)

ABOUT_MESSAGE = (
    "🤖 Конспект-бот\n\n"
    "Кейсовый проект для программы «Технологии искусственного "
    "и дополненного интеллекта».\n\n"
    "Технологии: python-telegram-bot, faster-whisper, sumy/TextRank, "
    "опционально OpenAI/Anthropic API.\n\n"
    "Исходный код:\n"
    "https://github.com/Mikka-mokka/NeimarkCase_Synopsis_Telegram-bot"
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(START_MESSAGE)


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP_MESSAGE)


async def about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(ABOUT_MESSAGE)


async def mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if LLM_PROVIDER == "openai":
        summarizer_info = f"LLM (OpenAI, модель {OPENAI_MODEL})"
    elif LLM_PROVIDER == "anthropic":
        summarizer_info = f"LLM (Anthropic, модель {ANTHROPIC_MODEL})"
    else:
        summarizer_info = "локальный алгоритм TextRank (без внешних API)"

    text = (
        f"⚙️ Текущие настройки:\n\n"
        f"Суммаризация: {summarizer_info}\n"
        f"Распознавание речи: faster-whisper, модель \"{WHISPER_MODEL_SIZE}\""
    )
    await update.message.reply_text(text)



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
    app.add_handler(CommandHandler("help", help)) #команда /help
    app.add_handler(CommandHandler("about", about)) #команда /about
    app.add_handler(CommandHandler("mode", mode)) #команда /mode

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
