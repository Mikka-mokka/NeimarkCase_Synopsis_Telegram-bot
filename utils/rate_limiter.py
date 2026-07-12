"""
Простое ограничение частоты сообщений (rate limiting) на пользователя.

Хранит в памяти время последнего ПРИНЯТОГО запроса для каждого user_id.
Если новое сообщение приходит раньше, чем прошло RATE_LIMIT_SECONDS с
прошлого — оно отклоняется, а таймер не сбрасывается (иначе можно было бы
"продлевать" себе бан, просто спамя дальше).

Хранилище — обычный словарь в памяти процесса. Это осознанное упрощение:
при перезапуске бота лимиты сбрасываются, а при нескольких инстансах бота
(что не наш случай) состояние не расшарено. Для учебного прототипа с одним
процессом этого достаточно; для продакшена так делать не стоит — тогда
нужен Redis или другое внешнее хранилище.
"""
import time

from config import RATE_LIMIT_SECONDS

_last_request_time: dict[int, float] = {}


def check_rate_limit(user_id: int) -> float | None:
    """
    Возвращает None, если запрос разрешён (и засчитывает его как принятый).
    Если запрос отклонён — возвращает, сколько секунд осталось подождать.
    """
    now = time.monotonic()
    last = _last_request_time.get(user_id)

    if last is not None:
        elapsed = now - last
        remaining = RATE_LIMIT_SECONDS - elapsed
        if remaining > 0:
            return remaining

    _last_request_time[user_id] = now
    return None
