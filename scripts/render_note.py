#!/usr/bin/env python3
from __future__ import annotations
import argparse, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from note_lib import NoteError, load_json, render_note, validate_note


def parse_args():
    p = argparse.ArgumentParser(description="Render a XHS note JSON into HTML preview.")
    p.add_argument("input", help="Path to note JSON")
    p.add_argument("-o", "--output", help="Write rendered HTML to this file")
    p.add_argument("--check", action="store_true", help="Validate before writing output")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    try:
        note      = load_json(args.input)
        html_text = render_note(note)
        if args.check:
            result = validate_note(note, html_text=html_text)
            if not result.ok:
                for e in result.errors:
                    print(f"ERROR: {e}", file=sys.stderr)
                return 1
            for w in result.warnings:
                print(f"WARNING: {w}", file=sys.stderr)
        if args.output:
            Path(args.output).write_text(html_text, encoding="utf-8")
        else:
            sys.stdout.write(html_text)
        return 0
    except (NoteError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
