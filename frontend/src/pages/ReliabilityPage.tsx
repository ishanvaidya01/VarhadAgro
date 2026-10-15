import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { api } from '../api/client';
import type { ReliabilityResponse } from '../api/client';
import { Info, Scale } from 'lucide-react';

const DISTRICTS = ['Akola', 'Amravati', 'Buldhana', 'Yavatmal', 'Wardha', 'Nagpur', 'Bhandara', 'Chandrapur'];

export const ReliabilityPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const districtParam = searchParams.get('district') || 'Akola';

  const [data, setData] = useState<ReliabilityResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);

    api.getReliability(districtParam)
      .then((res) => {
        if (!isMounted) return;
        setData(res);
        setLoading(false);
      })
      .catch((err) => {
        if (!isMounted) return;
        setError(err.message || 'Failed to load crop reliability ranking.');
        setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [districtParam]);

  const updateDistrict = (dist: string) => {
    const next = new URLSearchParams(searchParams);
    next.set('district', dist);
    setSearchParams(next);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="border-b border-hairline pb-4 flex flex-wrap justify-between items-end gap-4">
        <div>
          <span className="text-xs uppercase font-mono tracking-wider text-[#5A564F]">Downside Risk Comparison</span>
          <h1 className="text-2xl sm:text-3xl font-bold font-heading text-[#1B1A17] tracking-tight">
            Crop Reliability Ranking &bull; {districtParam}
          </h1>
          <p className="text-xs sm:text-sm text-[#5A564F] mt-1 max-w-3xl">
            Ranks crops by downside loss severity in severe drought years (CVaR 20%) and shortfall frequency, evaluated using 52 years of observed yield history with 1,000 bootstrap iterations on rank uncertainty.
          </p>
        </div>

        {/* District Selector */}
        <div className="flex items-center gap-2 text-xs">
          <label htmlFor="rel-dist" className="font-mono text-[#5A564F]">District:</label>
          <select
            id="rel-dist"
            value={districtParam}
            onChange={(e) => updateDistrict(e.target.value)}
            className="border border-hairline bg-white px-2.5 py-1.5 font-medium text-[#1B1A17] focus:outline-none focus:border-[#1E5144]"
          >
            {DISTRICTS.map((d) => (
              <option key={d} value={d}>{d}</option>
            ))}
          </select>
        </div>
      </div>

      {error && (
        <div className="p-4 border border-[#993404] bg-[#FDF6F0] text-[#993404] text-xs">
          {error}
        </div>
      )}

      {loading && !data ? (
        <div className="h-72 border border-hairline bg-[#FAF8F2] flex items-center justify-center text-[#5A564F] text-sm">
          Calculating bootstrap rank distributions and CVaR downside risks...
        </div>
      ) : data ? (
        <div className="space-y-6">
          {/* Main Ranking Table */}
          <div className="bg-[#FAF8F2] border border-hairline p-5 space-y-4">
            <div className="flex justify-between items-baseline border-b border-hairline pb-2">
              <h2 className="font-heading text-lg font-bold text-[#1B1A17]">
                Reliability &amp; Downside Volatility Table
              </h2>
              <span className="text-xs font-mono text-[#5A564F]">
                1,000 Bootstrap Resamples
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border border-hairline bg-white">
                <thead className="bg-[#EAE4D5] border-b border-hairline font-mono text-[#1B1A17]">
                  <tr>
                    <th className="p-3">Rank</th>
                    <th className="p-3">Crop</th>
                    <th className="p-3">95% Rank CI</th>
                    <th className="p-3">Expected Shortfall (CVaR 20%)</th>
                    <th className="p-3">PMFBY Shortfall Prob</th>
                    <th className="p-3">Sensitivity under +2 &deg;C</th>
                    <th className="p-3">Observed Years</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-hairline font-mono">
                  {data.ranked_crops.map((row) => (
                    <tr key={row.crop} className="hover:bg-[#FAF8F2] text-[#1B1A17]">
                      <td className="p-3 font-bold text-sm text-[#1E5144]">#{row.rank}</td>
                      <td className="p-3 font-sans font-bold text-sm text-[#1B1A17]">{row.crop}</td>
                      <td className="p-3 font-medium text-[#5A564F]">
                        [{row.rank_ci[0]} to {row.rank_ci[1]}]
                      </td>
                      <td className="p-3">
                        <span className="font-bold text-[#1B1A17]">{row.expected_shortfall_label}</span>
                        <span className="text-[11px] text-[#847F75] block mt-0.5">
                          anomaly: {(row.expected_shortfall_cvar20 * 100).toFixed(1)}%
                        </span>
                      </td>
                      <td className="p-3 font-semibold">
                        {(row.shortfall_probability * 100).toFixed(1)}%
                      </td>
                      <td className="p-3">
                        {row.heat_sensitivity_2c >= 0 ? '+' : ''}{(row.heat_sensitivity_2c * 100).toFixed(1)}%
                      </td>
                      <td className="p-3 text-[#5A564F]">{row.years_observed} years</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Indistinguishable Pairs Callout */}
          {data.indistinguishable_pairs.length > 0 && (
            <div className="bg-[#FAF8F2] border border-hairline p-5 space-y-3">
              <div className="flex items-center gap-2 text-xs font-bold font-mono text-[#1B1A17]">
                <Scale size={16} className="text-[#1E5144]" />
                <span>Statistically Indistinguishable Crops (Overlapping Confidence Intervals):</span>
              </div>
              <ul className="space-y-2 text-xs text-[#5A564F]">
                {data.indistinguishable_pairs.map((p, idx) => (
                  <li key={idx} className="p-3 bg-white border border-hairline flex items-start gap-2">
                    <span className="font-bold text-[#1B1A17] shrink-0 font-mono">
                      {p.crop_a} vs {p.crop_b}:
                    </span>
                    <span>{p.reason}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Agronomic Insight Note */}
          <div className="p-4 border border-hairline bg-[#FAF8F2] text-xs text-[#5A564F] flex items-start gap-3">
            <Info size={16} className="text-[#1E5144] shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold text-[#1B1A17]">Methodological Integrity Note: </span>
              <span>
                Unlike previous synthetic engines that computed arbitrary weighted sums of yield and weather, this reliability ranking uses transparent financial and insurance risk measures (CVaR 20% downside severity and empirical shortfall probability) computed strictly on relative anomalies without mixing physical kilograms across different crops.
              </span>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
};
