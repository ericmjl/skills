#!/usr/bin/env python
# /// script
# requires-python = ">=3.11"
# dependencies = ["pymupdf", "anthropic", "pillow"]
# ///
"""
Fill out PDF forms - works with both text-based and image-based (scanned) PDFs.

Text PDFs: Searches for label text and inserts values after them.
Image PDFs: Uses Claude Vision to identify form field positions.

Usage:
    # Extract text to find field labels (text PDFs)
    uv run fill_pdf.py --extract <input.pdf>

    # Fill text-based PDF
    uv run fill_pdf.py <input.pdf> <output.pdf> "Label:?=value" ...

    # Fill image-based PDF (uses Claude Vision)
    uv run fill_pdf.py --vision <input.pdf> <output.pdf>

    # Detect PDF type
    uv run fill_pdf.py --detect <input.pdf>

Environment variables:
    ANTHROPIC_API_KEY: Required for --vision mode
"""

import base64
import io
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import fitz
from PIL import Image

TEXT_THRESHOLD_CHARS = 100


@dataclass
class FieldPosition:
    """Represents a form field position."""

    label: str
    x: float
    y: float
    page: int
    width: float = 200
    height: float = 20
    fontsize: int = 11


def is_text_pdf(pdf_path: str, threshold: int = TEXT_THRESHOLD_CHARS) -> bool:
    """
    Detect if PDF is text-based or image-based.

    Args:
        pdf_path: Path to PDF file
        threshold: Minimum characters to consider text-based

    Returns:
        True if text-based, False if image-based
    """
    doc = fitz.open(pdf_path)
    total_chars = 0

    for page in doc:
        text = page.get_text()
        total_chars += len(text.strip())
        if total_chars >= threshold:
            doc.close()
            return True

    doc.close()
    return False


def pdf_page_to_image(pdf_path: str, page_num: int, dpi: int = 150) -> Image.Image:
    """
    Convert a PDF page to a PIL Image.

    Args:
        pdf_path: Path to PDF file
        page_num: Page number (0-indexed)
        dpi: Resolution for rendering

    Returns:
        PIL Image of the page
    """
    doc = fitz.open(pdf_path)
    page = doc[page_num]
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    doc.close()
    return img


def image_to_base64(img: Image.Image) -> str:
    """Convert PIL Image to base64 string."""
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def get_fields_from_vision(
    pdf_path: str, existing_values: dict[str, str] | None = None
) -> list[FieldPosition]:
    """
    Use Claude Vision to identify form fields in a PDF.

    Args:
        pdf_path: Path to PDF file
        existing_values: Optional dict of field labels -> values already filled

    Returns:
        List of FieldPosition objects
    """
    try:
        import anthropic
    except ImportError:
        print("ERROR: anthropic package required for vision mode")
        print("Install with: pip install anthropic")
        sys.exit(1)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    doc = fitz.open(pdf_path)
    all_fields: list[FieldPosition] = []

    for page_num in range(len(doc)):
        print(f"Analyzing page {page_num + 1} with Claude Vision...")

        img = pdf_page_to_image(pdf_path, page_num)
        img_b64 = image_to_base64(img)

        page_width = doc[page_num].rect.width
        page_height = doc[page_num].rect.height

        prompt = f"""Analyze this form image and identify all fillable form fields.

For each field, provide:
1. The label text (what the field is for)
2. The x,y coordinates where text should be inserted (in PDF coordinates, origin at bottom-left)
3. The approximate width and height of the fill area

The image dimensions are {img.width}x{img.height} pixels.
The PDF page dimensions are {page_width:.1f}x{page_height:.1f} points.

Convert pixel coordinates to PDF coordinates:
- x_pdf = (x_pixel / {img.width}) * {page_width:.1f}
- y_pdf = (({img.height} - y_pixel) / {img.height}) * {page_height:.1f}

Return a JSON array of objects with keys: label, x, y, width, height, fontsize (default 11)

Example format:
[
  {{"label": "Student Name", "x": 150, "y": 670, "width": 200, "height": 20, "fontsize": 11}},
  {{"label": "Date", "x": 450, "y": 100, "width": 100, "height": 20, "fontsize": 11}}
]

IMPORTANT: 
- Only include actual form fields that need to be filled (text fields, not labels)
- Skip signature areas - mark them with "SKIP" in the label
- Estimate reasonable fontsize based on the form's existing text
- Coordinates should be where the text baseline should start"""

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": img_b64,
                            },
                        },
                    ],
                }
            ],
        )

        response_text = message.content[0].text

        try:
            json_start = response_text.find("[")
            json_end = response_text.rfind("]") + 1
            fields_data = json.loads(response_text[json_start:json_end])

            for field in fields_data:
                if field.get("label", "").upper() == "SKIP":
                    continue
                all_fields.append(
                    FieldPosition(
                        label=field["label"],
                        x=float(field["x"]),
                        y=float(field["y"]),
                        page=page_num,
                        width=float(field.get("width", 200)),
                        height=float(field.get("height", 20)),
                        fontsize=int(field.get("fontsize", 11)),
                    )
                )
        except (json.JSONDecodeError, KeyError) as e:
            print(f"WARNING: Could not parse Claude response: {e}")
            print(f"Response was: {response_text[:500]}...")

    doc.close()
    return all_fields


