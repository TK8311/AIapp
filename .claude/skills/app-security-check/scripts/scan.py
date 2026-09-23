#!/usr/bin/env python3
"""Streamlit + Gemini アプリ向けの機械的なセキュリティ一次スキャン。

見つかるのは「確認すべき箇所の候補」であり、確定した脆弱性ではない。
最終判断はSKILL.mdの手順に沿って、コードの文脈を読んだうえで行うこと。

使い方: python3 scan.py [プロジェクトのルート]  (省略時はカレントディレクトリ)
出力: 標準出力にMarkdown形式の候補一覧
"""
from __future__ import annotations

import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path

SKIP_DIRS = {".venv", "venv", "__pycache__", ".git", "node_modules", ".claude", ".agents", "site-packages"}
TEXT_SUFFIXES = {".py", ".md", ".toml", ".json", ".txt", ".command", ".sh", ".yaml", ".yml", ".cfg", ".ini", ".example"}

SECRET_PATTERNS = [
    ("Google APIキー形式の文字列", re.compile(r"AIza[0-9A-Za-z_\-]{35}")),
    ("APIキーらしき代入", re.compile(r"""(?i)(api[_-]?key|secret|token)\s*[:=]\s*["'][A-Za-z0-9_\-]{20,}["']""")),
]

CODE_PATTERNS = [
    ("unsafe_allow_html=True (LLM出力や入力をHTMLとして描画するとXSSの恐れ)", re.compile(r"unsafe_allow_html\s*=\s*True")),
    ("components.html / iframe 描画", re.compile(r"components\.(v1\.)?(html|iframe)\(")),
    ("eval / exec", re.compile(r"(?<![\w.])(eval|exec)\(")),
    ("サブプロセス / シェル実行", re.compile(r"subprocess\.|os\.system\(|os\.popen\(")),
    ("pickle / 安全でないyaml読み込み", re.compile(r"pickle\.loads?\(|yaml\.load\((?![^)]*SafeLoader)")),
    ("例外の内容をそのまま画面表示", re.compile(r"st\.(error|warning|write|exception)\([^)]*\{e\}|st\.exception\(")),
    ("環境変数の値をウィジェットの初期値に使用 (ブラウザへ秘密情報が送られる恐れ)", re.compile(r"value\s*=.*(environ|getenv|default_key|API_KEY)", re.I)),
    ("APIキー等をprint/loggingで出力", re.compile(r"(print|logging\.\w+|logger\.\w+)\([^)]*(api_key|API_KEY|secret)")),
    ("file_uploader (サイズ・種類・デコードエラーの扱いを確認)", re.compile(r"st\.file_uploader\(")),
    ("ユーザー入力由来のパスでファイルを開いている可能性", re.compile(r"open\(\s*(f[\"']|[a-z_]+\s*[,)])")),
]


def iter_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            p = Path(dirpath) / name
            if p.suffix in TEXT_SUFFIXES or name in {".env", ".gitignore", "requirements.txt"}:
                yield p


def rel(root: Path, p: Path) -> str:
    return str(p.relative_to(root))


def scan_secrets(root: Path, out: list[str]):
    for p in iter_files(root):
        if p.name == ".env":
            continue  # .env に秘密があるのは正常。別途 gitignore と権限を確認する
        try:
            lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        for i, line in enumerate(lines, 1):
            for label, pat in SECRET_PATTERNS:
                if pat.search(line) and "your_api_key" not in line:
                    masked = pat.sub(lambda m: m.group(0)[:6] + "…(伏字)", line.strip())
                    out.append(f"- [秘密情報] {rel(root, p)}:{i} {label}: `{masked[:120]}`")


def scan_code(root: Path, out: list[str]):
    for p in iter_files(root):
        if p.suffix != ".py":
            continue
        lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
        for i, line in enumerate(lines, 1):
            for label, pat in CODE_PATTERNS:
                if pat.search(line):
                    out.append(f"- [コード] {rel(root, p)}:{i} {label}: `{line.strip()[:120]}`")


