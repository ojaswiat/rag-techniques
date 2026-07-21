"""Reusable LOCAL_TEST_THROTTLE pattern for every Phase 2-7 loop script.

Guardrails.md §7: every loop script (async_generator.py, async_critic.py,
loop_executor.py, async_judge.py, the P3 summary-build script) must copy
this exact pattern — a hardcoded LOCAL_TEST_THROTTLE boolean that forces a
3-item cap. Run the full workflow under throttle=True once, end to end,
before flipping to False for the real batch.
"""
import config

LOCAL_TEST_THROTTLE: bool = config.LOCAL_TEST_THROTTLE


def throttle_limit_clause() -> str:
    return f"LIMIT {config.THROTTLE_LIMIT}"


def apply_throttle(items: list) -> list:
    if LOCAL_TEST_THROTTLE:
        return items[: config.THROTTLE_LIMIT]
    return items
