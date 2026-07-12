"""
YAML Configuration Loader for TNIC Module

This module provides a configuration loader that reads YAML files from the config/
directory and supports environment variable substitution.

Usage:
    from tnic.config import TNICConfig

    config = TNICConfig()
    min_words = config.get("hp.filtering.min_words_per_firm")
    stopwords = config.get("nlp.stopwords")
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml


class TNICConfig:
    """
    Configuration loader for TNIC pipeline.

    Loads YAML configuration files and provides dot-notation access to nested values.
    Supports environment variable substitution using ${VAR_NAME} syntax.

    Attributes:
        config_dir: Path to directory containing YAML config files
        hp: Hoberg & Phillips methodology parameters
        nlp: Korean NLP settings
        paths: File paths and directories
        mongodb: MongoDB connection settings
    """

    def __init__(self, config_dir: Optional[Union[str, Path]] = None):
        """
        Initialize configuration loader.

        Args:
            config_dir: Path to config directory. If None, uses project root's config/
        """
        if config_dir is None:
            # Default to config/ in project root
            project_root = Path(__file__).parent.parent
            config_dir = project_root / "config"

        self.config_dir = Path(config_dir)

        if not self.config_dir.exists():
            raise FileNotFoundError(
                f"Config directory not found: {self.config_dir}. "
                f"Please create config/ directory with YAML files."
            )

        # Load all configuration files
        self.hp = self._load_yaml("hoberg_phillips.yaml")
        self.nlp = self._load_yaml("korean_nlp.yaml")
        self.paths = self._load_yaml("paths.yaml")
        self.mongodb = self._load_yaml("mongodb.yaml")

        # Create merged config for dot-notation access
        self._config = {
            "hp": self.hp,
            "nlp": self.nlp,
            "paths": self.paths,
            "mongodb": self.mongodb,
        }

    def _load_yaml(self, filename: str) -> Dict[str, Any]:
        """
        Load a YAML file and substitute environment variables.

        Args:
            filename: Name of YAML file in config directory

        Returns:
            Dictionary containing configuration values

        Raises:
            FileNotFoundError: If YAML file doesn't exist
            yaml.YAMLError: If YAML parsing fails
        """
        filepath = self.config_dir / filename

        if not filepath.exists():
            raise FileNotFoundError(
                f"Config file not found: {filepath}. "
                f"Please create {filename} in config/ directory."
            )

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Substitute environment variables
        content = self._substitute_env_vars(content)

        # Parse YAML
        try:
            config = yaml.safe_load(content)
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Error parsing {filename}: {e}")

        return config if config is not None else {}

    def _substitute_env_vars(self, content: str) -> str:
        """
        Substitute environment variables in YAML content.

        Replaces ${VAR_NAME} or $VAR_NAME with environment variable values.
        If variable is not set, raises an error.

        Args:
            content: YAML content string

        Returns:
            Content with environment variables substituted

        Raises:
            ValueError: If referenced environment variable is not set
        """
        # Pattern: ${VAR_NAME} or $VAR_NAME
        pattern = r'\$\{([^}]+)\}|\$([A-Za-z_][A-Za-z0-9_]*)'

        def replacer(match):
            var_name = match.group(1) or match.group(2)
            value = os.environ.get(var_name)

            if value is None:
                raise ValueError(
                    f"Environment variable '{var_name}' is not set. "
                    f"Please set it in your .env file or environment."
                )

            return value

        return re.sub(pattern, replacer, content)

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot-notation path.

        Args:
            key_path: Dot-separated path to config value
                     Examples: "hp.filtering.min_words_per_firm"
                              "nlp.stopwords"
                              "paths.outputs.corpus.base_dir"
            default: Default value if key not found

        Returns:
            Configuration value at specified path, or default if not found

        Examples:
            >>> config = TNICConfig()
            >>> config.get("hp.filtering.min_words_per_firm")
            20
            >>> config.get("nlp.pos_tags")
            ['NNG', 'NNP', 'NNB']
        """
        keys = key_path.split('.')
        value = self._config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def format_path(self, key_path: str, **kwargs) -> str:
        """
        Get a path from config and format it with variables.

        Useful for paths that contain placeholders like {year}.

        Args:
            key_path: Dot-separated path to path template
            **kwargs: Variables to substitute in path template

        Returns:
            Formatted path string

        Examples:
            >>> config = TNICConfig()
            >>> config.format_path("paths.outputs.corpus.firm_word_sets", year=2010)
            'data/korean_texts/by_year/2010/firm_word_sets_2010.parquet'
        """
        path_template = self.get(key_path)

        if path_template is None:
            raise KeyError(f"Path not found in config: {key_path}")

        if not isinstance(path_template, str):
            raise TypeError(
                f"Path at {key_path} is not a string: {type(path_template)}"
            )

        return path_template.format(**kwargs)

    def get_year_range(self, mode: str = "full") -> range:
        """
        Get year range for processing.

        Args:
            mode: One of "full" (all years), "pilot" (test years only)

        Returns:
            Range object for years to process

        Examples:
            >>> config = TNICConfig()
            >>> list(config.get_year_range("pilot"))
            [2010, 2011]
            >>> list(config.get_year_range("full"))
            [2010, 2011, 2012, ..., 2025]
        """
        if mode == "pilot":
            pilot_years = self.get("paths.years.pilot", [2010, 2011])
            return range(min(pilot_years), max(pilot_years) + 1)

        elif mode == "full":
            start = self.get("paths.years.start", 2010)
            end = self.get("paths.years.end", 2025)
            return range(start, end + 1)

        else:
            raise ValueError(
                f"Invalid mode: {mode}. Must be 'full' or 'pilot'."
            )

    def __repr__(self) -> str:
        """String representation of config object."""
        return (
            f"TNICConfig(config_dir='{self.config_dir}')\n"
            f"  - hp: {len(self.hp)} sections\n"
            f"  - nlp: {len(self.nlp)} sections\n"
            f"  - paths: {len(self.paths)} sections\n"
            f"  - mongodb: {len(self.mongodb)} sections"
        )


# Singleton instance for convenience
_default_config: Optional[TNICConfig] = None


def get_config(reload: bool = False) -> TNICConfig:
    """
    Get the default configuration instance (singleton).

    Args:
        reload: If True, reload configuration from files

    Returns:
        TNICConfig instance

    Examples:
        >>> from tnic.config import get_config
        >>> config = get_config()
        >>> min_words = config.get("hp.filtering.min_words_per_firm")
    """
    global _default_config

    if _default_config is None or reload:
        _default_config = TNICConfig()

    return _default_config
