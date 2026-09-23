import streamlit as st

from utils.gemini_client import generate, is_configured
from utils.sidebar import render_sidebar

st.set_page_config(page_title="文章校正", page_icon="✍️")
render_sidebar()

st.title("✍️ 文章校正・添削")
st.write("誤字脱字や表現のおかしい箇所を修正し、改善版と変更点を提示します。")

text = st.text_area("校正したい文章", height=250)
strictness = st.selectbox("校正の観点", ["誤字脱字・文法のみ", "表現・言い回しも改善", "文章全体を洗練させる"])

if st.button("校正する", type="primary", disabled=not is_configured()):
    if not text.strip():
        st.warning("校正したい文章を入力してください。")
    else:
        prompt = f"""あなたはプロの校正者です。以下の文章を校正してください。

# 校正の観点
{strictness}

# 出力形式(必ずこの2つのセクションで出力すること)
## 修正後の文章
(校正済みの文章全体をここに書く)

## 主な変更点
(箇条書きで、どこをどう直したか、理由とともに簡潔に説明する)

# 校正対象の文章
{text}
"""
        with st.spinner("校正しています..."):
            try:
                result = generate(prompt)
                st.session_state["proofread_result"] = result
            except Exception as e:
                st.error(f"生成に失敗しました: {e}")

if "proofread_result" in st.session_state:
    st.divider()
    st.markdown(st.session_state["proofread_result"])
