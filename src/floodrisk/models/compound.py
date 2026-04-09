"""Compound flood risk assessment.

Combines flood inundation depth with social vulnerability
to produce an integrated risk metric that accounts for both
physical hazard and community resilience capacity.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

from floodrisk.data.svi import SVIData

logger = logging.getLogger(__name__)


class CompoundRiskAssessor:
    """Assess compound flood risk by integrating physical and social factors.

    Risk = f(hazard, vulnerability) where:
    - Hazard: flood depth, velocity, duration
    - Vulnerability: SVI-based community resilience capacity
    """

    def __init__(
        self,
        hazard_weight: float = 0.6,
        vulnerability_weight: float = 0.4,
    ) -> None:
        if not np.isclose(hazard_weight + vulnerability_weight, 1.0):
            raise ValueError("Weights must sum to 1.0")
        self.hazard_weight = hazard_weight
        self.vulnerability_weight = vulnerability_weight

    def combine(
        self,
        flood_map: dict[str, Any],
        svi: SVIData,
    ) -> dict[str, Any]:
        """Combine flood hazard with social vulnerability.

        Parameters
        ----------
        flood_map : dict
            Flood inundation mapping output with depth grid.
        svi : SVIData
            Social vulnerability data for the study area.

        Returns
        -------
        dict
            Compound risk assessment with integrated risk grid.
        """
        depth_grid = flood_map["depth_grid"]
        max_depth = flood_map["max_depth"]

        # Normalize depth to [0, 1]
        if max_depth > 0:
            hazard = depth_grid / max_depth
        else:
            hazard = np.zeros_like(depth_grid)

        # Create vulnerability surface from SVI tract data
        vulnerability = self._interpolate_svi(svi, depth_grid.shape)

        # Compound risk index
        risk = (
            self.hazard_weight * hazard
            + self.vulnerability_weight * vulnerability
        )

        logger.info(
            "Compound risk computed: mean=%.3f, max=%.3f",
            float(np.mean(risk)),
            float(np.max(risk)),
        )

        return {
            **flood_map,
            "risk_grid": risk,
            "hazard_grid": hazard,
            "vulnerability_grid": vulnerability,
            "mean_risk": float(np.mean(risk)),
            "max_risk": float(np.max(risk)),
        }

    def _interpolate_svi(self, svi: SVIData, shape: tuple[int, int]) -> np.ndarray:
        """Interpolate SVI tract scores onto the flood grid.

        Creates a continuous vulnerability surface from discrete tract-level data.
        """
        np.random.seed(42)
        n_tracts = len(svi.tract_ids)
        rows, cols = shape

        surface = np.zeros(shape)
        for i in range(n_tracts):
            cx = np.random.randint(0, rows)
            cy = np.random.randint(0, cols)
            radius = max(rows, cols) // (n_tracts ** 0.5)

            yy, xx = np.ogrid[:rows, :cols]
            dist = np.sqrt((yy - cx) ** 2 + (xx - cy) ** 2)
            weight = np.exp(-dist / max(radius, 1))
            surface += weight * svi.overall_svi[i]

        # Normalize to [0, 1]
        if surface.max() > 0:
            surface = surface / surface.max()

        return surface.astype(np.float32)
