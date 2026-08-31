---
name: pdf-form-filler
description: "Fill flat PDF forms that have NO fillable fields (school enrollment packets, medical intakes, waivers, government paperwork) and reuse a prior year's filled PDF as the source of answers. Requires a vision-language-model coding agent (renders pages to images and looks at them); there is no non-VLM fallback. Use when: the user asks to fill out / complete / fill in a PDF form, especially recurring yearly forms (enrollment, renewal, intake) where a previously filled copy exists; when pypdf reports zero AcroForm fields but the form has lines and labels; when the user says 'agent, fill this form for me'; when transplanting prior answers onto a new PDF template; when reproducing a scanned or drawn signature as vector ink from an old PDF; or when a filled form's text overlaps lines or labels and placement needs verification against rendered pixels."
license: MIT
---

# PDF Form Filler

Fill flat PDFs (no AcroForm fields) by transplanting answers from a prior filled copy, drawing text at exact PDF coordinates, and verifying every page by rendering it and looking at the pixels. Requirement: you (the agent) must be able to view images. There is no non-VLM fallback; without vision, do not attempt this workflow, you will ship misaligned text and never know.

## Core insight

A form is a measured coordinate range, never a visual impression. The whole discipline is: get exact geometry from the PDF's own data, convert coordinate conventions correctly, and verify placement against rendered pixels because every library lies at least once.

## The one workflow that works

### 1. Mine a prior filled copy before writing any code

Search the user's machine (Downloads, Documents, email attachments) for a previously filled version of the same form. Recurring forms (yearly enrollment, renewals) are almost always the identical template year over year. A prior copy provides:

- Every answer (and the positions of its answers, which become your coordinates)
- The user's signature as vector ink (see signature section)
- Baseline offsets that a human already got right (steal them)

Diff the prior template against the new blank: extract all text lines with coordinates from both and compare position sets. If blanks align, transplant answers wholesale and update only what changed. Ask the user a batched list of just the changed fields (insurance plan, phone numbers, dates, names); never guess these.

Highest-leverage check: confirm the two templates are identical by testing that every static text line sits at the same (page, x, y). Only footer dates should differ.

### 2. Confirm the form has no fillable fields

```python
from pypdf import PdfReader
print(PdfReader("form.pdf").get_fields())  # None or {} = flat PDF, this skill applies
```

(If real AcroForm fields exist, set their values instead; this skill is for the flat case.)

### 3. Extract prior answers with positions

Use pdfminer.six to get text, position, size, and color per line: `extract_pages()` gives `LTTextContainer`/`LTTextLine` with `.bbox` (x0, y0 from BOTTOM-LEFT) and per-char `graphicstate.ncolor`. Filter to the fill color (often blue or black) to separate answers from form labels.

Dump the extracted fills to JSON (page, x, y, size, text) before transforming; you will reuse it every iteration.

### 4. Write text on the blank PDF, honoring the placement contract

Use PyMuPDF (`pymupdf`/`fitz`) to `insert_text()`. The placement contract, hard-earned:

- **Baseline sits ~2.5pt ABOVE the drawn line, never at it.** Text at the line's y crosses through glyphs like a strikethrough. y_top = page_height - extracted_y - 2.5 (the 2.5 came from measuring a human-filled exemplar).
- **Text must not overlap anything.** Not the printed label, not the line, not adjacent fields, not the page edge. Compute the string's rendered width (`fitz.get_text_length(text, fontname, fontsize)`) and shrink the font (min ~7pt) until `x + width <= blank_right_edge`.
- **Center on the blank's measured range.** Field blanks are the underscore runs inside the field's text span; measure their exact extent (char-level via `get_text('rawdict')`) and place text ON that run, not past its end, not on the label.
- Junk from the old form (stray single characters, mis-angled fragments near signature areas) gets DROPPED, never transplanted. Ask the user for real values where junk blocked a field.
- CJK text needs a CJK-capable font ("china-s" in PyMuPDF); measure its width with the same font you draw with.

