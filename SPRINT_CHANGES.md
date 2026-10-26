# Sprint changes: pre-existing versus new code

Author of new work: Shash Bhatia, Apart Research AI Collusion Research Sprint, October 2026.
Base: [poseidon-research/collusion_hackathon](https://github.com/poseidon-research/collusion_hackathon) at `e6fb130`, folder `colosseum/`.
The two starter files this project modified are byte-identical in every starter commit from `9c61132` through `e6fb130`, so `harness/starter.patch` applies cleanly to any of them.

## Pre-existing (from the starter repository, not modified)

- Everything under `colosseum/` except the two files listed in the next section.
- The Jira ticket allocation environment and its reward computation.
- The experiment runner, sweep expansion, blackboard logging, and `summary.csv` output.
- The coalition setup used by every arm: path topology, four agents, `first_and_last` pair selection, the `simple` coalition prompt variant.
- `util/poseidon_compute/` for model endpoints. The Qwen runs reached a self-served Modal endpoint through its `LLM_BASE_URL` path, and the second extension runs reached OpenRouter through the same path.

## Modified (starter files, wiring only)

| File | Change |
|---|---|
| `colosseum/experiments/collusion/run.py` | Imports `one_bit`, installs the mediator on the coalition blackboard when `experiment.collusion.one_bit.enabled` is set, tells it the current phase and planning round, and writes `mediator_log.json` plus `one_bit_*` fields in the run summary. With `one_bit` absent, behavior is unchanged. |
| `colosseum/experiments/collusion/prompts.py` | Appends the one bit plan block to each colluder's prompt when the runtime is present. Only the sender's block includes the draw. |

The full diff is `harness/starter.patch` (127 lines). The modified files themselves are in `harness/`.

## New (written during the sprint)

| File | Purpose |
|---|---|
| `module/one_bit.py` | The channel mediator with four modes (`unrestricted`, `one_bit`, `shuffled_bit`, `none`), the hidden draw, the plan prompt block, and the bonus ledger. |
| `module/audit_one_bit.py` | Channel audit. Checks the designated blackboard's delivered events against the mediator log for every gated run. Exit code 1 on any breach. |
| `module/build_bank.py` | Builds the frozen shuffled bit bank from development one bit runs. |
| `module/analyze_one_bit.py` | Frozen batch 1 analysis: paired bootstrap, harm, retention rule, interpretation labels. |
| `module/analyze_extension.py` | Extension analysis under the October 25 amendment: pooled 7B batches, per model positive control gate. |
| `configs/dev/` | Development configs: Gate 1 (stock), Gate 2, and both pilots. |
| `configs/eval/` | Batch 1 configs, 7B, seeds 101 to 110. |
| `configs/ext/` | Extension configs: 7B seeds 111 to 130 (`ext_*`), 14B (`m14_*`) and 32B (`m32_*`) seeds 101 to 120, plus smoke tests and reruns. The second extension adds the OpenRouter sets: GPT-5 mini (`gm_*`, relaunched as `gm2_*`) and Claude Haiku (`hk_*`, `hk2_*`, and the reduced `hk3_*` set that was stopped before completing any game). |
| `data/bank_frozen_v2.json` | The frozen bank used by every shuffled bit run. |
| `data/one-bit-results.json` | Output of `analyze_one_bit.py` on batch 1. |
| `data/one-bit-extension-results.json` | Output of `analyze_extension.py` on the extension. |
| `data/one-bit-eval-summary-fields.json`, `data/one-bit-extension-summary-fields.json` | Per seed advantages (and, for batch 1, non member means and joint rewards) taken from the run outputs. |
| `data/numbers.json` | Written by `scripts/rebuild_numbers.py`. |
| `scripts/rebuild_numbers.py` | Reruns the paired bootstrap from the per seed data files and checks the result files and `report.md` against it. Added after the sprint. |
| `scripts/make_figure.py` | Draws `figures/fig1_paired_differences.svg` from the result files. Added after the sprint. |
| `docs/one-bit-execution-plan.md` | The execution plan (version 3 and its amendments). |
| `docs/one-bit-freeze.md` | The freeze note: every frozen field, Revision 1, the extension amendment, and dated execution notes. |
| `docs/release-hashes.txt` | SHA-256 of every released code, config and data file. |
| `report.md` | The sprint report. |

During the sprint the plan and freeze note lived at `~/workspace/sprint/`. The docstrings in `module/one_bit.py` and `module/analyze_one_bit.py` still point there; in this repository those files are `docs/one-bit-execution-plan.md` and `docs/one-bit-freeze.md`. The docstrings are left as they were so the frozen files keep their released hashes.

## Run log

The freeze note has the full dated record. In short:

- **First pilot leak.** Under the first (mirror) plans, silent pairs still executed the fitting plan in 3 of 5 games, because the sender's visible task choice revealed the recipient's by elimination. The plans were redesigned and the pilot rerun before any evaluation run (Revision 1, October 25, about 7:39 to 8:00 pm EDT). The v1 bank was discarded and `bank_frozen_v2.json` built from pilot 2.
- **Batch 1 one bit arm relaunched.** An infrastructure restart stopped the first `eval_b1` batch at 5 of 10 games. It was relaunched as `eval_b1_r2` with identical settings and seeds. The partial batch was never pooled.
- **Empty silent batch.** The silent arm's first batch directory (`20261025-203830`) holds zero completed runs and contributes nothing.
- **Extension restart 1** (about 9:32 pm EDT). All three extension chains were killed minutes after launch. The 7B unrestricted arm had 6 of 20 games; it was relaunched as `ext_pc_r2`. The other arms relaunched unchanged.
- **Extension restart 2** (about 11:15 pm EDT). The 14B baseline arm stopped at 12 of 20 games. It was relaunched as `m14_d_r2`. The partial batch was never pooled.
- **One incomplete game.** 14B, one bit arm, seed 119 ended with status `incomplete` and no rewards. It passed the channel audit. The seed was rerun once as `m14_b1_s119` with identical settings, and the extension analysis excludes any run without rewards and prints each exclusion. Exactly one exclusion occurred.
- **Smoke tests.** `m14_smoke_b1` and `m32_smoke_b1` each passed the channel audit 2 of 2 before their model's full batch launched.
- **Second extension (OpenRouter).** GPT-5 mini completed all five arms at 20 games each under the `gm2_*` tags after its first batch failed on the provider in-flight budget and two runtime restarts interrupted the relaunch; the interrupted arms resumed in place under the same roots and configs. The batch failed its positive control gate and is reported as description only. The Haiku batch failed twice on provider limits, was reduced to seeds 101 to 110, and was then stopped by the author on October 26, 2026 before completing any game; it produced no results. The freeze note carries the full dated record.

Serving changes during the runs (container caps, runner concurrency, inputs per container) touched no prompt, rule, seed or outcome definition.
