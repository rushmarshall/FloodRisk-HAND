"""Quick start example for FloodRisk-HAND."""

from floodrisk import FloodRiskPipeline

pipeline = FloodRiskPipeline.from_config("config.yaml")

forecasts = pipeline.get_nwm_forecasts(huc_id="060101", forecast_hours=72)
print(f"Retrieved {len(forecasts['reach_ids'])} reaches, {len(forecasts['timestamps'])} timesteps")

flood_map = pipeline.generate_hand_fim(forecasts=forecasts)
print(f"Max depth: {flood_map['max_depth']:.2f}m, Inundated: {flood_map['inundated_fraction']:.1%}")

risk_map = pipeline.assess_risk(flood_map=flood_map, classify=True)
print(f"Risk categories: {risk_map['category_counts']}")
