"""Draw Figure 1 from the saved result files: paired differences with 95
percent bootstrap intervals, one bit against silence and real bit against
shuffled bit, per model and batch.

Usage, from the repository root, standard library only:

    python scripts/make_figure.py

Writes figures/fig1_paired_differences.svg.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures" / "fig1_paired_differences.svg"

X_MIN, X_MAX, X_TICK = -10.0, 20.0, 5.0
PANEL_W, ROW_H, LABEL_W, GAP = 300, 34, 200, 60
TOP, BOTTOM = 70, 50
INK, MUTED, GRID, ACCENT, SET_ASIDE = "#1f2328", "#59636e", "#d1d9e0", "#0969da", "#8c959f"


def load(name: str) -> dict:
    return json.loads((ROOT / "data" / name).read_text())


def rows() -> list[tuple[str, dict, dict, bool]]:
    b1 = load("one-bit-results.json")
    ext = load("one-bit-extension-results.json")
    return [
        ("7B, pooled (n = 30)", ext["7B_pooled"]["delta_message"], ext["7B_pooled"]["delta_episode"], False),
        ("7B, batch 1 (n = 10)", b1["delta_message"], b1["delta_episode"], False),
        ("7B, batch 2 (n = 20)", ext["7B_batch2"]["delta_message"], ext["7B_batch2"]["delta_episode"], False),
        ("14B (n = 20)", ext["14B"]["delta_message"], ext["14B"]["delta_episode"], False),
        ("32B (n = 20), set aside", ext["32B"]["delta_message"], ext["32B"]["delta_episode"], True),
    ]


def x_at(panel_left: float, value: float) -> float:
    return panel_left + (value - X_MIN) / (X_MAX - X_MIN) * PANEL_W


def panel(left: float, title: str, cis: list[tuple[dict, bool]], height: float) -> list[str]:
    out = [f'<text x="{left + PANEL_W / 2}" y="{TOP - 30}" text-anchor="middle" font-weight="600">{title}</text>']
    tick = X_MIN
    while tick <= X_MAX:
        x = x_at(left, tick)
        out.append(f'<line x1="{x}" y1="{TOP - 10}" x2="{x}" y2="{height - BOTTOM}" stroke="{GRID}"/>')
        label = "0" if tick == 0 else f"{tick:+g}"
        out.append(f'<text x="{x}" y="{height - BOTTOM + 18}" text-anchor="middle" fill="{MUTED}">{label}</text>')
        tick += X_TICK
    zero = x_at(left, 0)
    out.append(f'<line x1="{zero}" y1="{TOP - 10}" x2="{zero}" y2="{height - BOTTOM}" stroke="{INK}" stroke-dasharray="4 3"/>')
    for i, (ci, set_aside) in enumerate(cis):
        y = TOP + i * ROW_H + ROW_H / 2
        color = SET_ASIDE if set_aside else ACCENT
        lo, hi, mid = x_at(left, ci["ci95_low"]), x_at(left, ci["ci95_high"]), x_at(left, ci["mean"])
        out.append(f'<line x1="{lo}" y1="{y}" x2="{hi}" y2="{y}" stroke="{color}" stroke-width="2"/>')
        for end in (lo, hi):
            out.append(f'<line x1="{end}" y1="{y - 5}" x2="{end}" y2="{y + 5}" stroke="{color}" stroke-width="2"/>')
        fill = "#ffffff" if set_aside else color
        out.append(f'<circle cx="{mid}" cy="{y}" r="5" fill="{fill}" stroke="{color}" stroke-width="2"/>')
    out.append(
        f'<text x="{left + PANEL_W / 2}" y="{height - 12}" text-anchor="middle" fill="{MUTED}">'
        "Paired difference in coalition advantage (points)</text>"
    )
    return out


def main() -> int:
    data = rows()
    height = TOP + len(data) * ROW_H + BOTTOM
    width = LABEL_W + 2 * PANEL_W + GAP + 20
    left_a = LABEL_W
    left_b = LABEL_W + PANEL_W + GAP
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="-apple-system, Helvetica, Arial, sans-serif" '
        f'font-size="13" fill="{INK}">',
        f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
    ]
    for i, (label, _, _, set_aside) in enumerate(data):
        y = TOP + i * ROW_H + ROW_H / 2 + 4
        fill = MUTED if set_aside else INK
        parts.append(f'<text x="{LABEL_W - 14}" y="{y}" text-anchor="end" fill="{fill}">{label}</text>')
    parts += panel(left_a, "One bit minus silence (B1 - NC)", [(m, s) for _, m, _, s in data], height)
    parts += panel(left_b, "Real bit minus shuffled bit (B1 - B1S)", [(e, s) for _, _, e, s in data], height)
    parts.append("</svg>")
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text("\n".join(parts) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
