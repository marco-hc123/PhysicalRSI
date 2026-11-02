# Static audit of the publicly released reference controller

Audited **2026-10-11, Asia/Shanghai**. Repository:
[anonymous-report-421/GPT-as-Policy](https://github.com/anonymous-report-421/GPT-as-Policy),
commit **`8f3d362b077d8efb77e2a7274d5b2c20e2243846`**. Selected source files
are saved in [sources/comparator/source](source/), with
their MIT [license](LICENSE). No simulator, controller
launcher, model process or remote job was executed for this audit.

The package's [audit provenance](audit_provenance.json)
records URLs, SHA-256, byte counts and Git blob hashes. Downloaded bytes were
checked against the pinned Git tree and, where listed, the release manifest.
The manifest's `history = new-root-commit` explains “history-free”: this is a
source-release property, **not absence of controller memory**.

## Actual scheduling and state

All paths in this table are relative to `hybrid_rollout/robodojo/` in that
fixed-commit source snapshot. Line references describe code evidence, not a
runtime claim about an unavailable historical session.

| Question | Source location | Verified behavior | Research consequence |
| --- | --- | --- | --- |
| Model and effort | `settings.py:8` | `gpt-6-astra`, `xhigh`; backend profile selected explicitly | Freeze the actual backend for a matched comparison |
| Agent lifetime | `skill/run.py:176`, `skill/run.py:204` | Starts one persistent thread with `ephemeral=False`; subsequent turns reuse its ID | Do not assume a fresh stateless prompt every action |
| Hybrid control | `skill/SKILL.md:40`, `robodojo_server/client.py:204`, `robodojo_server/client.py:239` | Start once, infer fresh pi05 proposal, model reviews and executes, observe, repeat | Hybrid still reviews each execution segment; it is not a gate that calls the model only after failure |
| Direct control | `robodojo-gpt-only-rollout/SKILL.md:35`, `robodojo_server/gpt_only_client.py:99` | Start once, choose bounded EEF action, execute, observe, repeat | Direct is chunked control, not necessarily one model request per physical step |
| Action lengths | `robodojo_server/validation.py:44`, `skill/schema.py:45` | Student mode allows 1–15 steps; Direct EEF and hybrid corrections allow 1–5 | Segment duration is a protocol difference that can contribute to usage differences |
| Task context | `robodojo_server/client.py:153`, `prompt_context.py:20` | Supplies task-specific context at the initial observation | Do not assume all task descriptions are resent as an explicit payload every step |
| Working memory | `skill/workspace.py:13`, both controller `SKILL.md` files | Notes, scratch analyses and recorded history are available; conversation persists | Both comparison methods have memory and native analysis tools |
| Observed history | `robodojo_server/client.py:148`, `robodojo_server/client.py:227` | Tool packets link the history file and include recent result/state rather than embedding the whole history list explicitly | Full conversation accumulation and server compaction still need request/session logs |

The source does not expose an exact historical model-request count through
`chunks`. A model turn can contain multiple host service calls and native
analysis tools; transport retries and continuations are separate events.
Consequently, multiplying the physical step count by one prompt cost is not a
faithful reconstruction of either method.

## Image and context handling already present in the comparator

- `settings.py:12` defaults teacher image attachments to a maximum edge of
  480 pixels. `skill/image_preview.py:15` makes proportional PNG thumbnails,
  retaining the full-resolution original for optional inspection. This setting
  is configurable; it is not proof every historical run used the default.
- `skill/run.py:118` builds a compact JSON text packet and optional images.
  At `skill/run.py:317`, a `pi05_infer` reply suppresses repeated image
  attachments. The model already saw that observation before requesting the
  proposal; fresh observations can attach images again.
- `robodojo_server/client.py:232` removes `gate_instruction` from the returned
  proposal packet because the gate is already in the persistent workspace.
- Native shell, file and image tools remain available. A model can spend
  additional calls inspecting old images or writing notes between executions.
  We did not verify the backend's actual truncation, cache policy or compaction
  behavior from these source files alone.

These existing optimizations weaken explanations that attribute the gap solely
to “the comparison project resends every image and all history from scratch.”
Actual payload and usage traces are needed to decide where repeated context
still dominates.

## Token provenance and a reproducible numerical check

`skill/run.py:274` handles `thread/tokenUsage/updated` events. It saves the
reported `tokenUsage` object into the controller's `token_usage.json` and marks
`total_tokens_include_cached_input=True`. The report reads the **final cumulative
`usage.total`**, rather than summing cumulative events repeatedly:

1. `hybrid_rollout/report_site/build.py:76` reads each selected archive's
   `controller/history.json` and `controller/token_usage.json`.
2. The builder counts only history entries with `executed_steps > 0` as
   `chunks` and verifies they account for the reported control steps.
3. `build.py:219` sums each selected case's usage fields into the method totals.
4. The public JSON contains those summaries at `queries.cases.rows` and
   the aggregate at `reportData.totals`.

We checked all **100 public episode summaries** (50 per method). All token
fields, executed steps, segments and successes reconcile with the aggregate.
For each episode, `totalTokens = inputTokens + outputTokens`, with cached input
within input and reported reasoning output within output. The totals include
380,541 versus 873,464 reasoning-output tokens; those fields are **subsets** of
1,305,025 versus 2,086,564 output tokens and must not be added again.

This establishes consistency of the published summary and extraction logic.
It does not independently validate a provider invoice or prove that every
historical usage notification was received before the final snapshot.

## What the public release still cannot answer

`skill/transport.py:23` records app-server RPC input/output to JSONL files;
`skill/run.py:289` and `:315` record host tool requests/results. Those runtime
logs are **not** included in the public source release. The available JSON
therefore cannot reveal exact request-level context lengths, cache transitions,
all internal model retries or latency decomposition.

The code also permits recoverable pre-execution input rejection and continued
reasoning, plus same-thread network continuation (`skill/run.py:210`, `:350`).
Their cost belongs in an episode ledger even when no physical action executes.
Selected-case totals do not automatically include earlier abandoned attempts.

The next comparison should isolate: (a) longer action segments; (b) model-call
scheduling; (c) persistent executable skills; (d) state/context representation;
and (e) development cost. Static evidence already rules out two incorrect
shortcuts: **Direct is not a memoryless per-physics-step controller**, and
**the hybrid does not avoid all model review when pi05 is accepted**.
