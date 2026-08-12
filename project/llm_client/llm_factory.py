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
            One of "groq", "nvidia", or "openrouter".
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
        TreeIndex, VectorStoreIndex, etc. Constructed with `temperature=0`
        (Guardrails.md: "All LLM calls at temperature = 0") -- OpenAILike's
        own default is 0.1, not 0, so this must be set explicitly rather than
        relying on the library default.
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
                    temperature=0,
                )
                # OpenAILike/OpenAI has no `async_client` field -- passing one
                # as a kwarg is silently dropped (arbitrary_types_allowed
                # model config accepts and discards unknown kwargs), so the
                # retry+semaphore-wrapped client above would otherwise never
                # be used. `_get_aclient()` only builds its own AsyncOpenAI
                # when `self._aclient` is unset (with `reuse_client=True`,
                # the default), so setting it directly here makes every
                # achat()/acomplete() call route through raw_client's retry
                # and concurrency-limit wrapping instead.
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
                # See the groq branch above -- same fix, same reason.
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
                    # OpenRouter-routed models here (Generator, Critic) are
                    # reasoning-tuned (nemotron, gpt-oss); without this,
                    # reasoning tokens can exhaust the completion-token
                    # budget and leave message.content=None, crashing
                    # downstream json.loads() calls. effort="none" is
                    # rejected by some endpoints (e.g. gpt-oss-20b:free:
                    # "Reasoning is mandatory for this endpoint and cannot
                    # be disabled") -- "low" is accepted everywhere tested
                    # and still caps the reasoning-token spend. The openai
                    # SDK has no typed `reasoning` kwarg -- OpenRouter's
                    # unified reasoning field travels via extra_body.
                    additional_kwargs={"extra_body": {"reasoning": {"effort": "low"}}},
                )
                # See the groq branch above -- same fix, same reason.
                llm._aclient = raw_client
                return llm

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