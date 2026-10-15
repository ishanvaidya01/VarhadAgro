import { API_BASE } from './config';

export interface Provenance {
  yield_source: string;
  weather_source: string;
  spatial_resolution: string;
  history_span: string;
  model_version: string;
  build_date: string;
}

export interface DistrictInfo {
  id: string;
  name: string;
  parent_1966: string;
  modern_districts_included: string[];
  subregion: string;
  centroid: [number, number];
  primary_soil: string;
  irrigation_pct: number;
}

export interface CropInfo {
  crop: string;
  season_type: 'Kharif' | 'Rabi';
  start_month_day: string;
  cutoffs: string[];
  base_temp_c: number;
  description: string;
}

export interface RiskDistrictRecord {
  district: string;
  subregion: string;
  year: number;
  crop: string;
  cutoff: string;
  predicted_shortfall_prob: number | null;
  predicted_anomaly: number | null;
  ci_lower: number | null;
  ci_upper: number | null;
  shortfall_pred_class: number;
  actual_shortfall_event: number | null;
  actual_yield_anomaly: number | null;
  top_drivers: string;
  message?: string;
}

export interface RiskMapResponse {
  crop: string;
  cutoff: string;
  year: number;
  available_years: number[];
  decision_threshold: number;
  districts: RiskDistrictRecord[];
  provenance: Provenance;
}

export interface HistoryRecord {
  year: number;
  yield_kg_ha: number | null;
  trend_asof: number | null;
  yield_anomaly: number | null;
  pmfby_threshold_80: number | null;
  shortfall_event: number | null;
}

export interface BacktestRecord {
  year: number;
  actual_yield_kg_ha: number;
  actual_anomaly: number;
  predicted_anomaly: number;
  ci_lower: number;
  ci_upper: number;
  in_interval: boolean;
  predicted_shortfall_prob: number;
  shortfall_pred_class: number;
  actual_shortfall_event: number;
  top_drivers: string;
}

export interface DistrictDetailResponse {
  district: string;
  crop: string;
  history: HistoryRecord[];
  backtest: BacktestRecord[];
  skill_assessment: {
    skill_pct: number;
    status: 'beats_baseline' | 'exposure_only';
    statement: string;
    conformal_test_coverage_pct: number;
  };
  provenance: Provenance;
}

export interface LeadTimeRecord {
  cutoff: string;
  stage: string;
  lead_days: number;
  rmse: number;
  skill_score: number;
  pr_auc: number;
  samples: number;
}

export interface SeasonTrackerResponse {
  crop: string;
  lead_time_skill_progression: LeadTimeRecord[];
  season_tracker: {
    district: string;
    recent_observed_year: number;
    season: string;
    cumulative_rainfall_mm: number;
    historical_normal_mm: number;
    percent_of_normal: number;
    dry_days_in_monsoon: number;
    rainfall_status: string;
    note: string;
  };
  provenance: Provenance;
}

export interface ScenarioResponse {
  district: string;
  crop: string;
  scenario_parameters: {
    temp_shift_c: number;
    precip_shift_pct: number;
    heat_days_shift: number;
    weather_years_simulated: number;
  };
  ood_guard: {
    ood_fraction: number;
    outside_observed_range: boolean;
    mean_multivariate_distance: number;
    training_p95_distance: number;
    distance_ratio: number;
    extreme_features: string[];
    warning: string | null;
  };
  baseline_summary: {
    median_anomaly: number;
    anomaly_iqr: [number, number];
    shortfall_probability: number;
  };
  scenario_summary: {
    median_anomaly: number;
    anomaly_iqr: [number, number];
    shortfall_probability: number;
    delta_shortfall_prob: number;
    ci_lower_median: number;
    ci_upper_median: number;
  };
  distribution_points: {
    years: number[];
    baseline_anomalies: number[];
    scenario_anomalies: number[];
    scenario_shortfall_probs: number[];
  };
  provenance: Provenance;
}

export interface RankedCrop {
  crop: string;
  rank: number;
  rank_ci: [number, number];
  shortfall_probability: number;
  expected_shortfall_cvar20: number;
  expected_shortfall_label: string;
  heat_sensitivity_2c: number;
  years_observed: number;
}

export interface IndistinguishablePair {
  crop_a: string;
  crop_b: string;
  reason: string;
}

export interface ReliabilityResponse {
  district: string;
  ranked_crops: RankedCrop[];
  indistinguishable_pairs: IndistinguishablePair[];
  provenance: Provenance;
}

export interface AnalogItem {
  district: string;
  subregion: string;
  climate_distance: number;
  current_climate: {
    season_rainfall_mm: number;
    rainfall_cv: number;
    tmax_mean_c: number;
    heat_days_38: number;
  };
  dominant_crops: Array<{
    crop: string;
    area_1000ha: number;
    area_share_pct: number;
  }>;
}

