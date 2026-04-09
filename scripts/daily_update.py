#!/usr/bin/env python3
"""Daily flood warning monitor.

Queries NOAA public APIs for active flood warnings and NWM operational
status, then writes a Markdown summary to docs/flood-monitor.md and a
regional bar chart to docs/flood-warnings.png.
"""

import json
import os
import pathlib
from datetime import datetime, timezone

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import requests

DOCS_DIR = pathlib.Path(__file__).resolve().parent.parent / "docs"
MONITOR_MD = DOCS_DIR / "flood-monitor.md"
CHART_PNG = DOCS_DIR / "flood-warnings.png"

ALERTS_URL = "https://api.weather.gov/alerts/active?event=Flood Warning"
NWM_STATUS_URL = (
    "https://api.water.noaa.gov/nwps/v1/gauges?srid=nwm"
)

HEADERS = {
    "User-Agent": "FloodRisk-HAND-Monitor/1.0 (github.com/rushmarshall/FloodRisk-HAND)",
    "Accept": "application/geo+json",
}

# US state → region mapping
STATE_TO_REGION = {}
_REGIONS = {
    "Northeast": [
        "CT", "DE", "MA", "MD", "ME", "NH", "NJ", "NY", "PA", "RI", "VT",
    ],
    "Southeast": [
        "AL", "AR", "DC", "FL", "GA", "KY", "LA", "MS", "NC", "SC", "TN",
        "VA", "WV",
    ],
    "Midwest": [
        "IA", "IL", "IN", "KS", "MI", "MN", "MO", "ND", "NE", "OH", "OK",
        "SD", "WI",
    ],
    "West": [
        "AZ", "CO", "ID", "MT", "NM", "NV", "UT", "WY",
    ],
    "Pacific": [
        "AK", "CA", "HI", "OR", "WA",
    ],
    "Territories": [
        "AS", "GU", "MP", "PR", "VI",
    ],
}
for _region, _states in _REGIONS.items():
    for _st in _states:
        STATE_TO_REGION[_st] = _region

REGION_ORDER = ["Northeast", "Southeast", "Midwest", "West", "Pacific", "Territories"]


def fetch_flood_warnings() -> list[dict]:
    """Return list of active flood warning features from api.weather.gov."""
    resp = requests.get(ALERTS_URL, headers=HEADERS, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    return data.get("features", [])


def check_nwm_status() -> str:
    """Probe the NOAA NWM API and return a short status string."""
    try:
        resp = requests.get(NWM_STATUS_URL, headers=HEADERS, timeout=30)
        if resp.status_code == 200:
            return "Operational"
        return f"Degraded (HTTP {resp.status_code})"
    except requests.RequestException as exc:
        return f"Unavailable ({exc})"


def warnings_by_state(features: list[dict]) -> dict[str, int]:
    """Count warnings per two-letter state code."""
    counts: dict[str, int] = {}
    for feat in features:
        props = feat.get("properties", {})
        # areaDesc often looks like "County, ST; County, ST"
        area = props.get("areaDesc", "")
        # geocode.UGC contains state prefix e.g. ["TXC201", "TXC113"]
        ugc_codes = (
            props.get("geocode", {}).get("UGC", [])
            or props.get("geocode", {}).get("SAME", [])
        )
        seen: set[str] = set()
        for code in ugc_codes:
            st = code[:2]
            if st.isalpha() and st not in seen:
                seen.add(st)
                counts[st] = counts.get(st, 0) + 1
        # Fallback: parse from areaDesc if no UGC
        if not seen:
            for part in area.replace(";", ",").split(","):
                token = part.strip().split()
                if token:
                    candidate = token[-1].upper()
                    if len(candidate) == 2 and candidate.isalpha():
                        counts[candidate] = counts.get(candidate, 0) + 1
    return counts


def aggregate_by_region(state_counts: dict[str, int]) -> dict[str, int]:
    """Roll up state counts into region totals."""
    region_counts: dict[str, int] = {r: 0 for r in REGION_ORDER}
    for st, n in state_counts.items():
        region = STATE_TO_REGION.get(st, "Territories")
        region_counts[region] = region_counts.get(region, 0) + n
    return region_counts


def generate_chart(region_counts: dict[str, int]) -> None:
    """Save a bar chart of flood warnings by region."""
    regions = REGION_ORDER
    values = [region_counts.get(r, 0) for r in regions]

    fig, ax = plt.subplots(figsize=(8, 4))
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]
    bars = ax.bar(regions, values, color=colors[: len(regions)], edgecolor="black",
                  linewidth=0.5)

    for bar, val in zip(bars, values):
        if val > 0:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                    str(val), ha="center", va="bottom", fontsize=10, fontweight="bold")

    ax.set_ylabel("Active Flood Warnings")
    ax.set_title("Active NOAA Flood Warnings by Region")
    ax.set_ylim(0, max(max(values) * 1.2, 1))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(str(CHART_PNG), dpi=150)
    plt.close(fig)
    print(f"Chart saved → {CHART_PNG}")


def write_markdown(
    total: int,
    state_counts: dict[str, int],
    region_counts: dict[str, int],
    nwm_status: str,
    checked_at: str,
) -> str:
    """Generate the flood-monitor.md content and write it. Return content."""
    top_states = sorted(state_counts.items(), key=lambda x: -x[1])[:10]
    top_table = "\n".join(
        f"| {st} | {n} |" for st, n in top_states
    ) if top_states else "| — | 0 |"

    content = f"""# 🌊 Flood Warning Monitor

> Auto-generated by [daily-update workflow](../.github/workflows/daily-update.yml).
> **Last checked:** {checked_at}

## Summary

| Metric | Value |
|--------|-------|
| Active Flood Warnings | **{total}** |
| NWM Operational Status | {nwm_status} |
| States Affected | {len(state_counts)} |

## Regional Distribution

![Flood warnings by region](flood-warnings.png)

| Region | Warnings |
|--------|----------|
""" + "\n".join(
        f"| {r} | {region_counts.get(r, 0)} |" for r in REGION_ORDER
    ) + f"""

## Top States

| State | Warnings |
|-------|----------|
{top_table}

---
*Data source: [NOAA Weather Alerts API](https://api.weather.gov/alerts/active?event=Flood+Warning)*
"""
    MONITOR_MD.write_text(content)
    print(f"Markdown saved → {MONITOR_MD}")
    return content


def main() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    checked_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    print("Fetching active flood warnings …")
    try:
        features = fetch_flood_warnings()
    except requests.RequestException as exc:
        print(f"⚠ Could not fetch alerts: {exc}")
        features = []

    total = len(features)
    print(f"  → {total} active flood warning(s)")

    state_counts = warnings_by_state(features)
    region_counts = aggregate_by_region(state_counts)

    print("Checking NWM operational status …")
    nwm_status = check_nwm_status()
    print(f"  → {nwm_status}")

    write_markdown(total, state_counts, region_counts, nwm_status, checked_at)
    generate_chart(region_counts)

    print("Done ✓")


if __name__ == "__main__":
    main()
