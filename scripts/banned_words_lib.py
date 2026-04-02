#!/usr/bin/env python3
"""
Banned-word detection engine for xiaohongshu-claw-skill.

Usage:
    from banned_words_lib import BannedWordsChecker
    checker = BannedWordsChecker()
    result  = checker.check("在这里极致体验，顶级品质，全网第一！")
    for hit in result.hits:
        print(hit)
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

REPO_ROOT       = Path(__file__).resolve().parent.parent
BANNED_WORDS_DB = REPO_ROOT / "references" / "banned-words.json"

Severity = Literal["error", "warning"]


@dataclass
class BannedHit:
    word:        str
    category_id: str
    category_name: str
    severity:    Severity
    context:     str        # surrounding text snippet
    position:    int        # char offset in full text

    def __str__(self) -> str:
        tag = "❌ ERROR" if self.severity == "error" else "⚠️  WARN"
        return f"{tag}  [{self.category_name}]  「{self.word}」→ …{self.context}…"


@dataclass
class BannedCheckResult:
    hits:     list[BannedHit]   = field(default_factory=list)
    errors:   list[BannedHit]   = field(default_factory=list)
    warnings: list[BannedHit]   = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def summary(self) -> str:
        if not self.hits:
            return "✅ 未检测到违禁词"
        lines = [f"共发现 {len(self.errors)} 个错误、{len(self.warnings)} 个警告："]
        for h in self.hits:
            lines.append(f"  {h}")
        return "\n".join(lines)


class BannedWordsChecker:
    """Load banned-words.json and scan arbitrary text."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        path = Path(db_path) if db_path else BANNED_WORDS_DB
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        self._categories: list[dict] = data.get("categories", [])
        # pre-build sorted word list per category (longest first for greedy match)
        self._compiled: list[tuple[dict, list[str]]] = [
            (cat, sorted(cat["words"], key=len, reverse=True))
            for cat in self._categories
        ]

    # ── public API ────────────────────────────────────────────────────────────

    def check(self, text: str, *, dedupe: bool = True) -> BannedCheckResult:
        """Scan `text` and return all banned-word hits."""
        result     = BannedCheckResult()
        seen: set  = set()

        for cat, words in self._compiled:
            sev = cat["severity"]
            for word in words:
                key = (cat["id"], word)
                if dedupe and key in seen:
                    continue
                for m in re.finditer(re.escape(word), text):
                    seen.add(key)
                    start   = max(0, m.start() - 10)
                    end     = min(len(text), m.end() + 10)
                    context = text[start:end].replace("\n", " ")
                    hit = BannedHit(
                        word          = word,
                        category_id   = cat["id"],
                        category_name = cat["name"],
                        severity      = sev,
                        context       = context,
                        position      = m.start(),
                    )
                    result.hits.append(hit)
                    if sev == "error":
                        result.errors.append(hit)
                    else:
                        result.warnings.append(hit)
                    break  # one hit per word per category in dedupe mode

        result.hits.sort(key=lambda h: h.position)
        result.errors.sort(key=lambda h: h.position)
        result.warnings.sort(key=lambda h: h.position)
        return result

    def check_note(self, note: dict) -> BannedCheckResult:
        """Extract all text fields from a note dict and scan them."""
        parts: list[str] = []
        meta = note.get("meta") or {}
        _collect_str(meta.get("title"), parts)
        _collect_str(meta.get("location"), parts)
        for tag in (meta.get("tags") or []):
            _collect_str(tag, parts)
        cover = note.get("cover") or {}
        _collect_str(cover.get("caption"), parts)
        for sec in (note.get("sections") or []):
            _collect_str(sec.get("title"), parts)
            body = sec.get("body")
            if isinstance(body, list):
                for item in body:
                    _collect_str(item, parts)
            else:
                _collect_str(body, parts)
            for key in ("pros", "cons"):
                for item in (sec.get(key) or []):
                    _collect_str(item, parts)
            for item in (sec.get("items") or []):
                _collect_str(item.get("label"), parts)
            _collect_str(sec.get("text"), parts)
        _collect_str(note.get("cta"), parts)
        full_text = "\n".join(parts)
        return self.check(full_text)

    def categories(self) -> list[dict]:
        return self._categories


def _collect_str(value, parts: list[str]) -> None:
    if value and isinstance(value, str):
        parts.append(value.strip())
