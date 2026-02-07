from __future__ import annotations

import argparse
import asyncio
import os
import sys
import uuid
from dataclasses import dataclass

from agents import (
    Agent,
    Runner,
    SQLiteSession,
    set_default_openai_api,
    set_default_openai_client,
    set_tracing_disabled,
)
from dotenv import load_dotenv
from openai import AsyncOpenAI

DEFAULT_BASE_URL = "http://localhost:4000/v1"
DEFAULT_DB_PATH = "sessions.sqlite3"


@dataclass(frozen=True)
class RuntimeConfig:
    input_text: str
    session_id: str
    model: str
    base_url: str
    api_key: str
    db_path: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Chat with OpenAI Agents SDK through LiteLLM Proxy."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="User input to send to the agent.",
    )
    parser.add_argument(
        "--session-id",
        help="Reuse an existing session id. If omitted, a uuid7 is generated.",
    )
    parser.add_argument(
        "--model",
        help="Model alias on LiteLLM Proxy. Defaults to LITELLM_MODEL.",
    )
    parser.add_argument(
        "--db-path",
        default=None,
        help=f"SQLite path for sessions. Defaults to {DEFAULT_DB_PATH}.",
    )
    return parser.parse_args()


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _normalize_base_url(base_url: str) -> str:
    normalized = base_url.rstrip("/")
    if not normalized.endswith("/v1"):
        normalized = f"{normalized}/v1"
    return normalized


def _make_session_id(session_id: str | None) -> str:
    if session_id:
        return session_id
    if not hasattr(uuid, "uuid7"):
        raise RuntimeError(
            "uuid.uuid7() is unavailable. Run with Python 3.14+ (for example: uv run ...)."
        )
    return str(uuid.uuid7())


def build_config(args: argparse.Namespace) -> RuntimeConfig:
    load_dotenv(".env")

    model = args.model or os.getenv("LITELLM_MODEL")
    if not model:
        raise RuntimeError("Set LITELLM_MODEL or pass --model.")

    base_url = _normalize_base_url(os.getenv("LITELLM_BASE_URL", DEFAULT_BASE_URL))
    api_key = _require_env("LITELLM_API_KEY")
    db_path = args.db_path or os.getenv("SESSION_DB_PATH", DEFAULT_DB_PATH)
    session_id = _make_session_id(args.session_id)

    return RuntimeConfig(
        input_text=args.input,
        session_id=session_id,
        model=model,
        base_url=base_url,
        api_key=api_key,
        db_path=db_path,
    )


async def run_chat(config: RuntimeConfig) -> str:
    set_tracing_disabled(True)
    set_default_openai_api("responses")

    client = AsyncOpenAI(
        base_url=config.base_url,
        api_key=config.api_key,
    )
    set_default_openai_client(client, use_for_tracing=False)

    session = SQLiteSession(config.session_id, config.db_path)
    agent = Agent(
        name="proxy-assistant",
        model=config.model,
        instructions="You are a concise and helpful assistant.",
    )

    try:
        result = await Runner.run(
            agent,
            config.input_text,
            session=session,
        )
    finally:
        session.close()
        await client.close()

    if result.final_output is None:
        return ""
    return str(result.final_output)


def main() -> None:
    args = parse_args()
    config = None
    try:
        config = build_config(args)
        output = asyncio.run(run_chat(config))
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"SESSION_ID={config.session_id}")
    print(output)


if __name__ == "__main__":
    main()
