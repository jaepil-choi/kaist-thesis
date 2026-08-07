"""Safe command-line client for the Bank of Korea ECOS Open API."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from datetime import date
from io import StringIO
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


BASE_URL = "https://ecos.bok.or.kr/api"
DEFAULT_KEY_ENV = "BOK_ECOS_API_KEY"
MAX_ROW_WINDOW = 10_000


class EcosError(RuntimeError):
    """An ECOS response or transport error without credential leakage."""


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, raw_value = line.split("=", 1)
        values[name.strip()] = raw_value.strip().strip("\"'")
    return values


def env_candidates(explicit: str | None) -> list[Path]:
    if explicit:
        return [Path(explicit).expanduser().resolve()]

    candidates: list[Path] = []
    for origin in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for directory in (origin, *origin.parents):
            candidate = directory / ".env"
            if candidate not in candidates:
                candidates.append(candidate)
    return candidates


def load_api_key(name: str, env_file: str | None) -> str:
    value = os.environ.get(name)
    if value:
        return value

    for candidate in env_candidates(env_file):
        if candidate.is_file():
            value = parse_env_file(candidate).get(name)
            if value:
                return value
    raise EcosError(
        f"{name} is not set in the environment or an available .env file"
    )


def validate_row_window(start_row: int, end_row: int) -> None:
    if start_row < 1 or end_row < start_row:
        raise EcosError("row bounds must satisfy 1 <= start-row <= end-row")
    if end_row - start_row + 1 > MAX_ROW_WINDOW:
        raise EcosError(
            f"row window exceeds {MAX_ROW_WINDOW}; split the request"
        )


def valid_cycle_time(cycle: str, value: str) -> bool:
    if cycle == "A":
        return bool(re.fullmatch(r"\d{4}", value))
    if cycle == "S":
        return bool(re.fullmatch(r"\d{4}S[12]", value))
    if cycle == "Q":
        return bool(re.fullmatch(r"\d{4}Q[1-4]", value))
    if cycle == "M":
        if not re.fullmatch(r"\d{6}", value):
            return False
        return 1 <= int(value[4:]) <= 12
    if cycle == "SM":
        if not re.fullmatch(r"\d{6}S[12]", value):
            return False
        return 1 <= int(value[4:6]) <= 12
    if cycle == "D":
        if not re.fullmatch(r"\d{8}", value):
            return False
        try:
            date(int(value[:4]), int(value[4:6]), int(value[6:8]))
        except ValueError:
            return False
        return True
    return False


def redacted_template(service: str, lang: str, segments: list[str]) -> str:
    encoded = "/".join(quote(str(segment), safe="") for segment in segments)
    return f"{BASE_URL}/{service}/{{key}}/json/{lang}/{encoded}/"


def request_json(
    service: str,
    api_key: str,
    lang: str,
    segments: list[str],
    timeout: float,
) -> tuple[int, list[dict[str, Any]]]:
    encoded = "/".join(quote(str(segment), safe="") for segment in segments)
    url = f"{BASE_URL}/{service}/{api_key}/json/{lang}/{encoded}/"
    request = Request(url, headers={"User-Agent": "bok-ecos-api-skill/1.0"})
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.load(response)
    except HTTPError as exc:
        raise EcosError(f"ECOS HTTP error {exc.code}") from None
    except URLError as exc:
        raise EcosError(f"ECOS network error: {exc.reason}") from None
    except TimeoutError:
        raise EcosError("ECOS request timed out") from None
    except json.JSONDecodeError:
        raise EcosError("ECOS returned invalid JSON") from None

    result = payload.get("RESULT")
    if isinstance(result, dict):
        code = str(result.get("CODE", "UNKNOWN"))
        message = str(result.get("MESSAGE", "ECOS request failed")).strip()
        raise EcosError(f"{code}: {message}")

    envelope = payload.get(service)
    if not isinstance(envelope, dict):
        raise EcosError(
            f"unexpected ECOS response; missing service envelope {service}"
        )
    rows = envelope.get("row", [])
    if not isinstance(rows, list):
        raise EcosError("unexpected ECOS response; row is not a list")
    total = int(envelope.get("list_total_count", len(rows)))
    return total, rows


def add_runtime_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--lang", choices=("kr", "en"), default="kr")
    parser.add_argument("--start-row", type=int, default=1)
    parser.add_argument("--end-row", type=int, default=1000)
    parser.add_argument("--key-env", default=DEFAULT_KEY_ENV)
    parser.add_argument("--env-file")
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--format", choices=("json", "csv"), default="json")
    parser.add_argument("--output", default="-")
    parser.add_argument("--dry-run", action="store_true")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Discover and query Bank of Korea ECOS statistics safely."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    tables = subparsers.add_parser("tables", help="discover statistic tables")
    tables.add_argument("--stat-code")
    tables.add_argument("--contains")
    tables.add_argument("--cycle")
    add_runtime_options(tables)
    tables.set_defaults(service="StatisticTableList")

    items = subparsers.add_parser("items", help="list items for a table")
    items.add_argument("stat_code")
    items.add_argument("--contains")
    items.add_argument("--cycle")
    add_runtime_options(items)
    items.set_defaults(service="StatisticItemList", end_row=10_000)

    series = subparsers.add_parser("series", help="retrieve observations")
    series.add_argument("stat_code")
    series.add_argument("cycle", choices=("A", "S", "Q", "M", "SM", "D"))
    series.add_argument("start_time")
    series.add_argument("end_time")
    selection = series.add_mutually_exclusive_group(required=True)
    selection.add_argument(
        "--item",
        action="append",
        help="item code; repeat in item-group order, up to four times",
    )
    selection.add_argument(
        "--all-items",
        action="store_true",
        help="query all item combinations; use only with a narrow window",
    )
    add_runtime_options(series)
    series.set_defaults(service="StatisticSearch")

    key_stats = subparsers.add_parser(
        "key-stats", help="retrieve headline indicators"
    )
    add_runtime_options(key_stats)
    key_stats.set_defaults(service="KeyStatisticList", end_row=100)

    word = subparsers.add_parser("word", help="look up a statistical term")
    word.add_argument("term")
    add_runtime_options(word)
    word.set_defaults(service="StatisticWord", end_row=100)

    meta = subparsers.add_parser("meta", help="search statistical metadata")
    meta.add_argument("data_name")
    add_runtime_options(meta)
    meta.set_defaults(service="StatisticMeta")

    return parser


def build_segments(args: argparse.Namespace) -> list[str]:
    common = [str(args.start_row), str(args.end_row)]
    if args.command == "tables":
        return common + ([args.stat_code] if args.stat_code else [])
    if args.command == "items":
        return common + [args.stat_code]
    if args.command == "series":
        if not valid_cycle_time(args.cycle, args.start_time):
            raise EcosError(
                f"start time {args.start_time!r} does not match cycle {args.cycle}"
            )
        if not valid_cycle_time(args.cycle, args.end_time):
            raise EcosError(
                f"end time {args.end_time!r} does not match cycle {args.cycle}"
            )
        if args.start_time > args.end_time:
            raise EcosError("start time must not be after end time")
        items = list(args.item or [])
        if len(items) > 4:
            raise EcosError("StatisticSearch supports at most four item codes")
        items.extend(["?"] * (4 - len(items)))
        return common + [
            args.stat_code,
            args.cycle,
            args.start_time,
            args.end_time,
            *items,
        ]
    if args.command == "key-stats":
        return common
    if args.command == "word":
        return common + [args.term]
    if args.command == "meta":
        return common + [args.data_name]
    raise EcosError(f"unsupported command: {args.command}")


def filter_rows(
    args: argparse.Namespace,
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    result = rows
    contains = getattr(args, "contains", None)
    if contains:
        needle = contains.casefold()
        if args.command == "tables":
            fields = ("STAT_CODE", "STAT_NAME", "ORG_NAME")
        else:
            fields = ("ITEM_CODE", "ITEM_NAME", "P_ITEM_NAME", "GRP_NAME")
        result = [
            row
            for row in result
            if needle
            in " ".join(str(row.get(field, "")) for field in fields).casefold()
        ]

    cycle = getattr(args, "cycle", None)
    if cycle and args.command in {"tables", "items"}:
        result = [row for row in result if row.get("CYCLE") == cycle]
    return result


def write_output(
    args: argparse.Namespace,
    service: str,
    template: str,
    total: int,
    rows: list[dict[str, Any]],
) -> None:
    if args.format == "json":
        content = json.dumps(
            {
                "service": service,
                "request": template,
                "list_total_count": total,
                "returned_count": len(rows),
                "rows": rows,
            },
            ensure_ascii=False,
            indent=2,
        )
    elif not rows:
        content = ""
    else:
        fieldnames: list[str] = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
        buffer = StringIO(newline="")
        writer = csv.DictWriter(buffer, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        content = buffer.getvalue()

    if args.output == "-":
        sys.stdout.write(content)
        if content and not content.endswith("\n"):
            sys.stdout.write("\n")
    else:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        encoding = "utf-8-sig" if args.format == "csv" else "utf-8"
        output_path.write_text(content, encoding=encoding)
        print(
            json.dumps(
                {
                    "output": str(output_path.resolve()),
                    "service": service,
                    "returned_count": len(rows),
                },
                ensure_ascii=False,
            )
        )


def configure_console_encoding() -> None:
    """Emit machine-readable CLI output as UTF-8 on Windows consoles."""

    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8")


def main() -> int:
    configure_console_encoding()
    parser = build_parser()
    args = parser.parse_args()
    try:
        validate_row_window(args.start_row, args.end_row)
        segments = build_segments(args)
        template = redacted_template(args.service, args.lang, segments)
        if args.dry_run:
            write_output(args, args.service, template, 0, [])
            return 0

        api_key = load_api_key(args.key_env, args.env_file)
        total, rows = request_json(
            args.service,
            api_key,
            args.lang,
            segments,
            args.timeout,
        )
        rows = filter_rows(args, rows)
        write_output(args, args.service, template, total, rows)
        return 0
    except EcosError as exc:
        print(f"ECOS error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())