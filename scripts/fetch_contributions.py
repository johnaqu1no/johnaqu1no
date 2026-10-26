#!/usr/bin/env python3
"""Pull the last year of contributions from the GraphQL API into
data/contributions.json.

Needs a token. Use a classic PAT with `read:user` (as the PROFILE_TOKEN secret)
so private-repo contributions count; the Actions GITHUB_TOKEN only sees what
your public profile shows.

Usage: GITHUB_TOKEN=... python scripts/fetch_contributions.py
"""
import datetime as dt
import json
import os

import requests

from common import ROOT, config

QUERY = """
query($login: String!, $from: DateTime, $to: DateTime) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      totalCommitContributions
      totalPullRequestContributions
      restrictedContributionsCount
      totalRepositoriesWithContributedCommits
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount contributionLevel } }
      }
    }
  }
}
"""
LEVELS = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2,
          "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}


def main():
    cfg = config()
    username = cfg["username"]
    # "year" = Jan 1 to today, "rolling" = GitHub's default last 12 months
    span = cfg.get("range", "rolling")
    today = dt.date.today()
    variables = {"login": username}
    if span == "year":
        variables["from"] = f"{today.year}-01-01T00:00:00Z"
        variables["to"] = f"{today.isoformat()}T23:59:59Z"
    token = os.environ.get("PROFILE_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("set PROFILE_TOKEN or GITHUB_TOKEN")

    r = requests.post(
        "https://api.github.com/graphql",
        json={"query": QUERY, "variables": variables},
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    r.raise_for_status()
    body = r.json()
    if "errors" in body:
        raise SystemExit(body["errors"])
    col = body["data"]["user"]["contributionsCollection"]
    cal = col["contributionCalendar"]

    days = {}
    for week in cal["weeks"]:
        for d in week["contributionDays"]:
            days[d["date"]] = {"count": d["contributionCount"],
                               "level": LEVELS[d["contributionLevel"]]}

    ordered = sorted(days)
    counts = [days[d]["count"] for d in ordered]

    longest = cur = 0
    for c in counts:
        cur = cur + 1 if c > 0 else 0
        longest = max(longest, cur)
    current = 0
    for d in reversed(ordered):
        if days[d]["count"] > 0:
            current += 1
        elif d != ordered[-1]:  # an empty today doesn't break the streak
            break

    best = max(ordered, key=lambda d: days[d]["count"])
    out = {
        "fetched": today.isoformat(),
        "username": username,
        "range": span,
        "year": today.year,
        "total": cal["totalContributions"],
        "commits": col["totalCommitContributions"],
        "prs": col["totalPullRequestContributions"],
        "private": col["restrictedContributionsCount"],
        "repos_contributed": col["totalRepositoriesWithContributedCommits"],
        "current_streak": current,
        "longest_streak": longest,
        "best_day": {"date": best, "count": days[best]["count"]},
        "days": {d: days[d] for d in ordered},
    }
    (ROOT / "data").mkdir(exist_ok=True)
    (ROOT / "data" / "contributions.json").write_text(json.dumps(out, indent=1))
    print(f"{out['total']} contributions ({out['private']} private), "
          f"streak {current} (longest {longest})")


if __name__ == "__main__":
    main()
