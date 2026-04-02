#!/usr/bin/env python3
from __future__ import annotations
import argparse, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from note_lib import NoteError, load_json, validate_note
from banned_words_lib import BannedWordsChecker


def parse_args():
    p = argparse.ArgumentParser(description="Validate a XHS note JSON (structure + banned words).")
    p.add_argument("input", help="Path to note JSON")
    p.add_argument("--html",         help="Path to rendered HTML to validate alongside JSON")
    p.add_argument("--banned-only",  action="store_true", help="Only run banned-word check")
    p.add_argument("--no-banned",    action="store_true", help="Skip banned-word check")
    p.add_argument("--suggest",      action="store_true", help="Show replacement suggestions for banned words")
    p.add_argument("--format",       choices=["text", "json"], default="text")
    return p.parse_args()


SUGGESTIONS: dict[str, list[str]] = {
    "最好": ["非常好", "效果出色"], "最强": ["超强", "实力强劲"],
    "最佳": ["优选", "推荐"], "第一": ["领先", "优秀"],
    "顶级": ["高端", "优质"], "极致": ["出色", "精细"],
    "完美": ["很好", "令人满意"], "唯一": ["独特", "与众不同"],
    "永久": ["长期", "持久"], "100%": ["高效", "显著效果"],
    "绝对": ["非常", "很"], "万能": ["多功能", "用途广泛"],
    "微信号": ["（站内私信联系）"], "手机号": ["（站内私信联系）"],
    "淘宝": ["某宝"], "天猫": ["某宝旗舰店"], "京东": ["某东"],
    "抖音": ["某短视频平台"], "治疗": ["改善", "帮助缓解"],
    "减肥": ["管理体重", "健康生活"],
}


def main() -> int:
    args = parse_args()
    exit_code = 0

    try:
        note      = load_json(args.input)
        html_text = Path(args.html).read_text(encoding="utf-8") if args.html else None

        # ── Structure validation ──────────────────────────────────────────────
        if not args.banned_only:
            result = validate_note(note, html_text=html_text)
            struct_errors   = [e for e in result.errors   if "违禁词" not in e]
            struct_warnings = [w for w in result.warnings if "违禁词" not in w]
            banned_errors   = [e for e in result.errors   if "违禁词" in e]
            banned_warnings = [w for w in result.warnings if "违禁词" in w]

            if struct_errors or struct_warnings:
                print("── 结构校验 ──")
                for e in struct_errors:
                    print(f"ERROR: {e}", file=sys.stderr)
                    exit_code = 1
                for w in struct_warnings:
                    print(f"WARNING: {w}", file=sys.stderr)

            if not args.no_banned and (banned_errors or banned_warnings):
                print("\n── 违禁词检测 ──")
                for e in banned_errors:
                    print(f"ERROR: {e}", file=sys.stderr)
                    exit_code = 1
                for w in banned_warnings:
                    print(f"WARNING: {w}", file=sys.stderr)

        # ── Standalone banned-word check ──────────────────────────────────────
        if args.banned_only and not args.no_banned:
            checker = BannedWordsChecker()
            banned  = checker.check_note(note)
            print("── 违禁词检测 ──")
            if not banned.hits:
                print("✅ 未检测到违禁词")
            for h in banned.hits:
                tag = "ERROR" if h.severity == "error" else "WARNING"
                line = f"{tag}: [{h.category_name}] 「{h.word}」→ …{h.context}…"
                if args.suggest and h.word in SUGGESTIONS:
                    alts = " / ".join(SUGGESTIONS[h.word])
                    line += f"  💡 建议替换：{alts}"
                print(line, file=sys.stderr if h.severity == "error" else sys.stdout)
            if banned.errors:
                exit_code = 1

        if exit_code == 0:
            print("✅ OK — 结构和违禁词全部通过")
        return exit_code

    except (NoteError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
