#!/usr/bin/env python3
"""
XHS Title Generator — 基于 awesome-openclaw-skills 社区最佳实践
参考: xiaohongshu-title skill (gxkim) + b2c-marketing + content-creator

Usage:
    from title_generator import TitleGenerator
    gen = TitleGenerator()
    titles = gen.generate("探店咖啡", style="casual", count=10)
    for t in titles: print(t)

    # CLI
    python3 scripts/title_generator.py --topic "探店咖啡" --style casual --count 10
"""
from __future__ import annotations

import argparse
import random
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

sys.path.insert(0, str(Path(__file__).resolve().parent))

Style = Literal["casual", "professional", "cute", "edgy"]

# ── 公式库 ────────────────────────────────────────────────────────────────────
FORMULAS = [
    # 数字列表型
    {"id": "num_list",    "pattern": "{n}个{adj}{noun}，让你{benefit}",   "ctr": "high"},
    {"id": "num_tips",    "pattern": "一定要知道的{n}个{noun}技巧",        "ctr": "high"},
    {"id": "num_mistake", "pattern": "踩雷{n}次后，我发现{topic}的秘密",   "ctr": "high"},
    # 痛点/反转型
    {"id": "contrast",    "pattern": "你以为{wrong}，其实{right}",         "ctr": "high"},
    {"id": "hidden",      "pattern": "{city}藏着一家被低估的{noun}",        "ctr": "mid"},
    {"id": "regret",      "pattern": "早知道{topic}有这个，我就不会{mistake}", "ctr": "mid"},
    # 成就/分享型
    {"id": "achieve",     "pattern": "靠{method}，我{outcome}",            "ctr": "high"},
    {"id": "honest",      "pattern": "说实话，{topic}真的{verdict}",        "ctr": "mid"},
    # 疑问/钩子型
    {"id": "question",    "pattern": "为什么{topic}让人{reaction}？",       "ctr": "mid"},
    {"id": "secret",      "pattern": "{topic}背后没人告诉你的事",            "ctr": "high"},
    # 地域/场景型
    {"id": "location",    "pattern": "在{city}找到了心目中的{noun}",        "ctr": "mid"},
    {"id": "season",      "pattern": "{season}必去！{city}{noun}完整攻略",  "ctr": "mid"},
    # 对比/测评型
    {"id": "compare",     "pattern": "测评了{n}家{noun}，只有这家值得去",   "ctr": "high"},
    {"id": "price",       "pattern": "{price}的{topic}，意外地好用",        "ctr": "mid"},
    # Emoji 增强型（casual/cute）
    {"id": "emoji_hook",  "pattern": "✨{topic}真的绝了！{benefit}",        "ctr": "high", "styles": ["casual","cute"]},
    {"id": "emoji_list",  "pattern": "🔥{n}个{noun}推荐，{city}必打卡",    "ctr": "high", "styles": ["casual","cute"]},
]

FILLERS: dict[str, list[str]] = {
    "adj":     ["小众", "宝藏", "高质量", "高颜值", "性价比高", "隐藏", "冷门"],
    "benefit": ["生活品质提升", "省下很多时间", "少踩很多坑", "收获满满", "心情超好"],
    "wrong":   ["贵的就是好的", "网红一定好", "越复杂越有效", "跟风就对了"],
    "right":   ["性价比才是王道", "口碑才重要", "简单才是真理", "适合自己最重要"],
    "city":    ["上海", "北京", "成都", "广州", "杭州", "深圳", "武汉", "西安"],
    "season":  ["春日", "夏日", "秋日", "冬日", "节假日", "周末"],
    "price":   ["99元", "几十块", "不到百元", "人均50"],
    "verdict": ["值得", "超出预期", "不负众望", "有点惊喜", "良心推荐"],
    "reaction": ["上头", "念念不忘", "反复回购", "安利给朋友"],
    "method":  ["这个方法", "坚持打卡", "认真研究", "系统学习"],
    "mistake": ["浪费那么多钱", "走那么多弯路", "后悔那么久"],
    "outcome": ["省了好多钱", "效率提升了一倍", "坚持下来了", "交到了好朋友"],
}


