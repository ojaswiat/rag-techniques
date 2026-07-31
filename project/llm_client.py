"""Factory for obtaining LLM clients.

The factory reads the model name and provider from config.MODEL_ROUTING
and returns a ready‑to‑use client object (AsyncGroq or AsyncOpenAI) that
already includes retry‑on‑429 and semaphore logic.

Usage:
    from project.llm_client import LLMFactory
    client = LLMFactory.get_client("groq", "openai/gpt-oss-120b")
    response = await client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[...],
        temperature=0.0,
    )
"""

from __future__ import annotations

import importlib
from typing import Any

from . import config

logger = __import__('logging').getLogger(__name__)


class LLMFactory:
    """Static factory that returns a configured LLM client."""

    @staticmethod
    def get_client(provider: str, model: str) -> Any:
        """Return a client instance for the given provider and model.

        Parameters
        ----------
        provider: str
            Either "groq" or "nvidia".
        model: str
            Model identifier as expected by the provider API.

        Returns
        -------
        An object that implements the provider's chat.completions.create method
        with retry and semaphore logic applied.

        Raises
        ------
        ValueError
            If provider is not supported.
        """
        match provider:
            case "groq":
                groq_mod = importlib.import_module(".groq_client", package="project")
                return groq_mod.get_groq_client(model)
            case "nvidia":
                nim_mod = importlib.import_module(".nim_client", package="project")
                return nim_mod.get_nim_client(model)
            case _:
                raise ValueError(f"Unsupported LLM provider: {provider!r}")

    @staticmethod
    def get_client_for_stage(stage: str) -> Any:
        """Convenience: fetch client using config.MODEL_ROUTING for a stage."""
        try:
            entry = config.MODEL_ROUTING[stage]
        except KeyError as exc:
            raise KeyError(f"Stage {stage!r} not found in MODEL_ROUTING") from exc
        model = entry["model"]
        provider = entry["provider"]
        return LLMFactory.get_client(provider, model)


# Explicit public API
__all__ = ["LLMFactory"]