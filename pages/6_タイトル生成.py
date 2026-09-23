import streamlit as st

from utils.gemini_client import generate, is_configured
from utils.sidebar import render_sidebar

st.set_page_config(page_title="タイトル生成", page_icon="💡")
render_sidebar()

st.title("💡 タイトル・見出し生成")
st.write("記事の内容やテーマから、複数のタイトル案を生成します。")

content = st.text_area("記事の内容・テーマ・要約", height=200, placeholder="例: リモートワークで集中力を維持するための時間管理術についての記事")
col1, col2 = st.columns(2)
with col1:
    style = st.selectbox("スタイル", ["SEOを意識した", "キャッチーで興味を引く", "フォーマルで簡潔な", "疑問形で読者に問いかける", "数字を使った"])
with col2:
    num_titles = st.slider("生成する数", 3, 15, 8)

if st.button("タイトルを生成", type="primary", disabled=not is_configured()):
    if not content.strip():
        st.warning("記事の内容・テーマを入力してください。")
    else:
        prompt = f"""以下の内容の記事に対して、「{style}」タイトル案を{num_titles}個、箇条書きで提案してください。
それぞれのタイトルは重複せず、バリエーションを持たせてください。タイトル以外の説明は不要です。

# 記事の内容
{content}
"""
        with st.spinner("タイトルを生成しています..."):
            try:
                result = generate(prompt)
                st.session_state["title_result"] = result
            except Exception as e:
                st.error(f"生成に失敗しました: {e}")

if "title_result" in st.session_state:
    st.divider()
    st.markdown(st.session_state["title_result"])
