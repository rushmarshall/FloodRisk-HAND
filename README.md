<img width="100%" src="https://capsule-render.vercel.app/api?type=waving&color=0:111111,30:333333,60:666666,100:999999&height=180&section=header&text=FloodRisk-HAND&fontSize=42&fontColor=FFFFFF&animation=fadeIn&fontAlignY=36&desc=Flood%20Inundation%20Mapping%20%26%20Social%20Vulnerability%20Assessment&descSize=14&descColor=CCCCCC&descAlignY=56"/>

<p align="center">
<img src="https://img.shields.io/badge/Python-3.9+-333333?style=flat-square&logo=python&logoColor=white" alt="Python"/>
<img src="https://img.shields.io/badge/License-MIT-333333?style=flat-square" alt="License"/>
<img src="https://img.shields.io/badge/NOAA-NWM-333333?style=flat-square&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNiIgaGVpZ2h0PSIxNiI+PGNpcmNsZSBjeD0iOCIgY3k9IjgiIHI9IjciIGZpbGw9Im5vbmUiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMS41Ii8+PC9zdmc+&logoColor=white" alt="NOAA"/>
<img src="https://img.shields.io/badge/HAND--FIM-333333?style=flat-square" alt="HAND-FIM"/>
</p>

---

## Overview

**FloodRisk-HAND** is a Python framework for flood inundation mapping using the Height Above Nearest Drainage (HAND) method combined with NOAA National Water Model (NWM) forecasts and CDC Social Vulnerability Index (SVI) data. It provides an end-to-end pipeline from forecast retrieval to compound flood risk assessment.

Designed for researchers, emergency managers, and engineers working on real-time flood forecasting and community resilience — particularly for coastal regions and Small Island Developing States.

---

## Features

- **NWM Forecast Retrieval** — Access NOAA National Water Model discharge forecasts via cloud APIs
- **HAND-FIM Mapping** — Generate flood depth grids using Height Above Nearest Drainage methodology
- **Social Vulnerability** — Integrate CDC SVI data for equity-informed risk assessment
- **Compound Flood Risk** — Combine fluvial, pluvial, and coastal flood drivers
- **Risk Classification** — Quantile-based severity mapping (Minor / Moderate / Major / Extreme)
- **Interactive Visualization** — Folium-based web maps with risk overlays
- **Configurable Pipelines** — YAML-driven workflow configuration

---

## Installation

```bash
pip install floodrisk-hand
```

Or from source:

```bash
git clone https://github.com/rushmarshall/FloodRisk-HAND.git
cd FloodRisk-HAND
pip install -e ".[dev]"
```

---

## Quick Start

```python
from floodrisk import FloodRiskPipeline

pipeline = FloodRiskPipeline.from_config("config.yaml")

# Retrieve NWM forecasts for a watershed
forecasts = pipeline.get_nwm_forecasts(
    huc_id="060101",
    forecast_hours=72
)

# Generate HAND-FIM flood depth map
flood_map = pipeline.generate_hand_fim(
    forecasts=forecasts,
    hand_resolution=10  # meters
)

# Overlay social vulnerability
risk_map = pipeline.assess_risk(
    flood_map=flood_map,
    svi_year=2022,
    classify=True  # Minor/Moderate/Major/Extreme
)

# Export results
risk_map.to_geotiff("output/flood_risk.tif")
risk_map.to_interactive_map("output/risk_map.html")
```

---

## Architecture

```
floodrisk/
├── data/           # Data retrieval (NWM, HAND, SVI)
│   ├── nwm.py          National Water Model forecast access
│   ├── hand.py         HAND raster acquisition and processing
│   └── svi.py          CDC Social Vulnerability Index loader
├── models/         # Risk modeling
│   ├── fim.py          Flood Inundation Mapping (HAND-FIM)
│   ├── compound.py     Compound flood risk aggregation
│   └── classify.py     Severity classification engine
├── visualization/  # Output generation
│   ├── maps.py         Interactive Folium/Leaflet maps
│   └── reports.py      Statistical summary reports
└── pipeline.py     # End-to-end orchestration
```

---

## Configuration

```yaml
study_area:
  huc_id: "060101"
  name: "Upper French Broad"

nwm:
  forecast_type: "medium_range"
  ensemble_members: 7

hand:
  resolution: 10
  source: "ciroh"

svi:
  year: 2022
  themes: ["socioeconomic", "household", "minority", "housing"]

output:
  formats: ["geotiff", "html", "json"]
  directory: "./output"
```

---

## Contributing

Contributions welcome. Please open an issue to discuss proposed changes before submitting a pull request.

```bash
git clone https://github.com/rushmarshall/FloodRisk-HAND.git
cd FloodRisk-HAND
pip install -e ".[dev]"
pytest
```

---

<p align="center">
<sub>Developed at Hydrosense Lab, University of Virginia</sub>
<br>
<sub>Part of the Global Hydrology and Water Resources research group</sub>
</p>

<img width="100%" src="https://capsule-render.vercel.app/api?type=waving&color=0:999999,30:666666,60:333333,100:111111&height=100&section=footer"/>
