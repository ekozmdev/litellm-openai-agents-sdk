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

生成した値は `.env` の `LITELLM_MASTER_KEY` に設定してください。

- `LITELLM_MASTER_KEY`（LiteLLM Proxy 側 / 管理用）
- `LITELLM_API_KEY` は Proxy 起動後に発行した Virtual Key を設定（後述）

`.env.example` には用途別コメントを入れています。

- `Docker Compose / LiteLLM Proxy が読む設定`
- `chat.py が読む設定`

最低限必要な項目:

- `LITELLM_MASTER_KEY`
- `UI_USERNAME`（管理UIログイン用 / 初期ユーザー作成前に使用）
- `UI_PASSWORD`（管理UIログイン用 / 初期ユーザー作成前に使用）
- `LITELLM_API_KEY`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `DATABASE_URL`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`
- `LITELLM_BASE_URL`
- `SESSION_DB_PATH`

### 2. LiteLLM Proxy を起動

```bash
docker compose up -d
```

このリポジトリの `compose.yaml` は、Bedrock ツール実行時の重複 `toolUse` バグ回避のため
`docker.litellm.ai/berriai/litellm:main-latest` を使用しています。

### 3. 初期ユーザー登録と API Key 発行（LiteLLM 公式）

公式ドキュメント:

- Admin UI Quick Start: https://docs.litellm.ai/docs/proxy/ui
- User Onboarding Guide: https://docs.litellm.ai/docs/proxy/user_onboarding
- Virtual Keys: https://docs.litellm.ai/docs/proxy/virtual_keys

簡潔な手順:

1. `http://localhost:4000/ui` を開く（必要なら `UI_USERNAME` / `UI_PASSWORD` を設定）。
   このログイン情報は「初期ユーザー作成前に管理UIへ入るための認証」です。
2. `Internal Users` でユーザーを作成（`Add User`）。
3. `Keys` で `Generate Key` を実行し、モデルに `bedrock-claude-haiku-4-5-jp` を含める。
4. 発行された key (`sk-...`) を `.env` の `LITELLM_API_KEY` に設定する。

API で実施する場合（`<admin-key>` は `LITELLM_MASTER_KEY`）:

```bash
curl -X POST http://localhost:4000/user/new \
  -H "Authorization: Bearer <admin-key>" \
  -H "Content-Type: application/json" \
  -d '{"user_email":"user@example.com"}'
```

```bash
curl -X POST http://localhost:4000/key/generate \
  -H "Authorization: Bearer <admin-key>" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"<user-id>", "models":["bedrock-claude-haiku-4-5-jp"]}'
```

### 4. モデルエイリアス

このリポジトリの `litellm_config.yaml` には以下を定義済みです。

- `bedrock-claude-haiku-4-5-jp`（`jp.anthropic.claude-haiku-4-5-20251001-v1:0`）

他プロバイダー（Vertex など）は、検証できた段階で `litellm_config.yaml` と `.env` に追記してください。

### 5. エージェントとチャット

初回:

```bash
uv run chat.py --input "こんにちは" --model "bedrock-claude-haiku-4-5-jp"
```

セッション継続:

```bash
uv run chat.py --input "こんにちは" --model "bedrock-claude-haiku-4-5-jp" --session-id "XXXXXXX"
```

`--session-id` 未指定時は UUIDv7 で採番され、`SESSION_ID=...` が表示されます。

### 環境変数（chat.py 側 / `.env`）

- `LITELLM_BASE_URL`
- `LITELLM_API_KEY`（`/key/generate` で発行した Virtual Key）
- `SESSION_DB_PATH`

### 環境変数（Docker Compose / LiteLLM 側 / `.env`）

- `LITELLM_MASTER_KEY`
- `UI_USERNAME`（管理UIログイン用）
- `UI_PASSWORD`（管理UIログイン用）
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `DATABASE_URL`（上記 Postgres 値と整合させる）
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`（`jp.*` 推論プロファイル使用時は `ap-northeast-1` または `ap-northeast-3`）

### 補足

- Agents SDK はコード内で `responses` API に固定しています。
- トレース送信はコードで無効化しています。
- 会話セッションは SQLite で永続化します。
