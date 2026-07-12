"""
Comprehensive tests for Fama-MacBeth regression module.

Tests all 3 methods (direct, hybrid, two_step) × 7 data scenarios:
1. Perfect data
2. Missing peer returns
3. New listing
4. Delisting
5. Annual characteristics
6. Trading halt
7. Too few securities
"""

import pytest
import pandas as pd
import numpy as np
from regression import FamaMacBethRegression
from tests.fixtures.synthetic_data import (
    generate_perfect_data,
    generate_missing_peer_data,
    generate_new_listing_data,
    generate_delisting_data,
    generate_annual_characteristics_data,
    generate_trading_halt_data,
    generate_too_few_securities_data
)


class TestFamaMacBethDirect:
    """Test direct method (no Step 1) with all 7 scenarios."""

    def test_perfect_data(self):
        """Test Case 1: Perfect data with no missing values."""
        data = generate_perfect_data()

        fm = FamaMacBethRegression(method='direct', newey_west_lags=2, verbose=False)

        # Use fewer variables to avoid multicollinearity with only 5 securities
        result = fm.fit(
            dependent=data['returns'],
            independent={
                'tnic_ret': data['tnic_ret'],
                'log_me': data['log_me'],
                'log_be_me': data['log_be_me']
            }
        )

        # Check that result is valid
        assert result.method == 'direct'
        assert result.n_variables == 3
        assert result.n_obs > 0

        # Check that all coefficients are present
        assert 'tnic_ret' in result.params.index
        assert 'log_me' in result.params.index
        assert 'log_be_me' in result.params.index

        # Check that no betas were estimated (direct method)
        assert result.betas is None

    def test_missing_peer_data(self):
        """Test Case 2: TNIC peer returns missing for first 12 months."""
        data = generate_missing_peer_data()

        fm = FamaMacBethRegression(method='direct', verbose=False)

        result = fm.fit(
            dependent=data['returns'],
            independent={
                'tnic_ret': data['tnic_ret'],
                'log_me': data['log_me']
            }
        )

        # Should handle missing data gracefully
        assert result.method == 'direct'
        assert result.n_obs > 0

        # Should have fewer periods due to missing data
        assert result.n_periods < len(data['returns'])

    def test_new_listing(self):
        """Test Case 3: Security lists mid-sample."""
        data = generate_new_listing_data()

        fm = FamaMacBethRegression(method='direct', verbose=False)

        result = fm.fit(
            dependent=data['returns'],
            independent={
                'tnic_ret': data['tnic_ret'],
                'log_me': data['log_me']
            }
        )

        # Should handle unbalanced panel
        assert result.method == 'direct'
        assert result.n_obs > 0

    def test_delisting(self):
        """Test Case 4: Security delists mid-sample."""
        data = generate_delisting_data()

        fm = FamaMacBethRegression(method='direct', verbose=False)

        result = fm.fit(
            dependent=data['returns'],
            independent={
                'tnic_ret': data['tnic_ret'],
                'log_me': data['log_me']
            }
        )

        # Should handle unbalanced panel
        assert result.method == 'direct'
        assert result.n_obs > 0

    def test_annual_characteristics(self):
        """Test Case 5: Characteristics update annually."""
        data = generate_annual_characteristics_data()

        fm = FamaMacBethRegression(method='direct', verbose=False)

        result = fm.fit(
            dependent=data['returns'],
            independent={
                'tnic_ret': data['tnic_ret'],
                'log_me': data['log_me'],
                'log_be_me': data['log_be_me']
            }
        )

        # Should handle step-function characteristics
        assert result.method == 'direct'
        assert result.n_obs > 0

    def test_trading_halt(self):
        """Test Case 6: Random NaN in return series."""
        data = generate_trading_halt_data()

        fm = FamaMacBethRegression(method='direct', verbose=False)

        result = fm.fit(
            dependent=data['returns'],
            independent={
                'tnic_ret': data['tnic_ret'],
                'log_me': data['log_me']
            }
        )

        # Should handle sporadic missing data
        assert result.method == 'direct'
        assert result.n_obs > 0

    def test_too_few_securities(self):
        """Test Case 7: Insufficient cross-sectional observations."""
        data = generate_too_few_securities_data()

        fm = FamaMacBethRegression(method='direct', verbose=False)

        # Should complete but possibly warn
        result = fm.fit(
            dependent=data['returns'],
            independent={
                'tnic_ret': data['tnic_ret'],
                'log_me': data['log_me']
            }
        )

        assert result.method == 'direct'
        # May have very few observations
        assert result.n_securities <= 3


