"""Мелкие вспомогательные функции для работы с текстом и телеграм-сообщениями"""

TELEGRAM_MAX_MESSAGE_LEN = 4096


def split_for_telegram(text: str, limit: int = TELEGRAM_MAX_MESSAGE_LEN) -> list[str]:
    """
    Telegram не даёт отправить сообщение длиннее ~4096 символов.
    Режем длинный ответ на несколько сообщений по границам строк
    """
    if len(text) <= limit:
        return [text]

    parts, current = [], ""
    for line in text.split("\n"):
        if len(current) + len(line) + 1 > limit:
            parts.append(current)
            current = line
        else:
            current += ("\n" if current else "") + line
    if current:
        parts.append(current)
    return parts


async def reply_with_optional_markdown(message, text: str) -> None:
    """
    Отправляет текст с Markdown-разметкой (жирные слова через *звёздочки*).
    Если Telegram не может распарсить разметку (например, в тексте случайно
    оказались незакрытые * _ ` [ ),
    отправляет тот же текст обычным сообщением, чтобы ответ не терялся
    из-за ошибки форматирования.
    """
    from telegram.error import BadRequest

    for part in split_for_telegram(text):
        try:
            await message.reply_text(part, parse_mode="Markdown")
        except BadRequest:
            await message.reply_text(part)


def extract_forwarded_text(message) -> str | None:
    """
    Если сообщение переслано (forwarded) и содержит текст — возвращаем его.
    Функция сейчас нигде не используется. Она пока служит как задел на будущее
    (например, пометки источника пересылки)
    """
    if message.forward_origin is not None:
        return message.text or message.caption
    return None