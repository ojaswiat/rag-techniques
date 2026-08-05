# Challenges Encountered

Operational obstacles hit during the build (infrastructure/quota limits, external
constraints) and how each was handled. Distinct from `deviations.md` (departures
from the originally proposed design) and `issues.md` (known limitations left
undocumented in the codebase) -- this file is for obstacles to progress itself.
Newest first.

Each entry:

1. **Challenge:** what obstacle was hit.
2. **Impact:** what it blocked or slowed.
3. **Response:** what was done about it.
4. **Status:** resolved / ongoing / accepted limitation.

---

### 1. NIM API limits still throttling P3, now the longest-running phase (2026-08-05)

1. **Challenge:** Even after moving P3's summary build to NVIDIA NIM, the build still hits NIM's own rate/quota limits during long runs.
2. **Impact:** P3 (summary tree build) is the slowest phase of the project so far, wall-clock, of all phases run to date.
3. **Response:** Existing retry/backoff and 40 RPM throttling in `nim_client.py` absorb the limit hits without failing the run; builds continue, just slower. Per-filing resumability (`storage/summary_index/<document_id>/` skip-if-exists, atomic temp-dir-then-rename) means a long, throttled run is safe to interrupt and resume rather than needing to finish in one sitting.
4. **Status:** Ongoing -- accepted as a cost of the free-tier, no-per-hour-infrastructure constraint (Guardrails.md); not planned to be fixed further, just absorbed.

### 2. Groq free tier could not sustain the P3 summary build (2026-07-31)

1. **Challenge:** Groq's free-tier daily/per-minute request limits were repeatedly exhausted partway through P3 index builds and Phase 4 testing.
2. **Impact:** P3 builds could not complete in one run; builds stalled until quota reset, making the summary-tree corpus unreliable to finish on schedule.
3. **Response:** Added NVIDIA NIM as a second LLM provider, routed specifically to P3's index build, via a new `project/llm_client/` package (`LLMFactory`, `nim_client.py`) -- giving P3 quota headroom outside Groq's shared limits.
4. **Status:** Resolved for the immediate blocker (P3 builds now complete on NIM), but NIM has its own limits -- see Challenge 1.
