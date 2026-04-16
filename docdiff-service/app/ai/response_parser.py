import json
import logging
import re

from pydantic import BaseModel, ValidationError

logger = logging.getLogger("docdiff.ai")


def extract_json_from_text(text: str) -> str | None:
    code_block_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if code_block_match:
        return code_block_match.group(1).strip()
    json_match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
    if json_match:
        return json_match.group(1).strip()
    return None


def parse_ai_response(text: str, schema: type[BaseModel] | None = None) -> dict | list | None:
    json_str = extract_json_from_text(text)
    if json_str is None:
        logger.warning("No JSON found in AI response")
        return None
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse JSON from AI response: {e}")
        return None
    if schema is not None:
        try:
            validated = schema.model_validate(data)
            return validated.model_dump()
        except ValidationError as e:
            logger.warning(f"AI response failed schema validation: {e}")
            return data
    return data


def safe_parse_or_flag(
    text: str, schema: type[BaseModel] | None = None
) -> tuple[dict | None, bool]:
    result = parse_ai_response(text, schema)
    if result is None:
        return None, True
    return result, False
