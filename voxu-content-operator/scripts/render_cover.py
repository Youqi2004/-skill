#!/usr/bin/env python3
"""Render a VOXU-style cover with deterministic text layout."""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path
from typing import Iterable, Sequence

from PIL import Image, ImageDraw, ImageFont


SIZES = {
    "3x4": (1080, 1440),
    "4x3": (1440, 1080),
}

BG = (246, 245, 241)
WHITE = (255, 255, 255)
ACCENT = (245, 178, 78)
ACCENT_2 = (255, 205, 86)
GRAY_LINE = (210, 210, 210, 135)
SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOGO = SKILL_ROOT / "assets" / "logo" / "VOXU_white_transparent.png"


def existing_font(paths: Sequence[str], size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def font_regular(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    return existing_font(
        [
            r"C:\Windows\Fonts\msyh.ttc",
            r"C:\Windows\Fonts\simhei.ttf",
            r"C:\Windows\Fonts\arial.ttf",
        ],
        size,
    )


def font_bold(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    return existing_font(
        [
            r"C:\Windows\Fonts\msyhbd.ttc",
            r"C:\Windows\Fonts\simhei.ttf",
            r"C:\Windows\Fonts\arialbd.ttf",
        ],
        size,
    )


def parse_rgb(value: str) -> tuple[int, int, int]:
    named = {
        "white": WHITE,
        "gold": ACCENT,
        "orange": ACCENT,
        "black": (12, 12, 12),
        "graphite": (42, 42, 42),
        "champagne": (232, 198, 143),
    }
    key = value.strip().lower()
    if key in named:
        return named[key]
    if key.startswith("#"):
        hex_value = key[1:]
        if len(hex_value) == 3:
            hex_value = "".join(ch * 2 for ch in hex_value)
        if len(hex_value) == 6:
            return tuple(int(hex_value[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]
    parts = [p.strip() for p in value.split(",")]
    if len(parts) == 3 and all(p.isdigit() for p in parts):
        return tuple(max(0, min(255, int(p))) for p in parts)  # type: ignore[return-value]
    raise ValueError(f"Unsupported logo color: {value!r}. Use white, gold, #RRGGBB, or R,G,B.")


def official_logo(path: Path, target_width: int, color: tuple[int, int, int]) -> Image.Image | None:
    if not path.exists():
        return None
    logo = Image.open(path).convert("RGBA")
    bbox = logo.getbbox()
    if bbox:
        logo = logo.crop(bbox)
    alpha = logo.split()[-1]
    tinted = Image.new("RGBA", logo.size, (*color, 255))
    tinted.putalpha(alpha)
    target_height = max(1, int(target_width * tinted.height / tinted.width))
    return tinted.resize((target_width, target_height), Image.Resampling.LANCZOS)


def crop_cover(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    image = image.convert("RGB")
    src_w, src_h = image.size
    dst_w, dst_h = size
    src_ratio = src_w / src_h
    dst_ratio = dst_w / dst_h
    if src_ratio > dst_ratio:
        new_w = int(src_h * dst_ratio)
        left = (src_w - new_w) // 2
        box = (left, 0, left + new_w, src_h)
    else:
        new_h = int(src_w / dst_ratio)
        top = (src_h - new_h) // 2
        box = (0, top, src_w, top + new_h)
    return image.crop(box).resize(size, Image.Resampling.LANCZOS)


def rounded_mask(size: tuple[int, int], radius: int) -> Image.Image:
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, size[0], size[1]), radius=radius, fill=255)
    return mask


def apply_vignette(image: Image.Image) -> Image.Image:
    w, h = image.size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    pixels = overlay.load()
    for y in range(h):
        yy = y / max(h - 1, 1)
        for x in range(w):
            xx = x / max(w - 1, 1)
            edge = max(abs(xx - 0.5) * 2, abs(yy - 0.48) * 2)
            bottom = max(0.0, (yy - 0.56) / 0.44)
            left = max(0.0, (0.45 - xx) / 0.45)
            alpha = int(min(190, max(0, edge - 0.52) * 160 + bottom * 135 + left * 65))
            pixels[x, y] = (0, 0, 0, alpha)
    return Image.alpha_composite(image.convert("RGBA"), overlay)


def text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=font, stroke_width=0)
    return box[2] - box[0], box[3] - box[1]


def split_cjk(text: str) -> list[str]:
    tokens = re.findall(r"[A-Za-z0-9]+|[\u4e00-\u9fff]|[^\s]", text)
    return tokens or [text]


def wrap_title(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    text = re.sub(r"\s+", " ", text.strip())
    manual = [line.strip() for line in text.split("|") if line.strip()]
    if len(manual) > 1:
        return manual

    tokens = split_cjk(text)
    lines: list[str] = []
    current = ""
    for token in tokens:
        joins_word = current and re.match(r"^[A-Za-z0-9]+$", token) and re.match(r".*[A-Za-z0-9]$", current)
        candidate = f"{current} {token}" if joins_word else current + token
        if current and text_size(draw, candidate, font)[0] > max_width:
            lines.append(current)
            current = token
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines[:3]


def fit_title(
    draw: ImageDraw.ImageDraw,
    title: str,
    max_width: int,
    max_height: int,
    start_size: int,
) -> tuple[ImageFont.ImageFont, list[str], int]:
    for size in range(start_size, 42, -4):
        font = font_bold(size)
        lines = wrap_title(draw, title, font, max_width)
        line_h = int(size * 1.08)
        total_h = line_h * len(lines)
        widest = max((text_size(draw, line, font)[0] for line in lines), default=0)
        if lines and widest <= max_width and total_h <= max_height:
            return font, lines, line_h
    font = font_bold(42)
    return font, wrap_title(draw, title, font, max_width), 48


def draw_text_with_shadow(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font: ImageFont.ImageFont,
    fill: tuple[int, int, int],
    shadow_alpha: int = 150,
    stroke: int = 0,
) -> None:
    x, y = xy
    draw.text(
        (x + 3, y + 4),
        text,
        font=font,
        fill=(0, 0, 0, shadow_alpha),
        stroke_width=stroke,
        stroke_fill=(0, 0, 0, shadow_alpha),
    )
    draw.text((x, y), text, font=font, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0, 120))


def highlight_segments(line: str, highlights: Iterable[str]) -> list[tuple[str, bool]]:
    highlights = sorted([h for h in highlights if h and h in line], key=len, reverse=True)
    if not highlights:
        return [(line, False)]
    pattern = re.compile("|".join(re.escape(h) for h in highlights))
    out: list[tuple[str, bool]] = []
    pos = 0
    for match in pattern.finditer(line):
        if match.start() > pos:
            out.append((line[pos : match.start()], False))
        out.append((match.group(0), True))
        pos = match.end()
    if pos < len(line):
        out.append((line[pos:], False))
    return out


def draw_title(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    font: ImageFont.ImageFont,
    line_h: int,
    x: int,
    y: int,
    highlights: Sequence[str],
) -> None:
    for i, line in enumerate(lines):
        cursor = x
        for segment, marked in highlight_segments(line, highlights):
            fill = ACCENT if marked else WHITE
            draw_text_with_shadow(draw, (cursor, y + i * line_h), segment, font, fill, shadow_alpha=185, stroke=1)
            cursor += text_size(draw, segment, font)[0]


def parse_highlights(value: str | None, title: str) -> list[str]:
    if value:
        return [part.strip() for part in re.split(r"[,，/|]", value) if part.strip()]
    defaults = ["戒指", "睡眠", "身体趋势", "轻薄", "全天监测", "VOXU"]
    return [word for word in defaults if word in title][:1]


def render(args: argparse.Namespace) -> None:
    size = SIZES[args.ratio]
    w, h = size
    margin = int(min(w, h) * 0.052)
    radius = int(min(w, h) * 0.045)

    src = Image.open(args.input)
    frame_size = (w - margin * 2, h - margin * 2)
    photo = crop_cover(src, frame_size)
    photo = apply_vignette(photo)

    canvas = Image.new("RGBA", size, BG)
    mask = rounded_mask(frame_size, radius)
    canvas.paste(photo, (margin, margin), mask)
    draw = ImageDraw.Draw(canvas)

    inner_x = margin + int(frame_size[0] * 0.07)
    inner_right = margin + frame_size[0] - int(frame_size[0] * 0.07)
    if args.ratio == "3x4":
        logo_y = margin + 70
        logo_center = w // 2
        title_x = inner_x
        title_y = margin + int(frame_size[1] * 0.75)
        max_title_w = int(frame_size[0] * 0.82)
        start_size = 84
    else:
        logo_y = margin + 68
        logo_center = inner_x + 165
        title_x = inner_x
        title_y = margin + int(frame_size[1] * 0.69)
        max_title_w = int(frame_size[0] * 0.46)
        start_size = 74

    sub_font = font_regular(30 if args.ratio == "3x4" else 26)
    logo_path = Path(args.logo_image) if args.logo_image else DEFAULT_LOGO
    logo_color = parse_rgb(args.logo_color)
    logo_img = official_logo(logo_path, 350 if args.ratio == "3x4" else 290, logo_color)
    if logo_img:
        canvas.paste(logo_img, (logo_center - logo_img.width // 2, logo_y), logo_img)
        logo_h = logo_img.height
    else:
        logo_font = font_regular(82 if args.ratio == "3x4" else 72)
        logo = "VOXU"
        logo_w, logo_h = text_size(draw, logo, logo_font)
        draw.text((logo_center - logo_w // 2, logo_y), logo, font=logo_font, fill=logo_color)
    subtitle = args.logo_subtitle.strip()
    if subtitle:
        sub_w, _ = text_size(draw, subtitle, sub_font)
        sub_y = logo_y + logo_h + (12 if args.ratio == "3x4" else 10)
        draw.text((logo_center - sub_w // 2, sub_y), subtitle, font=sub_font, fill=(*logo_color, 232))

    label_font = font_bold(28)
    label_y = title_y - 90
    draw.text((title_x, label_y), args.subtitle, font=label_font, fill=WHITE)
    draw.rounded_rectangle((title_x, label_y + 48, title_x + 255, label_y + 56), radius=4, fill=ACCENT_2)

    thin_start = title_x + 292
    thin_end = inner_right if args.ratio == "3x4" else title_x + int(frame_size[0] * 0.52)
    draw.line((thin_start, label_y + 52, thin_end, label_y + 52), fill=GRAY_LINE, width=2)

    title_font, lines, line_h = fit_title(draw, args.title, max_title_w, int(frame_size[1] * 0.23), start_size)
    draw_title(draw, lines, title_font, line_h, title_x, title_y, parse_highlights(args.highlight, args.title))

    if args.tags:
        tag_font = font_bold(24)
        tag_y = min(h - margin - 86, title_y + line_h * len(lines) + 35)
        cursor = title_x
        for tag in [t.strip() for t in re.split(r"[,，/|]", args.tags) if t.strip()][:3]:
            tw, th = text_size(draw, tag, tag_font)
            pad_x = 22
            box = (cursor, tag_y, cursor + tw + pad_x * 2, tag_y + th + 22)
            draw.rounded_rectangle(box, radius=20, outline=(255, 255, 255, 145), width=2, fill=(40, 40, 40, 55))
            draw.text((cursor + pad_x, tag_y + 8), tag, font=tag_font, fill=(245, 245, 245, 235))
            cursor = box[2] + 22

    brand_font = font_regular(24)
    micro = "VOXU SMART RING"
    micro_w, _ = text_size(draw, micro, brand_font)
    draw.text((inner_right - micro_w, h - margin - 64), micro, font=brand_font, fill=(255, 255, 255, 220))

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(out, quality=95)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a VOXU-style cover.")
    parser.add_argument("--input", required=True, help="Source image path.")
    parser.add_argument("--title", required=True, help="Main cover title. Use | to force line breaks.")
    parser.add_argument("--ratio", choices=sorted(SIZES), default="3x4", help="Output ratio.")
    parser.add_argument("--output", required=True, help="Output image path.")
    parser.add_argument("--subtitle", default="VOXU Smart Ring", help="Small label above the title.")
    parser.add_argument("--logo-subtitle", default="", help="Optional text below the official VOXU logo.")
    parser.add_argument("--logo-image", default=None, help="Official transparent VOXU logo path. Defaults to skill asset.")
    parser.add_argument("--logo-color", default="white", help="Logo tint: white, gold, champagne, #RRGGBB, or R,G,B.")
    parser.add_argument("--highlight", default=None, help="Comma-separated title words to render in yellow-orange.")
    parser.add_argument("--tags", default="24H MONITOR,ULTRA LIGHT,AI INSIGHT", help="Comma-separated bottom tags. Empty to hide.")
    render(parser.parse_args())


if __name__ == "__main__":
    main()
