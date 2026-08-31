#!/usr/bin/env python
# /// script
# requires-python = ">=3.11"
# dependencies = ["pymupdf", "anthropic", "pillow"]
# ///
"""
VLM-guided iterative PDF form filler for flat PDFs (no AcroForm fields).

Best used BY a vision-capable coding agent interactively (the agent renders
pages, looks at them, and adjusts), with this script as the deterministic
engine: VLM discovery -> placement -> VLM verification loop -> final write.

Usage:
    export ANTHROPIC_API_KEY=sk-...
    uv run fill_form.py input.pdf output.pdf --fields '{"Child's Name": "value", "Date": "2026-08-30"}'

Notes:
    - Placement contract enforced here: baseline 2.5pt above the field's
      underline, shrink-to-fit inside the blank, CJK font when needed.
    - The verification loop asks the VLM to check the RENDERED page, not the
      coordinates, because libraries disagree about coordinate conventions.
"""

import argparse
import base64
import io
import json
import os
import sys
from dataclasses import dataclass, field

import anthropic
import pymupdf as fitz
from PIL import Image

MAX_ITERATIONS = 5
BASELINE_OFFSET = 2.5  # baseline floats this many points ABOVE the underline
MIN_FONTSIZE = 7.0
MODEL = os.environ.get("FILL_FORM_MODEL", "claude-sonnet-4-6")
CJK_FONT = "china-s"  # PyMuPDF's built-in CJK-capable font


@dataclass
class FieldPlacement:
    label: str
    value: str
    page: int
    x: float
    y: float
    fontsize: float
    max_x: float = 0.0
    correct: bool = False


def has_cjk(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)


def text_width(text: str, fontsize: float) -> float:
    font = CJK_FONT if has_cjk(text) else "helv"
    return fitz.get_text_length(text, fontname=font, fontsize=fontsize)


def page_to_base64(doc, page_num, dpi=150):
    page = doc[page_num]
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat, annots=False)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return (base64.b64encode(buf.getvalue()).decode("utf-8"),
            pix.width, pix.height)


def call_vlm(client, system, prompt, image_b64):
    message = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=system,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image",
                 "source": {"type": "base64", "media_type": "image/png",
                            "data": image_b64}},
                {"type": "text", "text": prompt},
            ],
        }],
    )
    return message.content[0].text


def parse_json_array(response):
    start = response.find("[")
    end = response.rfind("]") + 1
    if start == -1 or end == 0:
        raise ValueError(f"No JSON array in response: {response[:200]}")
    return json.loads(response[start:end])


def draw_placement(page, p: FieldPlacement, max_x: float = None):
    """Write one field's value honoring the placement contract.

    Contract: baseline ~2.5pt above where it should visually sit (the VLM's
    y_pixel is the visual location, the offset keeps the rule from striking
    through descenders); shrink-to-fit inside the blank; CJK font for CJK.
    """
    fontsize = p.fontsize
    if max_x:
        while (fontsize > MIN_FONTSIZE
               and p.x + text_width(p.value, fontsize) > max_x):
            fontsize -= 0.5
    font = CJK_FONT if has_cjk(p.value) else "helv"
    page.insert_text(fitz.Point(p.x, p.y + BASELINE_OFFSET), p.value,
                     fontname=font, fontsize=fontsize)


def discover_fields(client, doc, page_num, values):
    page = doc[page_num]
    pw, ph = page.rect.width, page.rect.height
    img_b64, iw, ih = page_to_base64(doc, page_num)

    system = ("You are a precise PDF form-filling assistant. "
              "Always return valid JSON and nothing else.")

    prompt = f"""Look at this flat PDF form page. I need to fill these fields:
{json.dumps(values, indent=2)}

The image is {iw}x{ih} pixels. Origin is TOP-LEFT of the image.

For each field that appears on THIS page, return the pixel coordinates where
the text VALUE should visually sit (roughly centered on the blank/underline),
and a right-edge limit so text stays inside the blank.

Return ONLY a JSON array:
[{{"label": "field name", "x_pixel": 100, "y_pixel": 200,
   "max_x_pixel": 300, "fontsize": 11}}]

Rules:
- y_pixel = where the BOTTOM of the value text should visually sit (just
  ABOVE any underline; never ON it).
- max_x_pixel = the right end of the blank/line the value must not cross.
- Skip signature lines, checkbox marks, and any field not on this page.
- Match fontsize to the form's printed text (usually 10-12)."""

    response = call_vlm(client, system, prompt, img_b64)
    data = parse_json_array(response)

    placements = []
    for item in data:
        if item["label"] not in values:
            continue
        placements.append(
            FieldPlacement(
                label=item["label"],
                value=values[item["label"]],
                page=page_num,
                x=(float(item["x_pixel"]) / iw) * pw,
                y=(float(item["y_pixel"]) / ih) * ph,
                fontsize=float(item.get("fontsize", 11)),
                max_x=(float(item.get("max_x_pixel", iw)) / iw) * pw,
            )
        )
    return placements


