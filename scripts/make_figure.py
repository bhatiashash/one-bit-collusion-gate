"""Draw Figure 1 from the saved result files: paired differences with 95
percent bootstrap intervals, one bit against silence and real bit against
shuffled bit, per model and batch.

Usage, from the repository root, standard library only:

    python scripts/make_figure.py

Writes figures/fig1_paired_differences.svg (for the README and report.md)
and figures/fig1_paired_differences.tex (a TikZ picture that
report/report.tex inputs). Both come from the same drawing commands.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_SVG = ROOT / "figures" / "fig1_paired_differences.svg"
OUT_TEX = ROOT / "figures" / "fig1_paired_differences.tex"

X_MIN, X_MAX, X_TICK = -10.0, 20.0, 5.0
PANEL_W, ROW_H, LABEL_W, GAP = 300, 34, 200, 80
TOP, BOTTOM = 70, 50
COLORS = {"ink": "1f2328", "muted": "59636e", "grid": "d1d9e0", "accent": "0969da", "setaside": "8c959f", "white": "ffffff"}
TEX_UNIT = 0.46  # points per SVG pixel; 880 px becomes about 405 pt, leaving room for the row labels in a 468 pt text width


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
        ("32B, set aside", ext["32B"]["delta_message"], ext["32B"]["delta_episode"], True),
        ("GPT-5 mini, set aside", ext["GPT5mini"]["delta_message"], ext["GPT5mini"]["delta_episode"], True),
    ]


# Drawing commands, in SVG pixel coordinates (y grows downward):
#   ("line", x1, y1, x2, y2, color, width, dashed)
#   ("text", x, y, anchor, color, size, bold, string)   anchor: start, middle, end; size: label, tick
#   ("circle", cx, cy, r, fill, stroke)


def x_at(panel_left: float, value: float) -> float:
    return panel_left + (value - X_MIN) / (X_MAX - X_MIN) * PANEL_W


def panel(left: float, title: str, cis: list[tuple[dict, bool]], height: float) -> list[tuple]:
    out: list[tuple] = [("text", left + PANEL_W / 2, TOP - 30, "middle", "ink", "label", True, title)]
    tick = X_MIN
    while tick <= X_MAX:
        x = x_at(left, tick)
        out.append(("line", x, TOP - 10, x, height - BOTTOM, "grid", 1, False))
        label = "0" if tick == 0 else f"{tick:+g}"
        out.append(("text", x, height - BOTTOM + 18, "middle", "muted", "tick", False, label))
        tick += X_TICK
    zero = x_at(left, 0)
    out.append(("line", zero, TOP - 10, zero, height - BOTTOM, "ink", 1, True))
    for i, (ci, set_aside) in enumerate(cis):
        y = TOP + i * ROW_H + ROW_H / 2
        color = "setaside" if set_aside else "accent"
        lo, hi, mid = x_at(left, ci["ci95_low"]), x_at(left, ci["ci95_high"]), x_at(left, ci["mean"])
        out.append(("line", lo, y, hi, y, color, 2, False))
        for end in (lo, hi):
            out.append(("line", end, y - 5, end, y + 5, color, 2, False))
        out.append(("circle", mid, y, 5, "white" if set_aside else color, color))
    out.append(("text", left + PANEL_W / 2, height - 12, "middle", "muted", "tick", False,
                "Paired difference (points)"))
    return out


def drawing() -> tuple[float, float, list[tuple]]:
    data = rows()
    height = TOP + len(data) * ROW_H + BOTTOM
    width = LABEL_W + 2 * PANEL_W + GAP + 20
    cmds: list[tuple] = []
    for i, (label, _, _, set_aside) in enumerate(data):
        y = TOP + i * ROW_H + ROW_H / 2 + 4
        cmds.append(("text", LABEL_W - 14, y, "end", "muted" if set_aside else "ink", "label", False, label))
    cmds += panel(LABEL_W, "One bit minus silence (B1 - NC)", [(m, s) for _, m, _, s in data], height)
    cmds += panel(LABEL_W + PANEL_W + GAP, "Real bit minus shuffled bit (B1 - B1S)", [(e, s) for _, _, e, s in data], height)
    return width, height, cmds


def to_svg(width: float, height: float, cmds: list[tuple]) -> str:
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="-apple-system, Helvetica, Arial, sans-serif" '
        f'font-size="13" fill="#{COLORS["ink"]}">',
        f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
    ]
    for c in cmds:
        if c[0] == "line":
            _, x1, y1, x2, y2, color, w, dashed = c
            dash = ' stroke-dasharray="4 3"' if dashed else ""
            width_attr = f' stroke-width="{w}"' if w != 1 else ""
            parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#{COLORS[color]}"{width_attr}{dash}/>')
        elif c[0] == "text":
            _, x, y, anchor, color, _, bold, s = c
            weight = ' font-weight="600"' if bold else ""
            parts.append(f'<text x="{x}" y="{y}" text-anchor="{anchor}" fill="#{COLORS[color]}"{weight}>{s}</text>')
        else:
            _, cx, cy, r, fill, stroke = c
            parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#{COLORS[fill]}" stroke="#{COLORS[stroke]}" stroke-width="2"/>')
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def to_tikz(height: float, cmds: list[tuple]) -> str:
    def pt(x: float, y: float) -> str:
        return f"({x * TEX_UNIT:.2f}pt,{(height - y) * TEX_UNIT:.2f}pt)"

    anchors = {"start": "west", "middle": "center", "end": "east"}
    sizes = {"label": r"\footnotesize", "tick": r"\scriptsize"}
    lines = ["% Generated by scripts/make_figure.py. Do not edit by hand.", r"\begin{tikzpicture}"]
    lines += [rf"\definecolor{{fig{name}}}{{HTML}}{{{hexa.upper()}}}" for name, hexa in COLORS.items()]
    for c in cmds:
        if c[0] == "line":
            _, x1, y1, x2, y2, color, w, dashed = c
            style = f"fig{color}, line width={w * TEX_UNIT * 1.5:.2f}pt" + (", dash pattern=on 2pt off 1.5pt" if dashed else "")
            lines.append(rf"\draw[{style}] {pt(x1, y1)} -- {pt(x2, y2)};")
        elif c[0] == "text":
            _, x, y, anchor, color, size, bold, s = c
            font = sizes[size] + (r"\bfseries" if bold else "")
            # SVG y is the text baseline; TikZ anchors on the baseline too.
            lines.append(rf"\node[anchor=base {anchors[anchor]}, inner sep=0, text=fig{color}, font={font}] at {pt(x, y)} {{{s}}};")
        else:
            _, cx, cy, r, fill, stroke = c
            lines.append(rf"\draw[fig{stroke}, fill=fig{fill}, line width=1.5pt] {pt(cx, cy)} circle ({r * TEX_UNIT:.2f}pt);")
    lines.append(r"\end{tikzpicture}")
    return "\n".join(lines).replace("base center", "base") + "\n"


def main() -> int:
    width, height, cmds = drawing()
    OUT_SVG.parent.mkdir(exist_ok=True)
    OUT_SVG.write_text(to_svg(width, height, cmds))
    OUT_TEX.write_text(to_tikz(height, cmds))
    for path in (OUT_SVG, OUT_TEX):
        print(f"wrote {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
