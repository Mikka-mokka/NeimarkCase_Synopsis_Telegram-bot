"""
Модуль суммаризации.

Есть два режима:
1. LLM-режим (LLM_PROVIDER = "openai" или "anthropic") — текст отправляется
   во внешнюю языковую модель с промптом на составление конспекта.
2. Локальный режим (LLM_PROVIDER = "none") — используется классический
   экстрактивный алгоритм TextRank (библиотека sumy), работающий полностью
   офлайн, без обращения к каким-либо API.

Длинные тексты разбиваются на чанки и суммаризируются по схеме map-reduce:
сначала кратко пересказывается каждый чанк, затем пересказы объединяются
в единый финальный конспект.
"""
import logging

from config import (
    LLM_PROVIDER,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    ANTHROPIC_API_KEY,
    ANTHROPIC_MODEL,
    CHUNK_SIZE_CHARS,
    OPENAI_BASE_URL
)

logger = logging.getLogger(__name__)

SUMMARY_PROMPT = (
    "Ты помощник, который делает конспекты для проверки понимания материала — "
    "не для общего впечатления, а для того, чтобы по конспекту можно было "
    "восстановить суть без обращения к оригиналу. Поверхностный пересказ "
    "\"о чём вообще текст\" не годится — нужны конкретные факты, детали, "
    "риски или нюансы, если они есть в тексте.\n\n"
    "Сначала реши, нужны ли подзаголовки:\n"
    "- Если текст короткий или посвящён одной теме — подзаголовки не нужны, "
    "просто список пунктов (или связные абзацы — смотри ниже).\n"
    "- Если текст длинный и в нём естественно выделяются несколько разных "
    "тем или частей — раздели конспект на смысловые блоки под короткими "
    "подзаголовками (*одна звёздочка*, 2-4 слова), которые ты сама "
    "придумываешь исходя из СОДЕРЖАНИЯ ИМЕННО ЭТОГО текста — не бери "
    "универсальные ярлыки вроде \"Основные идеи\" или \"Риски\", подзаголовок "
    "должен называть конкретную тему блока (например, для текста про "
    "внедрение ИИ в школах это могли бы быть *Причины внедрения*, "
    "*Позиции педагогов*, *Технические ограничения* — свои для каждого "
    "текста). Число подзаголовков не фиксировано — ровно столько, сколько "
    "естественно выделяется в тексте.\n\n"
    "Внутри каждого блока (или во всём конспекте, если подзаголовков нет) "
    "выбери формат под содержание:\n"
    "- Если материал состоит из отдельных фактов, идей, условий или шагов "
    "— оформи как список пунктов через \"- \", каждый пункт — законченная "
    "мысль полным предложением, с пустой строкой между пунктами.\n"
    "- Если материал — связное повествование, где события или мысли "
    "логически вытекают друг из друга — напиши связными абзацами обычным "
    "текстом, без списка, сохраняя причинно-следственные связи.\n\n"
    "В обоих случаях: объём не фиксирован — бери ровно столько пунктов или "
    "абзацев, сколько нужно, чтобы покрыть все самостоятельные мысли текста, "
    "без повторов и без искусственного раздувания или сокращения. Важные "
    "слова и цифры выделяй *одной звёздочкой* (разметка Telegram).\n\n"
    "В конце — одно предложение с главным выводом, без слова \"Вывод:\" "
    "впереди, просто отдельным абзацем.\n\n"
    "Не добавляй ничего, чего нет в исходном тексте. Текст:\n\n"
)

