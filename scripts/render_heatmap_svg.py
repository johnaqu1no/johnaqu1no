#!/usr/bin/env python3
"""Render data/contributions.json as an animated heatmap SVG.

53x7 calendar grid with a diagonal drop-in reveal that plays once and
freezes, plus a stats footer.

Usage: python scripts/render_heatmap_svg.py
Writes: contrib-heatmap.svg
"""
import datetime as dt

from common import FONT, config, contributions, write

CELL = 13
GAP = 3
LEFT = 46   # room for weekday labels
TOP = 34    # room for month labels


def main():
    t = config()["theme"]
    palette = t["heatmap"]
    data = contributions()
    if not data:
        raise SystemExit("run fetch_contributions.py first")
    days = data["days"]
    ordered = sorted(days)

    # week columns starting from the Sunday on/before the first day
    first = dt.date.fromisoformat(ordered[0])
    start = first - dt.timedelta(days=(first.weekday() + 1) % 7)
    last = dt.date.fromisoformat(ordered[-1])
    year_view = data.get("range") == "year"
    if year_view:
        # draw the whole calendar year, days still to come as empty outlines
        last = dt.date(data["year"], 12, 31)
    weeks = []
    d = start
    while d <= last:
        weeks.append([d + dt.timedelta(days=i) for i in range(7)])
        d += dt.timedelta(days=7)

    step = CELL + GAP
    grid_w = len(weeks) * step
    W = LEFT + grid_w + 16
    H = TOP + 7 * step + 58

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'font-family="{FONT}" font-size="11">',
        '<style>'
        '@keyframes drop{from{opacity:0;transform:translateY(-6px)}to{opacity:1;transform:translateY(0)}}'
        '.d{opacity:0;animation:drop .45s ease-out forwards}'
        '</style>',
        f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="8" fill="{t["bg"]}" stroke="{t["border"]}"/>',
    ]

    # a month label goes on the first week that starts in it, skipped when the
    # next label is too close (the partial weeks at either end)
    starts = [wi for wi, w in enumerate(weeks) if wi == 0 or w[0].month != weeks[wi - 1][0].month]
    for i, wi in enumerate(starts):
        nxt = starts[i + 1] if i + 1 < len(starts) else len(weeks)
        if nxt - wi >= 3:
            m = weeks[wi][0].strftime("%b")
            out.append(f'<text x="{LEFT + wi * step}" y="{TOP - 10}" fill="{t["dim"]}">{m}</text>')

    for label, row in (("Mon", 1), ("Wed", 3), ("Fri", 5)):
        y = TOP + row * step + CELL - 3
        out.append(f'<text x="{LEFT - 30}" y="{y}" fill="{t["dim"]}">{label}</text>')

    for wi, week in enumerate(weeks):
        for di, date in enumerate(week):
            day = days.get(date.isoformat())
            x, y = LEFT + wi * step, TOP + di * step
            if not day:
                if year_view and date.year == data["year"]:
                    out.append(
                        f'<rect x="{x + 0.5}" y="{y + 0.5}" width="{CELL - 1}" height="{CELL - 1}" '
                        f'rx="3" fill="none" stroke="{palette[0]}"/>'
                    )
                continue
            level = min(day["level"], len(palette) - 1)
            out.append(
                f'<rect class="d" x="{x}" y="{y}" width="{CELL}" '
                f'height="{CELL}" rx="3" fill="{palette[level]}" '
                f'style="animation-delay:{(wi + di) * 0.018:.3f}s"><title>{day["count"]} on {date}</title></rect>'
            )

    fy = H - 22
    period = f"in {data['year']}" if year_view else "in the last year"
    out.append(
        f'<text x="{LEFT}" y="{fy}" fill="{t["dim"]}">'
        f'<tspan fill="{t["key"]}">{data["total"]}</tspan> contributions {period}'
        f'<tspan dx="16">|</tspan>'
        f'<tspan dx="16">streak </tspan><tspan fill="{t["key"]}">{data["current_streak"]}d</tspan>'
        f'<tspan dx="10">(longest {data["longest_streak"]}d)</tspan></text>'
    )
    lx = LEFT + grid_w - 5 * step - 40
    out.append(f'<text x="{lx - 38}" y="{fy}" fill="{t["dim"]}">Less</text>')
    for i, color in enumerate(palette):
        out.append(f'<rect x="{lx + i * step}" y="{fy - 10}" width="{CELL}" height="{CELL}" rx="3" fill="{color}"/>')
    out.append(f'<text x="{lx + 5 * step + 6}" y="{fy}" fill="{t["dim"]}">More</text>')

    out.append("</svg>")
    write("contrib-heatmap.svg", "\n".join(out))


if __name__ == "__main__":
    main()
