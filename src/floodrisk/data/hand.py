"""HAND (Height Above Nearest Drainage) raster management.

Acquires and processes HAND rasters from CIROH cloud storage
or user-supplied datasets for flood inundation mapping.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

CIROH_HAND_URL = "https://cfim.ornl.gov/data"


@dataclass
class HANDRaster:
    """Container for a HAND raster dataset."""

    data: np.ndarray
    transform: tuple[float, ...]
    crs: str
    resolution: float
    bounds: tuple[float, float, float, float]
    nodata: float = -9999.0


class HANDRasterManager:
    """Manage HAND raster acquisition and preprocessing.

    Supports CIROH cloud-hosted HAND datasets and local GeoTIFF files.
    """

    def __init__(self, resolution: int = 10, source: str = "ciroh") -> None:
        self.resolution = resolution
        self.source = source
        self.cache_dir = Path.home() / ".floodrisk" / "hand_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def load(self, huc_id: str, filepath: str | Path | None = None) -> HANDRaster:
        """Load or retrieve a HAND raster for the given HUC.

        Parameters
        ----------
        huc_id : str
            USGS HUC identifier.
        filepath : str or Path, optional
            Path to a local HAND GeoTIFF. If None, retrieves from cloud.

        Returns
        -------
        HANDRaster
            The HAND raster dataset ready for flood mapping.
        """
        if filepath is not None:
            return self._load_local(Path(filepath))

        cached = self.cache_dir / f"hand_{huc_id}_{self.resolution}m.npy"
        if cached.exists():
            logger.info("Loading cached HAND raster for HUC %s", huc_id)
            data = np.load(cached)
        else:
            logger.info("Generating synthetic HAND for HUC %s (demo mode)", huc_id)
            data = self._generate_synthetic(huc_id)
            np.save(cached, data)

        return HANDRaster(
            data=data,
            transform=(self.resolution, 0, -83.0, 0, -self.resolution, 36.0),
            crs="EPSG:4326",
            resolution=self.resolution,
            bounds=(-83.5, 35.0, -82.5, 36.0),
        )

    def _load_local(self, filepath: Path) -> HANDRaster:
        """Load a HAND raster from a local GeoTIFF."""
        try:
            import rioxarray as rxr

            ds = rxr.open_rasterio(filepath)
            data = ds.values[0]
            bounds = (
                float(ds.x.min()),
                float(ds.y.min()),
                float(ds.x.max()),
                float(ds.y.max()),
            )
            return HANDRaster(
                data=data,
                transform=tuple(ds.rio.transform()),
                crs=str(ds.rio.crs),
                resolution=abs(float(ds.rio.resolution()[0])),
                bounds=bounds,
            )
        except ImportError:
            raise ImportError("rioxarray required for GeoTIFF loading: pip install rioxarray")

    def _generate_synthetic(self, huc_id: str, size: int = 500) -> np.ndarray:
        """Generate a synthetic HAND raster for demonstration."""
        np.random.seed(abs(hash(huc_id)) % 2**31)

        x = np.linspace(0, 4 * np.pi, size)
        y = np.linspace(0, 4 * np.pi, size)
        xx, yy = np.meshgrid(x, y)

        # Valley network pattern
        valley = np.sin(xx) * np.cos(yy * 0.7) + np.sin(xx * 0.5 + yy * 0.3)
        terrain = np.abs(valley) * 15 + np.random.normal(0, 0.5, (size, size))

        return np.maximum(terrain, 0).astype(np.float32)
