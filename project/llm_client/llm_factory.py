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

        Args:
            provider: One of "groq", "nvidia", or "openrouter".
            callback_manager: Attached to the returned LLM so events from
                llama_index's `llm_chat_callback()` decorator land on the
                caller's bus instead of a default empty one.
        """
        match provider:
            case "groq":
                groq_mod = importlib.import_module(".groq_client", package=__package__)
                raw_client = groq_mod.get_groq_client(model)

                api_base = getattr(config, "GROQ_API_ENDPOINT", "https://api.groq.com/openai/v1")
                llm = OpenAILike(
                    model=model,
                    api_base=api_base,
                    api_key=config.GROQ_API_KEY,
                    is_chat_model=True,
                    callback_manager=callback_manager,
                    temperature=0,  # OpenAILike defaults to 0.1; forced to 0 here
                )
                # OpenAILike has no async_client kwarg; passing one is silently
                # dropped, so the retry- and concurrency-wrapped client above
                # would otherwise never be used. _get_aclient() only builds its
                # own AsyncOpenAI when _aclient is unset, so assigning it here
                # routes every achat()/acomplete() call through raw_client
                # instead.
                llm._aclient = raw_client
                return llm

            case "nvidia":
                nim_mod = importlib.import_module(".nim_client", package=__package__)
                raw_client = nim_mod.get_nim_client(model)

                api_base = getattr(config, "NIM_API_ENDPOINT", "https://integrate.api.nvidia.com/v1")
                llm = OpenAILike(
                    model=model,
                    api_base=api_base,
                    api_key=config.NIM_API_KEY,
                    is_chat_model=True,
                    callback_manager=callback_manager,
                    temperature=0,
                )
                # Same reason as the groq branch above.
                llm._aclient = raw_client
                return llm

            case "openrouter":
                openrouter_mod = importlib.import_module(".openrouter_client", package=__package__)
                raw_client = openrouter_mod.get_openrouter_client(model)

                api_base = getattr(config, "OPENROUTER_API_ENDPOINT", "https://openrouter.ai/api/v1")
                llm = OpenAILike(
                    model=model,
                    api_base=api_base,
                    api_key=config.OPENROUTER_API_KEY,
                    is_chat_model=True,
                    callback_manager=callback_manager,
                    temperature=0,
                    # These OpenRouter-routed models (nemotron, gpt-oss) are
                    # reasoning-tuned: without a cap, reasoning tokens can
                    # exhaust the completion-token budget and leave
                    # message.content=None, crashing the caller's json.loads().
                    # effort="none" is rejected by some endpoints (gpt-oss-20b:free
                    # requires reasoning to stay on); "low" is accepted everywhere
                    # tested and still bounds the spend. The openai SDK has no
                    # typed reasoning kwarg, so it travels via extra_body.
                    additional_kwargs={"extra_body": {"reasoning": {"effort": "low"}}},
                )
                # Same reason as the groq branch above.
                llm._aclient = raw_client
                return llm

            case _:
                raise ValueError(f"Unsupported LLM provider: {provider!r}")

    @staticmethod
    def get_client_for_stage(
        stage: str,
        callback_manager: Optional[CallbackManager] = None,
    ) -> Any:
        """Return a client for the model and provider routed to this stage."""
        try:
            entry = config.MODEL_ROUTING[stage]
        except KeyError as exc:
            raise KeyError(f"Stage {stage!r} not found in MODEL_ROUTING") from exc
        model = entry["model"]
        provider = entry["provider"]
        return LLMFactory.get_client(provider, model, callback_manager=callback_manager)


__all__ = ["LLMFactory"]