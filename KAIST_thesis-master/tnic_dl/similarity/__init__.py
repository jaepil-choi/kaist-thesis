"""
Similarity and clustering module for TNIC-DL.

Contains:
- Cosine similarity computation
- Spherical k-means clustering
"""

from tnic_dl.similarity.cosine_similarity import compute_cosine_similarity
from tnic_dl.similarity.spherical_kmeans import SphericalKMeans

__all__ = [
    "compute_cosine_similarity",
    "SphericalKMeans",
]
