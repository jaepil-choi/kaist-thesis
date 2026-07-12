"""
Utility Functions for TNIC Module

Provides shared utilities for logging, file I/O, date handling, and progress tracking.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd


# ============================================================================
# Logging Setup
# ============================================================================

def setup_logger(
    name: str,
    level: Union[int, str] = logging.INFO,
    log_file: Optional[Path] = None,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Set up a logger with console and optional file output.

    Args:
        name: Logger name (typically __name__)
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional path to log file
        format_string: Custom format string for log messages

    Returns:
        Configured logger instance

    Examples:
        >>> logger = setup_logger(__name__)
        >>> logger.info("Processing started")

        >>> logger = setup_logger(__name__, level="DEBUG", log_file="output.log")
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    logger.handlers = []

    # Default format
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    formatter = logging.Formatter(format_string)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file is not None:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# ============================================================================
# File I/O Utilities
# ============================================================================

def ensure_dir(path: Union[str, Path]) -> Path:
    """
    Ensure directory exists, creating it if necessary.

    Args:
        path: Path to directory

    Returns:
        Path object for the directory

    Examples:
        >>> ensure_dir("data/output/2010")
        PosixPath('data/output/2010')
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def ensure_parent_dir(filepath: Union[str, Path]) -> Path:
    """
    Ensure parent directory of a file exists.

    Args:
        filepath: Path to file

    Returns:
        Path object for the file

    Examples:
        >>> ensure_parent_dir("data/output/2010/matrix.npz")
        PosixPath('data/output/2010/matrix.npz')
    """
    filepath = Path(filepath)
    if filepath.parent != Path("."):
        filepath.parent.mkdir(parents=True, exist_ok=True)
    return filepath


def get_file_size_mb(filepath: Union[str, Path]) -> float:
    """
    Get file size in megabytes.

    Args:
        filepath: Path to file

    Returns:
        File size in MB

    Examples:
        >>> get_file_size_mb("data/matrix.npz")
        42.3
    """
    filepath = Path(filepath)
    if not filepath.exists():
        return 0.0
    return filepath.stat().st_size / (1024 * 1024)


# ============================================================================
# Date and Time Utilities
# ============================================================================

def format_timestamp(dt: Optional[datetime] = None) -> str:
    """
    Format datetime as string for filenames and logs.

    Args:
        dt: Datetime object. If None, uses current time.

    Returns:
        Formatted timestamp string (YYYY-MM-DD_HH-MM-SS)

    Examples:
        >>> format_timestamp()
        '2024-01-15_14-30-45'
    """
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%Y-%m-%d_%H-%M-%S")


def parse_year_from_date(date: Union[str, pd.Timestamp]) -> int:
    """
    Extract year from date string or Timestamp.

    Args:
        date: Date as string or pandas Timestamp

    Returns:
        Year as integer

    Examples:
        >>> parse_year_from_date("2010-12-31")
        2010
        >>> parse_year_from_date(pd.Timestamp("2010-12-31"))
        2010
    """
    if isinstance(date, str):
        return int(date[:4])
    elif isinstance(date, pd.Timestamp):
        return date.year
    else:
        raise TypeError(f"Unsupported date type: {type(date)}")


# ============================================================================
# Stock Code Formatting
# ============================================================================

def format_stock_code(code: Union[str, int]) -> str:
    """
    Format stock code as 6-digit string with leading zeros.

    Korean stock codes are 6 digits (e.g., "000020" for 동화약품).

    Args:
        code: Stock code as string or integer

    Returns:
        6-digit stock code string

    Examples:
        >>> format_stock_code("20")
        '000020'
        >>> format_stock_code(20)
        '000020'
        >>> format_stock_code("000020")
        '000020'
    """
    if isinstance(code, int):
        code = str(code)

    # Remove any whitespace
    code = code.strip()

    # Pad to 6 digits
    return code.zfill(6)


def validate_stock_code(code: str) -> bool:
    """
    Validate that stock code is 6 digits.

    Args:
        code: Stock code string

    Returns:
        True if valid, False otherwise

    Examples:
        >>> validate_stock_code("000020")
        True
        >>> validate_stock_code("20")
        False
        >>> validate_stock_code("abc123")
        False
    """
    return len(code) == 6 and code.isdigit()


# ============================================================================
# Progress Tracking
# ============================================================================

