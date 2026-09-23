import streamlit as st

from utils.gemini_client import generate, is_configured
from utils.sidebar import render_sidebar

st.set_page_config(page_title="文章要約", page_icon="📄")
render_sidebar()

st.title("📄 文章要約")
st.write("長い文章を貼り付けると、指定した形式で要約します。")

uploaded_file = st.file_uploader("テキストファイルをアップロード (任意)", type=["txt", "md"])
default_text = uploaded_file.read().decode("utf-8") if uploaded_file else ""
text = st.text_area("要約したい文章", value=default_text, height=250)

col1, col2 = st.columns(2)
with col1:
    summary_type = st.selectbox("要約の形式", ["箇条書き", "一段落の要約", "一文で要約", "詳細な要約"])
with col2:
    summary_length = st.select_slider("要約の長さ", options=["とても短く", "短め", "普通", "やや長め"], value="普通")

if st.button("要約する", type="primary", disabled=not is_configured()):
    if not text.strip():
        st.warning("要約したい文章を入力してください。")
    else:
        prompt = f"""以下の文章を要約してください。

# 条件
- 形式: {summary_type}
- 長さ: {summary_length}
- 元の文章の重要なポイントや数値、固有名詞は漏らさないようにしてください。
- 日本語で出力してください。

# 元の文章
{text}
"""
        with st.spinner("要約しています..."):
            try:
                result = generate(prompt)
                st.session_state["summary_result"] = result
            except Exception as e:
                st.error(f"生成に失敗しました: {e}")

if "summary_result" in st.session_state:
    st.divider()
    st.markdown(st.session_state["summary_result"])
