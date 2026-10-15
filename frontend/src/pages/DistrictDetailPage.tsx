import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { api } from '../api/client';
import type { DistrictDetailResponse } from '../api/client';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  AreaChart, Area, ReferenceLine
} from 'recharts';
import { AlertTriangle, CheckCircle, Info } from 'lucide-react';

const DISTRICTS = ['Akola', 'Amravati', 'Buldhana', 'Yavatmal', 'Wardha', 'Nagpur', 'Bhandara', 'Chandrapur'];
const CROPS = ['Cotton', 'Soybean', 'Pigeonpea', 'Sorghum', 'Rice', 'Wheat', 'Chickpea'];

export const DistrictDetailPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const districtParam = searchParams.get('district') || 'Akola';
  const cropParam = searchParams.get('crop') || 'Cotton';

  const [data, setData] = useState<DistrictDetailResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);

    api.getDistrictDetail(districtParam, cropParam)
      .then((res) => {
        if (!isMounted) return;
        setData(res);
        setLoading(false);
      })
      .catch((err) => {
        if (!isMounted) return;
        setError(err.message || 'Failed to load district historical yield series.');
        setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [districtParam, cropParam]);

  const updateParam = (key: string, val: string) => {
    const next = new URLSearchParams(searchParams);
    next.set(key, val);
    setSearchParams(next);
  };

  // Prepare backtest chart data with error bounds
  const backtestChartData = (data?.backtest || []).map((b) => ({
    year: b.year,
    actual_anomaly: b.actual_anomaly,
    predicted_anomaly: b.predicted_anomaly,
    ci_lower: b.ci_lower,
    ci_upper: b.ci_upper,
    in_interval: b.in_interval,
    actual_shortfall_event: b.actual_shortfall_event,
    predicted_shortfall_prob: b.predicted_shortfall_prob
  }));

  return (
    <div className="space-y-6">
      {/* Editorial Header */}
      <div className="border-b border-hairline pb-4 flex flex-wrap justify-between items-end gap-4">
        <div>
          <span className="text-xs uppercase font-mono tracking-wider text-[#5A564F]">Detailed Evidence Series</span>
          <h1 className="text-2xl sm:text-3xl font-bold font-heading text-[#1B1A17] tracking-tight">
            {districtParam} &bull; {cropParam} Yield Series
          </h1>
          <p className="text-xs sm:text-sm text-[#5A564F] mt-1 max-w-2xl">
            52-year observed yield trajectory (1966-2017) with expanding as-of trend, PMFBY-style shortfall threshold, and 10-year out-of-sample backtest with conformal prediction intervals.
          </p>
        </div>

        {/* District & Crop Selectors */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-1.5 text-xs">
            <label htmlFor="dist-sel" className="font-mono text-[#5A564F]">District:</label>
            <select
              id="dist-sel"
              value={districtParam}
              onChange={(e) => updateParam('district', e.target.value)}
              className="border border-hairline bg-white px-2 py-1 text-xs font-medium text-[#1B1A17] focus:outline-none focus:border-[#1E5144]"
            >
              {DISTRICTS.map((d) => (
                <option key={d} value={d}>{d}</option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-1.5 text-xs">
            <label htmlFor="crop-sel" className="font-mono text-[#5A564F]">Crop:</label>
            <select
              id="crop-sel"
              value={cropParam}
              onChange={(e) => updateParam('crop', e.target.value)}
              className="border border-hairline bg-white px-2 py-1 text-xs font-medium text-[#1B1A17] focus:outline-none focus:border-[#1E5144]"
            >
              {CROPS.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-5 border border-[#D95F0E] bg-[#FFFBF5] text-[#1B1A17] text-sm space-y-3">
          <div className="flex items-start gap-3">
            <AlertTriangle size={20} className="shrink-0 mt-0.5 text-[#D95F0E]" />
            <div>
              <p className="font-bold text-[#993404]">Data Not Available: {error}</p>
              <p className="text-xs text-[#5A564F] mt-1">
                {cropParam} is not commercially cultivated in {districtParam} (for example, Eastern Vidarbha districts like Bhandara are predominantly rice/wetland ecosystems and do not report official cotton acreage).
              </p>
            </div>
          </div>
          <div className="pt-2 border-t border-hairline text-xs">
            <span className="font-semibold text-[#1B1A17] block mb-2">Switch to a cultivated crop in {districtParam}:</span>
            <div className="flex flex-wrap gap-2">
              {CROPS.filter((c) => c !== cropParam).map((c) => (
                <button
                  key={c}
                  type="button"
                  onClick={() => updateParam('crop', c)}
                  className="px-3 py-1.5 bg-white border border-hairline font-medium text-[#1E5144] hover:bg-[#FAF8F2] transition-colors"
                >
                  Inspect {c}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {loading && !data ? (
        <div className="h-96 border border-hairline bg-[#FAF8F2] flex items-center justify-center text-[#5A564F] text-sm">
          Loading 52-year historical records and backtest predictions...
        </div>
      ) : data ? (
        <div className="space-y-8">
          {/* Skill Assessment Banner (First line honesty) */}
          <div
            className={`p-4 border text-xs sm:text-sm flex items-start gap-3 ${
              data.skill_assessment.status === 'beats_baseline'
                ? 'bg-[#F2F7F4] border-[#1E5144] text-[#1B1A17]'
                : 'bg-[#FAF8F2] border-[#D6CFBF] text-[#5A564F]'
            }`}
          >
            {data.skill_assessment.status === 'beats_baseline' ? (
              <CheckCircle size={18} className="text-[#1E5144] shrink-0 mt-0.5" />
            ) : (
              <Info size={18} className="text-[#847F75] shrink-0 mt-0.5" />
            )}
            <div>
              <span className="font-semibold text-[#1B1A17]">Measured Out-of-Sample Skill: </span>
              <span>{data.skill_assessment.statement}</span>
              <div className="text-xs text-[#5A564F] mt-1 font-mono">
                Historical Held-Out Coverage: {data.skill_assessment.conformal_test_coverage_pct}% within 90% prediction band.
              </div>
            </div>
          </div>

          {/* Section 1: 52-Year Historical Yield Chart */}
          <div className="bg-[#FAF8F2] border border-hairline p-5 space-y-3">
            <div className="flex flex-wrap justify-between items-baseline gap-2 border-b border-hairline pb-2">
              <div>
                <h2 className="font-heading text-lg font-bold text-[#1B1A17]">
                  Historical Yield Trajectory &amp; PMFBY Shortfall Threshold
                </h2>
                <span className="text-xs text-[#5A564F]">
                  Observed annual kg/ha from ICRISAT DLD (1966-2017). Red dots indicate seasons where yield fell below 80% threshold.
                </span>
              </div>
              <div className="flex items-center gap-4 text-xs font-mono">
                <span className="flex items-center gap-1.5">
                  <span className="w-3 h-0.5 bg-[#1B1A17] inline-block"></span> Actual Yield
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-3 h-0.5 bg-[#1E5144] inline-block"></span> Expanding Trend
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-3 h-0.5 border-t border-dashed border-[#D95F0E] inline-block"></span> 80% Threshold
                </span>
              </div>
            </div>

            <div className="h-72 w-full pt-2">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data.history} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#D6CFBF" vertical={false} />
                  <XAxis dataKey="year" stroke="#5A564F" tick={{ fontSize: 11 }} />
                  <YAxis stroke="#5A564F" tick={{ fontSize: 11 }} unit=" kg" />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#FAF8F2', borderColor: '#D6CFBF', fontSize: '12px' }}
                    formatter={(value: any, name: any) => {
                      if (name === 'yield_kg_ha') return [`${value} kg/ha`, 'Observed Yield'];
                      if (name === 'trend_asof') return [`${value} kg/ha`, 'As-of Trend'];
                      if (name === 'pmfby_threshold_80') return [`${value} kg/ha`, '80% Threshold'];
                      return [value, name];
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="trend_asof"
                    stroke="#1E5144"
                    strokeWidth={1.5}
                    dot={false}
                    name="trend_asof"
                  />
                  <Line
                    type="monotone"
                    dataKey="pmfby_threshold_80"
                    stroke="#D95F0E"
                    strokeWidth={1.5}
                    strokeDasharray="4 4"
                    dot={false}
                    name="pmfby_threshold_80"
                  />
                  <Line
                    type="monotone"
                    dataKey="yield_kg_ha"
                    stroke="#1B1A17"
                    strokeWidth={1.5}
                    dot={(props: any) => {
                      const { cx, cy, payload } = props;
                      if (payload.shortfall_event === 1) {
                        return <circle key={payload.year} cx={cx} cy={cy} r={3.5} fill="#993404" stroke="#FAF8F2" strokeWidth={1} />;
                      }
                      return <circle key={payload.year} cx={cx} cy={cy} r={2} fill="#1B1A17" />;
                    }}
                    name="yield_kg_ha"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Section 2: 10-Year Held-Out Backtest Chart with Conformal Intervals */}
          <div className="bg-[#FAF8F2] border border-hairline p-5 space-y-3">
            <div className="flex flex-wrap justify-between items-baseline gap-2 border-b border-hairline pb-2">
              <div>
                <h2 className="font-heading text-lg font-bold text-[#1B1A17]">
                  Out-of-Sample Backtest (2008-2017) with 90% Conformal Interval
                </h2>
                <span className="text-xs text-[#5A564F]">
                  Relative anomaly scale [(yield - trend) / trend]. Shaded band indicates calibrated 90% uncertainty interval. Both hits and misses are shown.
                </span>
              </div>
              <div className="flex items-center gap-4 text-xs font-mono">
                <span className="flex items-center gap-1.5">
                  <span className="w-3 h-0.5 bg-[#1B1A17] inline-block"></span> Actual Anomaly
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-3 h-0.5 bg-[#1E5144] inline-block"></span> Predicted Anomaly
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-3 h-3 bg-[#EAE4D5] inline-block border border-hairline"></span> 90% CQR Band
                </span>
              </div>
            </div>

            <div className="h-72 w-full pt-2">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={backtestChartData} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
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
                        const pct = `${(val * 100).toFixed(1)}%`;
                        if (name === 'actual_anomaly') return [pct, 'Actual Anomaly'];
                        if (name === 'predicted_anomaly') return [pct, 'Predicted Anomaly'];
                        if (name === 'ci_lower') return [pct, 'Interval Lower'];
                        if (name === 'ci_upper') return [pct, 'Interval Upper'];
                      }
                      return [val, name];
                    }}
                  />
                  <ReferenceLine y={0} stroke="#847F75" strokeWidth={1} />
                  <Area
                    type="monotone"
                    dataKey="ci_upper"
                    stroke="none"
                    fill="#EAE4D5"
                    fillOpacity={0.6}
                  />
                  <Area
                    type="monotone"
                    dataKey="ci_lower"
                    stroke="none"
                    fill="#FAF8F2"
                    fillOpacity={1.0}
                  />
                  <Line
                    type="monotone"
                    dataKey="predicted_anomaly"
                    stroke="#1E5144"
                    strokeWidth={2}
                    dot={{ r: 3, fill: '#1E5144' }}
                    name="predicted_anomaly"
                  />
                  <Line
                    type="monotone"
                    dataKey="actual_anomaly"
                    stroke="#1B1A17"
                    strokeWidth={2}
                    dot={(props: any) => {
                      const { cx, cy, payload } = props;
                      const isCovered = payload.in_interval;
                      return (
                        <circle
                          key={payload.year}
                          cx={cx}
                          cy={cy}
                          r={3.5}
                          fill={isCovered ? '#1B1A17' : '#993404'}
                          stroke={isCovered ? '#FAF8F2' : '#FFFFFF'}
                          strokeWidth={1}
                        />
                      );
                    }}
                    name="actual_anomaly"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Section 3: Backtest Evaluation Table */}
          <div className="bg-[#FAF8F2] border border-hairline p-5 space-y-4">
            <h3 className="font-heading text-base font-bold text-[#1B1A17]">
              10-Year Backtest Breakdown &amp; Associated Explanations
            </h3>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border border-hairline">
                <thead className="bg-[#EAE4D5] border-b border-hairline font-mono text-[#1B1A17]">
                  <tr>
                    <th className="p-2.5">Year</th>
                    <th className="p-2.5">Observed Yield</th>
                    <th className="p-2.5">Actual Anom</th>
                    <th className="p-2.5">Predicted Anom</th>
                    <th className="p-2.5">90% CQR Interval</th>
                    <th className="p-2.5">In Interval?</th>
                    <th className="p-2.5">Shortfall Risk</th>
                    <th className="p-2.5">Actual Event</th>
                    <th className="p-2.5">Primary Associated Driver</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-hairline bg-white font-mono">
                  {data.backtest.map((row) => (
                    <tr key={row.year} className="hover:bg-[#FAF8F2] text-[#1B1A17]">
                      <td className="p-2.5 font-bold">{row.year}</td>
                      <td className="p-2.5">{row.actual_yield_kg_ha} kg/ha</td>
                      <td className="p-2.5">{row.actual_anomaly >= 0 ? '+' : ''}{(row.actual_anomaly * 100).toFixed(1)}%</td>
                      <td className="p-2.5">{row.predicted_anomaly >= 0 ? '+' : ''}{(row.predicted_anomaly * 100).toFixed(1)}%</td>
                      <td className="p-2.5">
                        [{(row.ci_lower * 100).toFixed(0)}% to +{(row.ci_upper * 100).toFixed(0)}%]
                      </td>
                      <td className="p-2.5">
                        {row.in_interval ? (
                          <span className="text-[#1E5144] font-bold">Yes</span>
                        ) : (
                          <span className="text-[#993404] font-bold">Miss</span>
                        )}
                      </td>
                      <td className="p-2.5">{(row.predicted_shortfall_prob * 100).toFixed(1)}%</td>
                      <td className="p-2.5">
                        {row.actual_shortfall_event === 1 ? (
                          <span className="text-[#993404] font-bold">Shortfall</span>
                        ) : (
                          <span className="text-[#5A564F]">Normal</span>
                        )}
                      </td>
                      <td className="p-2.5 font-sans text-[11px] text-[#5A564F] max-w-xs truncate" title={row.top_drivers}>
                        {row.top_drivers}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
};
