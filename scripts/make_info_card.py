#!/usr/bin/env python3
"""Generate the neofetch-style whoami card from profile.toml.

Lines fade and slide in one after another, then a cursor blinks.
Set STATIC=1 to skip animation.

Usage: python scripts/make_info_card.py
Writes: info-card.svg
"""
import html
import os

from common import FONT, config, contributions, write

LINE_H = 24
CHAR_W = 7.85       # monospace advance at font-size 13
KEY_W = 11          # key column width in chars
STATIC = os.environ.get("STATIC") == "1"


class Stats(dict):
    def __missing__(self, key):
        return "?"


def line(x, y, parts, idx):
    tspans = "".join(f'<tspan fill="{c}">{html.escape(s)}</tspan>' for s, c in parts)
    if STATIC:
        return f'<text x="{x}" y="{y}" xml:space="preserve">{tspans}</text>'
    begin = f"{0.15 + idx * 0.12:.2f}s"
    return (
        f'<text x="{x}" y="{y}" xml:space="preserve" opacity="0">{tspans}'
        f'<animate attributeName="opacity" from="0" to="1" begin="{begin}" dur="0.45s" fill="freeze"/>'
        f'<animateTransform attributeName="transform" type="translate" from="-14 0" to="0 0" '
        f'begin="{begin}" dur="0.45s" fill="freeze"/></text>'
    )


def main():
    cfg = config()
    t = cfg["theme"]
    who = cfg["whoami"]
    stats = Stats({k: f"{v:,}" if isinstance(v, int) else v
                   for k, v in (contributions() or {}).items()})

    host = cfg["prompt_host"]
    rows = [[host], ["-" * len(host)]] + who["rows"]
    longest = max(len(r[0]) if len(r) == 1 else KEY_W + len(r[1].format_map(stats)) for r in rows if r)
    W = max(490, round(48 + longest * CHAR_W))

    body = []
    y = 72
    idx = 0
    for row in rows:
        if not row:
            y += LINE_H // 2
            continue
        if len(row) == 1:
            color = t["title"] if row[0] == host else t["border"]
            body.append(line(24, y, [(row[0], color)], idx))
        else:
            key, val = row[0], row[1].format_map(stats)
            if key:
                parts = [(key.ljust(KEY_W - 2), t["key"]), ("> ", t["accent"]), (val, t["fg"])]
            else:
                parts = [(" " * KEY_W, t["fg"]), (val, t["fg"])]
            body.append(line(24, y, parts, idx))
        y += LINE_H
        idx += 1
    H = y + 12

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'font-family="{FONT}" font-size="13">',
        f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="8" fill="{t["bg"]}" stroke="{t["border"]}"/>',
        '<circle cx="22" cy="20" r="6" fill="#ff5f56"/>'
        '<circle cx="42" cy="20" r="6" fill="#ffbd2e"/>'
        '<circle cx="62" cy="20" r="6" fill="#27c93f"/>',
        f'<text x="{W // 2}" y="25" text-anchor="middle" fill="{t["dim"]}">{html.escape(who["title"])}</text>',
        f'<line x1="0" y1="38" x2="{W}" y2="38" stroke="{t["border"]}"/>',
        *body,
    ]
    if not STATIC:
        out.append(
            f'<rect x="24" y="{y - 12}" width="8" height="15" fill="{t["key"]}" opacity="0">'
            f'<animate attributeName="opacity" values="0;1;1;0;0" begin="{0.15 + idx * 0.12:.2f}s" '
            f'dur="1.2s" repeatCount="indefinite"/></rect>'
        )
    out.append("</svg>")
    write("info-card.svg", "\n".join(out))


if __name__ == "__main__":
    main()
