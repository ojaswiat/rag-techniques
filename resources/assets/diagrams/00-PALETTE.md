# Diagram Palette — Tailwind 500 Only

Binding style contract for every `.drawio` file in this folder. Assigned **before** any diagram
was drawn, so the same concept carries the same colour in every figure. If a new diagram needs a
concept not listed here, add the row first, then draw.

## Rules

- **Colour tier:** Tailwind CSS `500` shades only. No `400`, no `600`, no custom hex.
- **Corners:** `rounded=0` everywhere. Sharp edges only.
- **Borders:** `strokeColor=none` on all filled shapes. Edges carry colour instead.
- **Shadows / gradients / 3D:** none. `shadow=0`, pure flat fill.
- **Neutrals:** `slate-500` is the only permitted neutral, reserved for *not-started* status and
  axis rules. Black, white and grey appear only as label text on coloured fills.
- **Typography:** `Inter` for all prose labels and titles. `JetBrains Mono` for identifiers,
  table names, model slugs, file paths, and numeric parameters.
- **Spacing:** minimum 40px gutter between sibling nodes, 60px between bands. Breathable.

## Semantic colour assignment

| Concept | Tailwind | Hex | Used in |
|---|---|---|---|
| Raw source — SEC EDGAR, filings | `rose-500` | `#f43f5e` | 01, 02, 05, 12 |
| Parsing / ingestion / LlamaParse | `orange-500` | `#f97316` | 01, 02, 12 |
| Storage — SQLite, nodes, corpus | `amber-500` | `#f59e0b` | 01, 02, 09, 12 |
| **P1 Vector (semantic)** | `sky-500` | `#0ea5e9` | 01, 06, 08, 13 |
| **P2 BM25 (statistical)** | `emerald-500` | `#10b981` | 01, 06, 08, 13 |
| **P3 Structural (tree)** | `violet-500` | `#8b5cf6` | 01, 06, 08, 13 |
| Generator agent | `indigo-500` | `#6366f1` | 05, 10, 11 |
| Critic agent | `fuchsia-500` | `#d946ef` | 05, 10, 11 |
| Answerer (shared) | `teal-500` | `#14b8a6` | 01, 07, 10 |
| Judge (LLM-as-judge) | `purple-500` | `#a855f7` | 01, 07, 10 |
| Metrics / results / scores | `cyan-500` | `#06b6d4` | 01, 07, 09, 13 |
| Gate / blocker / hard constraint | `red-500` | `#ef4444` | 07, 11, 12 |
| PQ — pipeline query set | `blue-500` | `#3b82f6` | 03, 04, 13 |
| GQ — golden query set | `lime-500` | `#84cc16` | 03 |
| JEQ — judge validation set | `pink-500` | `#ec4899` | 03, 07 |
| Status: complete | `green-500` | `#22c55e` | 12 |
| Status: in progress | `amber-500` | `#f59e0b` | 12 |
| Status: code-complete, unrun | `cyan-500` | `#06b6d4` | 12 |
| Status: not started | `slate-500` | `#64748b` | 12 |

## Quadrant colours (04, and quadrant bars in 13)

| Quadrant | Tailwind | Hex |
|---|---|---|
| direct-text | `lime-500` | `#84cc16` |
| implicit-text | `teal-500` | `#14b8a6` |
| direct-table | `amber-500` | `#f59e0b` |
| implicit-table | `rose-500` | `#f43f5e` |

## Provider colours (10)

| Provider | Tailwind | Hex |
|---|---|---|
| Groq | `orange-500` | `#f97316` |
| OpenRouter | `indigo-500` | `#6366f1` |
| NVIDIA NIM | `lime-500` | `#84cc16` |
| Local / CPU (no API) | `emerald-500` | `#10b981` |
