"""
PyMuPDF-based PDF text extractor with Markdown support.

Usage examples:
  - Extract single PDF to markdown (default, creates .md file):
      python -m utils.pdf_text_extract input.pdf

  - Extract all PDFs in a directory to markdown:
      python -m utils.pdf_text_extract docs/papers/

  - Extract with custom output location:
      python -m utils.pdf_text_extract input.pdf -o output.md

  - Extract selected pages (0-based):
      python -m utils.pdf_text_extract input.pdf -p 0-2,4

  - Use legacy plain text mode (creates .txt file):
      python -m utils.pdf_text_extract input.pdf -m simple

Notes:
  - Default mode uses pymupdf4llm for markdown conversion (saves as .md).
  - Legacy modes (simple, blocks) use raw PyMuPDF text extraction (saves as .txt).
  - Bulk directory processing automatically skips PDFs with existing output files.
  - This utility does NOT perform OCR. It extracts embedded text only.
  - Page ranges are 0-based (e.g., "0-2,4" for pages 1-3 and 5).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable, List, Sequence

import pymupdf
import pymupdf4llm


def parse_page_ranges(ranges: str, num_pages: int) -> List[int]:
    """Parse a page range string like "0-2,4" into zero-based page indices.

    Args:
        ranges: Comma-separated list of 0-based page numbers and ranges.
        num_pages: Total number of pages in the document.

    Returns:
        Sorted list of unique zero-based page indices.
    """
    selected: set[int] = set()
    for part in ranges.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start_s, end_s = part.split("-", 1)
            try:
                start = int(start_s)
                end = int(end_s)
            except ValueError as exc:
                raise ValueError(f"Invalid page range component: '{part}'") from exc
            if start < 0 or end < 0:
                raise ValueError("Page numbers must be >= 0")
            if end < start:
                raise ValueError(f"Range end before start: '{part}'")
            for i in range(start, min(end + 1, num_pages)):
                selected.add(i)
        else:
            try:
                page_0based = int(part)
            except ValueError as exc:
                raise ValueError(f"Invalid page number: '{part}'") from exc
            if page_0based < 0:
                raise ValueError("Page numbers must be >= 0")
            if page_0based < num_pages:
                selected.add(page_0based)
    return sorted(selected)


def page_text_simple(page: pymupdf.Page) -> str:
    """Return plain text for a page."""
    return page.get_text("text")


def page_text_blocks(page: pymupdf.Page) -> str:
    """Return text by blocks in reading order, separated by blank lines."""
    blocks = page.get_text("blocks")
    # blocks are tuples: (x0, y0, x1, y1, text, block_no, block_type)
    blocks_sorted = sorted(blocks, key=lambda b: (b[1], b[0]))
    texts = []
    for b in blocks_sorted:
        text = b[4] if len(b) > 4 else ""
        if text:
            texts.append(text.rstrip())
    return "\n\n".join(texts) + ("\n" if texts else "")


def extract_text_markdown(
    input_path: Path,
    output_path: Path | None,
    pages: Sequence[int] | None,
) -> None:
    """Extract text from PDF as markdown using pymupdf4llm.

    Args:
        input_path: Path to input PDF.
        output_path: Destination path, or None to write to stdout.
        pages: Zero-based page indices to extract. If None, extract all.
    """
    # pymupdf4llm.to_markdown expects a list of pages if provided
    md_text = pymupdf4llm.to_markdown(
        str(input_path),
        pages=list(pages) if pages else None
    )

    if output_path is None:
        sys.stdout.write(md_text)
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(md_text.encode("utf-8"))


def extract_text_legacy(
    input_path: Path,
    output_path: Path | None,
    pages: Sequence[int] | None,
    mode: str,
    page_separator: str,
) -> None:
    """Extract text from PDF using legacy PyMuPDF methods.

    Args:
        input_path: Path to input PDF.
        output_path: Destination path, or None to write to stdout.
        pages: Zero-based page indices to extract. If None, extract all.
        mode: One of {"simple", "blocks"}.
        page_separator: String written between pages (default form-feed).
    """
    extractor = page_text_simple if mode == "simple" else page_text_blocks

    with pymupdf.open(input_path) as doc:
        page_indices: Iterable[int] = (
            range(len(doc)) if pages is None or len(pages) == 0 else pages
        )

        def write_all(out):
            first = True
            for i in page_indices:
                page = doc.load_page(i)
                text = extractor(page)
                if not first:
                    out.write(page_separator)
                out.write(text)
                first = False

        if output_path is None:
            write_all(sys.stdout)
        else:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with output_path.open("w", encoding="utf-8", newline="") as f:
                write_all(f)


def bulk_extract_directory(
    input_dir: Path,
    output_dir: Path | None,
    mode: str,
    pages: Sequence[int] | None,
) -> None:
    """Extract all PDFs in a directory to text files.

    Args:
        input_dir: Directory containing PDF files.
        output_dir: Output directory. If None, saves in same directory as input.
        mode: Extraction mode.
        pages: Page indices to extract from each PDF.
    """
    pdf_files = list(input_dir.glob("**/*.pdf"))
    
    if not pdf_files:
        print(f"No PDF files found in {input_dir}", file=sys.stderr)
        return

    print(f"Found {len(pdf_files)} PDF file(s) to process...")

    # Filter out PDFs that already have corresponding output files
    ext = ".md" if mode == "markdown" else ".txt"
    files_to_process = []
    skipped_count = 0
    
    for pdf_path in pdf_files:
        if output_dir:
            output_path = output_dir / f"{pdf_path.stem}{ext}"
        else:
            output_path = pdf_path.with_suffix(ext)
        
        if output_path.exists():
            print(f"Skipping (already exists): {pdf_path.name} -> {output_path.name}")
            skipped_count += 1
        else:
            files_to_process.append((pdf_path, output_path))
    
    if skipped_count > 0:
        print(f"Skipped {skipped_count} already-processed file(s).")
    
    if not files_to_process:
        print("No new files to process.")
        return
    
    print(f"Processing {len(files_to_process)} file(s)...")

    for pdf_path, output_path in files_to_process:
        print(f"Processing: {pdf_path.name} -> {output_path.name}")
        
        try:
            if output_dir:
                output_dir.mkdir(parents=True, exist_ok=True)
            
            if mode == "markdown":
                extract_text_markdown(pdf_path, output_path, pages)
            else:
                extract_text_legacy(pdf_path, output_path, pages, mode, "\f\n")
        except Exception as exc:
            print(f"  Error processing {pdf_path.name}: {exc}", file=sys.stderr)
            continue

    print(f"Completed processing {len(files_to_process)} file(s).")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract text from PDF(s) using PyMuPDF (no OCR).",
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Path to input PDF file or directory containing PDFs.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="Output path (file or directory). Use '-' for stdout (single file only). "
             "If omitted, saves .md/.txt files (based on mode) alongside input files.",
    )
    parser.add_argument(
        "-p",
        "--pages",
        type=str,
        default=None,
        help="0-based page ranges like '0-2,4' (pages 1-3 and 5). Omit for all pages.",
    )
    parser.add_argument(
        "-m",
        "--mode",
        choices=["markdown", "simple", "blocks"],
        default="markdown",
        help="Extraction mode: 'markdown' (default, uses pymupdf4llm), "
             "'simple' (plain text), or 'blocks' (layout-aware text).",
    )
    parser.add_argument(
        "--page-sep",
        type=str,
        default="\f\n",
        help="Separator between pages in legacy modes (default: form-feed + newline).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    input_path: Path = args.input
    if not input_path.exists():
        parser.error(f"Input path does not exist: {input_path}")

    # Handle directory input
    if input_path.is_dir():
        output_dir: Path | None
        if args.output is None:
            output_dir = None  # Save alongside originals
        elif args.output == "-":
            parser.error("Cannot use stdout ('-') with directory input")
        else:
            output_dir = Path(args.output)

        pages_arg: str | None = args.pages
        pages: List[int] | None = None
        if pages_arg:
            # For directory mode, we'll apply the same page selection to all PDFs
            # We can't validate page count here, so we'll handle it per-file
            try:
                # Use a large number as a placeholder for validation
                pages = parse_page_ranges(pages_arg, 10000)
            except ValueError as exc:
                parser.error(str(exc))

        try:
            bulk_extract_directory(
                input_dir=input_path,
                output_dir=output_dir,
                mode=args.mode,
                pages=pages,
            )
        except Exception as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        return 0

    # Handle single file input
    if not input_path.is_file():
        parser.error(f"Input must be a PDF file or directory: {input_path}")

    pages_arg: str | None = args.pages
    pages: List[int] | None = None
    if pages_arg:
        with pymupdf.open(input_path) as doc:
            pages = parse_page_ranges(pages_arg, len(doc))

    output_path: Path | None
    if args.output is None:
        # Use appropriate extension based on mode
        ext = ".md" if args.mode == "markdown" else ".txt"
        output_path = input_path.with_suffix(ext)
    elif args.output == "-":
        output_path = None
    else:
        output_path = Path(args.output)

    try:
        if args.mode == "markdown":
            extract_text_markdown(
                input_path=input_path,
                output_path=output_path,
                pages=pages,
            )
        else:
            extract_text_legacy(
                input_path=input_path,
                output_path=output_path,
                pages=pages,
                mode=args.mode,
                page_separator=args.page_sep,
            )
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


