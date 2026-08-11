"""Shared Answerer: turns (query, retrieved nodes) into a cited answer.

One Answerer serves all three pipelines (Architecture.md §4.1). Holding the
generation step constant is what makes the benchmark a comparison of
*retrieval* strategies -- any difference in answer quality between P1, P2
and P3 must come from which nodes reached this class, never from how those
nodes were turned into prose.

Anti-leakage (Architecture.md §4.1, Guardrails.md §3): the prompt carries
only the query text and the retrieved nodes' ids and content. No
exemplars, no ground-truth answer, no gt_citations, no quadrant label, and
no node metadata -- a node's parent_item_header or page number would hint
at where the answer lives, which is exactly what the retrieval step is
being measured on.
"""
import re
import time
from dataclasses import dataclass

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.core.schema import NodeWithScore

import llm_client.config as config
from llm_client.llm_factory import LLMFactory

_STAGE = "answerer"

# Architecture.md §4.2. Markers are kept in pipeline_output rather than
# stripped, so a stored answer stays auditable against its own citations.
_CITATION_PATTERN = re.compile(r"\[\[node:([\w\-]+)\]\]")

_SYSTEM_PROMPT = (
    "You answer questions using only the numbered sources provided. "
    "Do not use outside knowledge, and do not guess: if the sources do not "
    "contain the answer, say so plainly. "
    "After any claim drawn from a source, immediately append "
    "[[node:<node_id>]] citing the exact node it came from. "
    "Use the node_id exactly as given. Answer concisely."
)


@dataclass
class AnswerResult:
    raw_text: str
    cited_node_ids: list[str]
    input_tokens: int
    output_tokens: int
    latency_sec: float


def parse_citations(raw_text: str) -> list[str]:
    """Node ids cited in `raw_text`, deduplicated, first-appearance order."""
    seen: dict[str, None] = {}
    for node_id in _CITATION_PATTERN.findall(raw_text):
        seen.setdefault(node_id, None)
    return list(seen)


def build_prompt(query_text: str, nodes: list[NodeWithScore]) -> str:
    """The user-role message: retrieved sources, then the question.

    Each node contributes its id and its text and nothing else -- the id
    because the model has to be able to cite it, the text because it is the
    evidence. See this module's docstring for why metadata is excluded.
    """
    blocks = [
        f"[node:{node.node.node_id}]\n{node.node.get_content()}" for node in nodes
    ]
    sources = "\n\n".join(blocks) if blocks else "(no sources retrieved)"
    return f"Sources:\n{sources}\n\nQuestion: {query_text}"


class Answerer:
    def __init__(
        self,
        model: str = "llama-3.3-70b-versatile",
        temperature: float = 0.0,
    ):
        routed_model = config.MODEL_ROUTING[_STAGE]["model"]
        # The routing matrix and temperature=0 are fixed constraints, and
        # LLMFactory already applies both when it builds the client. These
        # parameters exist because Architecture.md §4.1 specifies them, so
        # a contradicting value is rejected outright rather than silently
        # ignored -- a benchmark run that thinks it used a different model
        # or a nonzero temperature would be unreproducible.
        if model != routed_model:
            raise ValueError(
                f"Answerer model is fixed to {routed_model!r} by "
                f"config.MODEL_ROUTING[{_STAGE!r}]; got {model!r}"
            )
        if temperature != 0.0:
            raise ValueError(
                f"All benchmark LLM calls run at temperature=0; got {temperature!r}"
            )
        self.model = model
        self.temperature = temperature
        self._client = None

    def _get_client(self):
        # Built on first use, not in __init__, so constructing an Answerer
        # never reaches for API credentials -- and so the whole 900-cell run
        # reuses one client (with its retry and concurrency wrapping) instead
        # of rebuilding it per call.
        if self._client is None:
            self._client = LLMFactory.get_client_for_stage(_STAGE)
        return self._client

    async def answer(self, query_text: str, nodes: list[NodeWithScore]) -> AnswerResult:
        client = self._get_client()
        messages = [
            ChatMessage(role=MessageRole.SYSTEM, content=_SYSTEM_PROMPT),
            ChatMessage(role=MessageRole.USER, content=build_prompt(query_text, nodes)),
        ]

        start = time.monotonic()
        response = await client.achat(messages)
        latency_sec = time.monotonic() - start

        raw_text = response.message.content or ""
        usage = response.additional_kwargs or {}

        return AnswerResult(
            raw_text=raw_text,
            cited_node_ids=parse_citations(raw_text),
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            latency_sec=latency_sec,
        )


__all__ = ["AnswerResult", "Answerer", "build_prompt", "parse_citations"]
