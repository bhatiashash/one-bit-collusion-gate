# One bit collusion gate

A mechanically enforced communication budget for the Colosseum Jira task, built for the Apart Research AI Collusion Research Sprint (October 2026), Track 3.1 with a secondary link to Track 1.5.

Author: Shash Bhatia ([@bhatiashash](https://github.com/bhatiashash))

## The question

Does one episode specific binary message per episode beat no message for a coalition of agents, measured on the original task rewards?

## What this repository holds

- `module/`: the channel mediator (`one_bit.py`), the channel audit (`audit_one_bit.py`), the frozen bank builder (`build_bank.py`), and the frozen analysis scripts (`analyze_one_bit.py`, `analyze_extension.py`).
- `harness/`: the two starter repository files this project modified to wire the mediator into the run path (`run.py`, `prompts.py`). Provenance note: these files originate in the sprint starter repository (see Credits). They are included so the integration is reproducible, with the mediator wiring as the only functional change.
- `configs/`: every configuration that produced a number in the report, in `dev/`, `eval/`, and `ext/` sets.
- `data/`: the frozen shuffled bit bank and the result files the report's tables are built from.
- `docs/`: the execution plan and the freeze note, including the dated extension amendment and the full protocol record.
- `report.md`: the sprint report.

## The result, stated plainly

The headline effect is not proven on any model. With 30 paired games per arm on Qwen2.5-7B-Instruct, the one bit arm scored -4.41 points of coalition advantage against -4.91 for a silent channel, a difference of +0.49 with a 95 percent bootstrap interval of -3.67 to +4.98. On Qwen2.5-14B-Instruct-AWQ the difference was +0.81 (interval -5.36 to +6.38). One secondary result is clean: on the 14B model the real bit beat a shuffled bit by +4.98 (interval +0.06 to +10.22). The 32B batch failed its predeclared positive control gate and is reported as description only, under the rule written before those runs began. The gate held in all 220 audited evaluation runs, and no arm harmed the non coalition players. The full report is in `report.md`.

## How to run it

1. Clone the sprint starter repository (see Credits) and complete its Colosseum setup.
2. Copy `module/` into `colosseum/experiments/collusion/` and replace `run.py` and `prompts.py` there with the versions in `harness/`.
3. Serve a model with tool choice enabled, then run any configuration in `configs/` with the experiment runner. The analysis scripts regenerate every reported number from the saved run outputs.

## Credits

The Colosseum environment, the Jira ticket allocation task, and the starter code are by Poseidon Research and Apart Research for the AI Collusion Research Sprint: https://github.com/poseidon-research/collusion_hackathon. This repository contains only the additions and modifications made for the one bit study, plus its report and data files.

## License

MIT, for the code and documents authored for this study. Files under `harness/` remain under the starter repository's terms.
