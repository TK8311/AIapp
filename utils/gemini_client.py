import os
import time

import streamlit as st
from google import genai
from google.genai import errors, types

DEFAULT_MODEL = "gemini-3.6-flash"
MODEL_OPTIONS = ["gemini-3.6-flash", "gemini-3.6-pro", "gemini-2.5-flash", "gemini-2.5-pro"]
CUSTOM_MODEL_LABEL = "カスタム(下に入力)"

MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 3


def get_api_key() -> str | None:
    return st.session_state.get("gemini_api_key") or os.environ.get("GEMINI_API_KEY")


def is_configured() -> bool:
    return bool(get_api_key())


def generate(prompt: str) -> str:
    """Send a prompt to Gemini and return the generated text."""
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError("Gemini APIキーが設定されていません。サイドバーから入力してください。")

    client = genai.Client(api_key=api_key)
    model_name = st.session_state.get("gemini_model", DEFAULT_MODEL)
    temperature = st.session_state.get("gemini_temperature", 0.7)

    last_error: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=temperature),
            )
            if not response.text:
                raise RuntimeError("Geminiから応答がありませんでした。プロンプトを見直してください。")
            return response.text
        except errors.ServerError as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_BACKOFF_SECONDS * (attempt + 1))

    raise RuntimeError(
        f"Geminiサーバーが混雑しているため、{MAX_RETRIES}回試しても応答がありませんでした。"
        "時間をおいて再試行するか、サイドバーで別のモデルに切り替えてください。"
        f" (詳細: {last_error})"
    )
