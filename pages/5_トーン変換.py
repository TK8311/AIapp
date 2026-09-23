import streamlit as st

from utils.gemini_client import generate, is_configured
from utils.sidebar import render_sidebar

st.set_page_config(page_title="トーン変換", page_icon="🔄")
render_sidebar()

st.title("🔄 トーン・文体変換")
st.write("文章のトーンや文体を、目的に合わせて変換します。")

text = st.text_area("変換したい文章", height=250)
target_tone = st.selectbox(
    "変換後のトーン",
    ["ビジネス・フォーマル", "丁寧語", "カジュアル・フレンドリー", "学術的", "SNS向け(親しみやすい)", "簡潔・要点のみ"],
)

if st.button("変換する", type="primary", disabled=not is_configured()):
    if not text.strip():
        st.warning("変換したい文章を入力してください。")
    else:
        prompt = f"""以下の文章を、意味内容は変えずに「{target_tone}」のトーンに書き換えてください。
出力は書き換え後の文章のみとしてください。

# 元の文章
{text}
"""
        with st.spinner("変換しています..."):
            try:
                result = generate(prompt)
                st.session_state["tone_result"] = result
            except Exception as e:
                st.error(f"生成に失敗しました: {e}")

if "tone_result" in st.session_state:
    st.divider()
    st.markdown(st.session_state["tone_result"])
