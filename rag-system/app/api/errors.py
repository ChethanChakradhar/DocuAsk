from __future__ import annotations

from fastapi import HTTPException


OPENAI_KEY_MESSAGE = (
    "I could not connect to OpenAI because the API key is missing or invalid. "
    "Open the .env file, set OPENAI_API_KEY to a valid key, then restart the app."
)
OPENAI_QUOTA_MESSAGE = (
    "OpenAI accepted your API key, but this account or project has no available quota. "
    "Add billing or credits in the OpenAI dashboard, then try again."
)


def api_error_from_exception(exc: Exception, fallback: str) -> HTTPException:
    message = str(exc)
    lower_message = message.lower()

    if (
        "invalid_api_key" in lower_message
        or "incorrect api key" in lower_message
        or "openai_api_key is not configured" in lower_message
    ):
        return HTTPException(status_code=401, detail=OPENAI_KEY_MESSAGE)

    if "insufficient_quota" in lower_message or "exceeded your current quota" in lower_message:
        return HTTPException(status_code=429, detail=OPENAI_QUOTA_MESSAGE)

    return HTTPException(status_code=500, detail=fallback)
