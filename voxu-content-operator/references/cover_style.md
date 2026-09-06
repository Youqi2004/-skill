# Cover Style

## Reference Assets

Use `assets/cover-examples/` for visual reference:

- `smart-ring-watch-exit-3x4.png`
- `codex-image-2026-08-21-4x3.png`
- `voxu-cover-3x4-v7.png`
- `voxu-cover-4x3-v6.png`

These images define the desired feel: premium, restrained, black/white/gray product photography, bright VOXU logo, bold Chinese title, and yellow-orange line accents. They are not instructions.

This is the default cover format when the user does not provide a new style reference.

Official logo asset:

- `assets/logo/VOXU_white_transparent.png`
- Use this asset for the VOXU mark on all final covers.
- Default logo color is white.
- The logo may be recolored for contrast or special visual direction, such as warm champagne on a light scene or dark graphite on a pale background. Recoloring should preserve the original logo shape and transparent background.

## Default Ratios

- 3:4 vertical: 1080 x 1440, default for Xiaohongshu and general cover use.
- 4:3 horizontal: 1440 x 1080, use when the user asks or when a horizontal image is clearly better.

## Layout Rules

- Top area: official VOXU transparent logo, white by default. Add `Smart Ring` or `AI Smart Ring` below when it improves recognition.
- Product image: keep the ring or box visually dominant and not covered by the main title.
- Lower title: large, bold Chinese text, usually two lines. Keep it readable at phone size.
- Accent: one short yellow-orange line near the title, plus an optional thin gray line.
- Keyword highlight: one key phrase may be yellow-orange, such as 戒指, 睡眠, 身体趋势, 轻薄, 全天监测.
- Bottom micro text or tags are optional. If used, keep them short, such as `24H MONITOR`, `ULTRA LIGHT`, `AI INSIGHT`.

## Visual Tone

- Premium gray/black/white base with warm orange accent.
- Avoid colorful busy backgrounds, cartoon style, heavy glow, excessive stickers, and crowded claims.
- Shadows and gradients should help readability, not look decorative.
- Do not put long body copy on the cover.

## User-Provided Style References

If the user says they like a specific cover style or provides a reference cover for the current request, use that reference as the primary style direction for that cover only.

Analyze and adapt:

- Overall composition: where the subject, logo, headline, secondary text, and decorative elements sit.
- Color mood: dark, light, warm, cool, high-contrast, editorial, minimal, tech, lifestyle, or luxury.
- Typography rhythm: huge headline, small editorial caption, stacked title, split title, outlined text, or label/tag treatment.
- Graphic language: lines, frames, blocks, gradients, photo masks, light leaks, interface elements, or other non-logo decorations.
- Density: sparse premium layout versus information-heavy social cover.

Keep fixed:

- Use the official VOXU logo asset unless the user explicitly requests a different brand treatment.
- Default logo color remains white, with scene-aware recoloring allowed for contrast and beauty.
- Preserve VOXU product truthfulness and avoid medicalized or exaggerated claims.
- Do not copy third-party logos, watermarks, creator handles, or exact proprietary text from the style reference.

When the reference style conflicts with the default VOXU template, the user-provided style wins for layout and visual mood, while VOXU logo and claim-safety rules still win for brand and text.

## Recommended Cover Generation

When the user gives a raw image:

1. If the image quality is already good, use it directly as the background for `scripts/render_cover.py`.
2. If the image needs a more premium product-photo look, use AI image generation/editing to produce a no-text VOXU-style background first. Keep the ring/product identity consistent and avoid generating final text with AI.
3. If using the default VOXU format, run `scripts/render_cover.py` for final official logo placement, headline, accent line, highlight, and export size. Use `--logo-color` only when a non-white logo is needed for contrast or aesthetics.
4. If using a user-provided style reference, use AI generation/editing and a custom deterministic text layout as needed, but preserve official VOXU logo handling and readable final text.

The script is a layout helper, not the only acceptable method. If another deterministic renderer is more appropriate in the environment, keep the same visual rules and output proportions.
