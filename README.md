# One bit collusion gate

A mechanically enforced communication budget for the Colosseum Jira task, built for the Apart Research AI Collusion Research Sprint (October 2026), Track 3.1 with a secondary link to Track 1.5.

Author: Shash Bhatia ([@bhatiashash](https://github.com/bhatiashash))

## The question

Does one episode specific binary message per episode beat no message for a coalition of agents, measured on the original task rewards?

## The result, stated plainly

The headline effect is not proven on any model. With 30 paired games per arm on Qwen2.5-7B-Instruct, the one bit arm scored -4.41 points of coalition advantage against -4.91 for a silent channel, a difference of +0.49 with a 95 percent bootstrap interval of -3.67 to +4.98. On Qwen2.5-14B-Instruct-AWQ the difference was +0.81 (interval -5.36 to +6.38). One secondary result is clean: on the 14B model the real bit beat a shuffled bit by +4.98 (interval +0.06 to +10.22). The 32B batch failed its predeclared positive control gate and is reported as description only, under the rule written before those runs began. A second extension batch on GPT-5 mini, run through OpenRouter under a dated amendment, failed the same gate (unrestricted -4.61 against silent +0.35) and is also reported as description only; its real bit beat its shuffled bit by +4.25 (interval +0.57 to +8.12) with executed plan fit of 0.90. The gate held in all 280 audited evaluation runs, and no arm harmed the non coalition players. The full report is in `report.md`.

## What is here

| Path | Contents |
|---|---|
| `module/` | The channel mediator (`one_bit.py`), the channel audit (`audit_one_bit.py`), the frozen bank builder (`build_bank.py`), and the frozen analysis scripts (`analyze_one_bit.py`, `analyze_extension.py`). These drop into `colosseum/experiments/collusion/`. |
| `harness/` | The two starter files this project modified to wire the mediator into the run path (`run.py`, `prompts.py`), and `starter.patch`, the full diff against the starter repository. |
| `configs/` | Every configuration that produced a number in the report, in `dev/`, `eval/` and `ext/`, plus `extension_spec.json` for the extension analysis. |
| `data/` | The frozen shuffled bit bank, the two analysis result files, the per seed fields the report's tables come from, and `numbers.json`. |
| `scripts/` | `rebuild_numbers.py` checks every headline number against the per seed data; `make_figure.py` draws Figure 1. Standard library only. |
| `figures/` | Figure 1. |
| `docs/` | The execution plan, the freeze note with its dated amendments and execution notes, and `release-hashes.txt`. |
| `SPRINT_CHANGES.md` | Pre-existing versus new code, the starter commit, and the run log. |
| `report.md` | The sprint report. |

## Check the numbers without rerunning anything

From the repository root, with any Python 3.10 or later:

```bash
python scripts/rebuild_numbers.py
python scripts/make_figure.py
```

`rebuild_numbers.py` reruns the paired bootstrap (same generator seed, same order of draws as the frozen scripts) on the per seed data in `data/`. Batch 1 reproduces exactly. The extension per seed values are stored to three decimals, so its intervals reproduce to within 0.001. The script then checks that every headline interval appears as written in `report.md`, and exits with code 1 if anything differs.

The raw per run outputs (`final_summary.json`, `run_config.json`, `mediator_log.json`, blackboard logs) are not in this repository, so the channel audit and the frozen analysis scripts cannot be rerun from here.

## Reproduce from scratch

1. Clone the starter repository and check out the commit this work was built on:

   ```bash
   git clone https://github.com/poseidon-research/collusion_hackathon.git
   cd collusion_hackathon && git checkout e6fb130
   ```

   Set up Colosseum as `colosseum/README.md` describes (`./setup.sh colosseum`, then `compute.env` at the repository root).
2. Add this project:

   ```bash
   git apply /path/to/one-bit-collusion-gate/harness/starter.patch
   cp /path/to/one-bit-collusion-gate/module/*.py colosseum/experiments/collusion/
   mkdir -p colosseum/experiments/collusion/configs/one_bit colosseum/experiments/collusion/outputs
   cp -r /path/to/one-bit-collusion-gate/configs/* colosseum/experiments/collusion/configs/one_bit/
   cp /path/to/one-bit-collusion-gate/data/bank_frozen_v2.json colosseum/experiments/collusion/outputs/
   cd colosseum
   ```

3. Serve the model on an OpenAI compatible endpoint with tool choice enabled and point `LLM_BASE_URL` at it. The runs used vLLM on Modal; the freeze note lists the exact serving settings.
4. Run a configuration, then audit it:

   ```bash
   python -m experiments.collusion.run --config experiments/collusion/configs/one_bit/eval/eval_b1_r2.yaml
   python -m experiments.collusion.audit_one_bit experiments/collusion/outputs/eval_b1_r2
   ```

5. After every arm has run, the two analyses:

   ```bash
   python -m experiments.collusion.analyze_one_bit \
       --pc experiments/collusion/outputs/eval_pc --b1 experiments/collusion/outputs/eval_b1_r2 \
       --b1s experiments/collusion/outputs/eval_b1s --nc experiments/collusion/outputs/eval_nc \
       --d experiments/collusion/outputs/eval_d --hu experiments/collusion/outputs/eval_hu \
       --out one-bit-results.json
   python -m experiments.collusion.analyze_extension \
       --spec experiments/collusion/configs/one_bit/extension_spec.json \
       --out one-bit-extension-results.json
   ```

`extension_spec.json` was rebuilt from the run log in `SPRINT_CHANGES.md` after the sprint; the original spec file was not saved. Model outputs are sampled at temperature 0.7, so reruns give different games. The files in `data/` are the ones the report uses.

## Verify the protocol record

The freeze note (`docs/one-bit-freeze.md`) records every frozen field, the plan redesign, the extension amendment and each execution incident, with times. `docs/release-hashes.txt` holds the SHA-256 of every released code, config and data file. To check one:

```bash
shasum -a 256 module/analyze_one_bit.py
```

These hashes were computed at release, after the runs. They show that the files you have are the released files. They do not show what existed before the runs; the dated freeze note is the record for that.

## Note on content

The run logs come from a synthetic ticket allocation task with no personal data. The agents are prompted to form a coalition, and their messages include coordination against the other agents. The report's Appendix A covers limitations and dual use.

## Credits

The Colosseum environment, the Jira ticket allocation task, and the starter code are by Poseidon Research and Apart Research for the AI Collusion Research Sprint: <https://github.com/poseidon-research/collusion_hackathon>. This repository contains only the additions and modifications made for the one bit study, plus its report and data files.

## License

MIT, for the code and documents authored for this study. Files under `harness/` remain under the starter repository's terms.
