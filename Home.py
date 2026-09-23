import streamlit as st
from dotenv import load_dotenv

from utils.sidebar import render_sidebar

load_dotenv()

st.set_page_config(page_title="AIライティングツール", page_icon="🖋️", layout="wide")

render_sidebar()

st.title("🖋️ AIライティングツール")
st.write(
    "Gemini APIを使った個人用のライティング支援ツール集です。"
    "左のサイドバーからAPIキーを設定し、使いたい機能を選んでください。"
)

st.divider()

tools = [
    ("pages/1_ブログ記事作成.py", "📝 ブログ記事作成", "テーマやキーワードからブログ記事の下書きを生成します。"),
    ("pages/2_メール返信作成.py", "📧 メール返信作成", "受信メールの内容から返信文の下書きを作成します。"),
    ("pages/3_文章要約.py", "📄 文章要約", "長い文章を要点・箇条書きなどに要約します。"),
    ("pages/4_文章校正.py", "✍️ 文章校正・添削", "誤字脱字や表現の違和感を修正し、改善点を提示します。"),
    ("pages/5_トーン変換.py", "🔄 トーン・文体変換", "文章のトーン(丁寧・カジュアルなど)を変換します。"),
    ("pages/6_タイトル生成.py", "💡 タイトル・見出し生成", "記事内容から複数のタイトル案を生成します。"),
    ("pages/7_翻訳.py", "🌐 翻訳", "文章を指定した言語に翻訳します。"),
]

cols = st.columns(2)
for i, (page, label, desc) in enumerate(tools):
    with cols[i % 2]:
        with st.container(border=True):
            st.page_link(page, label=label)
            st.caption(desc)

st.divider()
st.markdown(
    "**セットアップ方法**\n\n"
    "1. `pip install -r requirements.txt`\n"
    "2. [Google AI Studio](https://aistudio.google.com/apikey) でAPIキーを取得\n"
    "3. サイドバーにAPIキーを入力するか、`.env` に `GEMINI_API_KEY` を設定\n"
    "4. `streamlit run Home.py` で起動"
)
