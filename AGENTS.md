# AGENTS.md

このファイルの指示は、このリポジトリ配下に適用する。

## プロジェクトの目的

- LiteLLM Proxy（Docker）を OpenAI 互換エンドポイントとして公開する。
- OpenAI Agents SDK（Responses API）から Proxy 経由で Bedrock モデルと会話できる `chat.py` を提供する。
- セッションを SQLite で永続化し、同一 `session_id` で会話継続できるようにする。

## 基本

- Python は `3.14`（`.python-version` 準拠）。
- パッケージ管理は `uv` を使う。
- 依存変更時は `pyproject.toml` と `uv.lock` を整合させる。

## 実行コマンド

- Lint: `uv run ruff check .`
- Format確認: `uv run ruff format . --check`
- Proxy起動: `docker compose up -d`
- チャット実行: `uv run chat.py --input "こんにちは"`

## 設定ファイル運用

- Compose ファイル名は常に `compose.yaml` を使う。
- 設定は `.env` 1ファイルに集約する。
- サンプルは `.env.example` を更新する。
