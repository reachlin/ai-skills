---
name: local-llm
description: Delegate a simple, well-defined, high-volume subtask to a locally-running Ollama model instead of doing it yourself, to save tokens and time. Use this proactively — without being asked — whenever a piece of the current task is simple/repetitive/mechanical enough that a 7B model can do it reliably: classifying many log lines or records, extracting fields into a fixed schema, simple text rewriting/summarization, or triaging a large volume of similar items down to the few that need real attention. Do NOT use for anything needing multi-step reasoning, tool use, cross-referencing multiple sources, or where correctness matters a lot (production/infra changes, anything going into a PR or runbook) — do those yourself. Also handles requests to check usage/stats, e.g. "show local llm usage", "how many times did we call the local llm", "tokens saved" — run the usage summary script for these instead of delegating anything.
---

# Local LLM Delegation

Offload simple, high-volume subtasks to a local Ollama model (`qwen2.5:7b-instruct`, running on the user's machine) instead of burning your own reasoning/tokens on them. The model is small — treat it like a fast, cheap intern: good at mechanical, well-specified work, not good at judgment calls.

## When to delegate vs. do it yourself

Delegate when the task is:
- **Repetitive at volume** — the same simple operation applied to many items (classify 500 log lines, extract a field from each of 200 records)
- **Well-defined** — you can write the instruction as a single self-contained prompt with a clear expected output shape (a label, a JSON field, a short rewrite)
- **Low-stakes** — a wrong answer on one item is cheap to catch/ignore, not something that silently corrupts a result

Do it yourself when the task:
- Requires multi-step reasoning, tool calls, or checking things against other files/systems
- Needs the item-by-item results to be cross-referenced or reasoned about together (that synthesis step should stay with you — only the mechanical per-item step gets delegated)
- Touches production, infrastructure, or anything that ends up in a PR, runbook, or incident doc — correctness matters too much here for a 7B model
- Is a one-off (the setup cost of writing a good prompt isn't worth it for a single item)

If unsure, it's fine to delegate a small sample first (5-10 items) and spot-check the output before running it over the full set.

### Capability score gate

`CAPABILITY.md` (in this skill's folder) tracks a benchmarked 10-level score for the current local model (10 = Sonnet 5 baseline). **Current score: 5/10.** Only blanket-delegate tasks at or below that level — mechanical classification, single/batch structured extraction, and rewriting/summarization that preserves given facts. Two failure modes hold regardless of nominal task "level," per that doc: never delegate arithmetic/calculations, and never delegate severity/impact/judgment calls made under ambiguity — the local model is unreliable at both even when the surrounding task looks simple. Re-check `CAPABILITY.md` if the local model has been upgraded since its last-recorded benchmark date.

## How to delegate

1. **Check the server is up:**
   ```bash
   curl -s --max-time 2 http://localhost:11434/api/version
   ```
   If this fails, tell the user the Ollama server isn't running and ask them to start it — don't start it silently yourself, since it's a long-running background process:
   ```bash
   tmux new-session -d -s ollama-serve "ollama serve"
   ```
   (Per the user's standing preference, long-running processes like this always run in a named tmux session, never bare-backgrounded, and are never killed with `pkill`.)

2. **Call the model** via the bundled script. Write one fully self-contained prompt (task instructions + the data to process) and run:
   ```bash
   /opt/miniconda3/envs/claude-sandbox/bin/python ~/.claude/skills/local-llm/scripts/local_llm.py "<prompt>"
   ```
   For larger input data, write it to a temp file (in your scratchpad directory) and pass it via `--input-file`:
   ```bash
   /opt/miniconda3/envs/claude-sandbox/bin/python ~/.claude/skills/local-llm/scripts/local_llm.py "Classify each log line below as ERROR, WARN, or INFO. Reply with one label per line, same order, nothing else." --input-file /path/to/loglines.txt
   ```

3. **Batch, don't loop one-item-at-a-time.** A single call with 50 items and clear "one output per line, same order" instructions is far cheaper and faster than 50 separate calls. Reserve per-item calls for cases where inputs vary too much in length/shape to batch cleanly.

4. **Spot-check the output.** Since this is a 7B model, skim the results for obvious mistakes (misaligned line counts, malformed output) before treating them as final — especially the first time you use a new prompt shape.

## Prompt-writing tips for this model

- Be explicit about output format ("reply with only the label, nothing else", "output valid JSON, one object per line") — it follows format instructions well but will add explanatory text if you don't forbid it.
- Keep instructions in the prompt itself; the script sends a single stateless message, there's no conversation history.
- If output alignment with input order matters (e.g. classifying N lines into N labels), say so explicitly and verify the count matches after.

## Model / environment reference

- Model: `qwen2.5:7b-instruct` (already pulled)
- Server: Ollama, tmux session `ollama-serve`, listening on `localhost:11434`
- Script: `scripts/local_llm.py` — pass `--model NAME` to use a different pulled model if one is added later

## Usage tracking

Every call via `local_llm.py` appends one line to `usage_log.jsonl` (in this skill's folder) with the model name and Ollama's actual `prompt_eval_count`/`eval_count` token counts for that call — this approximates the tokens offloaded from Claude for that subtask.

### "show local llm usage"

When the user asks to see local-LLM usage/stats (e.g. "show local llm usage", "how many times have we called it", "tokens saved so far") — this is a report request, not a delegation task. Just run the summary script and show the output as-is:
```bash
/opt/miniconda3/envs/claude-sandbox/bin/python ~/.claude/skills/local-llm/scripts/usage_summary.py
```
