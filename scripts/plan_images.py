#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from note_lib import NoteError, dump_json, ensure_meta_defaults, load_json, paragraphs


def _safe_fragment(value: str) -> str:
    cleaned = "".join(ch.lower() if ch.isascii() and ch.isalnum() else "-" for ch in value)
    return "-".join(p for p in cleaned.split("-") if p) or "image"


def _cover_prompt(note: dict, meta: dict) -> str:
    title    = meta.get("title") or "小红书封面"
    template = note.get("template") or ""
    location = meta.get("location") or ""
    loc_tag  = f" at {location}," if location else ""
    if template == "travel-diary":
        return (
            f"Bright travel photo{loc_tag} themed '{title}'. "
            "Warm golden hour light, scenic landmark, high-saturation, Instagram-worthy, 3:4 vertical."
        )
    if template == "food-explore":
        return (
            f"Appetizing food photography{loc_tag} themed '{title}'. "
            "Top-down flat lay, vibrant colors, bokeh background, food blog style, 3:4 vertical."
        )
    if template == "knowledge-share":
        return (
            f"Clean aesthetic knowledge-sharing cover themed '{title}'. "
            "Minimal desk setup, pastel tones, stationery, soft natural light, 3:4 vertical."
        )
    return (
        f"Lifestyle photo themed '{title}'{loc_tag}. "
        "Bright, warm tones, natural light, aesthetically pleasing, 3:4 vertical."
    )


def _body_prompt(note: dict, title: str, detail: str) -> str:
    template = note.get("template") or ""
    if template == "travel-diary":
        return f"Travel photography of {title}. {detail}. Natural light, vivid colors, travel vlog style, 4:3."
    if template == "food-explore":
        return f"Close-up food photo of {title}. {detail}. Warm bokeh, appetizing colors, food blog aesthetic, 4:3."
    return f"Lifestyle photo about {title}. {detail}. Clean, aesthetic, warm tones, 4:3."


def attach_missing_image_plans(
    note: dict[str, Any],
    *,
    output_dir: str | Path,
    max_images: int = 9,
) -> dict[str, Any]:
    meta     = ensure_meta_defaults(note)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    date_s   = str(meta.get("date_short", "")).replace(".", "-")

    cover = dict(note.get("cover") or {})
    if not cover.get("prompt"):
        cover["prompt"] = _cover_prompt(note, meta)
    if not cover.get("local_path"):
        cover["local_path"] = str(out_path / f"cover-{date_s}.png")
    note["cover"] = cover

    plans: list[dict] = [{"target": "cover", **cover}]
    planned = 0

    for idx, sec in enumerate(note.get("sections") or []):
        if planned >= max_images - 1:
            break
        if sec.get("type") not in {"detail", "image"}:
            continue
        if sec.get("type") == "image" and sec.get("url"):
            continue
        img = dict(sec.get("image") or {})
        if not img.get("prompt"):
            title  = str(sec.get("title") or sec.get("type") or "配图")
            detail = paragraphs(sec.get("body"))[0][:100] if paragraphs(sec.get("body")) else ""
            img["prompt"] = sec.get("image_prompt") or _body_prompt(note, title, detail)
        if not img.get("caption"):
            img["caption"] = str(sec.get("title") or "配图")
        if not img.get("local_path"):
            frag = _safe_fragment(img["caption"])[:24]
            img["local_path"] = str(out_path / f"img-{planned:02d}-{frag}.png")
        sec["image"] = img
        plans.append({"target": f"sections[{idx}]", **img})
        planned += 1

    note.setdefault("_plans", {})
    note["_plans"]["images"] = plans
    return note


def parse_args():
    p = argparse.ArgumentParser(description="Plan cover and body image prompts for a XHS note JSON.")
    p.add_argument("input")
    p.add_argument("-o", "--output",    help="Write image plan JSON to this file")
    p.add_argument("--write-note",      help="Write updated note JSON with planned images")
    p.add_argument("--inplace",         action="store_true")
    p.add_argument("--output-dir",      default="build/images")
    p.add_argument("--max-images",      type=int, default=9)
    return p.parse_args()


def main() -> int:
    args    = parse_args()
    note    = load_json(args.input)
    updated = attach_missing_image_plans(note, output_dir=args.output_dir, max_images=args.max_images)
    plans   = updated.get("_plans", {}).get("images", [])
    payload = {"images": plans}
    if args.output:
        dump_json(args.output, payload)
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    if args.inplace:
        dump_json(args.input, updated)
    elif args.write_note:
        dump_json(args.write_note, updated)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
