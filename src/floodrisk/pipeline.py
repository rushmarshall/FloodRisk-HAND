"""End-to-end flood risk assessment pipeline."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from floodrisk.data.nwm import NWMForecastRetriever
from floodrisk.data.hand import HANDRasterManager
from floodrisk.data.svi import SVILoader
from floodrisk.models.fim import HANDFloodMapper
from floodrisk.models.compound import CompoundRiskAssessor
from floodrisk.models.classify import RiskClassifier

logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    """Configuration for the flood risk pipeline."""

    huc_id: str = "060101"
    study_name: str = "study_area"
    forecast_type: str = "medium_range"
    ensemble_members: int = 7
    hand_resolution: int = 10
    hand_source: str = "ciroh"
    svi_year: int = 2022
    svi_themes: list[str] = field(
        default_factory=lambda: ["socioeconomic", "household", "minority", "housing"]
    )
    output_dir: str = "./output"
    output_formats: list[str] = field(default_factory=lambda: ["geotiff", "html"])


class FloodRiskPipeline:
    """Orchestrates the complete flood risk assessment workflow.

    Retrieves NWM forecasts, generates HAND-FIM depth grids,
    overlays CDC SVI data, and produces classified risk maps.
    """

    def __init__(self, config: PipelineConfig) -> None:
        self.config = config
        self.nwm = NWMForecastRetriever(
            forecast_type=config.forecast_type,
            ensemble_members=config.ensemble_members,
        )
        self.hand = HANDRasterManager(
            resolution=config.hand_resolution,
            source=config.hand_source,
        )
        self.svi = SVILoader(year=config.svi_year, themes=config.svi_themes)
        self.mapper = HANDFloodMapper()
        self.risk_assessor = CompoundRiskAssessor()
        self.classifier = RiskClassifier()
        logger.info("FloodRiskPipeline initialized for %s", config.study_name)

    @classmethod
    def from_config(cls, config_path: str | Path) -> FloodRiskPipeline:
        """Create pipeline from a YAML configuration file."""
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        with open(path) as f:
            raw = yaml.safe_load(f)

        cfg = PipelineConfig(
            huc_id=raw.get("study_area", {}).get("huc_id", "060101"),
            study_name=raw.get("study_area", {}).get("name", "study_area"),
            forecast_type=raw.get("nwm", {}).get("forecast_type", "medium_range"),
            ensemble_members=raw.get("nwm", {}).get("ensemble_members", 7),
            hand_resolution=raw.get("hand", {}).get("resolution", 10),
            hand_source=raw.get("hand", {}).get("source", "ciroh"),
            svi_year=raw.get("svi", {}).get("year", 2022),
            svi_themes=raw.get("svi", {}).get("themes", []),
            output_dir=raw.get("output", {}).get("directory", "./output"),
            output_formats=raw.get("output", {}).get("formats", ["geotiff", "html"]),
        )
        return cls(cfg)

    def get_nwm_forecasts(
        self, huc_id: str | None = None, forecast_hours: int = 72
    ) -> dict[str, Any]:
        """Retrieve National Water Model discharge forecasts."""
        target_huc = huc_id or self.config.huc_id
        logger.info("Retrieving NWM forecasts for HUC %s (%dh)", target_huc, forecast_hours)
        return self.nwm.retrieve(huc_id=target_huc, hours=forecast_hours)

    def generate_hand_fim(
        self, forecasts: dict[str, Any], hand_resolution: int | None = None
    ) -> dict[str, Any]:
        """Generate flood inundation map from HAND and discharge forecasts."""
        res = hand_resolution or self.config.hand_resolution
        hand_raster = self.hand.load(huc_id=self.config.huc_id)
        return self.mapper.map_inundation(
            forecasts=forecasts, hand_raster=hand_raster, resolution=res
        )

    def assess_risk(
        self,
        flood_map: dict[str, Any],
        svi_year: int | None = None,
        classify: bool = True,
    ) -> dict[str, Any]:
        """Overlay social vulnerability and classify flood risk."""
        year = svi_year or self.config.svi_year
        svi_data = self.svi.load(huc_id=self.config.huc_id)
        risk = self.risk_assessor.combine(flood_map=flood_map, svi=svi_data)
        if classify:
            risk = self.classifier.classify(risk)
        return risk
