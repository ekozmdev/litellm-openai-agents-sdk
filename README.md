## LiteLLM Proxy + OpenAI Agents SDK チャット

LiteLLM Proxy を Docker で起動し、OpenAI Agents SDK（Responses API 前提）から Bedrock モデルへ会話します。

### 前提

- Docker / Docker Compose
- `uv`（`.python-version` は 3.14）
- Bedrock 呼び出し権限（`bedrock:InvokeModel*` など）がある AWS 認証情報

### 1. 機密情報ファイルを作成

1つの `.env` を使います（Docker Compose と `chat.py` で共通）。

```bash
cp .env.example .env
```

LiteLLM のマスターキーは `uv run` で生成できます。

```bash
uv run python -c "import secrets; print('sk-litellm-' + secrets.token_urlsafe(48))"
```

生成した値を `.env` の以下2つに同じ値で設定してください。

- `LITELLM_MASTER_KEY`（LiteLLM Proxy 側）
- `LITELLM_API_KEY`（`chat.py` 側）

`.env.example` には用途別コメントを入れています。

- `Docker Compose / LiteLLM Proxy が読む設定`
- `chat.py が読む設定`

最低限必要な項目:

- `LITELLM_MASTER_KEY`
- `LITELLM_API_KEY`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION_NAME`（例: `ap-northeast-1`）

### 2. LiteLLM Proxy を起動

```bash
docker compose up -d
```

このリポジトリの `litellm_config.yaml` には以下のエイリアスを定義済みです。

- `bedrock-claude-haiku-4-5-jp`（`jp.anthropic.claude-haiku-4-5-20251001-v1:0`）

他プロバイダー（Vertex など）は、検証できた段階で `litellm_config.yaml` と `.env` に追記してください。

### 3. エージェントとチャット

初回:

```bash
uv run chat.py --input "こんにちは"
```

セッション継続:

```bash
uv run chat.py --input "こんにちは" --session-id "XXXXXXX"
```

`--session-id` 未指定時は UUIDv7 で採番され、`SESSION_ID=...` が表示されます。

### 環境変数（chat.py 側 / `.env`）

- `LITELLM_BASE_URL`（デフォルト: `http://localhost:4000/v1`）
- `LITELLM_API_KEY`（LiteLLM Proxy の認証キー）
- `LITELLM_MODEL`（デフォルト: `bedrock-claude-haiku-4-5-jp`）
- `SESSION_DB_PATH`（デフォルト: `sessions.sqlite3`）

### 環境変数（Docker Compose / LiteLLM 側 / `.env`）

- `LITELLM_MASTER_KEY`
- `POSTGRES_DB`（デフォルト: `posgtres_db`）
- `POSTGRES_USER`（デフォルト: `postgres_user`）
- `POSTGRES_PASSWORD`（デフォルト: `posgtes_pass`）
- `DATABASE_URL`（上記 Postgres 値と整合させる）
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION_NAME`（`jp.*` 推論プロファイル使用時は `ap-northeast-1` または `ap-northeast-3`）

### 補足

- Agents SDK はコード内で `responses` API に固定しています。
- トレース送信はコードで無効化しています。
- 会話セッションは SQLite で永続化します。
