"""
Data Loaders for TNIC Pipeline

Provides data loading functionality for MongoDB and Parquet files.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from tnic.config import get_config
from tnic.utils import check_required_columns, setup_logger


class MongoDBLoader:
    """
    MongoDB data loader for Korean DART business descriptions.

    Handles connection to MongoDB and extraction of business descriptions
    according to configuration settings.

    Attributes:
        client: MongoDB client instance
        db: Database instance
        collection: Collection instance
        config: TNIC configuration
        logger: Logger instance
    """

    def __init__(
        self,
        uri: Optional[str] = None,
        database: Optional[str] = None,
        collection: Optional[str] = None,
        config_path: Optional[str] = None
    ):
        """
        Initialize MongoDB loader.

        Args:
            uri: MongoDB connection URI (default: from config or env)
            database: Database name (default: from config)
            collection: Collection name (default: from config)
            config_path: Path to config directory (default: uses default config)

        Examples:
            >>> loader = MongoDBLoader()  # Uses config defaults
            >>> loader = MongoDBLoader(uri="mongodb://localhost:27017")
        """
        # Load configuration
        if config_path is None:
            self.config = get_config()
        else:
            from tnic.config import TNICConfig
            self.config = TNICConfig(config_dir=config_path)

        # Get connection parameters
        if uri is None:
            # Try to get URI from config (legacy)
            uri = self.config.get("mongodb.connection.uri")

            # If no URI, construct from host
            if uri is None:
                host = self.config.get("mongodb.connection.host")
                if host is None:
                    # Fallback to environment variable
                    host = os.getenv("MONGO_HOST", "localhost:27017")

                # Construct MongoDB URI
                uri = f"mongodb://{host}/"

        if database is None:
            database = self.config.get("mongodb.connection.database")
            if database is None:
                database = os.getenv("DB_NAME", "dart")

        if collection is None:
            collection = self.config.get("mongodb.connection.collection")
            if collection is None:
                collection = os.getenv("COLLECTION_NAME", "business_reports")

        # Initialize logger
        self.logger = setup_logger(__name__)

        # Connect to MongoDB
        self.logger.info(f"Connecting to MongoDB: {uri}")
        self.client = MongoClient(uri)
        self.db: Database = self.client[database]
        self.collection: Collection = self.db[collection]

        self.logger.info(f"Connected to database: {database}")
        self.logger.info(f"Using collection: {collection}")

    def extract_business_descriptions(
        self,
        section_codes: Optional[List[str]] = None,
        year_range: Optional[tuple] = None,
        report_types: Optional[List[str]] = None,
        fields: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Extract business descriptions from MongoDB.

        Args:
            section_codes: List of section codes to extract (default: from config)
            year_range: Tuple of (start_year, end_year) (default: from config)
            report_types: List of report types (default: from config)
            fields: Fields to retrieve (default: from config)

        Returns:
            DataFrame with business descriptions

        Examples:
            >>> loader = MongoDBLoader()
            >>> df = loader.extract_business_descriptions(
            ...     section_codes=["020000", "020100"],
            ...     year_range=(2010, 2025)
            ... )
        """
        # Get parameters from config if not provided
        if section_codes is None:
            section_codes = self.config.get(
                "mongodb.extraction.section_codes",
                ["020000", "020100"]
            )

        if year_range is None:
            start = self.config.get("mongodb.extraction.year_range.start", 2010)
            end = self.config.get("mongodb.extraction.year_range.end", 2025)
            year_range = (start, end)

        if report_types is None:
            report_types = self.config.get(
                "mongodb.extraction.report_types",
                ["A001"]
            )

        if fields is None:
            fields = self.config.get(
                "mongodb.extraction.fields",
                [
                    "document_id", "rcept_no", "rcept_dt", "year",
                    "corp_code", "corp_name", "stock_code",
                    "report_type", "report_name", "section_code",
                    "section_title", "text", "char_count",
                    "word_count", "level"
                ]
            )

        # Build query
        query = {}

        if section_codes:
            query["section_code"] = {"$in": section_codes}

        if year_range:
            start_year, end_year = year_range
            query["year"] = {
                "$gte": str(start_year),
                "$lte": str(end_year)
            }

        if report_types:
            query["report_type"] = {"$in": report_types}

        # Build projection (limit fields)
        use_projection = self.config.get("mongodb.query.use_projection", True)
        projection = {field: 1 for field in fields} if use_projection else None

        # Log query
        self.logger.info("Extracting business descriptions from MongoDB:")
        self.logger.info(f"  Query: {query}")
        self.logger.info(f"  Fields: {len(fields)} fields")

        # Count documents
        count = self.collection.count_documents(query)
        self.logger.info(f"  Total documents: {count:,}")

        # Extract documents
        batch_size = self.config.get("mongodb.query.batch_size", 1000)
        docs = list(self.collection.find(query, projection).batch_size(batch_size))

        self.logger.info(f"  Retrieved: {len(docs):,} documents")

        # Convert to DataFrame
        df = pd.DataFrame(docs)

        # Remove MongoDB _id field
        if '_id' in df.columns:
            df = df.drop('_id', axis=1)

        self.logger.info(f"  DataFrame shape: {df.shape}")

        return df

    def get_document_count(
        self,
        query: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Get count of documents matching query.

        Args:
            query: MongoDB query (default: count all documents)

        Returns:
            Number of documents

        Examples:
            >>> loader = MongoDBLoader()
            >>> total = loader.get_document_count()
            >>> by_year = loader.get_document_count({"year": "2024"})
        """
        if query is None:
            query = {}

        count = self.collection.count_documents(query)
        return count

    def close(self):
        """Close MongoDB connection."""
        self.client.close()
        self.logger.info("MongoDB connection closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"MongoDBLoader("
            f"database={self.db.name}, "
            f"collection={self.collection.name})"
        )


class ParquetLoader:
    """
    Parquet data loader for processed TNIC data.

    Handles loading of parquet files with validation and error handling.

    Attributes:
        config: TNIC configuration
        logger: Logger instance
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize Parquet loader.

        Args:
            config_path: Path to config directory (default: uses default config)

        Examples:
            >>> loader = ParquetLoader()
        """
        # Load configuration
        if config_path is None:
            self.config = get_config()
        else:
            from tnic.config import TNICConfig
            self.config = TNICConfig(config_dir=config_path)

        # Initialize logger
        self.logger = setup_logger(__name__)

    def load_business_descriptions(
        self,
        filepath: Optional[Union[str, Path]] = None
    ) -> pd.DataFrame:
        """
        Load clean business descriptions from parquet file.

        Args:
            filepath: Path to parquet file (default: from config)

        Returns:
            DataFrame with business descriptions

        Raises:
            FileNotFoundError: If parquet file doesn't exist
            ValueError: If required columns are missing

        Examples:
            >>> loader = ParquetLoader()
            >>> df = loader.load_business_descriptions()
        """
        if filepath is None:
            filepath = self.config.get("paths.inputs.business_descriptions")

        if filepath is None:
            raise ValueError(
                "No filepath provided and no default in config. "
                "Specify filepath or set paths.inputs.business_descriptions in config."
            )

        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(
                f"Business descriptions file not found: {filepath}\n"
                f"Please run data extraction first."
            )

        self.logger.info(f"Loading business descriptions from: {filepath}")
        df = pd.read_parquet(filepath)

        # Validate required columns
        required = ['stock_code', 'year', 'text']
        check_required_columns(df, required, "Business descriptions")

        self.logger.info(f"  Loaded: {len(df):,} firm-years")
        self.logger.info(f"  Columns: {list(df.columns)}")

        return df

    def load_filled_descriptions(
        self,
        filepath: Optional[Union[str, Path]] = None
    ) -> pd.DataFrame:
        """
        Load filled business descriptions from parquet file (Phase 1.5 output).

        This loads data that has been forward-filled, backfilled, and masked
        to the trading universe.

        Args:
            filepath: Path to parquet file (default: from config)

        Returns:
            DataFrame with filled business descriptions
            Columns include: stock_code, year, text, char_count, corp_name,
                           is_filled, original_year, fill_method

        Raises:
            FileNotFoundError: If parquet file doesn't exist
            ValueError: If required columns are missing

        Examples:
            >>> loader = ParquetLoader()
            >>> df = loader.load_filled_descriptions()
        """
        if filepath is None:
            filepath = self.config.get("paths.outputs.universe_matching.filled_descriptions")

        if filepath is None:
            raise ValueError(
                "No filepath provided and no default in config. "
                "Specify filepath or set paths.outputs.universe_matching.filled_descriptions in config."
            )

        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(
                f"Filled descriptions file not found: {filepath}\n"
                f"Please run Phase 1.5 (universe matching) first."
            )

        self.logger.info(f"Loading filled business descriptions from: {filepath}")
        df = pd.read_parquet(filepath)

        # Validate required columns
        required = ['stock_code', 'year', 'text', 'is_filled', 'original_year', 'fill_method']
        check_required_columns(df, required, "Filled business descriptions")

        self.logger.info(f"  Loaded: {len(df):,} firm-years")
        self.logger.info(f"  Original: {(df['fill_method'] == 'original').sum():,}")
        self.logger.info(f"  Forward filled: {(df['fill_method'] == 'forward_fill').sum():,}")
        self.logger.info(f"  Backfilled: {(df['fill_method'] == 'backfill').sum():,}")
        self.logger.info(f"  Columns: {list(df.columns)}")

        return df

    def load_firm_word_sets(
        self,
        year: int,
        base_dir: Optional[Union[str, Path]] = None
    ) -> pd.DataFrame:
        """
        Load firm word sets for a specific year.

        Args:
            year: Year to load
            base_dir: Base directory (default: from config)

        Returns:
            DataFrame with firm_year, stock_code, year, unique_nouns, word_count

        Raises:
            FileNotFoundError: If file doesn't exist

        Examples:
            >>> loader = ParquetLoader()
            >>> df_2010 = loader.load_firm_word_sets(2010)
        """
        if base_dir is None:
            base_dir = self.config.get("paths.outputs.corpus.base_dir")

        if base_dir is None:
            raise ValueError("No base_dir provided and no default in config.")

        # Format path with year
        filepath = Path(str(base_dir).format(year=year)) / f"firm_word_sets_{year}.parquet"

        if not filepath.exists():
            raise FileNotFoundError(
                f"Firm word sets not found: {filepath}\n"
                f"Please run corpus building for year {year} first."
            )

        self.logger.info(f"Loading firm word sets for {year}: {filepath}")
        df = pd.read_parquet(filepath)

        # Validate required columns
        required = ['firm_year', 'stock_code', 'year', 'unique_nouns', 'word_count']
        check_required_columns(df, required, f"Firm word sets ({year})")

        self.logger.info(f"  Loaded: {len(df):,} firms")

        return df

    def load_fnguide_data(
        self,
        data_type: str = "dataguide"
    ) -> pd.DataFrame:
        """
        Load FnGuide financial data.

        Args:
            data_type: Type of data to load:
                      - "dataguide": Company metadata and industry codes
                      - "price": Monthly stock prices
                      - "turnover": Trading turnover

        Returns:
            DataFrame with FnGuide data

        Raises:
            ValueError: If data_type is invalid
            FileNotFoundError: If file doesn't exist

        Examples:
            >>> loader = ParquetLoader()
            >>> dataguide = loader.load_fnguide_data("dataguide")
            >>> prices = loader.load_fnguide_data("price")
        """
        valid_types = ["dataguide", "price", "turnover"]
        if data_type not in valid_types:
            raise ValueError(
                f"Invalid data_type: {data_type}. "
                f"Must be one of: {valid_types}"
            )

        # Get filepath from config
        config_key = f"paths.inputs.{data_type}_data" if data_type != "dataguide" else "paths.inputs.dataguide"
        filepath = self.config.get(config_key)

        if filepath is None:
            raise ValueError(
                f"No filepath configured for {data_type}. "
                f"Set {config_key} in config."
            )

        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(
                f"FnGuide {data_type} file not found: {filepath}"
            )

        self.logger.info(f"Loading FnGuide {data_type} data from: {filepath}")
        df = pd.read_parquet(filepath)

        self.logger.info(f"  Loaded: {df.shape}")

        return df

    def __repr__(self) -> str:
        """String representation."""
        return "ParquetLoader()"
