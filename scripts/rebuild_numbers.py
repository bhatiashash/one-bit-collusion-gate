"""Rebuild the report's headline numbers from the per seed data files.

The frozen analysis scripts (module/analyze_one_bit.py and
module/analyze_extension.py) read raw run directories. This script needs
only the files in data/: it reruns the same paired bootstrap, with the same
generator seed and the same order of draws, on the per seed advantages, and
checks the result against the saved result files and against report.md.

- Batch 1 (data/one-bit-eval-summary-fields.json) holds full precision
  advantages and non member means, so every interval reproduces exactly.
- The extension (data/one-bit-extension-summary-fields.json) holds
  advantages rounded to three decimals and no non member means. Its
  intervals reproduce to within rounding, and its harm intervals are not
  recomputed (the generator still makes the same draws, so later intervals
  stay aligned).

Usage, from the repository root, standard library only:

    python scripts/rebuild_numbers.py

Exit code is 1 if any check fails.
"""

from __future__ import annotations

import json
import random
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOT_SEED = 20261025
BOOT_N = 10_000
CI_KEYS = ("mean", "ci95_low", "ci95_high", "ci90_low", "ci90_high")

failures: list[str] = []


def load(name: str):
    return json.loads((ROOT / "data" / name).read_text())


def by_seed(fields: dict, key: str | None = None) -> dict[int, float]:
    return {int(s): (v[key] if key else v) for s, v in fields.items()}


def paired(a: dict[int, float], b: dict[int, float]) -> list[float]:
    return [a[s] - b[s] for s in sorted(set(a) & set(b))]


def boot_ci(diffs: list[float], rng: random.Random) -> dict:
    # Same draws, in the same order, as boot_ci in module/analyze_one_bit.py.
    n = len(diffs)
    means = sorted(
        statistics.mean(diffs[rng.randrange(n)] for _ in range(n)) for _ in range(BOOT_N)
    )
    return {
        "mean": statistics.mean(diffs),
        "ci95_low": means[int(0.025 * BOOT_N)],
        "ci95_high": means[int(0.975 * BOOT_N)],
        "ci90_low": means[int(0.05 * BOOT_N)],
        "ci90_high": means[int(0.95 * BOOT_N)],
    }


def skip_draws(n: int, rng: random.Random) -> None:
    for _ in range(BOOT_N * n):
        rng.randrange(n)


def check(label: str, got: dict, want: dict, tol: float) -> None:
    worst = max(abs(got[k] - want[k]) for k in CI_KEYS)
    status = "ok" if worst <= tol else "FAIL"
    if status == "FAIL":
        failures.append(label)
    print(f"  {status:4} {label:28} {fmt(got)}   (max diff {worst:.1e})")


def fmt(ci: dict) -> str:
    return f"{ci['mean']:+.2f} ({ci['ci95_low']:+.2f} to {ci['ci95_high']:+.2f})"


def batch1() -> dict[str, dict]:
    print("Batch 1, 7B, seeds 101 to 110 (exact)")
    fields = load("one-bit-eval-summary-fields.json")
    want = load("one-bit-results.json")
    adv = {arm: by_seed(fields[arm], "adv") for arm in ("PC", "B1", "B1S", "NC")}
    non = {arm: by_seed(fields[arm], "nonmem") for arm in ("PC", "B1", "B1S", "NC", "D")}
    rng = random.Random(BOOT_SEED)
    got = {
        "delta_message": boot_ci(paired(adv["B1"], adv["NC"]), rng),
        "delta_episode": boot_ci(paired(adv["B1"], adv["B1S"]), rng),
        "pc_minus_nc": boot_ci(paired(adv["PC"], adv["NC"]), rng),
    }
    for key, ci in got.items():
        check(key, ci, want[key], 1e-9)
    for arm in ("PC", "B1", "B1S", "NC"):
        check(f"harm {arm}", boot_ci(paired(non["D"], non[arm]), rng), want["harm"][arm], 1e-9)
    check("harm_b1_minus_nc", boot_ci(paired(non["NC"], non["B1"]), rng), want["harm_b1_minus_nc"], 1e-9)
    for arm in ("PC", "B1", "B1S", "NC"):
        mean = statistics.mean(adv[arm].values())
        if abs(mean - want["arms"][arm]["advantage_mean"]) > 1e-9:
            failures.append(f"batch 1 {arm} advantage mean")
    got["arms"] = {arm: statistics.mean(adv[arm].values()) for arm in adv}
    return got


def extension() -> dict[str, dict]:
    fields = load("one-bit-extension-summary-fields.json")
    want = load("one-bit-extension-results.json")
    rng = random.Random(BOOT_SEED)
    out: dict[str, dict] = {}
    # Model order matches the spec the extension analysis ran with.
    for model in want:
        print(f"Extension, {model} (rounded inputs)")
        adv = {arm: by_seed(fields[model][arm]) for arm in ("PC", "B1", "B1S", "NC", "D")}
        got = {
            "delta_message": boot_ci(paired(adv["B1"], adv["NC"]), rng),
            "delta_episode": boot_ci(paired(adv["B1"], adv["B1S"]), rng),
            "pc_minus_nc": boot_ci(paired(adv["PC"], adv["NC"]), rng),
        }
        for key, ci in got.items():
            check(key, ci, want[model][key], 2e-3)
        for arm in ("PC", "B1", "B1S", "NC"):
            skip_draws(want[model]["harm"][arm]["n"], rng)
        got["arms"] = {arm: statistics.mean(adv[arm].values()) for arm in adv}
        got["harm"] = want[model]["harm"]
        out[model] = got
    return out


def report_check(b1: dict, ext: dict) -> None:
    """Every headline cell must appear verbatim in report.md."""
    text = (ROOT / "report.md").read_text()
    cells = [
        fmt(ext["7B_pooled"]["delta_message"]),
        fmt(b1["delta_message"]),
        fmt(ext["7B_batch2"]["delta_message"]),
        fmt(ext["14B"]["delta_message"]),
        fmt(ext["32B"]["delta_message"]),
        fmt(ext["GPT5mini"]["delta_message"]),
        fmt(ext["7B_pooled"]["delta_episode"]),
        fmt(ext["14B"]["delta_episode"]),
        fmt(ext["32B"]["delta_episode"]),
        fmt(ext["GPT5mini"]["delta_episode"]),
        fmt(ext["7B_pooled"]["pc_minus_nc"]),
        fmt(ext["14B"]["pc_minus_nc"]),
        fmt(ext["32B"]["pc_minus_nc"]),
        fmt(ext["GPT5mini"]["pc_minus_nc"]),
    ]
    print("report.md")
    for cell in cells:
        found = cell in text
        if not found:
            failures.append(f"report.md cell {cell}")
        print(f"  {'ok' if found else 'FAIL':4} {cell}")


def main() -> int:
    b1 = batch1()
    ext = extension()
    report_check(b1, ext)
    (ROOT / "data" / "numbers.json").write_text(
        json.dumps({"batch1_7B": b1, "extension": ext}, indent=1) + "\n"
    )
    print("wrote data/numbers.json")
    if failures:
        print(f"{len(failures)} check(s) failed: {', '.join(failures)}")
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
