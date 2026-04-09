"""Interactive flood risk map generation using Folium."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

RISK_COLORS = {
    0: "#f0f0f0",  # None — light grey
    1: "#bdbdbd",  # Minor — grey
    2: "#737373",  # Moderate — dark grey
    3: "#333333",  # Major — charcoal
    4: "#000000",  # Extreme — black
}


def create_risk_map(
    risk_data: dict[str, Any],
    output_path: str | Path = "risk_map.html",
    title: str = "Flood Risk Assessment",
) -> Path:
    """Generate an interactive Folium map of classified flood risk.

    Parameters
    ----------
    risk_data : dict
        Classified risk assessment output.
    output_path : str or Path
        Where to save the HTML map.
    title : str
        Map title.

    Returns
    -------
    Path
        Path to the saved map file.
    """
    try:
        import folium
        from folium.plugins import FloatImage
    except ImportError:
        raise ImportError("folium required for interactive maps: pip install folium")

    bounds = risk_data["bounds"]
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=10,
        tiles="CartoDB positron",
    )

    classified = risk_data.get("classified_grid")
    if classified is not None:
        from folium.raster_layers import ImageOverlay

        rgba = np.zeros((*classified.shape, 4), dtype=np.uint8)
        for code, hex_color in RISK_COLORS.items():
            mask = classified == code
            r = int(hex_color[1:3], 16)
            g = int(hex_color[3:5], 16)
            b = int(hex_color[5:7], 16)
            rgba[mask] = [r, g, b, 180 if code > 0 else 0]

        ImageOverlay(
            image=rgba,
            bounds=[[bounds[1], bounds[0]], [bounds[3], bounds[2]]],
            opacity=0.7,
            name="Flood Risk",
        ).add_to(m)

    folium.LayerControl().add_to(m)

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    m.save(str(out))
    logger.info("Risk map saved to %s", out)
    return out