### 5. Signatures: replay vector ink, never paste pixels

A drawn signature in a PDF is NOT an image; it is hundreds of small path segments ('l', 'c' curve operators) in one or few drawing objects, filtered by stroke/fill color (e.g. blue 0,0.44,1). To move it to a new PDF:

1. Read the source page's `get_drawings()`.
2. Select paths whose color matches the ink.
3. Replay each path's items as raw PDF operators (m/l/c/re + h + f) appended to the destination page's content stream, coordinates as-is (see gotchas for the flip trap).
4. Never crop the source page as pixels: the region smuggles surrounding printed text into your output image. If a pixel region must be used (last resort), mask to keep only strongly-colored ink and alpha out the background.

Yes, the user should ideally sign by hand; also offer the replayed signature, they usually accept it (it is their own signature from their own prior form).

### 6. The verification loop (mandatory, this is the skill)

For every page: render to PNG (`page.get_pixmap()`), then LOOK at the image. Check: text on the correct blank, baseline above the line without crossing it, no overlap with labels or neighbors, nothing spilling past the page edge, signature present and in the right place. Iterate until clean. Render-verify-fix is the loop; text-length arithmetic is a hypothesis, the render is the verdict.

### 7. Pixel-profile check for signatures (fallback when unsure)

To find where ink actually is: render at 72dpi, scan for pixels where blue channel far exceeds red (b > 150 and b - r > 60), cluster the rows, and compare clusters against the old page's clusters. Same clusters = same placement. Do not trust coordinate math alone; measure ink.

## Coordinate systems (read this twice)

The single biggest source of wrong renders. Three conventions coexist:

- **pdfminer/PDF content space**: origin BOTTOM-LEFT, y up. Extraction gives you this.
- **PyMuPDF page.rect / get_pixmap**: origin TOP-LEFT, y down. Drawing with `insert_text()` uses this.
- **PDF content-stream path operators** (what `get_drawings()` items map to): origin BOTTOM-LEFT again, y up.

Converting extracted (bottom-left) positions to PyMuPDF drawing (top-left): `y_pymupdf = page_height - y_extracted`, plus your baseline offset (above). Note `page_height` is the page's actual height (letter = 792), and non-72dpi renders multiply everything by dpi/72.

Signatures replay in raw content-stream space: pymupdf's get_drawings() rect for a bottom-half signature may ALREADY be in top-down convention on some PDFs. Do not trust either convention: render, measure the ink's pixel rows, and compute the flip from evidence. Verify with the ink-profile technique above; if the signature lands mirrored (top of page instead of bottom), you flipped wrong, and the profile check catches it instantly.

## Rejected approaches (do not retry)

- **show_pdf_page with clip rects** to copy signature regions: copies ALL content in the rect, duplicating text and lines.
- **Rasterized region pastes** for signatures: smuggles printed text into the image at stamp resolution.
- **XObject indirection** for simple path replay: resource-dictionary failures ("cannot find XObject"); direct path operators in the content stream work.
- **Trusting any single library's coordinate report**: each must be calibrated against rendered pixels once per document.

The fallback loop for every failure: render, look at the image, measure ink pixels, reconcile the transform. Pixel measurement beats arithmetic every time they disagree.

## Working checklist

1. Locate prior filled PDF; diff templates; ask user for changed values in one batch.
2. Extract answers + positions + color (pdfminer); dump JSON.
3. Write text (pymupdf): baseline 2.5pt above line, no overlaps, shrink-to-fit, CJK font when needed, drop junk.
4. Replay signature/ink vector paths; determine flips from pixel evidence, not theory.
5. Render every page to PNG; LOOK at each. Zoom on dense areas (tables, signature rows, narrow blanks).
6. Iterate fixes until every field passes the placement contract.
7. Deliver: filled PDF + one PNG render per page for the user's own final check.

The user's final look is part of the pipeline, not a nicety. They will catch what the render-verify loop normalized.