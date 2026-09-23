# Home.pyを読み解く:AIライティングツールの入口はこうでできている

Streamlit + Gemini APIで作られた個人用ライティングツール集の入口ファイル、`Home.py`を1行ずつ読み解きます。

## このアプリの全体像

このリポジトリは、Gemini APIを使った「AIライティングツール集」です。ブログ記事作成、メール返信作成、要約、校正、トーン変換、タイトル生成、翻訳という7つのツールが、1つのStreamlitアプリの中に、それぞれ独立したページとして並んでいます。

`Home.py`はそのアプリを開いたときに最初に表示される「玄関」のページです。ここには機能自体(文章を生成する処理など)は一切書かれていません。役割は次の3つだけです。

- アプリ全体のタイトルと説明を表示する
- 7つのツールへのリンクをカード形式で並べる
- セットアップ手順(APIキーの取得方法など)を案内する

Streamlitでは`pages/`フォルダの中に番号付きファイル(`1_ブログ記事作成.py`など)を置くだけで、自動的にサイドバーのメニューに表示される仕組みがあります。`Home.py`はその「本体」であり、各ページを束ねる共通のルーター(交通整理役)は存在しません。各ページがそれぞれ独立して動く、シンプルな構成です。

## Home.pyを上から順に読む

全部45行と短いファイルです。ブロックごとに見ていきます。

### 1. 準備(1〜10行目)

```python
import streamlit as st
from dotenv import load_dotenv

from utils.sidebar import render_sidebar

load_dotenv()

st.set_page_config(page_title="AIライティングツール", page_icon="🖋️", layout="wide")

render_sidebar()
```

- `load_dotenv()`で`.env`ファイルの内容(`GEMINI_API_KEY`など)を環境変数として読み込みます。
- `st.set_page_config(...)`はStreamlitのページ設定(タブタイトルやレイアウト)で、各ページの先頭で必ず1回呼ばれます。
- `render_sidebar()`は`utils/sidebar.py`に定義された関数で、サイドバーのAPIキー入力欄やモデル選択を描画します。全ページが先頭でこれを呼んでいます。

### 2. タイトルと説明(12〜16行目)

```python
st.title("🖋️ AIライティングツール")
st.write(
    "Gemini APIを使った個人用ライティング支援ツール集です。"
    "左のサイドバーからAPIキーを設定し、使いたい機能を選んでください。"
)
```

ページ上部に見出しと使い方の案内文を表示するだけのシンプルな部分です。

### 3. ツール一覧のデータ(20〜28行目)

```python
tools = [
    ("pages/1_ブログ記事作成.py", "📝 ブログ記事作成", "テーマやキーワードからブログ記事の下書きを生成します。"),
    ("pages/2_メール返信作成.py", "📧 メール返信作成", "受信メールの内容から返信文の下書きを作成します。"),
    # 以下、7つのツール分がタプルで並ぶ
]
```

各タプルは`(ページのファイルパス, 表示ラベル, 説明文)`の3要素です。このリストが、ホーム画面のカード一覧とサイドバーナビの両方の元データになっています(サイドバーの方はStreamlitが`pages/`フォルダを自動読み取りして作っています)。

### 4. カード一覧の描画(30〜35行目)

```python
cols = st.columns(2)
for i, (page, label, desc) in enumerate(tools):
    with cols[i % 2]:
        with st.container(border=True):
            st.page_link(page, label=label)
            st.caption(desc)
```

2列のレイアウトを作り、`i % 2`で交互に左右の列に振り分けています。`st.page_link()`はStreamlitの機能で、クリックすると指定したページに遷移します。

### 5. セットアップ手順(37〜44行目)

```python
st.markdown(
    "**セットアップ方法**\n\n"
    "1. `pip install -r requirements.txt`\n"
    "2. [Google AI Studio](https://aistudio.google.com/apikey) でAPIキーを取得\n"
    "3. サイドバーにAPIキーを入力するか、`.env`に`GEMINI_API_KEY`を設定\n"
    "4. `streamlit run Home.py`で起動"
)
```

初めて使う人向けの手順をMarkdownで表示しています。

## 舞台裏の仕組み: render_sidebar() と generate()

`Home.py`自体はGemini APIを一切呼んでいません。実際のAI実行部分は`utils/`下の2つのファイルが担っています。

### utils/sidebar.py — 設定画面

`render_sidebar()`は以下3つを`st.session_state`に保存します。

| 項目 | 保存先のキー | 入力方法 |
| --- | --- | --- |
| APIキー | `gemini_api_key` | パスワード形式のテキスト入力(未入力時は`.env`の値を初期表示) |
| モデル名 | `gemini_model` | プルダウン選択(`gemini-3.6-flash`など)、またはカスタム入力 |
| temperature | `gemini_temperature` | 0.0〜1.0のスライダー(初期値0.7) |

APIキーが空のままだとサイドバーに警告を出します。

### utils/gemini_client.py — Geminiと話す唯一の場所

`generate(prompt: str) -> str`が各ツールページから呼ばれる関数です。呼ばれるたびに`st.session_state`からAPIキー・モデル・temperatureを読み取って`genai.Client`を作り直します。主な振る舞い:

- APIキー未設定 → `RuntimeError`
- Geminiサーバーが混雑(ServerError) → 最大3回まで自動リトライ(3秒・6秒・9秒と待機を伸ばす)
- 応答にテキストがない → `RuntimeError`

この設計のポイントは、**`generate()`はpythonの引数ではなく`st.session_state`を直接参照する**ことです。そのため、各ツールページは必ず`render_sidebar()`を先に呼んでおく必要があります(順番を間違えると設定が反映されません)。

つまり、各ツールページの流れは次の3ステップで共通しています。

1. `render_sidebar()`で設定を描画
2. ユーザー入力を集めてプロンプトを組み立てる
3. `generate(prompt)`を呼んで結果を表示する

Home.pyはこの中の1つとしか行わない(タイトルやカード一覧を出すだけでGeminiは一度も呼ばない)ページということです。

## まとめ: 新しいツールを追加するには

`Home.py`は「ツール一覧を出す受付台」であり、AIとのやりとりは全て`pages/`内の各ページが担います。全体の関係はこうなります。

```
Home.py (ツール一覧を表示)
   │
   ▼
pages/N_*.py (各ツールページ)
   ├─→ render_sidebar()  設定をsession_stateへ
   └─→ generate(prompt)  Gemini呼び出し
```

新しいツールを追加する手順はシンプルです。

1. `pages/N_名前.py`を新規作成し、既存ツールページと同じ構成(`set_page_config` → `render_sidebar()` → 入力受付 → ボタン押下で`generate(prompt)`)で実装する
2. `Home.py`の`tools`リストに`(パス, ラベル, 説明文)`のタプルを一行追加する

これだけでホーム画面のカード一覧とサイドバーナビの両方に新ツールが自動的に現れます。`Home.py`自体を変更する必要はこの1行追加だけです。
