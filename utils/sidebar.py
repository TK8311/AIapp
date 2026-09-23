import os

import streamlit as st

from utils.gemini_client import CUSTOM_MODEL_LABEL, DEFAULT_MODEL, MODEL_OPTIONS


def render_sidebar() -> None:
    st.sidebar.header("⚙️ 設定")

    default_key = os.environ.get("GEMINI_API_KEY", "")
    api_key = st.sidebar.text_input(
        "Gemini APIキー",
        value=st.session_state.get("gemini_api_key", default_key),
        type="password",
        help="Google AI Studio (https://aistudio.google.com/apikey) で取得したAPIキーを入力してください。",
    )
    st.session_state["gemini_api_key"] = api_key

    current_model = st.session_state.get("gemini_model", DEFAULT_MODEL)
    select_options = MODEL_OPTIONS + [CUSTOM_MODEL_LABEL]
    default_index = MODEL_OPTIONS.index(current_model) if current_model in MODEL_OPTIONS else len(MODEL_OPTIONS)
    selected = st.sidebar.selectbox("モデル", select_options, index=default_index)

    if selected == CUSTOM_MODEL_LABEL:
        model = st.sidebar.text_input(
            "モデル名を直接入力",
            value=current_model if current_model not in MODEL_OPTIONS else "",
            placeholder="例: gemini-3.6-flash",
            help="Gemini側でモデルが更新され一覧の候補が使えなくなった場合は、ここに新しいモデル名を入力してください。",
        )
    else:
        model = selected
    st.session_state["gemini_model"] = model

    temperature = st.sidebar.slider(
        "創造性 (temperature)",
        min_value=0.0,
        max_value=1.0,
        value=st.session_state.get("gemini_temperature", 0.7),
        step=0.05,
        help="低いほど堅実・一貫性のある出力、高いほど自由で多様な出力になります。",
    )
    st.session_state["gemini_temperature"] = temperature

    if not api_key:
        st.sidebar.warning("APIキー未設定です。各ツールは利用できません。")
