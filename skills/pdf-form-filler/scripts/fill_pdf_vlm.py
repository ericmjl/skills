#!/usr/bin/env python
# /// script
# requires-python = ">=3.11"
# dependencies = ["pymupdf", "anthropic", "pillow"]
# ///
"""
VLM-guided iterative PDF form filler.
"""

import argparse
import base64
import io
import json
import os
import sys
from dataclasses import dataclass

import anthropic
import fitz
from PIL import Image

MAX_ITERATIONS = 5
MODEL = "claude-sonnet-4-6"


@dataclass
class FieldPlacement:
    label: str
    value: str
    page: int
    x: float
    y: float
    fontsize: float
    correct: bool = False


def page_to_base64(doc, page_num, dpi=150):
    page = doc[page_num]
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8"), pix.width, pix.height


def call_claude(client, system, prompt, image_b64):
    message = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=system,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": image_b64,
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            },
        ],
    )
    return message.content[0].text


def parse_json_array(response):
    start = response.find("[")
    end = response.rfind("]") + 1
    if start == -1 or end == 0:
        raise ValueError("No JSON array found")
    return json.loads(response[start:end])


def discover_fields(client, doc, page_num, values):
    page = doc[page_num]
    pw, ph = page.rect.width, page.rect.height
    img_b64, iw, ih = page_to_base64(doc, page_num)

    system = "You are a precise PDF form-filling assistant. Always return valid JSON and nothing else."

    prompt = f"""Look at this form. I need to fill these fields:
{json.dumps(values, indent=2)}

The image is {iw}x{ih} pixels. Origin is top-left.

For each field that appears on THIS page, return pixel coordinates (x_pixel, y_pixel) for where the text BASELINE should go.

Return ONLY a JSON array:
[{{"label": "field name", "value": "the value", "x_pixel": 100, "y_pixel": 200, "fontsize": 11}}]

Important: y_pixel is where the BOTTOM of the text sits. Only include fields visible on this page."""

    response = call_claude(client, system, prompt, img_b64)
    data = parse_json_array(response)

    placements = []
    for item in data:
        x_pix = float(item["x_pixel"])
        y_pix = float(item["y_pixel"])
        x_pdf = (x_pix / iw) * pw
        y_pdf = (y_pix / ih) * ph
        placements.append(
            FieldPlacement(
                label=item["label"],
                value=item["value"],
                page=page_num,
                x=x_pdf,
                y=y_pdf,
                fontsize=float(item.get("fontsize", 11)),
            )
        )
    return placements


def verify_and_correct(client, pdf_path, placements, page_num):
    doc = fitz.open(pdf_path)
    page = doc[page_num]
    pw, ph = page.rect.width, page.rect.height

    pending = [p for p in placements if p.page == page_num and not p.correct]
    if not pending:
        doc.close()
        return placements

    # Render ONLY pending fields for this page
    for p in pending:
        page.insert_text((p.x, p.y), p.value, fontsize=p.fontsize, fontname="helv")

    img_b64, iw, ih = page_to_base64(doc, page_num)
    doc.close()

    current = [
        {
            "label": p.label,
            "x_pixel": int((p.x / pw) * iw),
            "y_pixel": int((p.y / ph) * ih),
        }
        for p in pending
    ]

    system = (
        "You verify if text is correctly positioned on forms. Always return valid JSON."
    )

    prompt = f"""Check if these text placements are correct:
{json.dumps(current, indent=2)}

For each, return:
[{{"label": "name", "correct": true/false, "x_pixel": corrected_x_or_same, "y_pixel": corrected_y_or_same, "reason": "why"}}]

If correct, keep same coordinates. If wrong, provide corrected pixel coordinates."""

    response = call_claude(client, system, prompt, img_b64)
    corrections = parse_json_array(response)
    corr_map = {c["label"]: c for c in corrections}

    for p in placements:
        if p.page == page_num and not p.correct and p.label in corr_map:
            c = corr_map[p.label]
            if c.get("correct"):
                print(f"    OK '{p.label}'")
                p.correct = True
            else:
                old_x, old_y = p.x, p.y
                p.x = (float(c["x_pixel"]) / iw) * pw
                p.y = (float(c["y_pixel"]) / ih) * ph
                print(
                    f"    FIX '{p.label}': ({old_x:.0f},{old_y:.0f}) -> ({p.x:.0f},{p.y:.0f}) - {c.get('reason', '')}"
                )

    return placements


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_pdf")
    parser.add_argument("output_pdf")
    parser.add_argument("--fields", required=True)
    parser.add_argument("--max-iter", type=int, default=MAX_ITERATIONS)
    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: Set ANTHROPIC_API_KEY")
        sys.exit(1)

    client = anthropic.Anthropic()
    values = json.loads(args.fields)

    doc = fitz.open(args.input_pdf)
    num_pages = len(doc)
    doc.close()

    all_placements = []
    for pn in range(num_pages):
        print(f"--- Page {pn + 1}: Discovering ---")
        doc = fitz.open(args.input_pdf)
        fields = discover_fields(client, doc, pn, values)
        doc.close()
        for f in fields:
            print(f"  '{f.label}' at ({f.x:.0f}, {f.y:.0f})")
        all_placements.extend(fields)

    for i in range(1, args.max_iter + 1):
        pending = [p for p in all_placements if not p.correct]
        if not pending:
            print(f"\nAll verified after {i - 1} iterations!")
            break
        print(f"\n=== Iteration {i} ({len(pending)} pending) ===")
        for pn in sorted(set(p.page for p in pending)):
            print(f"  Page {pn + 1}:")
            all_placements = verify_and_correct(
                client, args.input_pdf, all_placements, pn
            )

    print("\nWriting final PDF...")
    final = fitz.open(args.input_pdf)
    for p in all_placements:
        final[p.page].insert_text(
            (p.x, p.y), p.value, fontsize=p.fontsize, fontname="helv"
        )
        print(f"  Page {p.page + 1}: '{p.label}' = '{p.value}'")
    final.save(args.output_pdf)
    final.close()
    print(f"\nSaved: {args.output_pdf}")


if __name__ == "__main__":
    main()
