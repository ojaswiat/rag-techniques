"""Model routing, throttle flag, and env loading for the whole benchmark build."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

GROQ_API_ENDPOINT: str = os.getenv("GROQ_API_ENDPOINT", "https://api.groq.com/openai/v1")
NIM_API_ENDPOINT: str = os.getenv("NIM_API_ENDPOINT", "https://integrate.api.nvidia.com/v1")
OPENROUTER_API_ENDPOINT: str = os.getenv("OPENROUTER_API_ENDPOINT", "https://openrouter.ai/api/v1")

GROQ_API_KEY: str | None = os.getenv("GROQ_API_KEY")
LLAMA_CLOUD_API_KEY: str | None = os.getenv("LLAMA_CLOUD_API_KEY")
NIM_API_KEY: str | None = os.getenv("NIM_API_KEY")
OPENROUTER_API_KEY: str | None = os.getenv("OPENROUTER_API_KEY")
SEC_EDGAR_USER_AGENT: str = os.getenv("SEC_EDGAR_USER_AGENT", "rag-techniques-benchmark unknown@example.com")

LOCAL_TEST_THROTTLE: bool = os.getenv("LOCAL_TEST_THROTTLE", "true").lower() == "true"
THROTTLE_LIMIT: int = 3

# Guardrails.md §2 — fixed model routing matrix. Do not change without updating the spec.
MODEL_ROUTING: dict[str, dict] = {
    "generator":     {"model": "nvidia/nemotron-3-super-120b-a12b:free", "provider": "openrouter"},
    "critic":        {"model": "openai/gpt-oss-20b:free", "provider": "openrouter"},
    "p3_index_build":{"model": "nvidia/nemotron-3-super-120b-a12b", "provider": "nvidia"},
    "answerer":      {"model": "llama-3.3-70b-versatile","provider": "groq"},
    "judge":         {"model": "qwen/qwen3.6-27b",        "provider": "groq"},
    "debug":         {"model": "llama-3.1-8b-instant",   "provider": "groq"},
}

GROQ_MAX_CONCURRENCY: int = 5
NIM_MAX_CONCURRENCY: int = 5
OPENROUTER_MAX_CONCURRENCY: int = 5