"""Critic: independently re-derives an answer using a local search tool.

Uses qwen/qwen3.6-27b (config.MODEL_ROUTING["critic"]) -- a different model
family from the Generator (Task 5), per the anti-self-grading invariant.
Given only the query text (never the Generator's answer or citations), it
must search the filing itself before answering.
"""
import json

from llm_client import config
from llm_client.llm_factory import LLMFactory
from .search_tool import SEARCH_TOOL_SCHEMA, search_filing_nodes

_MAX_TOOL_ROUNDS = 5

_SYSTEM_PROMPT = (
    "You are a financial-filing fact-checker. You will be given a question about "
    "a SEC 10-K filing. You do not know the answer yet. Use the search_filing tool "
    "to find the relevant passages, then respond with ONLY a JSON object (no "
    "markdown fences, no commentary): {\"cited_node_ids\": [\"node_id\", ...], "
    "\"computed_answer\": \"...\"}. Cite only node_ids you actually found via search_filing."
)


async def critique_query(
    query_text: str, all_nodes: list[dict], return_messages: bool = False
) -> dict:
    """Run the Critic's search-then-answer loop and return the parsed final
    answer as {"cited_node_ids": [...], "computed_answer": "..."}.

    If return_messages is True, the returned dict additionally carries a
    "messages" key holding the full message history for the run
    (system/user/assistant/tool messages, including any tool-call and
    tool-result turns) -- useful for tests/diagnostics that need to assert
    directly on tool-call behaviour rather than inferring it from the final
    answer. Default is False, so existing callers are unaffected.
    """
    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": query_text},
    ]

    # Get client for critic stage
    critic_client = LLMFactory.get_client_for_stage("critic")

    for _ in range(_MAX_TOOL_ROUNDS):
        response = await critic_client.chat.completions.create(
            model=config.MODEL_ROUTING["critic"]["model"],
            messages=messages,
            temperature=0.0,
            tools=[SEARCH_TOOL_SCHEMA],
        )
        message = response.choices[0].message

        if getattr(message, "tool_calls", None):
            messages.append({
                "role": "assistant",
                "content": message.content,
                "tool_calls": message.tool_calls,
            })
            for tool_call in message.tool_calls:
                args = json.loads(tool_call.function.arguments)
                results = search_filing_nodes(all_nodes, args["query"])
                tool_output = json.dumps(
                    [{"node_id": r["node_id"], "content": r["content"]} for r in results]
                )
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_output,
                })
            continue

        final = json.loads(message.content)
        if return_messages:
            final["messages"] = messages + [
                {"role": "assistant", "content": message.content}
            ]
        return final

    raise RuntimeError(f"Critic exceeded {_MAX_TOOL_ROUNDS} tool-call rounds without a final answer")