"""Model routing, throttle flag, and env loading for the whole benchmark build."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

GROQ_API_KEY: str | None = os.getenv("GROQ_API_KEY")
LLAMA_CLOUD_API_KEY: str | None = os.getenv("LLAMA_CLOUD_API_KEY")

LOCAL_TEST_THROTTLE: bool = os.getenv("LOCAL_TEST_THROTTLE", "true").lower() == "true"
THROTTLE_LIMIT: int = 3

# Guardrails.md §2 — fixed model routing matrix. Do not change without updating the spec.
MODEL_ROUTING: dict[str, str] = {
    "generator": "openai/gpt-oss-120b",
    "critic": "qwen/qwen3-32b",
    "p3_index_build": "llama-3.1-8b-instant",
    "answerer": "llama-3.3-70b-versatile",
    "judge": "qwen/qwen3-32b",
    "debug": "llama-3.1-8b-instant",
}

GROQ_MAX_CONCURRENCY: int = 5
