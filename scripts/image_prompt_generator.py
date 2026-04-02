#!/usr/bin/env python3
"""
XHS Image Prompt Generator
— 生成适配 eachlabs-image-generation / fal-text-to-image / zhipu-cogview-image 的提示词
— 参考 awesome-openclaw-skills: image-and-video-generation 类别最佳实践

Usage:
    from image_prompt_generator import ImagePromptGenerator
    gen = ImagePromptGenerator()
    prompts = gen.generate_for_note(note_dict)
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

Service = Literal["eachlabs", "fal", "openai", "zhipu", "generic"]

STYLE_PRESETS: dict[str, dict] = {
    "food": {
        "base": "food photography, warm lighting, bokeh background, appetizing, high resolution",
        "negative": "text, watermark, blurry, dark, unappealing",
        "ratio": "3:4",
        "model_hint": "Flux Dev / Imagen3",
    },
    "travel": {
        "base": "travel photography, golden hour lighting, vibrant colors, cinematic, 35mm film",
        "negative": "text, watermark, overexposed, tourist crowd",
        "ratio": "3:4",
        "model_hint": "Flux Pro / SDXL",
    },
    "product": {
        "base": "product photography, white studio background, soft shadow, commercial quality, 8K",
        "negative": "text, watermark, dirty background, reflections",
        "ratio": "1:1",
        "model_hint": "GPT-Image-1 / Flux",
    },
    "lifestyle": {
        "base": "lifestyle photography, natural light, moody, cozy atmosphere, aesthetic",
        "negative": "text, watermark, harsh flash, staged look",
        "ratio": "3:4",
        "model_hint": "Flux Dev / Imagen3",
    },
    "outfit": {
        "base": "fashion photography, full body shot, urban background, editorial style",
        "negative": "text, watermark, blurry face, bad anatomy",
        "ratio": "3:4",
        "model_hint": "Flux Dev / eachlabs-fashion-ai",
    },
    "knowledge": {
        "base": "flat design illustration, clean background, infographic style, pastel colors",
        "negative": "photo-realistic, busy background, dark",
        "ratio": "1:1",
        "model_hint": "DALL-E 3 / Imagen3",
    },
    "study": {
        "base": "desk setup, stationery, cozy study atmosphere, warm light, aesthetic",
        "negative": "text, watermark, messy, dark",
        "ratio": "1:1",
        "model_hint": "Flux Dev",
    },
}

COVER_OVERLAY_TIPS = """
小红书封面建议：
- 左上 / 左下角预留文字区（避免被遮挡）
- 避免纯白底（平台压缩后损失大）
- 人物照片：脸部居中，留 1/3 天空或环境
- 产品照：留白 > 20%，突出主体
"""


@dataclass
class ImagePrompt:
    purpose:    str   # cover / section_1 / section_2 ...
    positive:   str
    negative:   str
    ratio:      str   # "3:4" / "1:1" / "4:3"
    model_hint: str
    service_params: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "purpose":    self.purpose,
            "positive":   self.positive,
            "negative":   self.negative,
            "ratio":      self.ratio,
            "model_hint": self.model_hint,
            "service":    self.service_params,
        }

    def for_service(self, service: Service) -> dict:
        """Return API-ready params for specific service."""
        base = self.to_dict()
        if service == "eachlabs":
            return {"prompt": self.positive, "negative_prompt": self.negative,
                    "aspect_ratio": self.ratio, "model": self.model_hint.split("/")[0].strip()}
        if service == "fal":
            return {"prompt": self.positive, "negative_prompt": self.negative,
                    "image_size": _ratio_to_fal_size(self.ratio)}
        if service == "openai":
            return {"prompt": self.positive, "size": _ratio_to_openai_size(self.ratio),
                    "quality": "hd", "style": "natural"}
        if service == "zhipu":
            return {"prompt": f"{self.positive}，{self.negative} 风格，高清"}
        return base


def _ratio_to_fal_size(ratio: str) -> str:
    return {"3:4": "portrait_4_3", "1:1": "square", "4:3": "landscape_4_3"}.get(ratio, "square")

def _ratio_to_openai_size(ratio: str) -> str:
    return {"3:4": "1024x1792", "1:1": "1024x1024", "4:3": "1792x1024"}.get(ratio, "1024x1024")


class ImagePromptGenerator:

    def generate_for_note(
        self,
        note: dict,
        style_key: str | None = None,
        service: Service = "generic",
    ) -> list[ImagePrompt]:
        if style_key is None:
            template = (note.get("meta") or {}).get("template", "lifestyle")
            style_key = _guess_style(template)

        preset = STYLE_PRESETS.get(style_key, STYLE_PRESETS["lifestyle"])
        prompts: list[ImagePrompt] = []

        # ── Cover image ───────────────────────────────────────────────────────
        title   = (note.get("meta") or {}).get("title", "")
        subject = _extract_subject(note)
        cover_prompt = (
            f"{subject}, {preset['base']}, "
            "XiaoHongShu cover photo, text-free, square crop safe area"
        )
        prompts.append(ImagePrompt(
            purpose="cover", positive=cover_prompt,
            negative=preset["negative"], ratio="3:4",
            model_hint=preset["model_hint"],
        ))

        # ── Section images ────────────────────────────────────────────────────
        for i, sec in enumerate((note.get("sections") or [])[:4], start=1):
            sec_title = sec.get("title", f"节段{i}")
            sec_prompt = (
                f"{sec_title}, {subject}, {preset['base']}, "
                "clean composition, Instagram aesthetic"
            )
            prompts.append(ImagePrompt(
                purpose=f"section_{i}", positive=sec_prompt,
                negative=preset["negative"], ratio="1:1",
                model_hint=preset["model_hint"],
            ))

        if service != "generic":
            for p in prompts:
                p.service_params = p.for_service(service)

        return prompts

    def generate_cover_only(
        self,
        subject:   str,
        style_key: str = "lifestyle",
        service:   Service = "generic",
    ) -> ImagePrompt:
        preset = STYLE_PRESETS.get(style_key, STYLE_PRESETS["lifestyle"])
        p = ImagePrompt(
            purpose="cover",
            positive=f"{subject}, {preset['base']}, XiaoHongShu cover photo, text-free",
            negative=preset["negative"],
            ratio="3:4",
            model_hint=preset["model_hint"],
        )
        if service != "generic":
            p.service_params = p.for_service(service)
        return p

    def list_styles(self) -> list[str]:
        return list(STYLE_PRESETS.keys())


def _guess_style(template_name: str) -> str:
    mapping = {
        "food": "food", "travel": "travel", "product": "product",
        "lifestyle": "lifestyle", "outfit": "outfit", "knowledge": "knowledge",
        "study": "study",
    }
    for k, v in mapping.items():
        if k in template_name.lower():
            return v
    return "lifestyle"


def _extract_subject(note: dict) -> str:
    title = (note.get("meta") or {}).get("title", "")
    tags  = (note.get("meta") or {}).get("tags", [])
    if tags:
        return f"{title}, {tags[0]}"
    return title or "lifestyle scene"


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("note_json", help="Note JSON file")
    p.add_argument("--style",   default=None)
    p.add_argument("--service", choices=["eachlabs","fal","openai","zhipu","generic"], default="generic")
    p.add_argument("--format",  choices=["text","json"], default="text")
    args = p.parse_args()

    note = json.loads(Path(args.note_json).read_text("utf-8"))
    gen  = ImagePromptGenerator()
    prompts = gen.generate_for_note(note, style_key=args.style, service=args.service)

    if args.format == "json":
        print(json.dumps([pr.to_dict() for pr in prompts], ensure_ascii=False, indent=2))
    else:
        for pr in prompts:
            print(f"\n[{pr.purpose}] ratio={pr.ratio}  model={pr.model_hint}")
            print(f"  ✅ {pr.positive}")
            print(f"  ❌ {pr.negative}")
        print(COVER_OVERLAY_TIPS)