class ProgressTracker:
    """
    Simple progress tracker for iterative operations.

    Examples:
        >>> tracker = ProgressTracker(total=1000, desc="Processing firms")
        >>> for i in range(1000):
        ...     # do work
        ...     tracker.update()
        Processing firms: 100/1000 (10.0%) - Elapsed: 0:00:05 - ETA: 0:00:45
    """

    def __init__(
        self,
        total: int,
        desc: str = "Progress",
        log_frequency: int = 100,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize progress tracker.

        Args:
            total: Total number of items to process
            desc: Description of operation
            log_frequency: Log progress every N items
            logger: Logger instance (if None, creates default)
        """
        self.total = total
        self.desc = desc
        self.log_frequency = log_frequency
        self.logger = logger or setup_logger(__name__)

        self.current = 0
        self.start_time = datetime.now()
        self.last_log_time = self.start_time

    def update(self, n: int = 1):
        """
        Update progress by n items.

        Args:
            n: Number of items processed
        """
        self.current += n

        # Log if reached frequency or completed
        if (self.current % self.log_frequency == 0) or (self.current == self.total):
            self._log_progress()

    def _log_progress(self):
        """Log current progress."""
        now = datetime.now()
        elapsed = now - self.start_time
        elapsed_seconds = elapsed.total_seconds()

        # Calculate percentage
        pct = (self.current / self.total) * 100

        # Estimate remaining time
        if self.current > 0:
            rate = self.current / elapsed_seconds
            remaining_items = self.total - self.current
            eta_seconds = remaining_items / rate
            eta = f"{int(eta_seconds // 60)}:{int(eta_seconds % 60):02d}"
        else:
            eta = "??:??"

        # Format elapsed time
        elapsed_str = f"{int(elapsed_seconds // 60)}:{int(elapsed_seconds % 60):02d}"

        self.logger.info(
            f"{self.desc}: {self.current}/{self.total} ({pct:.1f}%) - "
            f"Elapsed: {elapsed_str} - ETA: {eta}"
        )


# ============================================================================
# Dictionary Utilities
# ============================================================================

def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """
    Flatten nested dictionary with dot-separated keys.

    Args:
        d: Dictionary to flatten
        parent_key: Prefix for keys (used in recursion)
        sep: Separator for nested keys

    Returns:
        Flattened dictionary

    Examples:
        >>> d = {"a": {"b": 1, "c": 2}, "d": 3}
        >>> flatten_dict(d)
        {'a.b': 1, 'a.c': 2, 'd': 3}
    """
    items = []

    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k

        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))

    return dict(items)


def unflatten_dict(d: Dict[str, Any], sep: str = '.') -> Dict[str, Any]:
    """
    Unflatten dictionary with dot-separated keys into nested dict.

    Args:
        d: Flattened dictionary
        sep: Separator used in keys

    Returns:
        Nested dictionary

    Examples:
        >>> d = {'a.b': 1, 'a.c': 2, 'd': 3}
        >>> unflatten_dict(d)
        {'a': {'b': 1, 'c': 2}, 'd': 3}
    """
    result = {}

    for key, value in d.items():
        parts = key.split(sep)
        d_temp = result

        for part in parts[:-1]:
            if part not in d_temp:
                d_temp[part] = {}
            d_temp = d_temp[part]

        d_temp[parts[-1]] = value

    return result


# ============================================================================
# Data Validation
# ============================================================================

def check_required_columns(
    df: pd.DataFrame,
    required_columns: List[str],
    df_name: str = "DataFrame"
) -> None:
    """
    Check that DataFrame contains required columns.

    Args:
        df: DataFrame to check
        required_columns: List of required column names
        df_name: Name of DataFrame for error message

    Raises:
        ValueError: If required columns are missing

    Examples:
        >>> df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        >>> check_required_columns(df, ["a", "b"])  # OK
        >>> check_required_columns(df, ["a", "c"])  # Raises ValueError
    """
    missing = set(required_columns) - set(df.columns)

    if missing:
        raise ValueError(
            f"{df_name} is missing required columns: {sorted(missing)}\n"
            f"Available columns: {sorted(df.columns)}"
        )


def check_data_completeness(
    df: pd.DataFrame,
    columns: Optional[List[str]] = None,
    threshold: float = 1.0,
    df_name: str = "DataFrame"
) -> Dict[str, float]:
    """
    Check data completeness (non-null percentage) for DataFrame columns.

    Args:
        df: DataFrame to check
        columns: Columns to check (if None, checks all columns)
        threshold: Minimum required completeness (0.0 to 1.0)
        df_name: Name of DataFrame for error message

    Returns:
        Dictionary mapping column names to completeness percentages

    Raises:
        ValueError: If any column is below threshold

    Examples:
        >>> df = pd.DataFrame({"a": [1, 2, None], "b": [1, 2, 3]})
        >>> check_data_completeness(df, threshold=0.5)
        {'a': 0.6667, 'b': 1.0}
    """
    if columns is None:
        columns = df.columns.tolist()

    completeness = {}
    issues = []

    for col in columns:
        pct_complete = df[col].notna().sum() / len(df)
        completeness[col] = pct_complete

        if pct_complete < threshold:
            issues.append(
                f"  {col}: {pct_complete:.1%} complete (threshold: {threshold:.1%})"
            )

    if issues:
        raise ValueError(
            f"{df_name} has columns below completeness threshold:\n" +
            "\n".join(issues)
        )

    return completeness


# ============================================================================
# Memory Utilities
# ============================================================================

def format_bytes(num_bytes: int) -> str:
    """
    Format bytes as human-readable string.

    Args:
        num_bytes: Number of bytes

    Returns:
        Formatted string (e.g., "1.2 MB")

    Examples:
        >>> format_bytes(1024)
        '1.0 KB'
        >>> format_bytes(1024 ** 2)
        '1.0 MB'
        >>> format_bytes(1536 * 1024)
        '1.5 MB'
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if num_bytes < 1024.0:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} PB"
