# TNIC Module

Text-Based Network Industry Classification (TNIC) implementation for Korean market data.

## Overview

This module implements the Hoberg & Phillips (2016, 2018) methodology for building text-based industry classifications and analyzing industry momentum using Korean DART business descriptions.

## Status

This is a clean rebuild of the TNIC module. The previous untested implementation has been removed.

Core functionality will be added incrementally following the working pipeline in `scripts/`.

## Structure

```
tnic/
├── __init__.py          # Module initialization (this makes it discoverable)
├── README.md            # This file
└── [modules to be added]
```

## References

**Primary Methodology:**
- Hoberg, G., & Phillips, G. M. (2016). Text-based network industries and endogenous product differentiation. *Journal of Political Economy*, 124(5), 1423-1465.

**Application:**
- Hoberg, G., & Phillips, G. M. (2018). Text-based industry momentum. *Journal of Financial and Quantitative Analysis*, 53(6), 2355-2388.

## Development

The module is being built to support the main analysis scripts in `scripts/` directory.
