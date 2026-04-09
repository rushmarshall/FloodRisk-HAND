"""HAND-based Flood Inundation Mapping (FIM).

Implements the Height Above Nearest Drainage methodology
to convert discharge forecasts into spatially distributed
flood depth grids.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

from floodrisk.data.hand import HANDRaster

logger = logging.getLogger(__name__)


class HANDFloodMapper:
    """Generate flood inundation maps using HAND methodology.

    The HAND-FIM approach identifies areas likely to flood by comparing
    the height of each cell above its nearest drainage to the estimated
    flood stage derived from discharge forecasts via synthetic rating curves.
    """

    def __init__(self, rating_curve_method: str = "power_law") -> None:
        valid_methods = {"power_law", "manning", "lookup"}
        if rating_curve_method not in valid_methods:
            raise ValueError(f"rating_curve_method must be one of {valid_methods}")
        self.rating_curve_method = rating_curve_method

    def map_inundation(
        self,
        forecasts: dict[str, Any],
        hand_raster: HANDRaster,
        resolution: int = 10,
        return_max: bool = True,
    ) -> dict[str, Any]:
        """Generate flood depth grid from discharge forecasts and HAND.

        Parameters
        ----------
        forecasts : dict
            NWM forecast data with streamflow array.
        hand_raster : HANDRaster
            HAND raster dataset.
        resolution : int
            Target resolution in meters.
        return_max : bool
            If True, return maximum depth across all timesteps.

        Returns
        -------
        dict
            Flood map with depth grid, metadata, and statistics.
        """
        streamflow = forecasts["streamflow"]
        if return_max:
            peak_flows = np.max(streamflow, axis=0)
        else:
            peak_flows = streamflow[-1]

        # Convert peak discharge to flood stage via synthetic rating curve
        stages = self._discharge_to_stage(peak_flows)

        # Map inundation: cells with HAND < stage are flooded
        max_stage = float(np.percentile(stages, 95))
        depth_grid = np.maximum(max_stage - hand_raster.data, 0)

        inundated_fraction = float(np.mean(depth_grid > 0))
        logger.info(
            "Inundation mapped: %.1f%% area flooded, max depth %.2fm",
            inundated_fraction * 100,
            float(np.max(depth_grid)),
        )

        return {
            "depth_grid": depth_grid,
            "max_depth": float(np.max(depth_grid)),
            "mean_depth": float(np.mean(depth_grid[depth_grid > 0])) if inundated_fraction > 0 else 0,
            "inundated_fraction": inundated_fraction,
            "bounds": hand_raster.bounds,
            "crs": hand_raster.crs,
            "resolution": resolution,
            "peak_stage": max_stage,
        }

    def _discharge_to_stage(self, discharge: np.ndarray) -> np.ndarray:
        """Convert discharge to flood stage using synthetic rating curve.

        Uses a power-law relationship: stage = a * Q^b
        Coefficients derived from regional regression.
        """
        a, b = 0.3, 0.4  # Regional power-law coefficients
        return a * np.power(np.maximum(discharge, 0.01), b)
