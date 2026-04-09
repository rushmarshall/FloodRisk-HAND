"""Risk severity classification.

Classifies compound flood risk into actionable severity categories
using configurable quantile-based thresholds.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class RiskClassifier:
    """Classify compound flood risk into severity categories.

    Default classification scheme:
    - None (0): No risk (risk = 0)
    - Minor (1): Below 25th percentile
    - Moderate (2): 25th-75th percentile
    - Major (3): 75th-95th percentile
    - Extreme (4): Above 95th percentile
    """

    CATEGORIES = {0: "None", 1: "Minor", 2: "Moderate", 3: "Major", 4: "Extreme"}

    def __init__(
        self,
        thresholds: tuple[float, float, float] = (0.25, 0.75, 0.95),
    ) -> None:
        if len(thresholds) != 3:
            raise ValueError("Exactly 3 thresholds required (minor, moderate, extreme)")
        self.thresholds = sorted(thresholds)

    def classify(self, risk_data: dict[str, Any]) -> dict[str, Any]:
        """Classify risk grid into severity categories.

        Parameters
        ----------
        risk_data : dict
            Compound risk assessment output.

        Returns
        -------
        dict
            Original data plus classified grid and category counts.
        """
        risk_grid = risk_data["risk_grid"]
        nonzero = risk_grid[risk_grid > 0]

        if len(nonzero) == 0:
            classified = np.zeros_like(risk_grid, dtype=np.int8)
            category_counts = {name: 0 for name in self.CATEGORIES.values()}
            category_counts["None"] = int(risk_grid.size)
        else:
            q = np.quantile(nonzero, self.thresholds)
            classified = np.zeros_like(risk_grid, dtype=np.int8)
            classified[risk_grid > 0] = 1
            classified[risk_grid >= q[0]] = 2
            classified[risk_grid >= q[1]] = 3
            classified[risk_grid >= q[2]] = 4

            category_counts = {
                name: int(np.sum(classified == code))
                for code, name in self.CATEGORIES.items()
            }

        logger.info("Classification: %s", category_counts)

        return {
            **risk_data,
            "classified_grid": classified,
            "category_counts": category_counts,
            "thresholds": list(self.thresholds),
        }
