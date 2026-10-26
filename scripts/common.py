"""Shared config loading for the profile art generators."""
import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"


def config():
    with open(ROOT / "profile.toml", "rb") as f:
        return tomllib.load(f)


def contributions():
    path = ROOT / "data" / "contributions.json"
    return json.loads(path.read_text()) if path.exists() else None


def write(name, svg):
    (ROOT / name).write_text(svg)
    print(f"wrote {name} ({len(svg)} bytes)")
