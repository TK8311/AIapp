import streamlit as st

from utils.gemini_client import generate, is_configured
from utils.sidebar import render_sidebar

st.set_page_config(page_title="メール返信作成", page_icon="📧")
render_sidebar()

st.title("📧 メール返信作成")
st.write("受信したメールの内容と伝えたい要点を入力すると、返信文の下書きを作成します。")

original_email = st.text_area("受信したメールの本文", height=200, placeholder="ここに受信メールの本文を貼り付けてください")
key_points = st.text_area("返信で伝えたい要点", height=120, placeholder="例: 提案には賛成だが、納期は来月末に変更してほしい")

col1, col2 = st.columns(2)
with col1:
    tone = st.selectbox("トーン", ["丁寧・ビジネス的", "カジュアル", "謝罪・お詫び", "丁重にお断り", "感謝"])
with col2:
    length = st.selectbox("長さ", ["簡潔に", "普通", "詳しく"])

if st.button("返信文を生成", type="primary", disabled=not is_configured()):
    if not original_email or not key_points:
        st.warning("受信メールの本文と伝えたい要点の両方を入力してください。")
    else:
        prompt = f"""あなたは優秀なビジネスアシスタントです。以下の受信メールに対する返信メールの下書きを作成してください。

# 受信メール
{original_email}

# 返信で伝えたい要点
{key_points}

# 条件
- トーン: {tone}
- 長さ: {length}
- 適切な宛名・書き出し・結びの挨拶を含めてください。
- 自然で失礼のない日本語のビジネスメール文にしてください。
"""
        with st.spinner("返信文を生成しています..."):
            try:
                result = generate(prompt)
                st.session_state["email_result"] = result
            except Exception as e:
                st.error(f"生成に失敗しました: {e}")

if "email_result" in st.session_state:
    st.divider()
    st.text_area("生成された返信文", st.session_state["email_result"], height=300)
    st.download_button(
        "テキストでダウンロード",
        st.session_state["email_result"],
        file_name="email_reply.txt",
    )
