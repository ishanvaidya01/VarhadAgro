import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { api } from '../api/client';
import type { SeasonTrackerResponse } from '../api/client';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';
import { AlertCircle, Clock, CloudRain } from 'lucide-react';

const DISTRICTS = ['Akola', 'Amravati', 'Buldhana', 'Yavatmal', 'Wardha', 'Nagpur', 'Bhandara', 'Chandrapur'];
const CROPS = ['Cotton', 'Soybean', 'Pigeonpea', 'Sorghum', 'Rice', 'Wheat', 'Chickpea'];

export const SeasonTrackerPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const districtParam = searchParams.get('district') || 'Akola';
  const cropParam = searchParams.get('crop') || 'Cotton';

  const [data, setData] = useState<SeasonTrackerResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);

    api.getEarlyWarning(cropParam, districtParam)
      .then((res) => {
        if (!isMounted) return;
        setData(res);
        setLoading(false);
      })
      .catch((err) => {
        if (!isMounted) return;
        setError(err.message || 'Failed to load season tracker data.');
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

  const leadTimeChartData = (data?.lead_time_skill_progression || []).map((item) => ({
    cutoff: item.cutoff,
    stage: item.stage.split(' ')[0],
    lead_days: item.lead_days,
    skill_pct: Number((item.skill_score * 100).toFixed(1)),
    pr_auc: Number(item.pr_auc.toFixed(3)),
    rmse: Number(item.rmse.toFixed(3))
  }));

  return (
    <div className="space-y-6">
      {/* Editorial Header */}
      <div className="border-b border-hairline pb-4 flex flex-wrap justify-between items-end gap-4">
        <div>
          <span className="text-xs uppercase font-mono tracking-wider text-[#5A564F]">Intra-Season Monitoring</span>
          <h1 className="text-2xl sm:text-3xl font-bold font-heading text-[#1B1A17] tracking-tight">
            Season Tracker &amp; Early-Warning Skill
          </h1>
          <p className="text-xs sm:text-sm text-[#5A564F] mt-1 max-w-2xl">
            Monitors intra-seasonal monsoon precipitation against historical normals, and documents how predictive shortfall risk skill evolves from sowing to harvest.
          </p>
        </div>

        {/* Selectors */}
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
        <div className="p-4 border border-[#993404] bg-[#FDF6F0] text-[#993404] text-sm">
          {error}
        </div>
      )}

      {loading && !data ? (
        <div className="h-80 border border-hairline bg-[#FAF8F2] flex items-center justify-center text-[#5A564F] text-sm">
          Loading intra-seasonal precipitation and lead-time skill metrics...
        </div>
      ) : data ? (
        <div className="space-y-8">
          {/* Section 1: Weather Status Banner */}
          <div className="bg-[#FAF8F2] border border-hairline p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-hairline pb-2">
              <div className="flex items-center gap-2">
                <CloudRain size={18} className="text-[#1E5144]" />
                <h2 className="font-heading text-lg font-bold text-[#1B1A17]">
                  Intra-Seasonal Weather Status ({data.season_tracker.recent_observed_year}) &bull; {data.season_tracker.district}
                </h2>
              </div>
              <span className="text-xs font-mono text-[#5A564F]">
                Source: NASA POWER Observed Agroclimatology
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="p-3.5 bg-white border border-hairline">
                <span className="text-xs text-[#5A564F] block">Cumulative Rainfall</span>
                <span className="text-xl font-mono font-bold text-[#1B1A17] mt-0.5 block">
                  {data.season_tracker.cumulative_rainfall_mm} mm
                </span>
                <span className="text-[11px] text-[#847F75] block mt-1">
                  Historical Normal: {data.season_tracker.historical_normal_mm} mm
                </span>
              </div>

              <div className="p-3.5 bg-white border border-hairline">
                <span className="text-xs text-[#5A564F] block">Percentage of Normal</span>
                <span className="text-xl font-mono font-bold text-[#1B1A17] mt-0.5 block">
                  {data.season_tracker.percent_of_normal}%
                </span>
                <span className="text-[11px] text-[#847F75] block mt-1">
                  Status: {data.season_tracker.rainfall_status}
                </span>
              </div>

              <div className="p-3.5 bg-white border border-hairline">
                <span className="text-xs text-[#5A564F] block">Monsoon Dry Days</span>
                <span className="text-xl font-mono font-bold text-[#1B1A17] mt-0.5 block">
                  {data.season_tracker.dry_days_in_monsoon} days
                </span>
                <span className="text-[11px] text-[#847F75] block mt-1">
                  Days with rain &lt; 2.5 mm
                </span>
              </div>

              <div className="p-3.5 bg-white border border-hairline">
                <span className="text-xs text-[#5A564F] block">Active Season Window</span>
                <span className="text-xl font-mono font-bold text-[#1B1A17] mt-0.5 block">
                  {data.season_tracker.season}
                </span>
                <span className="text-[11px] text-[#847F75] block mt-1">
                  Crop: {data.crop}
                </span>
              </div>
            </div>

            <div className="p-3 bg-[#EAE4D5] border border-hairline text-xs text-[#1B1A17] flex items-start gap-2">
              <AlertCircle size={15} className="shrink-0 mt-0.5 text-[#1E5144]" />
              <span>
                <strong>Methodological Rule:</strong> {data.season_tracker.note}
              </span>
            </div>
          </div>

          {/* Section 2: Early Warning Skill as Function of Lead Time */}
          <div className="bg-[#FAF8F2] border border-hairline p-5 space-y-4">
            <div className="border-b border-hairline pb-2">
              <div className="flex items-center gap-2">
                <Clock size={18} className="text-[#1E5144]" />
                <h2 className="font-heading text-lg font-bold text-[#1B1A17]">
                  Predictive Skill by Lead Time Before Harvest
                </h2>
              </div>
              <p className="text-xs text-[#5A564F] mt-1">
                Models trained strictly on weather features available up to each cutoff date. PR-AUC measures shortfall discrimination skill compared to test prevalence (36.7%).
              </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
              {/* Chart */}
              <div className="lg:col-span-7 h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={leadTimeChartData} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#D6CFBF" vertical={false} />
                    <XAxis dataKey="cutoff" stroke="#5A564F" tick={{ fontSize: 11 }} />
                    <YAxis stroke="#5A564F" tick={{ fontSize: 11 }} domain={[0.3, 0.6]} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#FAF8F2', borderColor: '#D6CFBF', fontSize: '12px' }}
                      formatter={(val: any, name: any) => {
                        if (name === 'pr_auc') return [val, 'Shortfall PR-AUC'];
                        if (name === 'skill_pct') return [`+${val}%`, 'Regression Skill'];
                        return [val, name];
                      }}
                    />
                    <Line
                      type="monotone"
                      dataKey="pr_auc"
                      stroke="#1E5144"
                      strokeWidth={2}
                      dot={{ r: 4, fill: '#1E5144' }}
                      name="pr_auc"
                    />
                  </LineChart>
                </ResponsiveContainer>
                <div className="text-[11px] text-[#5A564F] text-center mt-1 font-mono">
                  Shortfall PR-AUC progression across cutoff dates (Baseline Prevalence: 0.367)
                </div>
              </div>

              {/* Lead time table */}
              <div className="lg:col-span-5 overflow-x-auto">
                <table className="w-full text-left text-xs border border-hairline bg-white">
                  <thead className="bg-[#EAE4D5] font-mono text-[#1B1A17] border-b border-hairline">
                    <tr>
                      <th className="p-2">Stage</th>
                      <th className="p-2">Lead</th>
                      <th className="p-2">PR-AUC</th>
                      <th className="p-2">Skill %</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-hairline font-mono">
                    {data.lead_time_skill_progression.map((item) => (
                      <tr key={item.cutoff} className="hover:bg-[#FAF8F2]">
                        <td className="p-2 font-sans font-medium text-[#1B1A17]">{item.stage}</td>
                        <td className="p-2">{item.lead_days}d</td>
                        <td className="p-2 font-bold text-[#1E5144]">{item.pr_auc.toFixed(3)}</td>
                        <td className="p-2">+{(item.skill_score * 100).toFixed(1)}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
};
