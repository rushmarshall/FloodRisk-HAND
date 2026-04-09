"""CDC Social Vulnerability Index (SVI) data loader.

Retrieves and processes SVI data at the census tract level
for equity-informed flood risk assessment.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

CDC_SVI_URL = "https://www.atsdr.cdc.gov/placeandhealth/svi/data_documentation_download.html"


@dataclass
class SVIData:
    """Container for Social Vulnerability Index data."""

    tract_ids: list[str]
    overall_svi: np.ndarray
    theme_scores: dict[str, np.ndarray]
    year: int
    geometry: Any = None


class SVILoader:
    """Load CDC Social Vulnerability Index data.

    SVI ranks census tracts on 16 social factors grouped into four themes:
    Socioeconomic Status, Household Characteristics, Racial & Ethnic
    Minority Status, and Housing Type & Transportation.
    """

    THEMES = ["socioeconomic", "household", "minority", "housing"]

    def __init__(self, year: int = 2022, themes: list[str] | None = None) -> None:
        self.year = year
        self.themes = themes or self.THEMES.copy()
        for t in self.themes:
            if t not in self.THEMES:
                raise ValueError(f"Unknown SVI theme: {t}. Valid: {self.THEMES}")

    def load(self, huc_id: str) -> SVIData:
        """Load SVI data for census tracts overlapping a HUC watershed.

        Parameters
        ----------
        huc_id : str
            Target HUC identifier for spatial intersection.

        Returns
        -------
        SVIData
            Social vulnerability scores for overlapping tracts.
        """
        logger.info("Loading SVI %d data for HUC %s", self.year, huc_id)

        # Synthetic SVI data for demonstration
        np.random.seed(abs(hash(f"svi_{huc_id}")) % 2**31)
        n_tracts = np.random.randint(20, 100)
        tract_ids = [f"{int(huc_id[:2]):02d}{i:04d}{np.random.randint(1000, 9999):04d}"
                     for i in range(n_tracts)]

        theme_scores = {}
        for theme in self.themes:
            theme_scores[theme] = np.random.beta(2, 3, size=n_tracts)

        overall = np.mean(list(theme_scores.values()), axis=0)

        return SVIData(
            tract_ids=tract_ids,
            overall_svi=overall,
            theme_scores=theme_scores,
            year=self.year,
        )
