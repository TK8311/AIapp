#!/bin/bash
# ダブルクリックでAIライティングツールを起動するスクリプト
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  echo "初回起動: 仮想環境を作成しています..."
  python3 -m venv .venv
fi

source .venv/bin/activate

echo "依存関係を確認しています..."
pip install -q -r requirements.txt

echo "アプリを起動します..."
streamlit run Home.py "$@"