MERGE_PROMPT = (
    "Ниже даны конспекты частей одного текста — каждый со своими "
    "подзаголовками (если они были нужны для этой части), пунктами или "
    "абзацами, и выводом. Части составлялись независимо, поэтому "
    "подзаголовки в разных частях могут не совпадать по формулировкам или "
    "не покрывать текст целиком согласованно.\n\n"
    "Собери из них единый связный конспект: перечитай все части целиком и "
    "заново реши, какие подзаголовки нужны для текста как единого целого "
    "(по тем же правилам — только если текст действительно длинный и "
    "многотемный, формулировки конкретные под содержание, не универсальные "
    "ярлыки). Убери повторы между частями, но сохрани все самостоятельные "
    "детали. Формат внутри блоков (список или связные абзацы) и выделение "
    "*одной звёздочкой* — как в частях. В конце — один общий вывод "
    "отдельным абзацем:\n\n"
)


def _split_into_chunks(text: str, chunk_size: int = CHUNK_SIZE_CHARS) -> list[str]:
    """Разбивает текст на чанки по границам абзацев, не превышая chunk_size."""
    paragraphs = text.split("\n")
    chunks, current = [], ""

    for p in paragraphs:
        if len(current) + len(p) + 1 <= chunk_size:
            current += p + "\n"
        else:
            if current.strip():
                chunks.append(current.strip())
            current = p + "\n"

    if current.strip():
        chunks.append(current.strip())

    return chunks or [text]


def _call_openai(prompt: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=2000,
    )
    return response.choices[0].message.content.strip()


def _call_anthropic(prompt: str) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in message.content if hasattr(block, "text")).strip()


def _call_llm(prompt: str) -> str:
    """
    Единая точка вызова LLM: сама выбирает провайдера по настройке LLM_PROVIDER.
    """
    if LLM_PROVIDER == "openai":
        return _call_openai(prompt)
    if LLM_PROVIDER == "anthropic":
        return _call_anthropic(prompt)
    raise ValueError(f"Неизвестный LLM_PROVIDER: {LLM_PROVIDER}")


def _summarize_with_llm(text: str) -> str:
    """Суммаризация одного куска исходного текста."""
    prompt = SUMMARY_PROMPT + text
    return _call_llm(prompt)


def _merge_with_llm(partial_summaries: list[str]) -> str:
    """Объединение нескольких частичных конспектов в один связный."""
    joined = "\n\n---\n\n".join(partial_summaries)
    prompt = MERGE_PROMPT + joined
    return _call_llm(prompt)


def _summarize_local(text: str, sentences_count: int = 5) -> str:
    """
    Экстрактивная суммаризация без внешних API: алгоритм TextRank
    из библиотеки sumy. Выбирает наиболее "весомые" предложения исходного
    текста — это не пересказ своими словами, а выжимка ключевых фраз.
    """
    from sumy.parsers.plaintext import PlaintextParser
    from sumy.nlp.tokenizers import Tokenizer
    from sumy.summarizers.text_rank import TextRankSummarizer

    parser = PlaintextParser.from_string(text, Tokenizer("russian"))
    summarizer = TextRankSummarizer()
    sentences = summarizer(parser.document, sentences_count)

    bullets = [str(s) for s in sentences]
    return "\n".join(bullets) if bullets else "Не удалось выделить ключевые предложения."


def summarize_text(text: str) -> str:
    """
    Главная точка входа. Сама решает: суммаризировать за один проход
    или разбить на чанки (map-reduce), в зависимости от длины текста.
    """
    text = text.strip()
    if not text:
        return "Текст пуст — нечего конспектировать."

    use_llm = LLM_PROVIDER in ("openai", "anthropic")

    if len(text) <= CHUNK_SIZE_CHARS:
        return _summarize_with_llm(text) if use_llm else _summarize_local(text)

    logger.info("Текст длинный (%d символов), разбиваю на чанки", len(text))
    chunks = _split_into_chunks(text)

    if use_llm:
        partial = [_summarize_with_llm(c) for c in chunks]
        return _merge_with_llm(partial)
    else:
        # для локального алгоритма просто суммаризируем каждый чанк короче
        # и склеиваем результат
        partial = [_summarize_local(c, sentences_count=3) for c in chunks]
        return "\n".join(partial)
