import streamlit as st

from utils.gemini_client import generate, is_configured
from utils.sidebar import render_sidebar

st.set_page_config(page_title="ブログ記事作成", page_icon="📝")
render_sidebar()

st.title("📝 ブログ記事作成")
st.write("テーマや条件を入力すると、Geminiがブログ記事の下書きを作成します。")

col1, col2 = st.columns(2)
with col1:
    topic = st.text_input("記事のテーマ・タイトル案", placeholder="例: 在宅ワークの生産性を上げる5つの習慣")
    audience = st.text_input("想定読者", placeholder="例: 20〜30代の在宅ワーカー")
with col2:
    tone = st.selectbox("トーン", ["親しみやすい", "フォーマル", "専門的", "カジュアル", "熱意のある"])
    length = st.selectbox("文字数の目安", ["短め (300〜500字)", "普通 (800〜1200字)", "長め (1500字以上)"])

keywords = st.text_area("含めたいキーワード・要点 (任意)", placeholder="例: ポモドーロテクニック, タスク管理, 集中力")
outline_only = st.checkbox("見出し構成(アウトライン)のみ生成する")
extra = st.text_area("その他の指示 (任意)", placeholder="例: 冒頭に読者への問いかけを入れてほしい")

if st.button("記事を生成", type="primary", disabled=not is_configured()):
    if not topic:
        st.warning("記事のテーマを入力してください。")
    else:
        prompt = f"""あなたはSEOに強いプロのブログライター兼編集者です。以下の条件でブログ記事{"の見出し構成(アウトライン)" if outline_only else ""}を作成してください。

# 条件
- テーマ: {topic}
- 想定読者: {audience or "特に指定なし"}
- トーン: {tone}
- 文字数の目安: {length}
- 含めたいキーワード・要点: {keywords or "特に指定なし"}
- その他の指示: {extra or "特に指定なし"}

# SEOの方針
- メインキーワード(上記のテーマ・キーワードから抽出)を、タイトル・導入文の冒頭100字以内・見出し(##)のいずれかに自然に含めてください。キーワードの詰め込みは避け、読みやすさを優先してください。
- 検索意図(知りたい・比較したい・やり方を知りたい等)を推測し、それに答える形で構成してください。
- 見出しは##(h2)・###(h3)の階層構造にし、1つの見出しには1つのトピックだけを扱ってください。
- 導入文で「この記事で分かること」を簡潔に示し、読者が読み続ける理由を提示してください。
- 可能な箇所で具体的な数字・手順・例を入れ、抽象的な言い回しを避けてください。
- まとめの最後に、読者の次のアクションを促す一文(CTA)を入れてください。

# 出力形式
- Markdown形式で見出し(##)を使い、読みやすい構成にしてください。
- {"見出しと各セクションで書く内容の要約(1〜2文)だけを出力してください。本文は書かないでください。" if outline_only else "導入・本文(複数セクション)・まとめの構成で、実際の本文を書いてください。"}
- {"" if outline_only else "本文の最後に、検索結果に表示するための「メタディスクリプション案」(120字前後、メインキーワードを含む)を1つ、`---` の区切り線の下に追加してください。"}
"""
        with st.spinner("記事を生成しています..."):
            try:
                result = generate(prompt)
                st.session_state["blog_result"] = result
            except Exception as e:
                st.error(f"生成に失敗しました: {e}")

if "blog_result" in st.session_state:
    st.divider()
    st.markdown(st.session_state["blog_result"])
    st.download_button(
        "Markdownでダウンロード",
        st.session_state["blog_result"],
        file_name="blog_draft.md",
        mime="text/markdown",
    )
