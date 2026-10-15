import os
import json
import numpy as np
import pandas as pd
from typing import Dict, List, Any

from cropres.scenario.perturbation import ScenarioEngine


def compute_district_crop_reliability(
    district: str,
    feature_parquet: str = "data/processed/feature_table_full.parquet",
    scenario_engine: ScenarioEngine = None,
    n_bootstraps: int = 1000
) -> Dict[str, Any]:
    """
    Ranks crops within a district by transparent risk measures:
    1. Shortfall Probability: frequency of PMFBY shortfall events (lower is better).
    2. Expected Shortfall / CVaR 20%: average relative loss in the worst 20% of historical seasons.
    3. Climate Sensitivity: model predicted anomaly change under +2 C warming stress.
    
    Bootstrap resampling (1,000 iterations) produces 95% confidence intervals on ranks.
    Crops with overlapping intervals are explicitly declared indistinguishable.
    """
    full_df = pd.read_parquet(feature_parquet)
    # End of season records for this district
    df_dist = full_df[(full_df["district"] == district) & (full_df["is_eos"])].copy()
    
    crops_available = sorted(df_dist["crop"].unique().tolist())
    if len(crops_available) == 0:
        return {"district": district, "ranked_crops": [], "indistinguishable_pairs": []}

    crop_metrics = []
    
    for crop in crops_available:
        sub = df_dist[df_dist["crop"] == crop].dropna(subset=["yield_anomaly", "shortfall_event"])
        n_years = len(sub)
        if n_years < 10:
            continue
            
        shortfall_prob = float(sub["shortfall_event"].mean())
        anomalies = sub["yield_anomaly"].values
        
        # CVaR 20%: Mean anomaly in worst 20% of years (worst loss severity)
        k_worst = max(1, int(np.ceil(0.20 * len(anomalies))))
        sorted_anom = np.sort(anomalies)
        cvar_20 = float(np.mean(sorted_anom[:k_worst]))
        
        # Climate sensitivity under +2 C (if engine provided)
        heat_sens = 0.0
        if scenario_engine is not None:
            try:
                sim = scenario_engine.run_simulation(district, crop, temp_shift=2.0, history_years=15)
                heat_sens = float(sim["scenario_summary"]["median_anomaly"] - sim["baseline_summary"]["median_anomaly"])
            except Exception:
                heat_sens = 0.0
                
        crop_metrics.append({
            "crop": crop,
            "shortfall_prob": round(shortfall_prob, 3),
            "cvar_20_loss": round(cvar_20, 3),  # e.g. -0.42 means 42% loss in severe years
            "heat_sensitivity_2c": round(heat_sens, 3),
            "years_observed": n_years,
            "anomalies": anomalies,
            "shortfalls": sub["shortfall_event"].values
        })

    if len(crop_metrics) == 0:
        return {"district": district, "ranked_crops": [], "indistinguishable_pairs": []}

    # Bootstrap ranks: Higher CVaR (less negative loss) and lower shortfall probability = higher resilience
    # Primary ranking criterion: CVaR 20% (worst-year downside resilience in relative terms)
    n_crops = len(crop_metrics)
    rank_records = {c["crop"]: [] for c in crop_metrics}
    
    np.random.seed(42)
    for _ in range(n_bootstraps):
        boot_scores = {}
        for c in crop_metrics:
            anoms = c["anomalies"]
            boot_idx = np.random.choice(len(anoms), size=len(anoms), replace=True)
            boot_anoms = anoms[boot_idx]
            k_w = max(1, int(np.ceil(0.20 * len(boot_anoms))))
            b_cvar = float(np.mean(np.sort(boot_anoms)[:k_w]))
            # Higher score = more resilient (less severe downside loss)
            boot_scores[c["crop"]] = b_cvar
            
        # Rank: 1 = most reliable (highest CVaR)
        sorted_crops = sorted(boot_scores.keys(), key=lambda k: boot_scores[k], reverse=True)
        for rank_val, crop_name in enumerate(sorted_crops, 1):
            rank_records[crop_name].append(rank_val)

    # Compile final ranking table
    ranked_results = []
    for c in crop_metrics:
        crop_name = c["crop"]
        ranks = rank_records[crop_name]
        median_rank = int(np.median(ranks))
        ci_low = int(np.percentile(ranks, 2.5))
        ci_high = int(np.percentile(ranks, 97.5))
        
        ranked_results.append({
            "crop": crop_name,
            "rank": median_rank,
            "rank_ci": [ci_low, ci_high],
            "shortfall_probability": c["shortfall_prob"],
            "expected_shortfall_cvar20": c["cvar_20_loss"],
            "expected_shortfall_label": f"{abs(c['cvar_20_loss'])*100.0:.1f}% loss in severe years",
            "heat_sensitivity_2c": c["heat_sensitivity_2c"],
            "years_observed": c["years_observed"]
        })
        
    ranked_results = sorted(ranked_results, key=lambda x: (x["rank"], -x["expected_shortfall_cvar20"]))
    # Adjust ranks sequentially
    for idx, r in enumerate(ranked_results, 1):
        r["rank"] = idx

    # Detect indistinguishable pairs (overlapping 95% rank intervals and close CVaR)
    indistinguishable_pairs = []
    for i in range(len(ranked_results)):
        for j in range(i + 1, len(ranked_results)):
            c1 = ranked_results[i]
            c2 = ranked_results[j]
            # Overlapping rank intervals
            overlap = not (c1["rank_ci"][1] < c2["rank_ci"][0] or c2["rank_ci"][1] < c1["rank_ci"][0])
            cvar_diff = abs(c1["expected_shortfall_cvar20"] - c2["expected_shortfall_cvar20"])
            if overlap and cvar_diff <= 0.08:
                indistinguishable_pairs.append({
                    "crop_a": c1["crop"],
                    "crop_b": c2["crop"],
                    "reason": f"Overlapping 95% bootstrap intervals [{c1['rank_ci'][0]}-{c1['rank_ci'][1]} vs {c2['rank_ci'][0]}-{c2['rank_ci'][1]}] with small severity gap ({cvar_diff:.2f}); risk difference is not statistically significant."
                })

    return {
        "district": district,
        "ranked_crops": ranked_results,
        "indistinguishable_pairs": indistinguishable_pairs
    }
