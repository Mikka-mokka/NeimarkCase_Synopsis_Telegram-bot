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


def extract_forwarded_text(message) -> str | None:
    """
    Если сообщение переслано (forwarded) и содержит текст — возвращаем его.
    Функция сейчас нигде не используется. Она пока служит как задел на будущее
    (например, пометки источника пересылки)
    """
    if message.forward_origin is not None:
        return message.text or message.caption
    return None
