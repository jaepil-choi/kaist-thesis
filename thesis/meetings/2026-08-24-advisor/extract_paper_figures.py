"""발표자료용 비교 그림을 잘라낸다.

두 종류를 만든다.

1. 원 논문(Guijarro-Ordonez et al. 2025, MS) PDF에서 Figure 5 · 6 · 11을 300 dpi PNG로 추출.
   crop 좌표는 PDF point 기준이며 "Figure N:" 제목줄은 빼고 panel과 subcaption만 담는다.
2. 위 그림 및 한국 재현 산출물에서 대표 사양(CNN+Transformer, PCA5) 단일 패널만 잘라낸
   확대 비교용 그림. 슬라이드에서 나란히 놓았을 때 읽을 수 있는 크기를 확보하기 위한 것이며
   원본 픽셀을 자르기만 할 뿐 다시 그리지 않는다.

산출물은 모두 `figures/paper/`(미국)와 `figures/korea/`(한국)에 들어간다.

실행:
    uv run --with pymupdf python thesis/meetings/2026-08-24-advisor/extract_paper_figures.py
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import pymupdf
from PIL import Image

HERE = Path(__file__).resolve().parent
REPO = Path(os.environ.get("THESIS_REPO", HERE.parents[2]))
PDF = REPO / "docs" / "pdfs" / (
    "2025 Deep Learning Statistical Arbitrage - Guijarro-Ordonez et al. (MS).pdf.pdf"
)
KOREAN_FIGS = REPO / "guijarro-ordonez-2025-replication" / "paper-assets" / "figures"
OUT_US = HERE / "figures" / "paper"
OUT_KR = HERE / "figures" / "korea"
DPI = 300

# (출력 파일명, 0-based page index, clip rect in PDF points)
PDF_CROPS = [
    ("fig_05_us_cumulative_returns.png", 29, (70, 90, 542, 482)),
    ("fig_06_us_turnover.png", 37, (73, 302, 539, 457)),
    ("fig_11_us_naive_reversal.png", 42, (66, 546, 535, 658)),
    # Figure 5 panel (b): CNN+Trans, PCA 5 — 한국 대표 사양과 직접 대응하는 단일 패널
    ("fig_05_us_cnn_pca5.png", 29, (226, 92, 383, 223)),
]

# 한국 재현 그림에서 잘라낼 단일 패널. (출력 파일명, 원본 파일명, 비율 기준 crop box)
# box는 (left, top, right, bottom)을 이미지 폭·높이 대비 비율로 준다.
KOREAN_CROPS = [
    (
        "fig_05_korean_cnn_panel.png",
        "fig_05_korean_cumulative_returns.png",
        (0.0, 0.045, 0.345, 1.0),
    ),
]

# 발표자료가 그대로 쓰는 한국 재현 그림. 저장소 상대경로를 슬라이드 소스에 남기지 않기 위해
# 원본을 수정 없이 복사만 한다.
KOREAN_COPIES = [
    "fig_05_korean_cumulative_returns.png",
    "fig_06_korean_turnover.png",
    "fig_11_naive_reversal.png",
]


def crop_pdf_figures() -> None:
    if not PDF.exists():
        raise SystemExit(f"원 논문 PDF를 찾을 수 없다: {PDF}")
    OUT_US.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(PDF)
    for name, page_index, rect in PDF_CROPS:
        pix = doc[page_index].get_pixmap(clip=pymupdf.Rect(*rect), dpi=DPI)
        path = OUT_US / name
        pix.save(path)
        print(f"WROTE {path}  ({pix.width}x{pix.height})")
    doc.close()


def crop_korean_figures() -> None:
    OUT_KR.mkdir(parents=True, exist_ok=True)
    for name, source_name, box in KOREAN_CROPS:
        source = KOREAN_FIGS / source_name
        if not source.exists():
            raise SystemExit(f"한국 재현 그림을 찾을 수 없다: {source}")
        with Image.open(source) as img:
            w, h = img.size
            left, top, right, bottom = box
            cropped = img.crop(
                (round(left * w), round(top * h), round(right * w), round(bottom * h))
            )
            path = OUT_KR / name
            cropped.save(path)
            print(f"WROTE {path}  ({cropped.width}x{cropped.height})")


def copy_korean_figures() -> None:
    OUT_KR.mkdir(parents=True, exist_ok=True)
    for name in KOREAN_COPIES:
        source = KOREAN_FIGS / name
        if not source.exists():
            raise SystemExit(f"한국 재현 그림을 찾을 수 없다: {source}")
        path = OUT_KR / name
        shutil.copyfile(source, path)
        print(f"COPIED {path}  ({path.stat().st_size} bytes)")


def main() -> None:
    crop_pdf_figures()
    crop_korean_figures()
    copy_korean_figures()


if __name__ == "__main__":
    main()
