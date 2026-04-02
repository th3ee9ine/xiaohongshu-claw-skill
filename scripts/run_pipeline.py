#!/usr/bin/env python3
"""
XHS Note Full Pipeline
— 选题 → 写作 → 违禁词检测 → 标题优化 → 图片规划 → HTML 渲染 → 质量评分

Usage:
    python3 scripts/run_pipeline.py --topic "探店咖啡厅" --template food-explore
    python3 scripts/run_pipeline.py --topic "穿搭分享" --template outfit-inspo --style cute
    python3 scripts/run_pipeline.py --json existing_note.json --template travel-diary
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from note_lib          import load_json, validate_note, NoteError
from banned_words_lib  import BannedWordsChecker
from title_generator   import TitleGenerator
from image_prompt_generator import ImagePromptGenerator
from analytics         import analyse_file


TEMPLATES = [
    "food-explore", "travel-diary", "product-unbox", "lifestyle-review",
    "knowledge-share", "outfit-inspo", "minimalist-card", "study-log",
]

STYLE_TEMPLATE_MAP = {
    "casual":       "lifestyle-review",
    "professional": "knowledge-share",
    "cute":         "minimalist-card",
    "edgy":         "outfit-inspo",
}


def step(msg: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"\n[{ts}] {'─'*3} {msg}")


def run_pipeline(args) -> int:
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # ── Step 1: Load or generate note JSON ───────────────────────────────────
    step("Step 1 / 6 — 准备笔记 JSON")
    if args.json:
        note_path = Path(args.json)
        try:
            note = load_json(note_path)
            print(f"  ✅ 加载现有笔记: {note_path}")
        except NoteError as e:
            print(f"  ❌ 加载失败: {e}", file=sys.stderr)
            return 1
    else:
        # Use collect_sources to build a note skeleton
        note_path = output_dir / "note.json"
        print(f"  🔍 收集素材 (topic={args.topic})…")
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/collect_sources.py"),
             "--keyword", args.topic, "--output", str(note_path)],
            capture_output=True, text=True,
        )
        if result.returncode != 0 or not note_path.exists():
            # Fallback: create minimal skeleton
            note = _make_skeleton(args.topic, args.template or STYLE_TEMPLATE_MAP.get(args.style, "lifestyle-review"))
            note_path.write_text(json.dumps(note, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"  ⚠️  素材采集失败，使用骨架笔记")
        else:
            note = load_json(note_path)
            print(f"  ✅ 素材采集完成 → {note_path}")

    # ── Step 2: Title generation & suggestion ────────────────────────────────
    step("Step 2 / 6 — 标题优化")
    gen    = TitleGenerator()
    topic  = (note.get("meta") or {}).get("title") or args.topic or "笔记"
    titles = gen.generate(topic=topic, style=args.style, count=6)
    current_title = (note.get("meta") or {}).get("title", "")
    print(f"  当前标题: {current_title}")
    print("  候选标题:")
    for t in titles[:5]:
        print(f"    {t}")

    # ── Step 3: Banned word check ─────────────────────────────────────────────
    step("Step 3 / 6 — 违禁词检测")
    checker = BannedWordsChecker()
    banned  = checker.check_note(note)
    if not banned.hits:
        print("  ✅ 未检测到违禁词")
    else:
        for h in banned.errors:
            print(f"  ❌ [{h.category_name}] 「{h.word}」→ …{h.context}…")
        for h in banned.warnings:
            print(f"  ⚠️  [{h.category_name}] 「{h.word}」→ …{h.context}…")
        if banned.errors:
            print(f"\n  ⛔ 发现 {len(banned.errors)} 个 ERROR 违禁词！")
            if not args.force:
                print("  流水线已终止。修正后重新运行，或加 --force 跳过。")
                return 1

    # ── Step 4: Image prompt generation ─────────────────────────────────────
    step("Step 4 / 6 — 图片提示词规划")
    if not args.no_images:
        img_gen  = ImagePromptGenerator()
        service  = args.image_service or "generic"
        prompts  = img_gen.generate_for_note(note, service=service)
        img_plan = output_dir / "images-plan.json"
        img_plan.write_text(
            json.dumps([p.to_dict() for p in prompts], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"  ✅ 生成 {len(prompts)} 个图片提示词 → {img_plan}")
        for p in prompts[:3]:
            print(f"    [{p.purpose}] {p.positive[:60]}…")
    else:
        print("  ⏭️  跳过（--no-images）")

    # ── Step 5: HTML render ───────────────────────────────────────────────────
    step("Step 5 / 6 — HTML 渲染")
    template    = args.template or STYLE_TEMPLATE_MAP.get(args.style, "lifestyle-review")
    html_output = output_dir / "note.html"
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/render_note.py"),
         str(note_path), "--template", template, "--output", str(html_output)],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        print(f"  ✅ HTML 渲染完成 → {html_output}")
    else:
        print(f"  ⚠️  渲染警告: {result.stderr.strip()}")

    # ── Step 6: Quality analytics ────────────────────────────────────────────
    step("Step 6 / 6 — 质量评分")
    score = analyse_file(note_path)
    print(f"  综合评分: {score.overall}/100  风险: {score.risk_level}")
    if score.suggestions:
        print("  改进建议:")
        for s in score.suggestions:
            print(f"    • {s}")

    report = {
        "note_path":     str(note_path),
        "html_path":     str(html_output),
        "overall_score": score.overall,
        "risk_level":    score.risk_level,
        "banned_errors": score.banned_errors,
        "banned_warnings": score.banned_warnings,
        "suggestions":   score.suggestions,
        "title_candidates": [t.text for t in titles],
    }
    report_path = output_dir / "pipeline-report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n{'='*50}")
    print(f"  🎉 流水线完成！评分 {score.overall}/100")
    print(f"  📄 笔记:    {note_path}")
    print(f"  🌐 预览:    {html_output}")
    print(f"  📊 报告:    {report_path}")
    if not args.no_images:
        print(f"  🖼️  图片计划: {img_plan}")
    return 0 if not banned.errors else 1


def _make_skeleton(topic: str, template: str) -> dict:
    return {
        "meta": {
            "title": f"{topic}分享",
            "tags": [topic, "生活", "分享", "推荐", "种草"],
            "template": template,
        },
        "cover": {"caption": f"{topic}封面图"},
        "sections": [
            {"title": f"为什么推荐{topic}", "body": ["这里写正文内容……"]},
            {"title": "我的使用体验",        "body": ["详细描述……"]},
        ],
        "cta": "如果你也喜欢，记得收藏哦～",
    }


def parse_args():
    p = argparse.ArgumentParser(description="Run full XHS note pipeline.")
    src = p.add_mutually_exclusive_group()
    src.add_argument("--topic", help="笔记主题（新建笔记）")
    src.add_argument("--json",  help="已有笔记 JSON 文件路径")
    p.add_argument("--template", choices=TEMPLATES, help="HTML 模板")
    p.add_argument("--style",    choices=["casual","professional","cute","edgy"], default="casual")
    p.add_argument("--output",   default="./output", help="输出目录")
    p.add_argument("--no-images",     action="store_true")
    p.add_argument("--force",         action="store_true", help="忽略违禁词 ERROR 继续运行")
    p.add_argument("--strict",        action="store_true", help="WARNING 也终止流程")
    p.add_argument("--image-service", choices=["eachlabs","fal","openai","zhipu","generic"],
                   default="generic")
    return p.parse_args()


if __name__ == "__main__":
    raise SystemExit(run_pipeline(parse_args()))
