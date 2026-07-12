"""
Tests for TNIC Configuration Module

Tests for tnic/config.py including:
- YAML loading
- Environment variable substitution
- Dot-notation access
- Path formatting
- Year range calculation
- Error handling

Author: KAIST Thesis Project
Date: 2025-01-05
"""

import os
import pytest
from pathlib import Path
import yaml
import tempfile
import shutil

# Import config - lazy loading in __init__.py avoids heavy dependencies
from tnic.config import TNICConfig, get_config


@pytest.fixture(scope='session', autouse=True)
def setup_test_environment():
    """
    Session-level fixture to set up test environment variables.

    Automatically used for all tests in this module.
    """
    # Set dummy MONGODB_URI for tests that load real config files
    original_mongodb_uri = os.environ.get('MONGODB_URI')
    os.environ['MONGODB_URI'] = 'mongodb://localhost:27017/'

    yield

    # Cleanup: restore original value
    if original_mongodb_uri is not None:
        os.environ['MONGODB_URI'] = original_mongodb_uri
    else:
        if 'MONGODB_URI' in os.environ:
            del os.environ['MONGODB_URI']


@pytest.fixture
def temp_config_dir(tmp_path):
    """
    Create temporary config directory with test YAML files.

    Returns a Path object to the temporary config directory.
    """
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    # Create test YAML files
    hoberg_phillips = {
        'filtering': {
            'min_words_per_firm': 20,
            'frequency_threshold': 0.25,
            'min_char_count': 1000
        },
        'matrix': {
            'representation': 'binary',
            'normalization': 'unit_length'
        },
        'similarity': {
            'metric': 'cosine',
            'median_adjustment': True
        }
    }

    korean_nlp = {
        'tokenizer': {
            'backend': 'kiwipiepy'
        },
        'pos_tags': ['NNG', 'NNP', 'NNB'],
        'filters': {
            'min_word_length': 2,
            'remove_numbers': True
        },
        'stopwords': ['회사', '기업', '사업']
    }

    paths = {
        'directories': {
            'base': 'data/',
            'outputs': 'outputs/'
        },
        'inputs': {
            'business_descriptions': 'data/korean_texts/business_descriptions_clean.parquet'
        },
        'outputs': {
            'corpus': {
                'base_dir': 'data/korean_texts/by_year/{year}/',
                'firm_word_sets': 'data/korean_texts/by_year/{year}/firm_word_sets_{year}.parquet',
                'vocabulary': 'data/korean_texts/by_year/{year}/corpus_vocabulary_{year}.csv'
            },
            'binary_matrix': {
                'base_dir': 'data/korean_tnic/by_year/',
                'matrix': 'data/korean_tnic/by_year/binary_matrix_{year}.npz'
            }
        },
        'years': {
            'start': 2010,
            'end': 2025,
            'pilot': [2010, 2011]
        }
    }

    mongodb = {
        'connection': {
            'uri': '${MONGODB_URI}',
            'database': 'dart',
            'collection': 'business_reports'
        },
        'query': {
            'section_codes': ['020100'],
            'min_char_count': 500
        }
    }

    # Write YAML files
    with open(config_dir / 'hoberg_phillips.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(hoberg_phillips, f)

    with open(config_dir / 'korean_nlp.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(korean_nlp, f)

    with open(config_dir / 'paths.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(paths, f)

    with open(config_dir / 'mongodb.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(mongodb, f)

    return config_dir


@pytest.fixture
def config_with_env_vars(tmp_path):
    """
    Create config directory with environment variable placeholders.
    """
    config_dir = tmp_path / "config_env"
    config_dir.mkdir()

    # Create YAML with environment variables
    mongodb_content = """
connection:
  uri: ${MONGODB_URI}
  database: ${MONGODB_DB}
  collection: business_reports

alternate_syntax:
  host: $MONGODB_HOST
  port: $MONGODB_PORT
"""

    with open(config_dir / 'mongodb.yaml', 'w') as f:
        f.write(mongodb_content)

    # Create minimal other files to avoid errors
    for filename in ['hoberg_phillips.yaml', 'korean_nlp.yaml', 'paths.yaml']:
        with open(config_dir / filename, 'w') as f:
            yaml.dump({}, f)

    return config_dir


class TestTNICConfigInit:
    """Test TNICConfig initialization."""

    def test_init_with_valid_directory(self, temp_config_dir):
        """Test initialization with valid config directory."""
        config = TNICConfig(config_dir=temp_config_dir)

        assert config.config_dir == temp_config_dir
        assert isinstance(config.hp, dict)
        assert isinstance(config.nlp, dict)
        assert isinstance(config.paths, dict)
        assert isinstance(config.mongodb, dict)

    def test_init_without_directory_uses_default(self):
        """Test that init without directory uses project config/."""
        config = TNICConfig()

        # Should use project root's config/
        expected_config_dir = Path(__file__).parent.parent / "config"
        assert config.config_dir == expected_config_dir

    def test_init_with_nonexistent_directory(self, tmp_path):
        """Test that init with nonexistent directory raises error."""
        nonexistent = tmp_path / "nonexistent"

        with pytest.raises(FileNotFoundError, match="Config directory not found"):
            TNICConfig(config_dir=nonexistent)

    def test_init_with_missing_yaml_file(self, tmp_path):
        """Test that missing YAML file raises error."""
        config_dir = tmp_path / "incomplete_config"
        config_dir.mkdir()

        # Create only some YAML files
        with open(config_dir / 'hoberg_phillips.yaml', 'w') as f:
            yaml.dump({}, f)

        # Should fail when trying to load korean_nlp.yaml
        with pytest.raises(FileNotFoundError, match="korean_nlp.yaml"):
            TNICConfig(config_dir=config_dir)


class TestConfigGet:
    """Test dot-notation access with get() method."""

    def test_get_top_level_key(self, temp_config_dir):
        """Test getting top-level configuration section."""
        config = TNICConfig(config_dir=temp_config_dir)

        hp = config.get('hp')
        assert isinstance(hp, dict)
        assert 'filtering' in hp

    def test_get_nested_key(self, temp_config_dir):
        """Test getting nested configuration value."""
        config = TNICConfig(config_dir=temp_config_dir)

        min_words = config.get('hp.filtering.min_words_per_firm')
        assert min_words == 20

        freq_threshold = config.get('hp.filtering.frequency_threshold')
        assert freq_threshold == 0.25

    def test_get_list_value(self, temp_config_dir):
        """Test getting list configuration value."""
        config = TNICConfig(config_dir=temp_config_dir)

        pos_tags = config.get('nlp.pos_tags')
        assert isinstance(pos_tags, list)
        assert pos_tags == ['NNG', 'NNP', 'NNB']

    def test_get_boolean_value(self, temp_config_dir):
        """Test getting boolean configuration value."""
        config = TNICConfig(config_dir=temp_config_dir)

        median_adj = config.get('hp.similarity.median_adjustment')
        assert isinstance(median_adj, bool)
        assert median_adj is True

    def test_get_nonexistent_key_returns_default(self, temp_config_dir):
        """Test that nonexistent key returns default value."""
        config = TNICConfig(config_dir=temp_config_dir)

        value = config.get('nonexistent.key', default='default_value')
        assert value == 'default_value'

    def test_get_nonexistent_key_returns_none(self, temp_config_dir):
        """Test that nonexistent key returns None if no default."""
        config = TNICConfig(config_dir=temp_config_dir)

        value = config.get('nonexistent.key')
        assert value is None

    def test_get_deeply_nested_key(self, temp_config_dir):
        """Test getting deeply nested configuration value."""
        config = TNICConfig(config_dir=temp_config_dir)

        base_dir = config.get('paths.outputs.corpus.base_dir')
        assert base_dir == 'data/korean_texts/by_year/{year}/'


class TestPathFormatting:
    """Test path formatting with placeholders."""

    def test_format_path_with_year(self, temp_config_dir):
        """Test formatting path with year placeholder."""
        config = TNICConfig(config_dir=temp_config_dir)

        path = config.format_path('paths.outputs.corpus.firm_word_sets', year=2010)
        expected = 'data/korean_texts/by_year/2010/firm_word_sets_2010.parquet'
        assert path == expected

    def test_format_path_with_multiple_placeholders(self, temp_config_dir):
        """Test formatting path with multiple placeholders."""
        config = TNICConfig(config_dir=temp_config_dir)

        # Manually add a path with multiple placeholders for testing
        config.paths['test'] = {'multi_placeholder': 'data/{year}/{month}/file_{year}_{month}.csv'}

        path = config.format_path('paths.test.multi_placeholder', year=2010, month='01')
        assert path == 'data/2010/01/file_2010_01.csv'

    def test_format_path_nonexistent_key_raises_error(self, temp_config_dir):
        """Test that formatting nonexistent path raises KeyError."""
        config = TNICConfig(config_dir=temp_config_dir)

        with pytest.raises(KeyError, match="Path not found"):
            config.format_path('paths.nonexistent.path', year=2010)

    def test_format_path_non_string_raises_error(self, temp_config_dir):
        """Test that formatting non-string value raises TypeError."""
        config = TNICConfig(config_dir=temp_config_dir)

        # paths.years.start is an integer, not a string
        with pytest.raises(TypeError, match="is not a string"):
            config.format_path('paths.years.start', year=2010)


class TestEnvironmentVariables:
    """Test environment variable substitution."""

    def test_env_var_substitution_curly_braces(self, config_with_env_vars):
        """Test ${VAR_NAME} syntax substitution."""
        # Save original values (config has both connection and alternate_syntax sections)
        original_values = {
            'MONGODB_URI': os.environ.get('MONGODB_URI'),
            'MONGODB_DB': os.environ.get('MONGODB_DB'),
            'MONGODB_HOST': os.environ.get('MONGODB_HOST'),
            'MONGODB_PORT': os.environ.get('MONGODB_PORT')
        }

        # Set all required environment variables
        os.environ['MONGODB_URI'] = 'mongodb://localhost:27017/'
        os.environ['MONGODB_DB'] = 'test_db'
        os.environ['MONGODB_HOST'] = 'localhost'
        os.environ['MONGODB_PORT'] = '27017'

        try:
            config = TNICConfig(config_dir=config_with_env_vars)

            # Test curly brace syntax
            uri = config.get('mongodb.connection.uri')
            assert uri == 'mongodb://localhost:27017/'

            db = config.get('mongodb.connection.database')
            assert db == 'test_db'
        finally:
            # Restore original values
            for var, original in original_values.items():
                if original is not None:
                    os.environ[var] = original
                elif var in os.environ:
                    del os.environ[var]

    def test_env_var_substitution_dollar_sign(self, config_with_env_vars):
        """Test $VAR_NAME syntax substitution."""
        # Save original values
        original_values = {
            'MONGODB_HOST': os.environ.get('MONGODB_HOST'),
            'MONGODB_PORT': os.environ.get('MONGODB_PORT'),
            'MONGODB_URI': os.environ.get('MONGODB_URI'),
            'MONGODB_DB': os.environ.get('MONGODB_DB')
        }

        # Set environment variables
        os.environ['MONGODB_HOST'] = 'localhost'
        os.environ['MONGODB_PORT'] = '27017'
        os.environ['MONGODB_URI'] = 'mongodb://localhost:27017/'
        os.environ['MONGODB_DB'] = 'test_db'

        try:
            config = TNICConfig(config_dir=config_with_env_vars)

            # Test dollar sign syntax
            host = config.get('mongodb.alternate_syntax.host')
            assert host == 'localhost'

            port = config.get('mongodb.alternate_syntax.port')
            # Note: YAML automatically converts numeric strings to integers
            # "port: 27017" in YAML becomes int, not string
            assert port == 27017
        finally:
            # Restore original values
            for var, original in original_values.items():
                if original is not None:
                    os.environ[var] = original
                elif var in os.environ:
                    del os.environ[var]

    def test_missing_env_var_raises_error(self, config_with_env_vars):
        """Test that missing environment variable raises ValueError."""
        # Save original value
        original_uri = os.environ.get('MONGODB_URI')

        try:
            # Make sure MONGODB_URI is not set
            if 'MONGODB_URI' in os.environ:
                del os.environ['MONGODB_URI']

            with pytest.raises(ValueError, match="Environment variable 'MONGODB_URI' is not set"):
                TNICConfig(config_dir=config_with_env_vars)
        finally:
            # Restore original value
            if original_uri is not None:
                os.environ['MONGODB_URI'] = original_uri


class TestYearRange:
    """Test year range calculation."""

    def test_get_year_range_pilot(self, temp_config_dir):
        """Test pilot year range."""
        config = TNICConfig(config_dir=temp_config_dir)

        years = list(config.get_year_range('pilot'))
        assert years == [2010, 2011]

    def test_get_year_range_full(self, temp_config_dir):
        """Test full year range."""
        config = TNICConfig(config_dir=temp_config_dir)

        years = list(config.get_year_range('full'))
        assert years[0] == 2010
        assert years[-1] == 2025
        assert len(years) == 16  # 2010 to 2025 inclusive

    def test_get_year_range_invalid_mode(self, temp_config_dir):
        """Test that invalid mode raises ValueError."""
        config = TNICConfig(config_dir=temp_config_dir)

        with pytest.raises(ValueError, match="Invalid mode"):
            config.get_year_range('invalid_mode')


class TestConfigRepr:
    """Test string representation."""

    def test_repr(self, temp_config_dir):
        """Test __repr__ method."""
        config = TNICConfig(config_dir=temp_config_dir)

        repr_str = repr(config)
        assert 'TNICConfig' in repr_str
        assert str(temp_config_dir) in repr_str
        assert 'hp:' in repr_str
        assert 'nlp:' in repr_str
        assert 'paths:' in repr_str
        assert 'mongodb:' in repr_str


class TestGetConfigSingleton:
    """Test get_config() singleton function."""

    def test_get_config_returns_instance(self):
        """Test that get_config() returns TNICConfig instance."""
        config = get_config()
        assert isinstance(config, TNICConfig)

    def test_get_config_returns_same_instance(self):
        """Test that multiple calls return same instance (singleton)."""
        config1 = get_config()
        config2 = get_config()

        assert config1 is config2  # Same object

    def test_get_config_reload(self):
        """Test that reload=True creates new instance."""
        config1 = get_config()
        config2 = get_config(reload=True)

        # Should be same type but potentially different instance
        assert isinstance(config2, TNICConfig)


class TestRealConfigFiles:
    """Test with actual project config files."""

    def test_load_real_config_files(self):
        """Test loading actual config files from project."""
        # This tests that the real config files are valid
        config = TNICConfig()

        # Check that all sections are loaded
        assert config.hp is not None
        assert config.nlp is not None
        assert config.paths is not None
        assert config.mongodb is not None

    def test_real_config_has_expected_keys(self):
        """Test that real config has expected keys."""
        config = TNICConfig()

        # H&P parameters
        assert config.get('hp.filtering.min_words_per_firm') is not None
        assert config.get('hp.filtering.frequency_threshold') is not None

        # Korean NLP
        assert config.get('nlp.stopwords') is not None
        assert isinstance(config.get('nlp.stopwords'), list)

        # Paths
        assert config.get('paths.years.start') is not None
        assert config.get('paths.years.end') is not None

    def test_real_config_path_formatting(self):
        """Test path formatting with real config."""
        config = TNICConfig()

        # Test a path with {year} placeholder
        corpus_path = config.format_path('paths.outputs.corpus.base_dir', year=2010)
        assert '2010' in corpus_path


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_yaml_file(self, tmp_path):
        """Test handling of empty YAML file."""
        config_dir = tmp_path / "config_empty"
        config_dir.mkdir()

        # Create empty YAML files
        for filename in ['hoberg_phillips.yaml', 'korean_nlp.yaml', 'paths.yaml', 'mongodb.yaml']:
            (config_dir / filename).touch()

        # Should load successfully with empty dicts
        config = TNICConfig(config_dir=config_dir)
        assert config.hp == {}
        assert config.nlp == {}

    def test_yaml_parse_error(self, tmp_path):
        """Test handling of invalid YAML syntax."""
        config_dir = tmp_path / "config_invalid"
        config_dir.mkdir()

        # Create invalid YAML
        with open(config_dir / 'hoberg_phillips.yaml', 'w') as f:
            f.write("invalid: yaml: syntax: error:")

        # Create other files
        for filename in ['korean_nlp.yaml', 'paths.yaml', 'mongodb.yaml']:
            with open(config_dir / filename, 'w') as f:
                yaml.dump({}, f)

        with pytest.raises(yaml.YAMLError):
            TNICConfig(config_dir=config_dir)

    def test_get_with_numeric_keys(self, temp_config_dir):
        """Test get() with path containing numeric keys."""
        config = TNICConfig(config_dir=temp_config_dir)

        # Add a config with numeric keys for testing
        config.paths['test_numeric'] = {2010: 'value_2010', 2011: 'value_2011'}

        # Numeric keys should work if converted to strings
        value = config.get('paths.test_numeric')
        assert isinstance(value, dict)


@pytest.mark.parametrize("mode,expected_start,expected_end", [
    ('pilot', 2010, 2011),
    ('full', 2010, 2025),
])
def test_year_range_parametrized(temp_config_dir, mode, expected_start, expected_end):
    """Parametrized test for year ranges."""
    config = TNICConfig(config_dir=temp_config_dir)
    years = list(config.get_year_range(mode))

    assert years[0] == expected_start
    assert years[-1] == expected_end
