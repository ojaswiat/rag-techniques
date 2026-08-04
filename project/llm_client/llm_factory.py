from __future__ import annotations

import importlib
from typing import Any, Optional

from llama_index.core.callbacks import CallbackManager
from llama_index.llms.openai_like import OpenAILike

from . import config

logger = __import__('logging').getLogger(__name__)


class LLMFactory:
    """Static factory that returns LlamaIndex-compatible LLM client objects."""

    @staticmethod
    def get_client(
        provider: str,
        model: str,
        callback_manager: Optional[CallbackManager] = None,
    ) -> Any:
        """Return a LlamaIndex LLM instance for the given provider and model.

        Parameters
        ----------
        provider: str
            Either "groq" or "nvidia".
        model: str
            Model identifier as expected by the provider API.
        callback_manager: Optional[CallbackManager]
            Callback manager to attach to the returned LLM so that events
            fired by llama_index's `llm_chat_callback()` decorator (e.g.
            token-usage tracking) land on the caller's bus instead of an
            empty default one. If None, OpenAILike falls back to its own
            default behaviour.

        Returns
        -------
        A LlamaIndex LLM object (subclass of BaseLLM) ready for use in
        TreeIndex, VectorStoreIndex, etc.
        """
        match provider:
            case "groq":
                groq_mod = importlib.import_module(".groq_client", package=__package__)
                raw_client = groq_mod.get_groq_client(model)

                api_base = getattr(config, "GROQ_API_ENDPOINT", "https://api.groq.com/openai/v1")
                return OpenAILike(
                    model=model,
                    api_base=api_base,
                    api_key=config.GROQ_API_KEY,
                    async_client=raw_client,
                    is_chat_model=True,
                    callback_manager=callback_manager,
                )

            case "nvidia":
                nim_mod = importlib.import_module(".nim_client", package=__package__)
                raw_client = nim_mod.get_nim_client(model)

                api_base = getattr(config, "NIM_API_ENDPOINT", "https://integrate.api.nvidia.com/v1")
                return OpenAILike(
                    model=model,
                    api_base=api_base,
                    api_key=config.NIM_API_KEY,
                    async_client=raw_client,
                    is_chat_model=True,
                    callback_manager=callback_manager,
                )

            case _:
                raise ValueError(f"Unsupported LLM provider: {provider!r}")

    @staticmethod
    def get_client_for_stage(
        stage: str,
        callback_manager: Optional[CallbackManager] = None,
    ) -> Any:
        """Convenience: fetch client using config.MODEL_ROUTING for a stage."""
        try:
            entry = config.MODEL_ROUTING[stage]
        except KeyError as exc:
            raise KeyError(f"Stage {stage!r} not found in MODEL_ROUTING") from exc
        model = entry["model"]
        provider = entry["provider"]
        return LLMFactory.get_client(provider, model, callback_manager=callback_manager)


__all__ = ["LLMFactory"]