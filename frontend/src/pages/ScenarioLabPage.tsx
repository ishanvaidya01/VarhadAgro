import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { api } from '../api/client';
import type { ScenarioResponse } from '../api/client';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  ReferenceLine
} from 'recharts';
import { Download, Sliders, ShieldAlert } from 'lucide-react';

const DISTRICTS = ['Akola', 'Amravati', 'Buldhana', 'Yavatmal', 'Wardha', 'Nagpur', 'Bhandara', 'Chandrapur'];
const CROPS = ['Cotton', 'Soybean', 'Pigeonpea', 'Sorghum', 'Rice', 'Wheat', 'Chickpea'];

const PRESETS = [
  { label: 'Baseline (No shift)', temp: 0.0, precip: 0.0, heat: 0 },
  { label: 'Illustrative: +1.5 C Warming', temp: 1.5, precip: 0.0, heat: 3 },
  { label: 'Illustrative: +2.5 C & -15% Monsoon Deficit', temp: 2.5, precip: -0.15, heat: 8 },
  { label: 'Illustrative: +4.0 C & -30% Severe Stress', temp: 4.0, precip: -0.30, heat: 18 }
];

export const ScenarioLabPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();

  const district = searchParams.get('district') || 'Akola';
  const crop = searchParams.get('crop') || 'Cotton';
  const tempShift = parseFloat(searchParams.get('temp') || '1.5');
  const precipShift = parseFloat(searchParams.get('precip') || '-0.10');
  const heatDaysShift = parseInt(searchParams.get('heat') || '4', 10);

  const [result, setResult] = useState<ScenarioResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const updateParam = (key: string, val: string) => {
    const next = new URLSearchParams(searchParams);
    next.set(key, val);
    setSearchParams(next);
  };

  const applyPreset = (preset: typeof PRESETS[0]) => {
    const next = new URLSearchParams(searchParams);
    next.set('temp', preset.temp.toString());
    next.set('precip', preset.precip.toString());
    next.set('heat', preset.heat.toString());
    setSearchParams(next);
  };

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);

    api.runScenario({
      district,
      crop,
      temp_shift: tempShift,
      precip_shift: precipShift,
      heat_days_shift: heatDaysShift
    })
      .then((res) => {
        if (!isMounted) return;
        setResult(res);
        setLoading(false);
      })
      .catch((err) => {
        if (!isMounted) return;
        setError(err.message || 'Scenario simulation failed.');
        setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [district, crop, tempShift, precipShift, heatDaysShift]);

  const downloadCSV = () => {
    if (!result) return;
    const pts = result.distribution_points;
    const rows = [
      ['Year', 'Baseline_Anomaly', 'Scenario_Anomaly', 'Scenario_Shortfall_Prob']
    ];
    for (let i = 0; i < pts.years.length; i++) {
      rows.push([
        pts.years[i].toString(),
        pts.baseline_anomalies[i].toString(),
        pts.scenario_anomalies[i].toString(),
        pts.scenario_shortfall_probs[i].toString()
      ]);
    }
    const csvContent = 'data:text/csv;charset=utf-8,' + rows.map((e) => e.join(',')).join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `scenario_${district}_${crop}_T${tempShift}_P${precipShift}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Distribution chart data
  const chartData = (result?.distribution_points?.years || []).map((y, idx) => ({
    year: y,
    baseline: result?.distribution_points?.baseline_anomalies[idx] ?? 0,
    scenario: result?.distribution_points?.scenario_anomalies[idx] ?? 0
  }));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="border-b border-hairline pb-4 flex flex-wrap justify-between items-end gap-4">
        <div>
          <span className="text-xs uppercase font-mono tracking-wider text-[#5A564F]">Climate Stress Simulator</span>
          <h1 className="text-2xl sm:text-3xl font-bold font-heading text-[#1B1A17] tracking-tight">
            Scenario Lab: Change-Factor Weather Perturbation
          </h1>
          <p className="text-xs sm:text-sm text-[#5A564F] mt-1 max-w-3xl">
            Perturbs 30 years of observed daily weather by specified temperature and precipitation factors, recomputes season features, and simulates the resulting yield anomaly distribution with multivariate out-of-distribution guards.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {loading && (
            <span className="text-xs font-mono text-[#1E5144] animate-pulse">
              Simulating 30 weather seasons...
            </span>
          )}
          {result && (
            <button
              type="button"
              onClick={downloadCSV}
              className="px-3.5 py-1.5 border border-hairline bg-white text-xs font-mono font-medium text-[#1B1A17] hover:bg-[#FAF8F2] flex items-center gap-1.5"
            >
              <Download size={14} />
              <span>Export 30-Year Simulation (CSV)</span>
            </button>
          )}
        </div>
      </div>

      {/* Preset Buttons */}
      <div className="flex flex-wrap items-center gap-2 text-xs">
        <span className="font-mono text-[#5A564F] mr-1">Illustrative Presets:</span>
        {PRESETS.map((p) => {
          const isSelected =
            tempShift === p.temp && precipShift === p.precip && heatDaysShift === p.heat;
          return (
            <button
              key={p.label}
              type="button"
              onClick={() => applyPreset(p)}
              className={`px-2.5 py-1 text-xs border font-medium ${
                isSelected
                  ? 'border-[#1E5144] bg-[#1E5144] text-[#F3EFE6]'
                  : 'border-hairline bg-white text-[#5A564F] hover:text-[#1B1A17]'
              }`}
            >
              {p.label}
            </button>
          );
        })}
      </div>

      {/* Main Grid: Controls + Output */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Controls Column */}
        <div className="lg:col-span-4 bg-[#FAF8F2] border border-hairline p-5 space-y-5">
          <div className="flex items-center gap-2 border-b border-hairline pb-2">
            <Sliders size={16} className="text-[#1E5144]" />
            <h2 className="font-heading text-base font-bold text-[#1B1A17]">Perturbation Controls</h2>
          </div>

          <div className="space-y-4 text-xs">
            {/* District & Crop */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label htmlFor="scen-dist" className="font-mono text-[#5A564F] block mb-1">District:</label>
                <select
                  id="scen-dist"
                  value={district}
                  onChange={(e) => updateParam('district', e.target.value)}
                  className="w-full border border-hairline bg-white px-2 py-1.5 font-medium text-[#1B1A17] focus:outline-none"
                >
                  {DISTRICTS.map((d) => (
                    <option key={d} value={d}>{d}</option>
                  ))}
                </select>
              </div>

              <div>
                <label htmlFor="scen-crop" className="font-mono text-[#5A564F] block mb-1">Crop:</label>
                <select
                  id="scen-crop"
                  value={crop}
                  onChange={(e) => updateParam('crop', e.target.value)}
                  className="w-full border border-hairline bg-white px-2 py-1.5 font-medium text-[#1B1A17] focus:outline-none"
                >
                  {CROPS.map((c) => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Temperature Shift Slider */}
            <div className="space-y-1 pt-2 border-t border-hairline">
              <div className="flex justify-between font-mono">
                <label htmlFor="temp-slider" className="text-[#5A564F]">Temperature Shift:</label>
                <span className="font-bold text-[#1B1A17]">+{tempShift.toFixed(1)} &deg;C</span>
              </div>
              <input
                id="temp-slider"
                type="range"
                min="-1.0"
                max="5.0"
                step="0.5"
                value={tempShift}
                onChange={(e) => updateParam('temp', e.target.value)}
                className="w-full accent-[#1E5144] cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-[#847F75] font-mono">
                <span>-1.0 &deg;C</span>
                <span>+2.0 &deg;C</span>
                <span>+5.0 &deg;C</span>
              </div>
            </div>

            {/* Precipitation Factor Slider */}
            <div className="space-y-1 pt-2 border-t border-hairline">
              <div className="flex justify-between font-mono">
                <label htmlFor="precip-slider" className="text-[#5A564F]">Rainfall Perturbation:</label>
                <span className="font-bold text-[#1B1A17]">{precipShift >= 0 ? '+' : ''}{(precipShift * 100).toFixed(0)}%</span>
              </div>
              <input
                id="precip-slider"
                type="range"
                min="-0.40"
                max="0.40"
                step="0.05"
                value={precipShift}
                onChange={(e) => updateParam('precip', e.target.value)}
                className="w-full accent-[#1E5144] cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-[#847F75] font-mono">
                <span>-40% (Drought)</span>
                <span>0% (Normal)</span>
                <span>+40% (Excess)</span>
              </div>
            </div>

            {/* Additional Heat Days Slider */}
            <div className="space-y-1 pt-2 border-t border-hairline">
              <div className="flex justify-between font-mono">
                <label htmlFor="heat-slider" className="text-[#5A564F]">Additional Heat Days (&gt;38 &deg;C):</label>
                <span className="font-bold text-[#1B1A17]">+{heatDaysShift} days</span>
              </div>
              <input
                id="heat-slider"
                type="range"
                min="0"
                max="30"
                step="2"
                value={heatDaysShift}
                onChange={(e) => updateParam('heat', e.target.value)}
                className="w-full accent-[#1E5144] cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-[#847F75] font-mono">
                <span>0 days</span>
                <span>+15 days</span>
                <span>+30 days</span>
              </div>
            </div>

            <div className="pt-2 text-[11px] text-[#847F75] leading-normal border-t border-hairline">
              Note: Shifts apply daily change-factors to {result?.scenario_parameters.weather_years_simulated || 30} real historical weather seasons. Presets represent illustrative sensitivity experiments, not official IPCC/SSP forecasts.
            </div>
          </div>
        </div>

        {/* Results Column */}
        <div className="lg:col-span-8 space-y-5">
          {error && (
            <div className="p-4 border border-[#993404] bg-[#FDF6F0] text-[#993404] text-xs">
              {error}
            </div>
          )}

          {/* OOD Guard Alert Banner */}
          {result?.ood_guard.outside_observed_range && (
            <div className="p-4 border-2 border-[#D95F0E] bg-[#FFF8F0] text-[#993404] text-xs space-y-1.5">
              <div className="flex items-center gap-2 font-bold text-sm">
                <ShieldAlert size={18} className="text-[#D95F0E]" />
                <span>Out-of-Distribution Warning: Extrapolation Beyond Historical Range</span>
              </div>
              <p className="leading-relaxed">
                This perturbation pushes weather in {(result.ood_guard.ood_fraction * 100).toFixed(1)}% of simulated seasons outside the empirical training envelope (Multivariate distance ratio: {result.ood_guard.distance_ratio.toFixed(2)}x historical p95).
                {result.ood_guard.extreme_features.length > 0 && (
                  <span> Extreme variables: {result.ood_guard.extreme_features.join(', ')}.</span>
                )}
              </p>
              <p className="text-[11px] text-[#847F75]">
                Tree-based regressions cannot extrapolate monotonically outside training boundaries; uncertainty intervals have been automatically widened.
              </p>
            </div>
          )}

          {/* Summary Metrics Cards */}
          {result && (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="p-3.5 bg-[#FAF8F2] border border-hairline">
                <span className="text-xs text-[#5A564F] block">Median Anomaly Shift</span>
                <span className="text-xl font-mono font-bold text-[#1B1A17] mt-0.5 block">
                  {result.scenario_summary.median_anomaly >= 0 ? '+' : ''}
                  {(result.scenario_summary.median_anomaly * 100).toFixed(1)}%
                </span>
                <span className="text-[11px] text-[#847F75] block mt-1">
                  Baseline: {(result.baseline_summary.median_anomaly * 100).toFixed(1)}%
                </span>
              </div>

              <div className="p-3.5 bg-[#FAF8F2] border border-hairline">
                <span className="text-xs text-[#5A564F] block">Shortfall Probability</span>
                <span className="text-xl font-mono font-bold text-[#1B1A17] mt-0.5 block">
                  {(result.scenario_summary.shortfall_probability * 100).toFixed(1)}%
                </span>
                <span className="text-[11px] text-[#847F75] block mt-1">
                  Delta: {result.scenario_summary.delta_shortfall_prob >= 0 ? '+' : ''}
                  {(result.scenario_summary.delta_shortfall_prob * 100).toFixed(1)}% vs baseline
                </span>
              </div>

              <div className="p-3.5 bg-[#FAF8F2] border border-hairline">
                <span className="text-xs text-[#5A564F] block">OOD Weather Fraction</span>
                <span className={`text-xl font-mono font-bold mt-0.5 block ${result.ood_guard.outside_observed_range ? 'text-[#D95F0E]' : 'text-[#1E5144]'}`}>
                  {(result.ood_guard.ood_fraction * 100).toFixed(1)}%
                </span>
                <span className="text-[11px] text-[#847F75] block mt-1">
                  {result.ood_guard.outside_observed_range ? 'Above 25% tolerance' : 'Within observed bounds'}
                </span>
              </div>
            </div>
          )}

          {/* Distribution Chart across 30 weather years */}
          <div className="bg-[#FAF8F2] border border-hairline p-5 space-y-3">
            <div className="flex flex-wrap justify-between items-baseline gap-2 border-b border-hairline pb-2">
              <div>
                <h3 className="font-heading text-base font-bold text-[#1B1A17]">
                  Simulation Distribution Across 30 Historical Weather Years
                </h3>
                <span className="text-xs text-[#5A564F]">
                  Shows how each historical year would perform under the perturbed climate.
                </span>
              </div>
              <div className="flex items-center gap-4 text-xs font-mono">
                <span className="flex items-center gap-1.5">
                  <span className="w-3 h-0.5 bg-[#847F75] inline-block"></span> Baseline Anomaly
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-3 h-0.5 bg-[#1E5144] inline-block"></span> Perturbed Scenario
                </span>
              </div>
            </div>

            <div className="h-64 w-full pt-2">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#D6CFBF" vertical={false} />
                  <XAxis dataKey="year" stroke="#5A564F" tick={{ fontSize: 11 }} />
                  <YAxis
                    stroke="#5A564F"
                    tick={{ fontSize: 11 }}
                    tickFormatter={(val) => `${(val * 100).toFixed(0)}%`}
                  />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#FAF8F2', borderColor: '#D6CFBF', fontSize: '12px' }}
                    formatter={(val: any, name: any) => {
                      if (typeof val === 'number') {
                        return [`${(val * 100).toFixed(1)}%`, name === 'baseline' ? 'Baseline Anomaly' : 'Scenario Anomaly'];
                      }
                      return [val, name];
                    }}
                  />
                  <ReferenceLine y={0} stroke="#847F75" strokeWidth={1} />
                  <Line
                    type="monotone"
                    dataKey="baseline"
                    stroke="#847F75"
                    strokeWidth={1.5}
                    strokeDasharray="3 3"
                    dot={false}
                    name="baseline"
                  />
                  <Line
                    type="monotone"
                    dataKey="scenario"
                    stroke="#1E5144"
                    strokeWidth={2}
                    dot={{ r: 2.5, fill: '#1E5144' }}
                    name="scenario"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
