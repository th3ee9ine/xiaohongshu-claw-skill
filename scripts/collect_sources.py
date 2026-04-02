#!/usr/bin/env python3
"""Collect local files, URLs, or raw text into a normalized source bundle for XHS notes."""
from __future__ import annotations

import argparse, json, re, sys
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

MISSING_SOURCE_MESSAGE = (
    "No data sources specified. 请先指定至少一个数据源。"
    "可用方式：提供 source-spec.json，或使用 --source-file / --source-url / --source-text / --stdin-text。"
)


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self._in_title = False
        self.chunks: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "title":
            self._in_title = True

    def handle_endtag(self, tag):
        if tag.lower() == "title":
            self._in_title = False

    def handle_data(self, data):
        text = " ".join(data.split())
        if not text:
            return
        if self._in_title and not self.title:
            self.title = text
        self.chunks.append(text)


def _parse_labeled(raw: str) -> tuple[str | None, str]:
    v = str(raw).strip()
    if "::" in v:
        label, payload = v.split("::", 1)
        label   = label.strip() or None
        payload = payload.strip()
        if not payload:
            raise ValueError("Source value cannot be empty after label:: prefix.")
        return label, payload
    return None, v


def _build_cli_sources(args: argparse.Namespace) -> list[dict]:
    sources: list[dict] = []
    for raw in args.source_file:
        label, path = _parse_labeled(raw)
        e = {"type": "file", "path": path}
        if label:
            e["label"] = label
        sources.append(e)
    for raw in args.source_url:
        label, url = _parse_labeled(raw)
        e = {"type": "url", "url": url}
        if label:
            e["label"] = label
        sources.append(e)
    for raw in args.source_text:
        label, text = _parse_labeled(raw)
        e = {"type": "text", "text": text}
        if label:
            e["label"] = label
            e["title"] = label
        sources.append(e)
    if args.stdin_text:
        text = sys.stdin.read().strip()
        if not text:
            raise ValueError("--stdin-text was set, but stdin is empty.")
        sources.append({"type": "text", "label": args.stdin_label or "stdin",
                        "title": args.stdin_label or "stdin", "text": text})
    return sources


def resolve_spec(args: argparse.Namespace) -> dict[str, Any]:
    spec = {}
    if args.spec:
        with Path(args.spec).open("r", encoding="utf-8") as fh:
            spec = json.load(fh)
    sources = list(spec.get("sources") or [])
    sources.extend(_build_cli_sources(args))
    if not sources:
        raise ValueError(MISSING_SOURCE_MESSAGE)
    spec["sources"] = sources
    return spec


def fetch_url(url: str, timeout: int, max_chars: int) -> dict:
    req  = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=timeout) as resp:
        ct   = resp.headers.get_content_type()
        body = resp.read().decode("utf-8", errors="ignore")
    if ct == "text/plain":
        text, title = " ".join(body.split()), ""
    else:
        parser = TextExtractor()
        parser.feed(re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", body))
        title = parser.title
        text  = " ".join(parser.chunks)
    return {"title": title, "content": text[:max_chars], "content_type": ct}


def read_file(path: str | Path, max_chars: int) -> dict:
    text = Path(path).read_text(encoding="utf-8")
    return {"title": Path(path).name, "content": text[:max_chars], "content_type": "text/plain"}


def collect(spec: dict, timeout: int, max_chars: int) -> dict:
    items = []
    for entry in spec.get("sources") or []:
        etype = entry.get("type")
        label = entry.get("label") or entry.get("title") or entry.get("path") or entry.get("url") or etype
        try:
            if etype == "file":
                payload = read_file(entry["path"], max_chars)
                payload.update({"type": "file", "label": label, "path": entry["path"]})
            elif etype == "text":
                text = str(entry.get("text") or "")
                payload = {"type": "text", "label": label, "title": entry.get("title") or label,
                           "content": text[:max_chars], "content_type": "text/plain"}
            elif etype == "url":
                payload = fetch_url(entry["url"], timeout, max_chars)
                payload.update({"type": "url", "label": label, "url": entry["url"]})
            else:
                payload = {"type": etype or "unknown", "label": label, "error": f"Unsupported type: {etype}"}
        except Exception as exc:
            payload = {"type": etype or "unknown", "label": label, "error": str(exc)}
        content = payload.get("content", "")
        payload["excerpt"] = content[:min(240, len(content))]
        payload["ok"] = "error" not in payload
        items.append(payload)
    ok = sum(1 for i in items if i.get("ok"))
    return {"generated_at": datetime.now(timezone.utc).isoformat(),
            "count": len(items), "ok_count": ok, "items": items}


def parse_args():
    p = argparse.ArgumentParser(description="Collect sources into a normalized bundle for XHS notes.")
    p.add_argument("spec", nargs="?")
    p.add_argument("--source-file",  action="append", default=[])
    p.add_argument("--source-url",   action="append", default=[])
    p.add_argument("--source-text",  action="append", default=[])
    p.add_argument("--stdin-text",   action="store_true")
    p.add_argument("--stdin-label")
    p.add_argument("-o", "--output")
    p.add_argument("--timeout",   type=int, default=15)
    p.add_argument("--max-chars", type=int, default=4000)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    try:
        payload = collect(resolve_spec(args), timeout=args.timeout, max_chars=args.max_chars)
        output  = json.dumps(payload, ensure_ascii=False, indent=2)
        if args.output:
            Path(args.output).write_text(output + "\n", encoding="utf-8")
        else:
            print(output)
        return 0 if payload["ok_count"] else 1
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
