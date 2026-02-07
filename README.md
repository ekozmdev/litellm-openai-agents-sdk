## LiteLLM Proxy + OpenAI Agents SDK チャット

LiteLLM Proxy を Docker で起動し、OpenAI Agents SDK（Responses API 前提）から Bedrock / Azure AI Foundry / Vertex AI モデルへ会話します。

### 前提

- Docker / Docker Compose
- `uv`（`.python-version` は 3.14）
- Bedrock 呼び出し権限（`bedrock:InvokeModel*` など）がある AWS 認証情報
- Azure AI Foundry の endpoint URL と API Key（Foundry を使う場合）
- Vertex AI 呼び出し権限がある GCP サービスアカウント JSON（Vertex を使う場合）

### 1. 機密情報ファイルを作成

用途ごとに 2 つの env ファイルを作成します。

```bash
cp .env.app.example .env.app
cp .env.litellm.example .env.litellm
```

`chat.py` 用の `.env.app` では最低限以下を設定してください。

- `LITELLM_API_KEY`（Proxy にアクセスするためのキー）
- 必要なら `LITELLM_MODEL`（デフォルトは `bedrock-claude-3-5-sonnet`）

LiteLLM Proxy 用の `.env.litellm` では最低限以下を設定してください。

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION_NAME`（例: `us-east-1`）
- `AZURE_FOUNDRY_API_BASE`（Foundry endpoint URL）
- `AZURE_FOUNDRY_API_KEY`（Foundry API Key）
- `VERTEX_PROJECT_ID`（Vertex 利用時）
- `VERTEX_LOCATION`（例: `us-central1`, Vertex 利用時）

Vertex を使う場合、サービスアカウント JSON を以下に配置してください。

```bash
cp /path/to/your-service-account.json ./secrets/vertex-service-account.json
```

`compose.yaml` で `./secrets` をコンテナの `/run/secrets` にマウントし、
`GOOGLE_APPLICATION_CREDENTIALS=/run/secrets/vertex-service-account.json` を利用します。

### 2. LiteLLM Proxy を起動

```bash
docker compose up -d
```

このリポジトリの `litellm_config.yaml` には以下のエイリアスを定義済みです。

- `bedrock-claude-3-5-sonnet`
- `azure-foundry-claude`
- `vertex-gemini-2.0-flash`

必要に応じてモデルIDを変更してください。

### 3. エージェントとチャット

初回:

```bash
uv run chat.py --input "こんにちは"
```

Vertex モデルを使う例:

```bash
uv run chat.py --input "こんにちは" --model "vertex-gemini-2.0-flash"
```

Azure Foundry モデルを使う例:

```bash
uv run chat.py --input "こんにちは" --model "azure-foundry-claude"
```

セッション継続:

```bash
uv run chat.py --input "こんにちは" --session-id "XXXXXXX"
```

`--session-id` 未指定時は UUIDv7 で採番され、`SESSION_ID=...` が表示されます。

### 環境変数（chat.py 側 / `.env.app`）

- `LITELLM_BASE_URL`（デフォルト: `http://localhost:4000/v1`）
- `LITELLM_API_KEY`（LiteLLM Proxy の認証キー）
- `LITELLM_MODEL`（デフォルト: `bedrock-claude-3-5-sonnet`）
- `SESSION_DB_PATH`（デフォルト: `sessions.sqlite3`）

### 補足

- Agents SDK はコード内で `responses` API に固定しています。
- トレース送信はコードで無効化しています。
- 会話セッションは SQLite で永続化します。
