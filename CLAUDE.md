# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## これは何か

StreamlitとGemini APIで作った個人用(認証なし・DBなし)のAIライティングツール集です。ブログ執筆、メール返信作成、要約、校正、トーン変換、タイトル生成、翻訳といった複数のライティングツールを、1つのマルチページStreamlitアプリにまとめています。

## コマンド

```bash
pip install -r requirements.txt        # 依存関係のインストール
streamlit run Home.py                  # アプリを起動 (http://localhost:8501)
python3 -m py_compile Home.py utils/*.py pages/*.py   # 編集後の構文チェック
```

このリポジトリに自動テストやlint設定はありません。

APIキーの設定方法: `.env` ファイルに `GEMINI_API_KEY` を設定するか(`Home.py` で `python-dotenv` により読み込まれる)、実行時にサイドバーの入力欄に貼り付けるか、どちらでも可。どちらも `utils/gemini_client.get_api_key()` が読み取ります。

## アーキテクチャ

**Streamlit標準のマルチページアプリ構成。** `Home.py` がエントリーポイントで、`pages/` 内の各ファイル(`1_ブログ記事作成.py` のように番号プレフィックス付き)はStreamlitがサイドバーのナビゲーションに自動表示する、それぞれ独立して実行されるスクリプトです。共通のルーターは存在せず、各ページが冒頭で `render_sidebar()` と自前の `st.set_page_config(...)` を呼び出します。

**全ページから読み込まれる `utils/` 配下の共有モジュール:**
- `utils/gemini_client.py` — Geminiと通信する唯一の場所。`google-genai` SDK(`from google import genai`)を使用しており、**非推奨の `google-generativeai` パッケージは使っていません**(このプロジェクトからは削除済み)。`generate(prompt: str) -> str` は呼び出しごとに `st.session_state` から現在のAPIキー・モデル・temperatureを読み取って `genai.Client` を作成し、キー未設定またはGeminiがテキストを返さなかった場合は `RuntimeError` を送出します。
- `utils/sidebar.py` — `render_sidebar()` がAPIキー入力欄・モデル選択・temperatureスライダーを描画し、`st.session_state` の `gemini_api_key` / `gemini_model` / `gemini_temperature` に書き込みます。`generate()` はこれらのセッション状態をパラメータではなく直接参照するため、各ページは `generate()` を呼ぶ前に必ず `render_sidebar()` を呼び出す必要があります。

**各ページ共通のパターン**(`pages/` 内の7つのツールページはすべて同じ構成 — 新しいツールを追加する際はこの形をコピーする):
1. `st.set_page_config(...)` + `render_sidebar()`
2. `st.text_input` / `st.text_area` / `st.selectbox` で入力を収集
3. ボタン押下時(`disabled=not is_configured()`)、`# 条件` / `# 出力形式` 形式の日本語指示ブロックを含む1つのプロンプト文字列を組み立て、`st.spinner(...)` 内で `generate(prompt)` を呼び出し、結果を `st.session_state[<page>_result]` に保存する
4. 保存した結果は `if button:` ブロックの外側で描画する(rerun後も表示され続けるようにするため)。必要に応じて `st.download_button` も用意する

UIの文言・生成されるコンテンツはすべて日本語。新しいツールを追加する際もこれに合わせること。

## 新しいツールの追加方法

上記の各ページ共通パターンに従って `pages/N_名前.py` を新規作成し、`Home.py` の `tools` リストにそのエントリ(パス・ラベル・説明文)を追加すればホーム画面のグリッドに表示されます。