@dataclass
class Title:
    text:    str
    formula: str
    ctr:     str     # high / mid / low

    def __str__(self) -> str:
        star = "⭐" if self.ctr == "high" else "·"
        return f"{star} [{self.formula}] {self.text}"


class TitleGenerator:
    def __init__(self, seed: int | None = None) -> None:
        self._rng = random.Random(seed)

    def generate(
        self,
        topic:  str,
        noun:   str | None = None,
        style:  Style = "casual",
        count:  int   = 10,
        city:   str | None = None,
        n_range: tuple[int, int] = (3, 8),
    ) -> list[Title]:
        noun  = noun  or topic
        city  = city  or self._rng.choice(FILLERS["city"])
        results: list[Title] = []

        formulas = [
            f for f in FORMULAS
            if "styles" not in f or style in f["styles"]
        ]
        self._rng.shuffle(formulas)

        for formula in formulas:
            if len(results) >= count:
                break
            try:
                text = formula["pattern"].format(
                    topic   = topic,
                    noun    = noun,
                    city    = city,
                    n       = self._rng.randint(*n_range),
                    adj     = self._rng.choice(FILLERS["adj"]),
                    benefit = self._rng.choice(FILLERS["benefit"]),
                    wrong   = self._rng.choice(FILLERS["wrong"]),
                    right   = self._rng.choice(FILLERS["right"]),
                    season  = self._rng.choice(FILLERS["season"]),
                    price   = self._rng.choice(FILLERS["price"]),
                    verdict = self._rng.choice(FILLERS["verdict"]),
                    reaction= self._rng.choice(FILLERS["reaction"]),
                    method  = self._rng.choice(FILLERS["method"]),
                    mistake = self._rng.choice(FILLERS["mistake"]),
                    outcome = self._rng.choice(FILLERS["outcome"]),
                )
                results.append(Title(text=text, formula=formula["id"], ctr=formula["ctr"]))
            except KeyError:
                continue

        # 截断超长标题（小红书建议 ≤ 20 字）
        trimmed = []
        for t in results:
            if len(t.text) > 24:
                t.text = t.text[:22] + "…"
            trimmed.append(t)

        return trimmed[:count]

    def score(self, title: str) -> dict:
        """简单评分：长度、数字、emoji、疑问词"""
        has_num     = bool(re.search(r"\d", title))
        has_emoji   = bool(re.search(r"[\U00010000-\U0010ffff✨🔥💥❗]", title))
        has_q       = "？" in title or "?" in title
        length_ok   = 10 <= len(title) <= 20
        score       = sum([has_num, has_emoji, has_q, length_ok]) * 25
        return {
            "title":      title,
            "score":      score,
            "has_number": has_num,
            "has_emoji":  has_emoji,
            "has_question": has_q,
            "length_ok":  length_ok,
            "length":     len(title),
        }


def parse_args():
    p = argparse.ArgumentParser(description="Generate XHS titles for a topic.")
    p.add_argument("--topic",  required=True, help="笔记主题，如「探店咖啡」")
    p.add_argument("--noun",   help="具体名词（默认同 topic）")
    p.add_argument("--style",  choices=["casual","professional","cute","edgy"], default="casual")
    p.add_argument("--count",  type=int, default=10)
    p.add_argument("--city",   help="城市（默认随机）")
    p.add_argument("--score",  action="store_true", help="附加评分")
    p.add_argument("--format", choices=["text","json"], default="text")
    return p.parse_args()


def main():
    args = parse_args()
    gen  = TitleGenerator()
    titles = gen.generate(
        topic=args.topic, noun=args.noun, style=args.style,
        count=args.count, city=args.city,
    )

    if args.format == "json":
        import json
        out = []
        for t in titles:
            row = {"title": t.text, "formula": t.formula, "ctr": t.ctr}
            if args.score:
                row["score"] = gen.score(t.text)
            out.append(row)
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        for t in titles:
            line = str(t)
            if args.score:
                s = gen.score(t.text)
                line += f"  (得分 {s['score']}/100)"
            print(line)


if __name__ == "__main__":
    main()