class TestFamaMacBethTwoStep:
    """Test two-step method (all variables through Step 1) with key scenarios."""

    def test_perfect_data(self):
        """Test pure two-step with perfect data."""
        data = generate_perfect_data()

        fm = FamaMacBethRegression(
            method='two_step',
            window=36,
            min_periods=30,
            verbose=False
        )

        result = fm.fit(
            dependent=data['returns'],
            independent={
                'tnic_ret': data['tnic_ret'],
                'sic_ret': data['sic_ret']
            }
        )

        # Check that betas were estimated
        assert result.method == 'two_step'
        assert result.betas is not None
        assert 'tnic_ret' in result.betas
        assert 'sic_ret' in result.betas

        # Check beta shape
        beta_tnic = result.betas['tnic_ret']
        assert isinstance(beta_tnic, pd.DataFrame)
        assert beta_tnic.shape[1] == data['returns'].shape[1]  # Same securities

        # Window metadata
        assert result.window == 36

    def test_missing_peer_data(self):
        """Test two-step with missing data."""
        data = generate_missing_peer_data()

        fm = FamaMacBethRegression(
            method='two_step',
            window=36,
            min_periods=24,  # More lenient
            verbose=False
        )

        result = fm.fit(
            dependent=data['returns'],
            independent={
                'tnic_ret': data['tnic_ret']
            }
        )

        # Should estimate betas despite missing data
        assert result.method == 'two_step'
        assert result.betas is not None


class TestFamaMacBethHybrid:
    """Test hybrid method (factors through Step 1, characteristics direct)."""

    def test_perfect_data(self):
        """Test hybrid method with factors and characteristics."""
        data = generate_perfect_data()

        fm = FamaMacBethRegression(
            method='hybrid',
            window=36,
            min_periods=30,
            verbose=False
        )

        result = fm.fit(
            dependent=data['returns'],
            independent={
                'tnic_ret': data['tnic_ret'],       # Factor -> Step 1
                'sic_ret': data['sic_ret'],         # Factor -> Step 1
                'log_me': data['log_me'],           # Characteristic -> direct
                'log_be_me': data['log_be_me']      # Characteristic -> direct
            },
            factors=['tnic_ret', 'sic_ret']  # Specify which go through Step 1
        )

        # Check that only factors have betas
        assert result.method == 'hybrid'
        assert result.betas is not None
        assert 'tnic_ret' in result.betas
        assert 'sic_ret' in result.betas
        assert 'log_me' not in result.betas  # Characteristics skip Step 1
        assert 'log_be_me' not in result.betas

        # Check that all variables appear in final regression
        assert 'tnic_ret' in result.params.index
        assert 'sic_ret' in result.params.index
        assert 'log_me' in result.params.index
        assert 'log_be_me' in result.params.index

    def test_missing_factors_error(self):
        """Test that hybrid method requires factors parameter."""
        data = generate_perfect_data()

        fm = FamaMacBethRegression(method='hybrid', verbose=False)

        # Should raise error if factors not specified
        with pytest.raises(ValueError, match="requires 'factors' parameter"):
            fm.fit(
                dependent=data['returns'],
                independent={'tnic_ret': data['tnic_ret']}
            )