def fill_at_positions(
    pdf_path: str, output_path: str, fields: list[FieldPosition], values: dict[str, str]
) -> None:
    """
    Fill a PDF at specific positions.

    Args:
        pdf_path: Input PDF path
        output_path: Output PDF path
        fields: List of field positions
        values: Dict mapping labels to values
    """
    doc = fitz.open(pdf_path)

    for field in fields:
        if field.label not in values:
            print(f"  Skipping '{field.label}' (no value provided)")
            continue

        value = values[field.label]
        page = doc[field.page]
        page.insert_text(
            (field.x, field.y + field.fontsize * 0.8),
            str(value),
            fontsize=field.fontsize,
            fontname="helv",
        )
        print(
            f"  Page {field.page + 1}: '{field.label}' = '{value}' at ({field.x:.1f}, {field.y:.1f})"
        )

    doc.save(output_path)
    doc.close()
    print(f"\nFilled PDF saved to: {output_path}")


def fill_text_pdf(input_pdf: str, output_pdf: str, field_specs: list[str]) -> None:
    """
    Fill a text-based PDF by searching for labels.

    Args:
        input_pdf: Input PDF path
        output_pdf: Output PDF path
        field_specs: List of "label?=value" strings
    """
    doc = fitz.open(input_pdf)

    for field_spec in field_specs:
        parts = field_spec.split("?=")
        if len(parts) != 2:
            print(f"WARNING: Invalid field format '{field_spec}', skipping")
            continue

        search_text, value = parts

        x_offset = 5
        y_offset = 0
        fontsize = 11

        if "?x_offset=" in value:
            value, xoff = value.split("?x_offset=")
            x_offset = float(xoff.split("?")[0])
        if "?y_offset=" in value:
            value, yoff = value.split("?y_offset=")
            y_offset = float(yoff.split("?")[0])
        if "?fontsize=" in value:
            value, fs = value.split("?fontsize=")
            fontsize = int(fs.split("?")[0])

        found = False
        for page_num in range(len(doc)):
            page = doc[page_num]
            areas = page.search_for(search_text)

            if areas:
                rect = areas[0]
                x = rect.x1 + x_offset
                y = rect.y0 + y_offset
                page.insert_text(
                    (x, y + fontsize * 0.8),
                    str(value),
                    fontsize=fontsize,
                    fontname="helv",
                )
                print(
                    f"Page {page_num + 1}: Inserted '{value}' after '{search_text}' at ({x:.1f}, {y:.1f})"
                )
                found = True
                break

        if not found:
            print(f"WARNING: Could not find '{search_text}' in PDF")

    doc.save(output_pdf)
    doc.close()
    print(f"\nFilled PDF saved to: {output_pdf}")


def interactive_fill_vision(input_pdf: str, output_pdf: str) -> None:
    """
    Interactively fill an image-based PDF using Claude Vision.

    Args:
        input_pdf: Input PDF path
        output_pdf: Output PDF path
    """
    print(f"Analyzing {input_pdf} with Claude Vision...\n")

    fields = get_fields_from_vision(input_pdf)

    if not fields:
        print("No form fields detected.")
        return

    print(f"\nDetected {len(fields)} form fields:\n")
    for i, field in enumerate(fields, 1):
        print(f"  {i}. {field.label} (page {field.page + 1})")

    print("\nEnter values for each field (press Enter to skip):\n")
    values: dict[str, str] = {}

    for field in fields:
        value = input(f"  {field.label}: ").strip()
        if value:
            values[field.label] = value

    if not values:
        print("\nNo values provided, exiting.")
        return

    print("\nFilling PDF...")
    fill_at_positions(input_pdf, output_pdf, fields, values)


def extract_fields(input_pdf: str) -> None:
    """Extract and display all text from a PDF."""
    doc = fitz.open(input_pdf)

    print(f"PDF: {input_pdf}")
    print(f"Pages: {len(doc)}")
    print(f"Type: {'Text-based' if is_text_pdf(input_pdf) else 'Image-based'}\n")

    for page_num in range(len(doc)):
        page = doc[page_num]
        print(f"=== Page {page_num + 1} ===")
        print(page.get_text())
        print()

    doc.close()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    if sys.argv[1] == "--detect":
        if len(sys.argv) < 3:
            print("Usage: uv run fill_pdf.py --detect <input.pdf>")
            sys.exit(1)
        pdf_type = "text-based" if is_text_pdf(sys.argv[2]) else "image-based"
        print(f"{sys.argv[2]}: {pdf_type}")

    elif sys.argv[1] == "--extract" or sys.argv[1] == "-e":
        if len(sys.argv) < 3:
            print("Usage: uv run fill_pdf.py --extract <input.pdf>")
            sys.exit(1)
        extract_fields(sys.argv[2])

    elif sys.argv[1] == "--vision" or sys.argv[1] == "-v":
        if len(sys.argv) < 4:
            print("Usage: uv run fill_pdf.py --vision <input.pdf> <output.pdf>")
            sys.exit(1)
        interactive_fill_vision(sys.argv[2], sys.argv[3])

    else:
        if len(sys.argv) < 4:
            print(__doc__)
            sys.exit(1)

        input_pdf = sys.argv[1]
        output_pdf = sys.argv[2]
        field_specs = sys.argv[3:]

        if is_text_pdf(input_pdf):
            print("Detected text-based PDF, using text search...\n")
            fill_text_pdf(input_pdf, output_pdf, field_specs)
        else:
            print("Detected image-based PDF, use --vision mode instead.")
            print("Usage: uv run fill_pdf.py --vision <input.pdf> <output.pdf>")
            sys.exit(1)


if __name__ == "__main__":
    main()
