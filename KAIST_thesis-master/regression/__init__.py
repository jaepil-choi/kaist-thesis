"""
Fama-MacBeth regression module.

Supports two methodologies:
1. Direct: Skip beta estimation, run cross-sectional regressions directly (modern approach)
2. Two-step: Estimate betas first, then run cross-sectional regressions (Fama-MacBeth 1973)

Uses the Strategy pattern for clean separation of regression algorithms.
"""

from .fama_macbeth import FamaMacBethRegression
from .results import FMResults
from .strategies import DirectStrategy, TwoStepStrategy, RegressionStrategy

__all__ = [
    'FamaMacBethRegression',
    'FMResults',
    # Strategy classes (for advanced users)
    'DirectStrategy',
    'TwoStepStrategy',
    'RegressionStrategy'
]
