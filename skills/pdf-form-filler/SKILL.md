---
name: pdf-form-filler
description: "Fill static PDF forms (without fillable fields) using text search for text-based PDFs or Claude Vision for image-based/scanned PDFs. Use when: (1) User wants to fill out a PDF form, (2) PDF has no fillable form fields, (3) User asks to fill in or complete a PDF form. Auto-detects PDF type and uses appropriate method."
---

# PDF Form Filler

Fill static PDF forms by detecting PDF type and using the appropriate method:
- **Text-based PDFs**: Search for label text and insert values at found positions
- **Image-based PDFs**: Use Claude Vision iteratively for pixel-perfect placement

## Quick Start

```bash
# Option 1: Text-based PDF (fast, uses label search)
uv run scripts/fill_pdf.py form.pdf filled.pdf "Label:?=value"

# Option 2: VLM-guided (works for ANY PDF, iteratively verifies placement)
uv run scripts/fill_pdf_vlm.py form.pdf filled.pdf --fields '{"Field": "value"}'
```

---

## Method 1: Text Search Positioning (Text-Based PDFs)

**This is how pixel-perfect filling works:**

Instead of guessing x/y coordinates, we:
1. **Search for the label text** using PyMuPDF's `page.search_for("Label:")`
2. **Get the bounding rectangle** of the found text
3. **Insert value after the label** at `x = rect.x1 + offset` (right edge of label + small offset)

```
┌─────────────────────────────────────┐
│ Student's name: ________________    │
│                ↑                    │
│         rect.x1 (right edge)        │
│              + 5px offset           │
│              = insertion point      │
└─────────────────────────────────────┘
```

**Code pattern:**
```python
areas = page.search_for("Student's name:")
if areas:
    rect = areas[0]
    x = rect.x1 + 5  # right edge + small offset
    y = rect.y0      # top of the text
    page.insert_text((x, y + fontsize * 0.8), "Philip Ma", fontsize=11)
```

**Why this works:**
- PDFs store text with precise positions
- PyMuPDF returns exact bounding boxes for found text
- Inserting right after the label naturally aligns with the form field

### Usage

```bash
# Detect PDF type
uv run scripts/fill_pdf.py --detect form.pdf

# Extract text to find labels
uv run scripts/fill_pdf.py --extract form.pdf

# Fill using label?=value format
uv run scripts/fill_pdf.py form.pdf filled.pdf \
    "Student's name:?=John Doe" \
    "Total:?=1500.00"
```

---

## Method 2: VLM-Guided Iterative Filling (Any PDF)

**For complex forms or when text search fails:**

Uses Claude Vision to:
1. **Discover**: Identify where each value should be placed
2. **Render**: Place text and render the page
3. **Verify**: Ask VLM if placement is correct
4. **Iterate**: Correct positions up to N times until verified

```
┌──────────────────────────────────────────┐
│  PDF Page                                │
│  ┌─────────────────────────────────────┐ │
│  │ Print Name                          │ │
│  │ ══════════════════════════════════  │ │
│  │         ↑ VLM sees: "above line!"   │ │
│  │ Date                                │ │
│  │ ══════════════════════════════════  │ │
│  └─────────────────────────────────────┘ │
│                                          │
│  VLM: "Print Name should be ABOVE line"  │
│  → Corrects y-position automatically     │
└──────────────────────────────────────────┘
```

### Key Features

1. **Only renders pending fields** during verification (not all fields)
2. **Uses pixel coordinates** for VLM communication, converts to PDF points internally
3. **Iterative convergence** until all fields are correctly positioned

### Usage

```bash
# Requires ANTHROPIC_API_KEY
export ANTHROPIC_API_KEY=sk-...

uv run scripts/fill_pdf_vlm.py form.pdf filled.pdf --fields '{
    "Student Name": "Philip Ma",
    "Print Name (first)": "Eric Ma",
    "Date (first)": "March 08, 2026",
    "Print Name (second)": "Nan Li",
    "Date (second)": "March 08, 2026"
}'
```

### How It Works

1. **Discovery Phase**: For each page, Claude Vision analyzes the form and returns pixel coordinates for each field
2. **Iteration Phase**: 
   - Render PDF with only PENDING (uncorrected) fields
   - VLM checks if text is correctly positioned
   - If wrong, VLM provides corrected pixel coordinates
   - Repeat up to `--max-iter` times (default: 5)
3. **Final Output**: Write all verified placements to output PDF

### Example Run
```bash
--- Page 1: Discovering ---
  'Student Name' at (134, 84)
  'Print Name (p1)' at (306, 763)
  
=== Iteration 1 (11 pending) ===
  Page 1:
    OK 'Student Name'
    FIX 'Print Name (p1)': (306,763) -> (306,749) - Text should be ABOVE signature line
    
=== Iteration 2 (10 pending) ===
  Page 1:
    OK 'Print Name (p1)'
    
All verified after 2 iterations!
```

### When to Use

- **Scanned/image PDFs** where text extraction fails
- **Complex layouts** where labels don't clearly indicate position
- **Forms with horizontal lines** where text goes above/below
- **High precision needed** and willing to use API calls

### Cost Considerations

Each iteration makes ~1 API call per page for verification.
Most forms complete in 2-3 iterations.

---

## Environment Variables

- `ANTHROPIC_API_KEY`: Required for VLM-guided mode (`fill_pdf_vlm.py`)

## Limitations

- Signature areas should remain blank for manual signing
- Does not handle checkboxes or radio buttons
- VLM mode uses Claude API tokens per iteration