def scan_git_and_env(root: Path, out: list[str]):
    gi = root / ".gitignore"
    ignored = gi.read_text(encoding="utf-8").splitlines() if gi.exists() else []
    ignored = [l.strip() for l in ignored]
    if not gi.exists():
        out.append("- [設定] .gitignore がありません (.env が誤ってコミットされる恐れ)")
    else:
        for must in (".env", ".streamlit/secrets.toml"):
            if must not in ignored:
                out.append(f"- [設定] .gitignore に `{must}` が含まれていません")
    env = root / ".env"
    if env.exists():
        mode = stat.S_IMODE(env.stat().st_mode)
        if mode & (stat.S_IRGRP | stat.S_IROTH):
            out.append(f"- [設定] .env が他ユーザーから読める権限です ({oct(mode)})。`chmod 600 .env` を推奨")
        if (root / ".git").exists():
            r = subprocess.run(["git", "-C", str(root), "ls-files", "--error-unmatch", ".env"], capture_output=True)
            if r.returncode == 0:
                out.append("- [秘密情報] .env がgitで追跡されています (履歴に残っている場合はキーの再発行が必要)")
    else:
        out.append("- [情報] .env は存在しません (APIキーはサイドバー入力のみ、または未設定)")


def scan_streamlit_config(root: Path, out: list[str]):
    cfg = root / ".streamlit" / "config.toml"
    launch_text = ""
    for name in ("start.command", "start.sh", "Makefile", "Procfile", "Dockerfile"):
        f = root / name
        if f.exists():
            launch_text += f.read_text(encoding="utf-8", errors="ignore")
    cfg_text = cfg.read_text(encoding="utf-8", errors="ignore") if cfg.exists() else ""
    bound_local = re.search(r"""address\s*=\s*["'](localhost|127\.0\.0\.1)["']""", cfg_text) or re.search(
        r"--server\.address[= ](localhost|127\.0\.0\.1)", launch_text
    )
    if not bound_local:
        out.append(
            "- [ネットワーク] server.address が localhost に固定されていません。"
            "Streamlitは未設定だと全インターフェースで待ち受けるため、同じWi-Fi等の他人から"
            "アプリ(=あなたのAPIキー)を使われる恐れがあります"
        )
    for key, label in (("enableXsrfProtection", "XSRF保護"), ("enableCORS", "CORS保護")):
        if re.search(rf"{key}\s*=\s*false", cfg_text):
            out.append(f"- [ネットワーク] .streamlit/config.toml で {label} ({key}) が無効化されています")
    if (root / ".streamlit" / "secrets.toml").exists():
        out.append("- [情報] .streamlit/secrets.toml が存在します (gitignore対象か確認)")


def scan_dependencies(root: Path, out: list[str]):
    req = root / "requirements.txt"
    if not req.exists():
        return
    for line in req.read_text(encoding="utf-8").splitlines():
        s = line.split("#")[0].strip()
        if s and "==" not in s:
            out.append(f"- [依存関係] `{s}` はバージョンが固定されていません (起動のたびに新バージョンが入る可能性)")
    if shutil.which("pip-audit"):
        r = subprocess.run(["pip-audit", "-r", str(req), "--progress-spinner", "off"], capture_output=True, text=True)
        body = (r.stdout + r.stderr).strip()
        out.append("- [依存関係] pip-audit の結果:\n\n```\n" + body[:3000] + "\n```")
    else:
        out.append("- [情報] pip-audit が未インストールのため既知脆弱性DBとの照合はスキップ (`pip install pip-audit` で有効化)")


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    sections = {
        "秘密情報": scan_secrets,
        "コード": scan_code,
        "Git・.env": scan_git_and_env,
        "Streamlit設定・ネットワーク": scan_streamlit_config,
        "依存関係": scan_dependencies,
    }
    print(f"# 一次スキャン結果: {root}\n")
    print("以下は機械的に拾った候補です。誤検知・見落としがあり得るため、必ずコードを読んで判断してください。\n")
    for title, fn in sections.items():
        out: list[str] = []
        fn(root, out)
        print(f"## {title}\n")
        print("\n".join(out) if out else "- 候補なし")
        print()


if __name__ == "__main__":
    main()
