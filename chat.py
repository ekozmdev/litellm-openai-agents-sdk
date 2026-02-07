from __future__ import annotations

import argparse
import asyncio
import os
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime

from agents import (
    Agent,
    ModelSettings,
    Runner,
    SQLiteSession,
    function_tool,
    set_default_openai_api,
    set_default_openai_client,
    set_tracing_disabled,
)
from dotenv import load_dotenv
from openai import AsyncOpenAI


@dataclass(frozen=True)
class RuntimeConfig:
    input_text: str
    session_id: str
    is_new_session: bool
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
        required=True,
        help="Model alias on LiteLLM Proxy.",
    )
    parser.add_argument(
        "--db-path",
        default=None,
        help="SQLite path for sessions. If omitted, SESSION_DB_PATH is used.",
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

    base_url = _normalize_base_url(_require_env("LITELLM_BASE_URL"))
    api_key = _require_env("LITELLM_API_KEY")
    db_path = args.db_path or _require_env("SESSION_DB_PATH")
    is_new_session = args.session_id is None
    session_id = _make_session_id(args.session_id)

    return RuntimeConfig(
        input_text=args.input,
        session_id=session_id,
        is_new_session=is_new_session,
        model=args.model,
        base_url=base_url,
        api_key=api_key,
        db_path=db_path,
    )


@function_tool
def get_current_time() -> str:
    """Return the current local date and time with timezone."""
    now = datetime.now().astimezone()
    tz_name = now.tzname() or "local"
    return f"{now.isoformat()} ({tz_name})"


@function_tool
def add_numbers(a: float, b: float) -> str:
    """Return the sum of two numbers."""
    return str(a + b)



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
        model_settings=ModelSettings(
            store=False,
            response_include=["reasoning.encrypted_content"],
        ),
        instructions=(
            "You are a concise and helpful assistant. "
            "When the user asks for the current date/time, call get_current_time tool. "
            "When the user asks for arithmetic addition, call add_numbers tool."
        ),
        tools=[get_current_time, add_numbers],
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

    if config.is_new_session:
        print("SESSION_ID_STATUS=New")
    print(f"SESSION_ID={config.session_id}")
    print(output)


if __name__ == "__main__":
    main()
