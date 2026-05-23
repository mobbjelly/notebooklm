import json
import logging
import re
import time
from json import JSONDecodeError
from typing import Any

from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.messages import BaseMessage

from core.config import settings

logger = logging.getLogger("knowbase.llm")


def make_llm() -> ChatTongyi:
    return ChatTongyi(
        model_name=settings.LLM_MODEL,
        dashscope_api_key=settings.DASHSCOPE_API_KEY,
    )


async def invoke_llm_json(operation: str, messages: list[BaseMessage]) -> dict[str, Any]:
    started = time.perf_counter()
    input_chars = sum(len(str(message.content)) for message in messages)
    logger.info("LLM call start operation=%s model=%s input_chars=%s", operation, settings.LLM_MODEL, input_chars)
    try:
        resp = await make_llm().ainvoke(messages)
        raw = str(resp.content).strip()
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        logger.info("LLM call done operation=%s elapsed_ms=%s output_chars=%s", operation, elapsed_ms, len(raw))
        logger.debug("LLM raw output operation=%s content=%s", operation, raw[:4000])
        return parse_llm_json(raw)
    except Exception:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        logger.exception("LLM call failed operation=%s elapsed_ms=%s", operation, elapsed_ms)
        raise


def parse_llm_json(raw: str) -> dict[str, Any]:
    cleaned = _strip_code_fence(raw)
    try:
        return json.loads(cleaned)
    except JSONDecodeError as first_error:
        extracted = _extract_json_object(cleaned)
        if extracted != cleaned:
            try:
                return json.loads(extracted)
            except JSONDecodeError:
                pass
        escaped = _escape_invalid_json_backslashes(extracted)
        if escaped != extracted:
            try:
                return json.loads(escaped)
            except JSONDecodeError:
                pass
        repaired = _repair_truncated_json(escaped)
        if repaired:
            repaired = _escape_invalid_json_backslashes(repaired)
            try:
                return json.loads(repaired)
            except JSONDecodeError:
                pass
        raise first_error


def _strip_code_fence(raw: str) -> str:
    text = raw.strip()
    if not text.startswith("```"):
        return text
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _extract_json_object(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1:
        return text
    if end == -1 or end <= start:
        return text[start:]
    return text[start:end + 1]


def _escape_invalid_json_backslashes(text: str) -> str:
    valid_escapes = {'"', "\\", "/", "b", "f", "n", "r", "t", "u"}
    result = []
    in_string = False
    escaped = False
    index = 0

    while index < len(text):
        char = text[index]
        if not in_string:
            result.append(char)
            if char == '"':
                in_string = True
            index += 1
            continue

        if escaped:
            if char in valid_escapes:
                result.append(char)
            else:
                result.append("\\")
                result.append(char)
            escaped = False
            index += 1
            continue

        if char == "\\":
            result.append(char)
            escaped = True
        else:
            result.append(char)
            if char == '"':
                in_string = False
        index += 1

    if escaped:
        result.append("\\")
    return "".join(result)


def _repair_truncated_json(text: str) -> str | None:
    start = text.find("{")
    if start == -1:
        return None
    text = text[start:].rstrip()
    if not text:
        return None

    in_string = False
    escaped = False
    stack: list[str] = []
    for char in text:
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            stack.append("}")
        elif char == "[":
            stack.append("]")
        elif char in "}]":
            if stack and stack[-1] == char:
                stack.pop()

    repaired = text
    if in_string:
        repaired += '"'
    while stack:
        closer = stack.pop()
        if repaired.rstrip().endswith(":"):
            repaired += ' ""'
        elif repaired.rstrip().endswith(","):
            repaired = repaired.rstrip().rstrip(",")
        repaired += closer
    return repaired
