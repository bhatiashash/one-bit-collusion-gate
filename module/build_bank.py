"""Build the frozen shuffled-bit bank from B1 development runs.

Collects the delivered bit from every B1 (mode=one_bit) mediator log under
the given output roots, in seed order, and writes a bank file:

    {"bits": [...], "source": "B1 development runs", "runs": [...]}

The shuffled-bit mediator samples from this bank with replacement using a
per-episode seeded generator (see one_bit.py, BANK_SALT). Build the bank
once, before the evaluation freeze, and record its path and contents in the
freeze note. The evaluation bank is never rebuilt from evaluation data.

Usage (from the colosseum directory):

    python -m experiments.collusion.build_bank \
        experiments/collusion/outputs/gate2_b1 \
        experiments/collusion/outputs/pilot_b1 \
        --out experiments/collusion/outputs/bank_frozen.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("roots", nargs="+", help="B1 output roots")
    ap.add_argument("--out", required=True, help="bank JSON path to write")
    args = ap.parse_args()

    entries = []
    for root in args.roots:
        for log_path in sorted(Path(root).rglob("mediator_log.json")):
            med = json.loads(log_path.read_text())
            if med.get("mode") != "one_bit":
                continue
            run_cfg = json.loads((log_path.parent / "run_config.json").read_text())
            bit = med.get("delivered_bit")
            if bit is None:
                print(f"WARNING: no delivered bit in {log_path.parent}")
                continue
            entries.append(
                {"seed": int(run_cfg["seed"]), "bit": int(bit),
                 "run": str(log_path.parent)}
            )
    entries.sort(key=lambda e: e["seed"])
    if not entries:
        print("No B1 delivered bits found; bank not written.")
        return 1
    bank = {
        "bits": [e["bit"] for e in entries],
        "source": "B1 development runs (delivered bits, seed order)",
        "runs": entries,
    }
    out = Path(args.out)
    out.write_text(json.dumps(bank, indent=1))
    print(f"Wrote bank with {len(entries)} bits to {out}: {bank['bits']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
