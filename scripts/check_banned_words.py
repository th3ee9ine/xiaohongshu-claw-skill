#!/usr/bin/env python3
"""
CLI: check a note JSON (or raw text file) for banned words.

Usage:
    python3 scripts/check_banned_words.py note.json
    python3 scripts/check_banned_words.py note.json --format json
    python3 scripts/check_banned_words.py --text "全网第一，顶级品质！"
    python3 scripts/check_banned_words.py note.json --suggest
"""
from __future__ import annotations

import argparse, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from banned_words_lib import BannedWordsChecker
from note_lib import NoteError, load_json

SUGGESTIONS: dict[str, list[str]] = {
    # 极限词替换建议
    "最好":    ["非常好", "很好", "效果出色"],
    "最强":    ["超强", "很强", "实力强劲"],
    "最佳":    ["优选", "推荐", "效果很棒"],
    "第一":    ["领先", "优秀", "出色"],
    "顶级":    ["高端", "优质", "品质出色"],
    "极致":    ["出色", "精细", "用心"],
    "完美":    ["很好", "令人满意", "效果不错"],
    "唯一":    ["独特", "别具一格", "与众不同"],
    "独一无二":["独特", "别具特色"],
    "永久":    ["长期", "持久"],
    "100%":   ["高效", "显著效果"],
    "绝对":    ["非常", "很"],
    "万能":    ["多功能", "用途广泛"],
    # 导流词替换建议
    "微信号":  ["（站内私信联系）"],
    "手机号":  ["（站内私信联系）"],
    "淘宝":    ["某宝", "购物平台"],
    "天猫":    ["某宝旗舰店"],
    "京东":    ["某东"],
    "抖音":    ["某短视频平台"],
    # 医疗词替换建议
    "治疗":    ["改善", "帮助缓解"],
    "治愈":    ["帮助改善", "有所改善"],
    "减肥":    ["管理体重", "健康生活"],
}


def format_text(result, note_or_text, fmt: str, suggest: bool) -> str:
    if fmt == "json":
        hits = [
            {
                "word": h.word, "severity": h.severity,
                "category": h.category_name, "context": h.context,
                "position": h.position,
                **({"suggestions": SUGGESTIONS[h.word]} if suggest and h.word in SUGGESTIONS else {}),
            }
            for h in result.hits
        ]
        return json.dumps(
            {"ok": result.ok, "error_count": len(result.errors),
             "warning_count": len(result.warnings), "hits": hits},
            ensure_ascii=False, indent=2,
        )

    lines = []
    if not result.hits:
        lines.append("✅ 未检测到违禁词，内容合规！")
        return "\n".join(lines)

    lines.append(f"📋 违禁词检测报告")
    lines.append(f"   ❌ 错误（必须修改）: {len(result.errors)} 个")
    lines.append(f"   ⚠️  警告（建议修改）: {len(result.warnings)} 个")
    lines.append("")

    current_cat = None
    for h in result.hits:
        if h.category_name != current_cat:
            current_cat = h.category_name
            lines.append(f"── {current_cat} ──")
        tag = "❌" if h.severity == "error" else "⚠️ "
        line = f"  {tag} 「{h.word}」  位置 {h.position}  → …{h.context}…"
        if suggest and h.word in SUGGESTIONS:
            alts = " / ".join(SUGGESTIONS[h.word])
            line += f"\n     💡 建议替换为：{alts}"
        lines.append(line)

    lines.append("")
    if result.errors:
        lines.append("⛔ 存在 ERROR 违禁词，发布前必须全部修改。")
    else:
        lines.append("⚠️  仅有 WARNING，可斟酌修改后发布。")
    return "\n".join(lines)


def parse_args():
    p = argparse.ArgumentParser(description="Check a XHS note JSON for banned words.")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("input",  nargs="?", help="Path to note JSON or plain text file")
    src.add_argument("--text", help="Scan a raw string directly")
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.add_argument("--suggest", action="store_true", help="Show replacement suggestions")
    p.add_argument("--db", help="Path to custom banned-words.json")
    return p.parse_args()


def main() -> int:
    args    = parse_args()
    checker = BannedWordsChecker(db_path=args.db) if args.db else BannedWordsChecker()

    try:
        if args.text:
            result = checker.check(args.text)
        else:
            path = Path(args.input)
            if path.suffix == ".json":
                note   = load_json(path)
                result = checker.check_note(note)
            else:
                raw    = path.read_text(encoding="utf-8")
                result = checker.check(raw)
    except (NoteError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(format_text(result, None, args.format, args.suggest))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