export interface AnalogsResponse {
  target_district: string;
  perturbation: {
    temp_shift_c: number;
    precip_shift_pct: number;
    heat_days_shift: number;
  };
  analogs: AnalogItem[];
  disclaimer: string;
  provenance: Provenance;
}

export interface EvidenceResponse {
  metrics: {
    evaluation_period: string;
    total_test_instances: number;
    prevalence: number;
    regression: {
      baseline_a: { rmse: number; skill_score: number; mae: number };
      ridge_panel: { rmse: number; skill_score: number; mae: number };
      lightgbm_median: { rmse: number; skill_score: number; mae: number; spearman_rank_correlation: number };
    };
    classification: {
      baseline_b_historical_rate: { brier_score: number };
      calibrated_shortfall_classifier: {
        pr_auc: number;
        brier_score: number;
        brier_skill_score: number;
        decision_threshold: number;
        precision: number;
        recall: number;
        f1_score: number;
        false_alarm_rate: number;
      };
    };
    uncertainty_conformal_cqr: {
      target_coverage: number;
      empirical_coverage_overall: number;
      mean_interval_width: number;
      coverage_by_crop: Record<string, { coverage: number; n_samples: number; mean_width: number }>;
      coverage_by_district: Record<string, { coverage: number; n_samples: number }>;
    };
    early_warning_lead_time: LeadTimeRecord[];
  };
  plots_data: {
    calibration_curve: { prob_pred: number[]; prob_true: number[] };
    pr_curve: { recall: number[]; precision: number[] };
    lead_time_skill: Array<{ cutoff: string; lead_days: number; skill_score: number; pr_auc: number }>;
    crop_coverage: Record<string, number>;
  };
  model_card_summary: {
    framework: string;
    conformal_target_coverage: string;
    empirical_test_coverage: string;
    test_period: string;
    validation_period: string;
    training_period: string;
    test_skill_rmse: string;
    pr_auc_test: number;
    test_prevalence: number;
  };
  provenance: Provenance;
}

async function fetchJson<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const response = await fetch(url, options);
  if (!response.ok) {
    let errorMsg = `HTTP Error ${response.status}: ${response.statusText}`;
    try {
      const errJson = await response.json();
      if (errJson && errJson.message) {
        errorMsg = errJson.message;
      }
    } catch {
      // Use fallback
    }
    throw new Error(errorMsg);
  }
  return response.json();
}

export const api = {
  getMeta: () => fetchJson<{ provenance: Provenance; districts_count: number; crops: string[] }>('/api/meta'),
  getDistricts: () => fetchJson<{ districts: DistrictInfo[]; geojson: GeoJSON.FeatureCollection }>('/api/districts'),
  getCrops: () => fetchJson<{ crops: CropInfo[] }>('/api/crops'),
  getRiskMap: (crop: string, cutoff?: string, year?: number) => {
    const params = new URLSearchParams({ crop });
    if (cutoff) params.set('cutoff', cutoff);
    if (year) params.set('year', year.toString());
    return fetchJson<RiskMapResponse>(`/api/risk-map?${params.toString()}`);
  },
  getDistrictDetail: (district: string, crop: string) => {
    const params = new URLSearchParams({ crop });
    return fetchJson<DistrictDetailResponse>(`/api/district/${encodeURIComponent(district)}?${params.toString()}`);
  },
  getEarlyWarning: (crop: string, district?: string) => {
    const params = new URLSearchParams({ crop });
    if (district) params.set('district', district);
    return fetchJson<SeasonTrackerResponse>(`/api/early-warning?${params.toString()}`);
  },
  runScenario: (payload: {
    district: string;
    crop: string;
    temp_shift: number;
    precip_shift: number;
    heat_days_shift: number;
    history_years?: number;
  }) => {
    return fetchJson<ScenarioResponse>('/api/scenario', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
  },
  getReliability: (district: string) => {
    const params = new URLSearchParams({ district });
    return fetchJson<ReliabilityResponse>(`/api/reliability?${params.toString()}`);
  },
  getAnalogs: (district: string, temp_shift = 0.0, precip_shift = 0.0, heat_days_shift = 0, top_k = 4) => {
    const params = new URLSearchParams({
      district,
      temp_shift: temp_shift.toString(),
      precip_shift: precip_shift.toString(),
      heat_days_shift: heat_days_shift.toString(),
      top_k: top_k.toString()
    });
    return fetchJson<AnalogsResponse>(`/api/analogs?${params.toString()}`);
  },
  getEvidence: () => fetchJson<EvidenceResponse>('/api/evidence')
};