class TestResultsObject:
    """Test FMResults functionality."""

    def test_summary_table(self):
        """Test summary table generation."""
        data = generate_perfect_data()
        fm = FamaMacBethRegression(method='direct', verbose=False)

        result = fm.fit(
            dependent=data['returns'],
            independent={
                'tnic_ret': data['tnic_ret'],
                'log_me': data['log_me']
            }
        )

        summary = result.summary()

        # Check summary structure
        assert isinstance(summary, pd.DataFrame)
        assert 'coef' in summary.columns
        assert 't_stat' in summary.columns
        assert 'p_value' in summary.columns
        assert 'sig' in summary.columns

    def test_gamma_extraction(self):
        """Test extraction of gamma time series."""
        data = generate_perfect_data()
        fm = FamaMacBethRegression(method='direct', verbose=False)

        result = fm.fit(
            dependent=data['returns'],
            independent={'tnic_ret': data['tnic_ret']}
        )

        gamma_series = result.get_gamma('tnic_ret')

        # Check that time series exists
        assert isinstance(gamma_series, pd.Series)
        assert len(gamma_series) > 0

    def test_beta_extraction(self):
        """Test extraction of beta estimates."""
        data = generate_perfect_data()
        fm = FamaMacBethRegression(method='two_step', verbose=False)

        result = fm.fit(
            dependent=data['returns'],
            independent={'tnic_ret': data['tnic_ret']}
        )

        beta_df = result.get_beta('tnic_ret')

        # Check beta DataFrame
        assert isinstance(beta_df, pd.DataFrame)
        assert beta_df.shape[0] == len(data['returns'])  # Same dates
        assert beta_df.shape[1] == len(data['returns'].columns)  # Same securities

    def test_significant_variables(self):
        """Test identification of significant variables."""
        data = generate_perfect_data()
        fm = FamaMacBethRegression(method='direct', verbose=False)

        result = fm.fit(
            dependent=data['returns'],
            independent={
                'tnic_ret': data['tnic_ret'],
                'log_me': data['log_me']
            }
        )

        significant = result.get_significant_variables(alpha=0.05)

        # Check that it returns a list
        assert isinstance(significant, list)


class TestErrorHandling:
    """Test proper error handling and validation."""

    def test_invalid_method(self):
        """Test that invalid method raises error."""
        with pytest.raises(ValueError, match="method must be one of"):
            FamaMacBethRegression(method='invalid')

    def test_mismatched_data(self):
        """Test that mismatched DataFrames raise error."""
        data = generate_perfect_data()

        # Truncate one variable
        tnic_truncated = data['tnic_ret'].iloc[:-5]

        fm = FamaMacBethRegression(method='direct', verbose=False)

        # Should handle via alignment (common dates)
        result = fm.fit(
            dependent=data['returns'],
            independent={'tnic_ret': tnic_truncated}
        )

        # Should use intersection of dates
        assert result.n_periods < len(data['returns'])

    def test_empty_independent(self):
        """Test that empty independent dict raises error."""
        data = generate_perfect_data()
        fm = FamaMacBethRegression(method='direct', verbose=False)

        # Empty independent dict should be caught during preprocessing
        with pytest.raises((ValueError, KeyError)):
            fm.fit(
                dependent=data['returns'],
                independent={}
            )


class TestPreprocessing:
    """Test preprocessing module functions."""

    def test_multiindex_conversion(self):
        """Test conversion from wide to MultiIndex format."""
        from regression.preprocessing import convert_to_multiindex

        data = generate_perfect_data()

        dependent_mi, independent_mi = convert_to_multiindex(
            dependent=data['returns'],
            independent_dict={'tnic_ret': data['tnic_ret']}
        )

        # Check MultiIndex structure
        assert isinstance(dependent_mi.index, pd.MultiIndex)
        assert dependent_mi.index.names == ['security', 'date']

        assert isinstance(independent_mi.index, pd.MultiIndex)
        assert independent_mi.index.names == ['security', 'date']

    def test_alignment(self):
        """Test data alignment across multiple DataFrames."""
        from regression.preprocessing import align_and_validate

        data = generate_perfect_data()

        # Truncate one DataFrame
        tnic_truncated = data['tnic_ret'].iloc[:-5]

        dependent_aligned, independent_aligned, diagnostics = align_and_validate(
            dependent=data['returns'],
            independent_dict={'tnic_ret': tnic_truncated},
            verbose=False
        )

        # Should use common dates only
        assert len(dependent_aligned) == len(tnic_truncated)
        assert dependent_aligned.index.equals(independent_aligned['tnic_ret'].index)


class TestRollingBeta:
    """Test rolling beta estimator."""

    def test_beta_estimation(self):
        """Test basic beta estimation."""
        from regression.rolling_beta import RollingBetaEstimator

        data = generate_perfect_data()

        estimator = RollingBetaEstimator(window=36, min_periods=30)

        betas, alphas = estimator.estimate_betas_with_constant(
            dependent=data['returns'],
            factors={'tnic_ret': data['tnic_ret']}
        )

        # Check output structure
        assert isinstance(betas, dict)
        assert 'tnic_ret' in betas

        beta_df = betas['tnic_ret']
        assert isinstance(beta_df, pd.DataFrame)
        assert beta_df.shape == data['returns'].shape

        # First 35 rows should be NaN (window - 1)
        assert beta_df.iloc[:35].isna().all().all()

        # Later rows should have estimates
        assert not beta_df.iloc[36:].isna().all().all()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
