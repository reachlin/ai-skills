# Local LLM Capability Score

A 10-level rubric for what to safely delegate to the local Ollama model, benchmarked
against real test cases so the score isn't a guess. **Level 10 = Sonnet 5 baseline**
(full multi-step reasoning, code review, judgment under ambiguity). Each lower level
is a progressively simpler/more mechanical task type.

## Current score

**5 / 10** — model: `qwen2.5:7b-instruct`, benchmarked 2026-09-17.

Safe to blanket-delegate tasks at **level 5 or below** per the skill's normal
"when to delegate" guidance (repetitive, well-defined, low-stakes). Do not
round up to a higher level just because a specific higher-level case happened
to pass below — see "Known false ceilings" below.

## The 10 levels

1. Trivial fixed-format lookup/copy (single obvious classification, case transforms)
2. Simple single-label classification from clear keywords
3. Single-record structured field extraction from clean text
4. Batch classification/extraction across many items, strict order-preserving format
5. Short rewriting/summarization while preserving specific facts
6. Structured extraction requiring inference on ambiguous/missing fields
7. Light reasoning: arithmetic, applying an explicit rule table
8. Multi-step reasoning / cross-referencing multiple facts in one prompt
9. Technical/code reasoning (bug-finding, regex comprehension)
10. Sonnet-5 baseline: complex multi-step reasoning and judgment calls under ambiguity

## Benchmark results (qwen2.5:7b-instruct, 2026-09-17)

Run via `scripts/capability_benchmark.py` (2 cases per level, 20 total).

| Level | Result | Notes |
|---|---|---|
| 1 | 2/2 PASS | |
| 2 | 2/2 PASS | |
| 3 | 2/2 PASS | |
| 4 | 2/2 PASS | |
| 5 | 2/2 PASS | preserved specific facts (dollar figure, meeting time/location) correctly |
| 6 | 1/2 FAIL | correctly extracted structured fields, but underrated a multi-restaurant payment-failure ticket as "medium" severity when it should be critical/high |
| 7 | 1/2 FAIL | correctly applied an explicit rule table, but got a simple percentage-discount calculation wrong ($28.50 instead of $31.50) |
| 8 | 2/2 PASS | correctly correlated two deploy timelines and produced correct dependency ordering |
| 9 | 2/2 PASS | correctly found an off-by-one bug and correctly reasoned through a regex edge case |
| 10 | 1/2 FAIL | solved a constraint-scheduling puzzle correctly, but gave a shallow "not a concern" security judgment that missed a least-privilege/hygiene angle a senior review would flag |

## Known false ceilings — do not delegate these even though a case passed

- **Arithmetic / calculations of any kind** (level 7 case failed a simple percentage discount). Never delegate math, even "simple" math — verify or do it yourself.
- **Severity/impact/judgment calls under ambiguity** (level 6 and 10 cases both underrated real-world stakes). Never delegate anything where getting the judgment wrong has consequences (incident severity, security review, prioritization calls).
- Passing a level-8/9 case does NOT mean levels 8-9 are safe to delegate in general — those passes were on clean, unambiguous logic puzzles (dependency graphs, regex, an isolated bug). Real level 8/9 tasks are rarely that clean.

## Re-benchmarking after a model upgrade

When the local model changes (new version pulled, different model swapped in):

1. Run the same benchmark against the new model:
   ```bash
   /opt/miniconda3/envs/claude-sandbox/bin/python ~/.claude/skills/local-llm/scripts/capability_benchmark.py --model <new-model-name>
   ```
2. Grade each case the same way this doc did (auto-checked cases are objective; manual-review cases need a real read — check whether facts/logic are actually correct, not just "an answer was given").
3. Update the results table and "Current score" section above with the new model name, date, and score. Only raise the score if a full level's cases pass AND there's no known-failure-mode overlap with what caused lower scores before (re-test arithmetic and ambiguous-judgment cases specifically — those are the recurring weak points across model sizes).
4. Update `SKILL.md`'s reference to the current score if it changes.
