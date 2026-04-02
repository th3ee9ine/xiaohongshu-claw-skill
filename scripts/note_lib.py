#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

REPO_ROOT     = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = REPO_ROOT / "templates"
XHS_IMAGE_HOST_PATTERNS = (
    "sns-img-bd.xhscdn.com",
    "ci.xiaohongshu.com",
    "sns-img-hw.xhscdn.com",
)
XHS_RED     = "#fe2c55"
XHS_DARK    = "#1a1a1a"
XHS_GRAY    = "#666666"
XHS_BG      = "#ffffff"
XHS_CARD_BG = "#fff5f6"


class NoteError(RuntimeError):
    pass


@dataclass
class ValidationResult:
    errors: list[str]
    warnings: list[str]

    @property
    def ok(self) -> bool:
        return not self.errors


def available_templates() -> set[str]:
    return {p.stem for p in TEMPLATES_DIR.glob("*.html")}


def load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise NoteError("Note input must be a JSON object.")
    return data


def dump_json(path: str | Path, payload: Any) -> None:
    with Path(path).open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def esc(value: Any, *, raw: bool = False) -> str:
    text = "" if value is None else str(value).strip()
    return text if raw else html.escape(text)


def paragraphs(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        parts = [p.strip() for p in re.split(r"\n{2,}", value) if p.strip()]
        return parts or [value.strip()]
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    raise NoteError(f"Expected str or list, got {type(value)!r}")


def parse_iso_date(raw: str | None) -> date:
    if raw:
        return datetime.strptime(raw, "%Y-%m-%d").date()
    return date.today()


def ensure_meta_defaults(note: dict[str, Any]) -> dict[str, Any]:
    meta = note.get("meta") or {}
    if not isinstance(meta, dict):
        meta = {}
    note["meta"] = meta
    d = parse_iso_date(meta.get("date"))
    meta.setdefault("date", d.isoformat())
    meta.setdefault("date_short", d.strftime("%Y.%m.%d"))
    meta.setdefault("author", "39Claw")
    meta.setdefault("tags", [])
    meta.setdefault("location", "")
    return meta


def read_template(name: str) -> str:
    p = TEMPLATES_DIR / f"{name}.html"
    if not p.exists():
        raise NoteError(f"Template not found: {name}")
    return p.read_text(encoding="utf-8")


def strip_comments(t: str) -> str:
    return re.sub(r"<!--.*?-->", "", t, flags=re.S)


def _paras_html(value: Any, color: str = "#333", size: str = "15px") -> str:
    return "".join(
        f'<p style="font-size:{size};color:{color};line-height:1.88;margin:0 0 8px;">' +
        esc(p, raw=True) + "</p>"
        for p in paragraphs(value)
    )


def render_hook(sec: dict) -> str:
    return (
        f'<section style="background:{XHS_BG};padding:18px 18px 10px;">' +
        _paras_html(sec.get("body"), color=XHS_DARK, size="16px") +
        "</section>"
    )


def render_detail(sec: dict) -> str:
    title  = esc(sec.get("title") or "")
    t_html = (
        f'<p style="font-size:17px;font-weight:800;color:{XHS_RED};margin:0 0 10px;line-height:1.4;">' +
        title + "</p>"
    ) if title else ""
    img_html = _inline_img(sec.get("image") or {})
    return (
        f'<section style="background:{XHS_BG};padding:14px 18px 10px;">' +
        t_html + _paras_html(sec.get("body")) + img_html +
        "</section>"
    )


def render_pros_cons(sec: dict) -> str:
    pros = "".join(
        f'<p style="font-size:14px;color:#22a745;line-height:1.8;margin:0 0 5px;">✅ {esc(p)}</p>'
        for p in (sec.get("pros") or [])
    )
    cons = "".join(
        f'<p style="font-size:14px;color:#dc3545;line-height:1.8;margin:0 0 5px;">❌ {esc(c)}</p>'
        for c in (sec.get("cons") or [])
    )
    return (
        f'<section style="background:{XHS_CARD_BG};margin:10px 0;padding:16px 18px;' +
        f'border-radius:12px;border-left:4px solid {XHS_RED};">' +
        f'<p style="font-size:16px;font-weight:800;color:{XHS_RED};margin:0 0 10px;">🔍 优缺点一览</p>' +
        pros + cons + "</section>"
    )


def render_tips(sec: dict) -> str:
    return (
        '<section style="background:#fff9e6;margin:10px 0;padding:14px 18px;' +
        'border-radius:12px;border-left:4px solid #f5a623;">' +
        '<p style="font-size:15px;font-weight:800;color:#f5a623;margin:0 0 8px;">💡 Tips</p>' +
        _paras_html(sec.get("body"), color=XHS_DARK, size="14px") +
        "</section>"
    )


def render_rating(sec: dict) -> str:
    rows = "".join(
        f'<p style="font-size:14px;color:{XHS_DARK};line-height:1.8;margin:0 0 5px;">' +
        esc(str(item.get("label", ""))) +
        f' <strong style="color:{XHS_RED};">{esc(str(item.get("score", "")))}</strong></p>'
        for item in (sec.get("items") or [])
    )
    overall  = esc(str(sec.get("overall", "")))
    ov_html  = (
        f'<p style="font-size:18px;font-weight:900;color:{XHS_RED};margin:10px 0 0;">总评：{overall}</p>'
    ) if overall else ""
    return (
        f'<section style="background:{XHS_CARD_BG};margin:10px 0;padding:16px 18px;border-radius:12px;">' +
        f'<p style="font-size:16px;font-weight:800;color:{XHS_RED};margin:0 0 10px;">⭐ 综合评分</p>' +
        rows + ov_html + "</section>"
    )


def render_quote(sec: dict) -> str:
    text     = esc(sec.get("text") or "", raw=True)
    attr     = esc(sec.get("attribution") or "")
    attr_html = f'<p style="font-size:11px;color:{XHS_GRAY};margin:0;">{attr}</p>' if attr else ""
    return (
        f'<section style="background:{XHS_BG};padding:10px 18px 14px;">' +
        f'<section style="border-left:4px solid {XHS_RED};padding:6px 0 6px 14px;">' +
        f'<p style="font-size:15px;color:#3f3f3f;line-height:1.9;margin:0 0 8px;">{text}</p>' +
        attr_html + "</section></section>"
    )


def render_image_sec(sec: dict) -> str:
    url     = esc(sec.get("url") or "")
    caption = esc(sec.get("caption") or "配图")
    if not url:
        return ""
    return (
        f'<section style="background:{XHS_BG};padding:10px 18px;text-align:center;">' +
        f'<img src="{url}" style="width:100%;border-radius:8px;margin:0;" />' +
        f'<p style="font-size:11px;color:{XHS_GRAY};text-align:center;margin:5px 0 0;">{caption} | AI 生成</p>' +
        "</section>"
    )


def render_cta_block(sec: dict) -> str:
    body = esc(sec.get("body") or sec.get("text") or "", raw=True)
    return (
        f'<section style="background:{XHS_CARD_BG};margin:14px 0 0;padding:16px 18px;' +
        'border-radius:12px;text-align:center;">' +
        f'<p style="font-size:15px;color:{XHS_RED};font-weight:800;line-height:1.8;">{body}</p>' +
        "</section>"
    )


def _inline_img(img: dict) -> str:
    url     = esc(img.get("url") or "")
    caption = esc(img.get("caption") or "配图")
    if not url:
        return ""
    return (
        '<section style="margin:10px 0;text-align:center;">' +
        f'<img src="{url}" style="width:100%;border-radius:8px;" />' +
        f'<p style="font-size:11px;color:{XHS_GRAY};margin:4px 0 0;">{caption} | AI 生成</p>' +
        "</section>"
    )


def render_section(sec: dict) -> str:
    t = sec.get("type", "detail")
    if t == "hook":      return render_hook(sec)
    if t == "detail":    return render_detail(sec)
    if t == "pros-cons": return render_pros_cons(sec)
    if t == "tips":      return render_tips(sec)
    if t == "rating":    return render_rating(sec)
    if t == "quote":     return render_quote(sec)
    if t == "image":     return render_image_sec(sec)
    if t == "cta-block": return render_cta_block(sec)
    raise NoteError(f"Unsupported section type: {t}")


def render_sections(note: dict) -> str:
    return "".join(render_section(s) for s in (note.get("sections") or []))


def render_cover(note: dict) -> str:
    cover   = note.get("cover") or {}
    url     = esc(cover.get("url") or "")
    caption = esc(cover.get("caption") or "封面图")
    if not url:
        return ""
    return (
        f'<section style="background:{XHS_BG};padding:0 0 10px;text-align:center;">' +
        f'<img src="{url}" style="width:100%;border-radius:10px;" />' +
        f'<p style="font-size:11px;color:{XHS_GRAY};margin:5px 0 0;">{caption} | AI 生成</p>' +
        "</section>"
    )


def render_hook_from_meta(note: dict) -> str:
    for s in (note.get("sections") or []):
        if s.get("type") == "hook":
            return render_hook(s)
    return ""


def render_tags_line(meta: dict) -> str:
    tags = meta.get("tags") or []
    if not tags:
        return ""
    tag_html = " ".join(
        f'<span style="color:{XHS_RED};font-size:14px;margin-right:8px;">{esc(t)}</span>'
        for t in tags
    )
    return f'<section style="background:{XHS_BG};padding:14px 18px 10px;">{tag_html}</section>'


def apply_replacements(tmpl: str, reps: dict[str, str]) -> str:
    for k, v in reps.items():
        tmpl = tmpl.replace(f"{{{{{k}}}}}", v)
    return tmpl


def render_note(note: dict) -> str:
    meta  = ensure_meta_defaults(note)
    tname = str(note.get("template") or "").strip()
    tmpl  = strip_comments(read_template(tname))
    loc   = esc(meta.get("location") or "")
    loc_html = (
        f'<p style="font-size:12px;color:{XHS_GRAY};margin:0 0 6px;">📍 {loc}</p>'
    ) if loc else ""
    cta_raw = esc(note.get("cta") or "你怎么看？评论区聊聊🙌", raw=True)
    return apply_replacements(tmpl, {
        "TITLE":          esc(meta.get("title") or ""),
        "AUTHOR":         esc(meta.get("author") or ""),
        "DATE_SHORT":     esc(meta.get("date_short") or ""),
        "LOCATION":       loc_html,
        "COVER_IMAGE":    render_cover(note),
        "HOOK_SECTION":   render_hook_from_meta(note),
        "BODY_SECTIONS":  render_sections(note),
        "TAGS_LINE":      render_tags_line(meta),
        "CTA": f'<p style="font-size:15px;color:{XHS_RED};font-weight:800;line-height:1.8;">{cta_raw}</p>',
    })


def find_content_images(note: dict) -> list[dict]:
    imgs = []
    for sec in (note.get("sections") or []):
        if isinstance(sec.get("image"), dict):
            imgs.append(sec["image"])
        if sec.get("type") == "image":
            imgs.append(sec)
    return imgs


def validate_note(note: dict, *, html_text: str | None = None) -> ValidationResult:
    errors:   list[str] = []
    warnings: list[str] = []

    tname = str(note.get("template") or "").strip()
    if tname not in available_templates():
        errors.append(f"template must be one of: {', '.join(sorted(available_templates()))}")

    meta  = ensure_meta_defaults(note)
    title = str(meta.get("title") or "").strip()
    if not title:
        errors.append("meta.title is required")
    elif len(title) > 20:
        errors.append(f"meta.title must be <= 20 chars, got {len(title)}")

    tags = meta.get("tags") or []
    if not tags:
        warnings.append("meta.tags is empty; recommend 3-5 topic tags")
    elif len(tags) > 10:
        warnings.append(f"meta.tags has {len(tags)} items; recommend <= 5")

    secs = note.get("sections") or []
    if not secs:
        errors.append("sections must be a non-empty array")
    elif not any(s.get("type") == "hook" for s in secs):
        warnings.append("No hook section found; recommend adding a hook at the top")

    image_count = 1 if (note.get("cover") or {}).get("url") else 0
    for sec in secs:
        if sec.get("type") == "image" and sec.get("url"):
            image_count += 1
        if isinstance(sec.get("image"), dict) and sec["image"].get("url"):
            image_count += 1
    if image_count == 2:
        warnings.append("Image count is 2; XHS algorithm prefers 1 or 3-9 images")
    if image_count > 9:
        errors.append(f"Image count {image_count} exceeds XHS limit of 9")

    if html_text is not None:
        clean = strip_comments(html_text)
        if "{{" in clean or "}}" in clean:
            errors.append("rendered HTML still contains unresolved placeholders")
        wc = len(re.sub(r"<[^>]+>", "", html_text).strip())
        if wc < 100:
            warnings.append(f"Note body seems too short ({wc} chars); recommend 500-1000")
        elif wc > 2000:
            warnings.append(f"Note body is long ({wc} chars); recommend <= 1000")


    # ── Banned-word check ─────────────────────────────────────────────────────
    berrs, bwarns = _try_banned_check(note)
    errors.extend(berrs)
    warnings.extend(bwarns)

    return ValidationResult(errors=errors, warnings=warnings)

# ── Banned-word integration ───────────────────────────────────────────────────
def _try_banned_check(note: dict) -> tuple[list[str], list[str]]:
    """Import BannedWordsChecker lazily so note_lib has no hard dep."""
    try:
        import sys as _sys
        from pathlib import Path as _Path
        _sys.path.insert(0, str(_Path(__file__).resolve().parent))
        from banned_words_lib import BannedWordsChecker
        checker = BannedWordsChecker()
        result  = checker.check_note(note)
        berrs   = [f"违禁词[{h.category_name}] 「{h.word}」→ …{h.context}…" for h in result.errors]
        bwarns  = [f"违禁词[{h.category_name}] 「{h.word}」→ …{h.context}…" for h in result.warnings]
        return berrs, bwarns
    except Exception:
        return [], []
