"""Verify the repo-local ROCm Torch environment and inventory checkpoints.

Run from the repository root with ``uv run --no-sync`` so uv does not replace
the vendor ROCm Torch wheel recorded in the versioned requirements file.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


REPOSITORY = Path(__file__).resolve().parents[2]
PROJECT = Path(__file__).resolve().parents[1]
EXPECTED_PREFIX = (REPOSITORY / ".venv").resolve()
DEFAULT_CHECKPOINT_ROOT = PROJECT / "outputs"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--device-index",
        type=int,
        default=0,
        help="ROCm device index exposed through torch.cuda (default: 0).",
    )
    parser.add_argument(
        "--skip-smoke",
        action="store_true",
        help="Skip the GPU forward/backward numerical smoke test.",
    )
    parser.add_argument(
        "--checkpoint-root",
        type=Path,
        default=DEFAULT_CHECKPOINT_ROOT,
        help="Root used for checkpoint inventory and relative glob matching.",
    )
    parser.add_argument(
        "--inspect-checkpoint",
        action="append",
        default=[],
        metavar="GLOB",
        help=(
            "Load checkpoints matching a relative glob and report saved epoch; "
            "repeat the option for multiple patterns."
        ),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        help="Optionally persist the complete report as an atomic JSON artifact.",
    )
    return parser.parse_args()


def resolve_from_repository(path: Path) -> Path:
    return path.resolve() if path.is_absolute() else (REPOSITORY / path).resolve()


def verify_local_environment() -> dict[str, Any]:
    actual_prefix = Path(sys.prefix).resolve()
    if actual_prefix != EXPECTED_PREFIX:
        raise RuntimeError(
            "Python is not running from the repository-local .venv: "
            f"expected {EXPECTED_PREFIX}, got {actual_prefix}"
        )

    import torch

    if torch.version.hip is None:
        raise RuntimeError(f"Torch {torch.__version__} is not a ROCm build")
    if not torch.cuda.is_available():
        raise RuntimeError("ROCm did not expose an AMD GPU through torch.cuda")

    return {
        "repository": str(REPOSITORY),
        "python_executable": sys.executable,
        "python_prefix": str(actual_prefix),
        "torch_version": torch.__version__,
        "torch_path": str(Path(torch.__file__).resolve()),
        "torch_hip": torch.version.hip,
        "rocm_available": True,
        "device_count": torch.cuda.device_count(),
        "device_names": [
            torch.cuda.get_device_name(index)
            for index in range(torch.cuda.device_count())
        ],
    }


def run_gpu_smoke(device_index: int) -> dict[str, Any]:
    import torch

    if device_index < 0 or device_index >= torch.cuda.device_count():
        raise ValueError(
            f"device index {device_index} is outside 0..{torch.cuda.device_count() - 1}"
        )
    device = torch.device(f"cuda:{device_index}")
    values = torch.arange(
        1,
        1025,
        dtype=torch.float32,
        device=device,
        requires_grad=True,
    )
    loss = values.square().mean() + values.sin().mean()
    loss.backward()
    torch.cuda.synchronize(device)
    return {
        "device_index": device_index,
        "device_name": torch.cuda.get_device_name(device_index),
        "device_memory_bytes": torch.cuda.get_device_properties(
            device_index
        ).total_memory,
        "loss": loss.item(),
        "gradient_finite": bool(torch.isfinite(values.grad).all().item()),
    }


def inspect_checkpoints(root: Path, patterns: list[str]) -> dict[str, Any]:
    import torch

    if not root.exists():
        return {"root": str(root), "count": 0, "inspected": []}

    all_checkpoints = sorted(root.rglob("*.pt"))
    selected = {
        checkpoint.resolve()
        for pattern in patterns
        for checkpoint in root.glob(pattern)
        if checkpoint.is_file() and checkpoint.suffix == ".pt"
    }
    inspected = []
    for checkpoint in sorted(selected):
        payload = torch.load(checkpoint, map_location="cpu", weights_only=False)
        inspected.append(
            {
                "path": checkpoint.relative_to(root).as_posix(),
                "bytes": checkpoint.stat().st_size,
                "epoch": payload.get("epoch") if isinstance(payload, dict) else None,
            }
        )
    return {
        "root": str(root),
        "count": len(all_checkpoints),
        "inspected": inspected,
    }


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def main() -> None:
    args = parse_args()
    checkpoint_root = resolve_from_repository(args.checkpoint_root)
    report: dict[str, Any] = {
        "environment": verify_local_environment(),
        "gpu_smoke": None if args.skip_smoke else run_gpu_smoke(args.device_index),
        "checkpoints": inspect_checkpoints(
            checkpoint_root, args.inspect_checkpoint
        ),
    }
    rendered = json.dumps(report, indent=2, ensure_ascii=False)
    print(rendered)
    if args.output_json is not None:
        write_json_atomic(resolve_from_repository(args.output_json), report)


if __name__ == "__main__":
    main()
