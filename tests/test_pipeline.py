"""Tests for the FloodRisk-HAND pipeline."""
import numpy as np
import pytest


def test_nwm_retriever():
    from floodrisk.data.nwm import NWMForecastRetriever
    nwm = NWMForecastRetriever(forecast_type="medium_range")
    result = nwm.retrieve(huc_id="060101", hours=24)
    assert "streamflow" in result
    assert result["streamflow"].shape[0] == 24
    assert len(result["reach_ids"]) > 0


def test_hand_raster():
    from floodrisk.data.hand import HANDRasterManager
    mgr = HANDRasterManager(resolution=10)
    raster = mgr.load(huc_id="060101")
    assert raster.data.shape[0] > 0
    assert raster.crs == "EPSG:4326"


def test_svi_loader():
    from floodrisk.data.svi import SVILoader
    svi = SVILoader(year=2022)
    data = svi.load(huc_id="060101")
    assert len(data.tract_ids) > 0
    assert 0 <= data.overall_svi.mean() <= 1


def test_fim_mapper():
    from floodrisk.data.nwm import NWMForecastRetriever
    from floodrisk.data.hand import HANDRasterManager
    from floodrisk.models.fim import HANDFloodMapper
    nwm = NWMForecastRetriever()
    forecasts = nwm.retrieve("060101", hours=6)
    hand = HANDRasterManager().load("060101")
    mapper = HANDFloodMapper()
    result = mapper.map_inundation(forecasts, hand)
    assert "depth_grid" in result
    assert result["max_depth"] >= 0


def test_risk_classifier():
    from floodrisk.models.classify import RiskClassifier
    classifier = RiskClassifier()
    risk_grid = np.random.uniform(0, 1, (100, 100))
    result = classifier.classify({"risk_grid": risk_grid})
    assert "classified_grid" in result
    assert set(np.unique(result["classified_grid"])).issubset({0, 1, 2, 3, 4})


def test_invalid_forecast_type():
    from floodrisk.data.nwm import NWMForecastConfig
    with pytest.raises(ValueError):
        NWMForecastConfig(forecast_type="invalid")
