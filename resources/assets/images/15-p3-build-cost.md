# Phase 3 — P3 Summary-Tree Build Cost

Source: `project/logs/index_build_costs.json`

```json
[
  {
    "document_id": "AAPL_2023",
    "skipped": false,
    "wall_clock_sec": 1193.6749380709953,
    "input_tokens": 91455,
    "output_tokens": 33333
  },
  {
    "document_id": "AAPL_2024",
    "skipped": false,
    "wall_clock_sec": 1217.5664782090025,
    "input_tokens": 89583,
    "output_tokens": 32762
  }
]
```

## Token and wall-clock cost

| Scope                     | Input tokens | Output tokens | Wall clock | Basis                |
| ------------------------- | ------------ | ------------- | ---------- | -------------------- |
| Per filing (average)      | 145,698      | 81,094        | 36 min     | measured, 11 filings |
| 13 filings, one full pass | ~1.89M       | ~1.05M        | ~7.7 h     | measured x 13        |
| All runs logged to date   | 1,783,711    | 958,129       | 15.5 h     | measured, 24 runs    |

Not CPU-bound: the build is throttled to 40 RPM by the provider, so wall clock is set by
the rate limit and not by local hardware. This is the slowest phase in the project, and it
is what a $0 budget actually costs — money converted into elapsed time.

`JPM_2023` and `JPM_2024` logged 0 tokens despite roughly 2 hours each. That is the
zero-cost logging defect recorded as `bugs.md` #10, fixed only after those two builds ran,
so their real spend was never captured and is imputed from the 11-filing average above.
