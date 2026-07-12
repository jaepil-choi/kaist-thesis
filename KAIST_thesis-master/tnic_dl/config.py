"""
Configuration management for TNIC-DL module.

Centralized configuration loading and access for all TNIC-DL settings.
Loads from config/tnic_dl.yaml and provides type-safe access methods.
"""

import yaml
from pathlib import Path
from typing import Any, Optional, List, Dict
from dataclasses import dataclass


class DotDict(dict):
    """Dictionary with dot-notation access."""

    def __getattr__(self, key):
        try:
            value = self[key]
            if isinstance(value, dict):
                return DotDict(value)
            return value
        except KeyError:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{key}'")

    def __setattr__(self, key, value):
        self[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get value using dot notation (e.g., 'tnic_dl.autoencoder.latent_dim')."""
        keys = key.split('.')
        value = self
        for k in keys:
            if isinstance(value, dict):
                # Use dict.__getitem__ to avoid recursion
                try:
                    value = dict.__getitem__(value, k)
                except KeyError:
                    return default
            else:
                return default
        return value


@dataclass
class AutoencoderConfig:
    """Autoencoder architecture and training configuration."""
    # Architecture
    input_dim: int = 2000
    encoder_hidden: List[int] = None
    latent_dim: int = 10
    decoder_hidden: List[int] = None
    output_dim: int = 2000

    # Training
    learning_rate: float = 0.001
    batch_size: int = 64
    epochs: int = 100
    early_stopping_patience: int = 10
    validation_split: float = 0.1
    device: str = "cpu"
    save_best_only: bool = True
    verbose: bool = True

    def __post_init__(self):
        if self.encoder_hidden is None:
            self.encoder_hidden = [500, 125]
        if self.decoder_hidden is None:
            self.decoder_hidden = [125, 500]


@dataclass
class VocabularyConfig:
    """Vocabulary building configuration."""
    top_n_words: int = 2000
    max_document_frequency: float = 0.20
    min_document_frequency: int = 2
    min_words_per_document: int = 20
    exclude_geographic: bool = True
    save_word_frequencies: bool = True


@dataclass
class ClusteringConfig:
    """Clustering configuration."""
    algorithm: str = "spherical_kmeans"
    n_clusters: int = 25
    max_iter: int = 300
    n_init: int = 10
    random_state: int = 42
    tolerance: float = 0.0001


@dataclass
class SimilarityConfig:
    """Similarity computation configuration."""
    metric: str = "cosine"
    threshold: float = 0.20
    save_sparse: bool = True
    batch_size: int = 1000
    min_similarity: float = 0.0


@dataclass
class PathsConfig:
    """Output paths configuration."""
    base_dir: str = "data/korean_tnic_dl"
    models_dir: str = None
    training_logs_dir: str = None
    embeddings_dir: str = None
    similarity_dir: str = None
    figures_dir: str = None
    peer_groups_dir: str = None
    input_noun_data: str = None

    def __post_init__(self):
        # Compute derived paths from base_dir if not explicitly specified
        if self.models_dir is None:
            self.models_dir = f"{self.base_dir}/models"

        if self.training_logs_dir is None:
            self.training_logs_dir = f"{self.base_dir}/models/training_logs"

        if self.embeddings_dir is None:
            self.embeddings_dir = f"{self.base_dir}/by_year/{{year}}"

        if self.similarity_dir is None:
            self.similarity_dir = f"{self.base_dir}/by_year/{{year}}"

        if self.figures_dir is None:
            self.figures_dir = f"{self.base_dir}/outputs/figures"

        if self.peer_groups_dir is None:
            self.peer_groups_dir = f"{self.base_dir}/outputs/peer_groups"

        if self.input_noun_data is None:
            self.input_noun_data = "data/korean_texts/by_year/{year}/firm_word_sets_{year}.parquet"


class TNICDLConfig:
    """
    Centralized configuration manager for TNIC-DL.

    Singleton pattern ensures configuration is loaded once and shared across modules.
    """

    _instance = None
    _config_loaded = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TNICDLConfig, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._config_loaded:
            self._load_config()
            TNICDLConfig._config_loaded = True

    def _load_config(self):
        """Load configuration from YAML file."""
        config_path = Path("config/tnic_dl.yaml")

        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            raw_config = yaml.safe_load(f)

        # Store raw config for backward compatibility
        self._raw_config = DotDict(raw_config)

        # Parse into typed dataclasses
        tnic_dl = raw_config.get('tnic_dl', {})

        # Autoencoder config
        ae_config = tnic_dl.get('autoencoder', {})
        arch = ae_config.get('architecture', {})
        train = ae_config.get('training', {})

        self.autoencoder = AutoencoderConfig(
            input_dim=arch.get('input_dim', 2000),
            encoder_hidden=arch.get('encoder_hidden', [500, 125]),
            latent_dim=arch.get('latent_dim', 10),
            decoder_hidden=arch.get('decoder_hidden', [125, 500]),
            output_dim=arch.get('output_dim', 2000),
            learning_rate=train.get('learning_rate', 0.001),
            batch_size=train.get('batch_size', 64),
            epochs=train.get('epochs', 100),
            early_stopping_patience=train.get('early_stopping_patience', 10),
            validation_split=train.get('validation_split', 0.1),
            device=train.get('device', 'cpu'),
            save_best_only=train.get('save_best_only', True),
            verbose=train.get('verbose', True),
        )

        # Vocabulary config
        vocab_config = tnic_dl.get('vocabulary', {})
        self.vocabulary = VocabularyConfig(
            top_n_words=vocab_config.get('top_n_words', 2000),
            max_document_frequency=vocab_config.get('max_document_frequency', 0.20),
            min_document_frequency=vocab_config.get('min_document_frequency', 2),
            min_words_per_document=vocab_config.get('min_words_per_document', 20),
            exclude_geographic=vocab_config.get('exclude_geographic', True),
            save_word_frequencies=vocab_config.get('save_word_frequencies', True),
        )

        # Clustering config
        cluster_config = tnic_dl.get('clustering', {})
        self.clustering = ClusteringConfig(
            algorithm=cluster_config.get('algorithm', 'spherical_kmeans'),
            n_clusters=cluster_config.get('n_clusters', 25),
            max_iter=cluster_config.get('max_iter', 300),
            n_init=cluster_config.get('n_init', 10),
            random_state=cluster_config.get('random_state', 42),
            tolerance=cluster_config.get('tolerance', 0.0001),
        )

        # Similarity config
        sim_config = tnic_dl.get('similarity', {})
        self.similarity = SimilarityConfig(
            metric=sim_config.get('metric', 'cosine'),
            threshold=sim_config.get('threshold', 0.20),
            save_sparse=sim_config.get('save_sparse', True),
            batch_size=sim_config.get('batch_size', 1000),
            min_similarity=sim_config.get('min_similarity', 0.0),
        )

        # Paths config
        paths_config = tnic_dl.get('paths', {})
        self.paths = PathsConfig(
            base_dir=paths_config.get('base_dir', 'data/korean_tnic_dl'),
            models_dir=paths_config.get('models_dir'),
            training_logs_dir=paths_config.get('training_logs_dir'),
            embeddings_dir=paths_config.get('embeddings_dir'),
            similarity_dir=paths_config.get('similarity_dir'),
            figures_dir=paths_config.get('figures_dir'),
            peer_groups_dir=paths_config.get('peer_groups_dir'),
            input_noun_data=paths_config.get('input_noun_data'),
        )

    def get_raw(self, key: str, default: Any = None) -> Any:
        """
        Get raw configuration value using dot notation (backward compatibility).

        Args:
            key: Dot-notation key (e.g., "tnic_dl.autoencoder.latent_dim")
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self._raw_config.get(key, default)

    def reload(self):
        """Reload configuration from file."""
        self._load_config()


# Global configuration instance
_config_instance = None


def get_config() -> TNICDLConfig:
    """
    Get global TNIC-DL configuration instance.

    Returns:
        TNICDLConfig singleton instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = TNICDLConfig()
    return _config_instance


def get_dl_config(key: str, default: Any = None) -> Any:
    """
    Get TNIC-DL configuration value using dot notation (backward compatibility).

    Args:
        key: Dot-notation key (e.g., "tnic_dl.autoencoder.latent_dim")
        default: Default value if key not found

    Returns:
        Configuration value or default
    """
    config = get_config()
    return config.get_raw(key, default)


def get_output_path(year: int, filename: str, create_dir: bool = True) -> Path:
    """
    Get output path for TNIC-DL results.

    Args:
        year: Year for the output
        filename: Filename (e.g., "embeddings_autoencoder_2010.npy")
        create_dir: Whether to create the directory if it doesn't exist

    Returns:
        Path object for the output file
    """
    config = get_config()
    base_dir = Path(config.paths.base_dir)
    year_dir = base_dir / "by_year" / str(year)

    if create_dir:
        year_dir.mkdir(parents=True, exist_ok=True)

    return year_dir / filename


def get_model_path(filename: str, create_dir: bool = True) -> Path:
    """
    Get path for saved models.

    Args:
        filename: Model filename (e.g., "autoencoder_2010.pt")
        create_dir: Whether to create the directory if it doesn't exist

    Returns:
        Path object for the model file
    """
    config = get_config()
    models_dir = Path(config.paths.models_dir)

    if create_dir:
        models_dir.mkdir(parents=True, exist_ok=True)

    return models_dir / filename


def get_input_path(year: int, data_type: str = "noun") -> Path:
    """
    Get path to existing input data from traditional TNIC pipeline.

    Args:
        year: Year of the data
        data_type: Type of data ("noun" or "text")

    Returns:
        Path object for the input file
    """
    if data_type == "noun":
        # Existing noun extraction data
        return Path(f"data/korean_texts/by_year/{year}/firm_word_sets_{year}.parquet")
    elif data_type == "text":
        # Raw business descriptions
        return Path("data/korean_texts/business_descriptions_filled.parquet")
    else:
        raise ValueError(f"Unknown data_type: {data_type}")