def verify_and_correct(client, placements, page_num, src_pdf):
    """Render page with pending fields, ask VLM to check placement."""
    doc = fitz.open(src_pdf)
    page = doc[page_num]
    pw, ph = page.rect.width, page.rect.height
    iw = ih = None

    pending = [p for p in placements if p.page == page_num and not p.correct]
    if not pending:
        doc.close()
        return placements

    for p in pending:
        draw_placement(page, p)

    img_b64, iw, ih = page_to_base64(doc, page_num)
    doc.close()

    current = [{
        "label": p.label,
        "x_pixel": int((p.x / pw) * iw),
        "y_pixel": int((p.y / ph) * ih),
        "max_x_pixel": int((p.max_x / pw) * iw),
        "value": p.value,
    } for p in pending]

    system = ("You verify text placement on rendered form pages. "
              "Be strict. Always return valid JSON.")

    prompt = f"""Check each text placement on this rendered form page.

Placement contract:
1. The value sits on ITS blank/underline (the one its label points to).
2. The baseline floats just ABOVE the line; the line must NOT strike
   through any glyph.
3. No overlap with printed labels, other text, table borders, or page edges.
4. The value starts inside the blank's left end and does not extend past
   max_x_pixel.

Placements to check:
{json.dumps(current, indent=2)}

Return ONLY a JSON array, one entry per placement:
[{{"label": "name", "correct": true, "x_pixel": same_or_fixed,
   "y_pixel": same_or_fixed, "max_x_pixel": same_or_fixed,
   "reason": "why"}}]

Set correct=false with corrected coordinates for any violation."""

    response = call_vlm(client, system, prompt, img_b64)
    for c in parse_json_array(response):
        for p in pending:
            if p.label != c["label"]:
                continue
            if c.get("correct"):
                p.correct = True
                print(f"    OK   '{p.label}'")
            else:
                old = (p.x, p.y)
                p.x = (float(c["x_pixel"]) / iw) * pw
                p.y = (float(c["y_pixel"]) / ih) * ph
                p.max_x = (float(c.get("max_x_pixel", p.max_x / pw * iw)) / iw) * pw
                print(f"    FIX  '{p.label}': ({old[0]:.0f},{old[1]:.0f}) -> "
                      f"({p.x:.0f},{p.y:.0f}) {c.get('reason', '')}")
    return placements


def ink_profile(path, page_num):
    """Cluster blue-ink rows (72dpi) for signature-position verification."""
    doc = fitz.open(path)
    pix = doc[page_num].get_pixmap(dpi=72, annots=False)
    data, s, n = pix.samples, pix.stride, pix.n
    rows = set()
    for y in range(pix.height):
        for x in range(0, pix.width, 2):
            off = y * s + x * n
            if data[off + 2] > 150 and data[off + 2] - data[off] > 60:
                rows.add(y)
                break
    if not rows:
        return []
    rows = sorted(rows)
    clusters, start, prev = [], rows[0], rows[0]
    for y in rows[1:]:
        if y - prev > 8:
            clusters.append((start, prev))
            start = y
        prev = y
    clusters.append((start, prev))
    return clusters


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_pdf")
    parser.add_argument("output_pdf")
    parser.add_argument("--fields", required=True,
                        help='JSON object: {"label": "value", ...}')
    parser.add_argument("--max-iter", type=int, default=5)
    parser.add_argument("--reference-pdf",
                        help="Optional prior filled PDF; when set, blue-ink "
                             "cluster profiles are compared against it per "
                             "page to catch misplaced signature replays.")
    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: Set ANTHROPIC_API_KEY")
        sys.exit(1)

    client = anthropic.Anthropic()
    values = json.loads(args.fields)
    unassigned = dict(values)

    doc = fitz.open(args.input_pdf)
    num_pages = len(doc)
    doc.close()

    all_placements = []
    for pn in range(num_pages):
        remaining = {k: v for k, v in unassigned.items()
                     if k not in {p.label for p in all_placements}}
        if not remaining:
            break
        print(f"--- Page {pn + 1}: discovering ---")
        doc = fitz.open(args.input_pdf)
        found = discover_fields(client, doc, pn, remaining)
        doc.close()
        for f in found:
            print(f"  '{f.label}' at ({f.x:.0f},{f.y:.0f})")
            unassigned.pop(f.label, None)
        all_placements.extend(found)

    if unassigned:
        print(f"\nWARNING: no location found on any page for: "
              f"{sorted(unassigned)}")

    for i in range(1, args.max_iter + 1):
        pending = [p for p in all_placements if not p.correct]
        if not pending:
            print(f"\nAll fields verified after {i - 1} correction round(s).")
            break
        print(f"\n=== Verify/correct round {i} ({len(pending)} pending) ===")
        for pn in sorted({p.page for p in pending}):
            print(f"  Page {pn + 1}:")
            all_placements = verify_and_correct(
                client, all_placements, pn, args.input_pdf)

    print("\nWriting final PDF...")
    final = fitz.open(args.input_pdf)
    for p in all_placements:
        draw_placement(final[p.page], p)
        print(f"  Page {p.page + 1}: '{p.label}' = '{p.value}'")
    final.save(args.output_pdf)
    final.close()
    print(f"\nSaved: {args.output_pdf}")

    if args.reference_pdf:
        print("\nInk-cluster comparison (signature placement sanity):")
        for pn in range(num_pages):
            a = ink_profile(args.reference_pdf, pn)
            b = ink_profile(args.output_pdf, pn)
            status = "MATCH" if a == b else "CHECK MANUALLY"
            print(f"  page {pn + 1}: ref={a} new={b} -> {status}")


if __name__ == "__main__":
    main()