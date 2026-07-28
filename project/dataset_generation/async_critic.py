"""Critic: independently re-derives an answer using a local search tool.

Uses qwen/qwen3.6-27b (config.MODEL_ROUTING["critic"]) -- a different model
family from the Generator (Task 5), per the anti-self-grading invariant.
Given only the query text (never the Generator's answer or citations), it
must search the filing itself before answering.
"""
import json

import config
import groq_client
from dataset_generation.search_tool import SEARCH_TOOL_SCHEMA, search_filing_nodes

_MAX_TOOL_ROUNDS = 5

_SYSTEM_PROMPT = (
    "You are a financial-filing fact-checker. You will be given a question about "
    "a SEC 10-K filing. You do not know the answer yet. Use the search_filing tool "
    "to find the relevant passages, then respond with ONLY a JSON object (no "
    'markdown fences, no commentary): {"cited_node_ids": ["node_id", ...], '
    '"computed_answer": "..."}. Cite only node_ids you actually found via search_filing.'
)


async def critique_query(query_text: str, all_nodes: list[dict]) -> dict:
    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": query_text},
    ]

    for _ in range(_MAX_TOOL_ROUNDS):
        response = await groq_client.call_groq(
            model=config.MODEL_ROUTING["critic"],
            messages=messages,
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

        return json.loads(message.content)

    raise RuntimeError(f"Critic exceeded {_MAX_TOOL_ROUNDS} tool-call rounds without a final answer")
