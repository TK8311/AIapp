import streamlit as st

from utils.gemini_client import generate, is_configured
from utils.sidebar import render_sidebar

st.set_page_config(page_title="翻訳", page_icon="🌐")
render_sidebar()

st.title("🌐 翻訳")
st.write("文章を指定した言語・トーンで翻訳します。")

text = st.text_area("翻訳したい文章", height=250)
col1, col2 = st.columns(2)
with col1:
    target_lang = st.selectbox(
        "翻訳先の言語",
        ["英語", "日本語", "中国語(簡体字)", "韓国語", "フランス語", "スペイン語", "ドイツ語", "その他(下に入力)"],
    )
    custom_lang = ""
    if target_lang == "その他(下に入力)":
        custom_lang = st.text_input("言語名を入力")
with col2:
    tone = st.selectbox("トーン", ["自然な標準的な文体", "フォーマル・ビジネス的", "カジュアル"])

if st.button("翻訳する", type="primary", disabled=not is_configured()):
    lang = custom_lang if target_lang == "その他(下に入力)" else target_lang
    if not text.strip():
        st.warning("翻訳したい文章を入力してください。")
    elif not lang:
        st.warning("翻訳先の言語を入力してください。")
    else:
        prompt = f"""以下の文章を{lang}に翻訳してください。トーンは「{tone}」にしてください。
翻訳結果のみを出力し、説明や元の文章の再掲は不要です。

# 元の文章
{text}
"""
        with st.spinner("翻訳しています..."):
            try:
                result = generate(prompt)
                st.session_state["translate_result"] = result
            except Exception as e:
                st.error(f"生成に失敗しました: {e}")

if "translate_result" in st.session_state:
    st.divider()
    st.markdown(st.session_state["translate_result"])
