#!/usr/bin/env bash
# self-review.sh — Export a PPTX to slide JPEGs for agent review.
#
# Usage:
#   bash self-review.sh /path/to/deck.pptx              # full review (all slides)
#   bash self-review.sh /path/to/deck.pptx --only 3,5   # re-review only slides 3 & 5
#   bash self-review.sh /path/to/deck.pptx --scan        # contact sheet (one image)
#
# Output: <pptx-dir>/review/slide-NN.jpg   (individual slides)
#         <pptx-dir>/review/contact.jpg    (--scan mode)
#
# Status per slide: OK / Resized / SKIP
# SKIP = file still >1 MB after resize. Do NOT read SKIP files.

set -euo pipefail

PPTX="${1:?Usage: self-review.sh /path/to/presentation.pptx [--only N,M] [--scan]}"
shift
REVIEW_DIR="$(dirname "$PPTX")/review"
mkdir -p "$REVIEW_DIR"

# Parse flags
ONLY=""
SCAN=false
while [[ $# -gt 0 ]]; do
  case "$1" in
    --only) ONLY="$2"; shift 2 ;;
    --scan) SCAN=true; shift ;;
    *) echo "Unknown flag: $1"; exit 1 ;;
  esac
done

# ── 0. Clean old review images ───────────────────────────────────────────────
# Remove stale files from previous runs to avoid format mismatches.
rm -f "$REVIEW_DIR"/slide-*.png "$REVIEW_DIR"/slide-*.jpg \
      "$REVIEW_DIR"/contact.png "$REVIEW_DIR"/contact.jpg 2>/dev/null || true

# ── 1. Export PPTX → PDF ──────────────────────────────────────────────────────
LO_BIN="$(command -v soffice 2>/dev/null || echo '/Applications/LibreOffice.app/Contents/MacOS/soffice')"
if [[ ! -x "$LO_BIN" ]]; then
  echo "ERROR: LibreOffice not found. Install it or ensure 'soffice' is on PATH." >&2
  exit 1
fi
"$LO_BIN" --headless --convert-to pdf "$PPTX" --outdir "$REVIEW_DIR" 2>/dev/null

PDF="$REVIEW_DIR/$(basename "${PPTX%.pptx}").pdf"

# ── 2. Render PDF pages → JPEG at 100 dpi (~1280×720, good enough for review)
# Using JPEG throughout avoids media-type mismatches when the agent reads images.
pdftoppm -r 100 -jpeg -jpegopt quality=85 "$PDF" "$REVIEW_DIR/slide"

# ── 3. Build comma-separated list of slides to keep (if --only was given) ─────
# Use simple string matching since macOS bash 3 lacks associative arrays
ONLY_LIST=""
if [[ -n "$ONLY" ]]; then
  ONLY_LIST=",$ONLY,"   # wrap in commas for easy substring matching
fi

# Helper: extract slide number from filename like slide-03.jpg → 3
slide_num() {
  local base
  base="$(basename "$1" .jpg)"       # slide-03
  base="${base#slide-}"               # 03
  echo "$((10#$base))"               # 3 (strip leading zero)
}

# Helper: check if slide number is in the --only list
in_only_list() {
  local n="$1"
  [[ -z "$ONLY_LIST" ]] && return 0         # no filter → include all
  [[ "$ONLY_LIST" == *",$n,"* ]] && return 0 # found in list
  return 1
}

# ── 4. Check / resize JPEGs ─────────────────────────────────────────────────
# pdftoppm at 100 DPI + quality 85 produces compact JPEGs.  Some slides
# (large photos) may still exceed 512 KB.  Re-compress at lower quality.
KEPT=()
for f in "$REVIEW_DIR"/slide-*.jpg; do
  num=$(slide_num "$f")

  # If --only was given, skip slides not in the set
  if ! in_only_list "$num"; then
    continue
  fi

  size=$(wc -c < "$f")
  if [ "$size" -gt 512000 ]; then
    # Re-compress at quality 60
    tmp="${f}.tmp"
    uv run python -c "
from PIL import Image
import sys
img = Image.open(sys.argv[1])
img = img.convert('RGB')
img.save(sys.argv[2], 'JPEG', quality=60, optimize=True)
" "$f" "$tmp" 2>/dev/null
    if [[ -f "$tmp" ]]; then
      new_size=$(wc -c < "$tmp")
      mv -f "$tmp" "$f"
      echo "Resized slide $num: ${size} → ${new_size} bytes (JPEG q60)"
      if [ "$new_size" -gt 1048576 ]; then
        echo "SKIP slide $num ($(basename "$f")) — still ${new_size} bytes after recompression"
        rm -f "$f"
        continue
      fi
    else
      echo "SKIP slide $num ($(basename "$f")) — recompression failed, ${size} bytes"
      rm -f "$f"
      continue
    fi
  else
    echo "OK slide $num — ${size} bytes"
  fi
  KEPT+=("$f")
done

# ── 5. Contact sheet mode (--scan) ──────────────────────────────────────────
if [[ "$SCAN" == true ]] && [[ ${#KEPT[@]} -gt 0 ]]; then
  CONTACT="$REVIEW_DIR/contact.jpg"
  # Use Pillow (already a skill prerequisite) to build a 2-column contact sheet
  uv run python -c "
import sys, os
from PIL import Image, ImageDraw

files = sys.argv[1:-1]
out = sys.argv[-1]
cols = 2
thumb_w, thumb_h = 640, 360
pad = 4
rows_count = (len(files) + cols - 1) // cols
cw = cols * thumb_w + (cols + 1) * pad
ch = rows_count * (thumb_h + 20) + (rows_count + 1) * pad
canvas = Image.new('RGB', (cw, ch), 'white')
draw = ImageDraw.Draw(canvas)
for i, f in enumerate(files):
    r, c = divmod(i, cols)
    img = Image.open(f)
    img.thumbnail((thumb_w, thumb_h), Image.LANCZOS)
    x = pad + c * (thumb_w + pad)
    y = pad + r * (thumb_h + 20 + pad)
    ox = x + (thumb_w - img.width) // 2
    oy = y + (thumb_h - img.height) // 2
    canvas.paste(img, (ox, oy))
    num = os.path.basename(f).replace('slide-','').replace('.jpg','')
    draw.text((x + thumb_w // 2, y + thumb_h + 2), f'Slide {int(num)}',
              fill='black', anchor='mt')
canvas.save(out, 'JPEG', quality=80, optimize=True)
" "${KEPT[@]}" "$CONTACT"
  if [[ -f "$CONTACT" ]]; then
    echo ""
    echo "Contact sheet: $CONTACT ($(wc -c < "$CONTACT") bytes)"
    echo "Read contact.jpg for a quick scan. Then read individual slide-NN.jpg for detail."
  else
    echo ""
    echo "Contact sheet generation failed. Read individual slide-NN.jpg files instead."
  fi
else
  echo ""
  echo "Review images in: $REVIEW_DIR"
  echo "Files to read (all JPEG):"
  for img in "${KEPT[@]}"; do
    echo "  $(basename "$img")"
  done
  if [[ -n "$ONLY" ]]; then
    echo "Re-reviewed slides: $ONLY"
    echo "Read only the re-reviewed slide .jpg files listed above."
  else
    echo "Read 2-3 consecutive .jpg files per Read call (they are small at 100 DPI)."
    echo "Do NOT read files marked SKIP. All files are .jpg — never use .png."
  fi
fi
