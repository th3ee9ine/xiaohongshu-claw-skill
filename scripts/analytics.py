#!/usr/bin/env python3
"""
XHS Note Analytics — 笔记数据分析与评分
参考 awesome-openclaw-skills: data-and-analytics / performance-reporter 最佳实践

给定一批笔记 JSON 文件，输出：
- 标题质量评分
- 违禁词风险等级
- Tag 覆盖率
- 内容长度分析
- 综合发布建议

Usage:
    python3 scripts/analytics.py examples/  --format table
    python3 scripts/analytics.py note.json  --format json
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from banned_words_lib import BannedWordsChecker
from title_generator import TitleGenerator

_checker = BannedWordsChecker()
_titler  = TitleGenerator()


@dataclass
class NoteScore:
    file:            str
    title:           str
    title_score:     int    # 0-100
    banned_errors:   int
    banned_warnings: int
    tag_count:       int
    section_count:   int
    total_chars:     int
    has_cta:         bool
    has_cover:       bool
    risk_level:      Literal["safe","caution","danger"]
    suggestions:     list[str] = field(default_factory=list)

    @property
    def overall(self) -> int:
        score = self.title_score
        score -= self.banned_errors   * 20
        score -= self.banned_warnings * 5
        score += min(self.tag_count, 5) * 3
        score += min(self.section_count, 4) * 5
        score += (10 if self.has_cta else 0)
        score += (5  if self.has_cover else 0)
        return max(0, min(100, score))


def analyse_file(path: Path) -> NoteScore:
    try:
        note = json.loads(path.read_text("utf-8"))
    except Exception as e:
        return NoteScore(
            file=path.name, title="[解析失败]", title_score=0,
            banned_errors=0, banned_warnings=0, tag_count=0,
            section_count=0, total_chars=0, has_cta=False, has_cover=False,
            risk_level="danger", suggestions=[f"JSON 解析失败: {e}"],
        )

    meta     = note.get("meta") or {}
    title    = meta.get("title", "")
    tags     = meta.get("tags") or []
    sections = note.get("sections") or []
    cta      = note.get("cta", "")
    cover    = note.get("cover") or {}

    # 标题评分
    ts = _titler.score(title)
    t_score = ts["score"]

    # 违禁词
    banned = _checker.check_note(note)

    # 字数
    texts = [title]
    for sec in sections:
        texts.append(sec.get("title",""))
        body = sec.get("body")
        if isinstance(body, list):
            texts += [b for b in body if isinstance(b, str)]
        elif isinstance(body, str):
            texts.append(body)
    total_chars = sum(len(t) for t in texts)

    # 风险等级
    if banned.errors:
        risk = "danger"
    elif banned.warnings:
        risk = "caution"
    else:
        risk = "safe"

    # 建议
    suggestions = []
    if not ts["has_number"]:
        suggestions.append("标题建议加入数字，提升 CTR")
    if len(title) < 10:
        suggestions.append("标题偏短（<10字），建议扩展")
    if len(title) > 20:
        suggestions.append("标题偏长（>20字），建议精简")
    if len(tags) < 3:
        suggestions.append(f"Tag 数量仅 {len(tags)} 个，建议增加到 5-10 个")
    if total_chars < 200:
        suggestions.append("正文字数偏少，建议 200 字以上增强权重")
    if not cta:
        suggestions.append("缺少 CTA（号召性用语），建议结尾引导互动")
    if not cover:
        suggestions.append("缺少封面图规划，建议添加 cover 字段")

    return NoteScore(
        file=path.name, title=title,
        title_score=t_score,
        banned_errors=len(banned.errors),
        banned_warnings=len(banned.warnings),
        tag_count=len(tags),
        section_count=len(sections),
        total_chars=total_chars,
        has_cta=bool(cta),
        has_cover=bool(cover),
        risk_level=risk,
        suggestions=suggestions,
    )


def print_table(scores: list[NoteScore]) -> None:
    sep  = "-" * 90
    hdr  = f"{'文件':<20} {'标题':<20} {'综合':<6} {'风险':<8} {'禁词E':<6} {'禁词W':<6} {'Tags':<5} {'字数':<6}"
    print(sep)
    print(hdr)
    print(sep)
    for s in scores:
        risk_tag = {"safe":"✅","caution":"⚠️ ","danger":"❌"}[s.risk_level]
        print(f"{s.file:<20} {s.title[:18]:<20} {s.overall:<6} {risk_tag:<8} {s.banned_errors:<6} {s.banned_warnings:<6} {s.tag_count:<5} {s.total_chars:<6}")
    print(sep)
    for s in scores:
        if s.suggestions:
            print(f"\n💡 [{s.file}] 改进建议：")
            for sug in s.suggestions:
                print(f"   • {sug}")


def main():
    import argparse
    p = argparse.ArgumentParser(description="Analyse XHS note JSON files.")
    p.add_argument("path",   help="JSON file or directory")
    p.add_argument("--format", choices=["table","json"], default="table")
    args = p.parse_args()

    target = Path(args.path)
    if target.is_dir():
        files = sorted(target.glob("*.json"))
    else:
        files = [target]

    if not files:
        print("No JSON files found.", file=sys.stderr)
        sys.exit(1)

    scores = [analyse_file(f) for f in files]

    if args.format == "json":
        out = []
        for s in scores:
            out.append({
                "file": s.file, "title": s.title, "overall": s.overall,
                "risk": s.risk_level, "banned_errors": s.banned_errors,
                "banned_warnings": s.banned_warnings, "tags": s.tag_count,
                "chars": s.total_chars, "suggestions": s.suggestions,
            })
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print_table(scores)


if __name__ == "__main__":
    main()
