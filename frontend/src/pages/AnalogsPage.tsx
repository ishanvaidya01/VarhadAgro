import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { api } from '../api/client';
import type { AnalogsResponse } from '../api/client';
import { Info } from 'lucide-react';

const DISTRICTS = ['Akola', 'Amravati', 'Buldhana', 'Yavatmal', 'Wardha', 'Nagpur', 'Bhandara', 'Chandrapur'];

export const AnalogsPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const district = searchParams.get('district') || 'Akola';
  const tempShift = parseFloat(searchParams.get('temp') || '2.0');
  const precipShift = parseFloat(searchParams.get('precip') || '-0.20');

  const [data, setData] = useState<AnalogsResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);

    api.getAnalogs(district, tempShift, precipShift, 0, 4)
      .then((res) => {
        if (!isMounted) return;
        setData(res);
        setLoading(false);
      })
      .catch((err) => {
        if (!isMounted) return;
        setError(err.message || 'Failed to match climate analogs.');
        setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [district, tempShift, precipShift]);

  const updateParam = (key: string, val: string) => {
    const next = new URLSearchParams(searchParams);
    next.set(key, val);
    setSearchParams(next);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="border-b border-hairline pb-4 flex flex-wrap justify-between items-end gap-4">
        <div>
          <span className="text-xs uppercase font-mono tracking-wider text-[#5A564F]">Spatial Climate Analogy</span>
          <h1 className="text-2xl sm:text-3xl font-bold font-heading text-[#1B1A17] tracking-tight">
            Climate Analogs: Which Region Resembles This Shift Today?
          </h1>
          <p className="text-xs sm:text-sm text-[#5A564F] mt-1 max-w-3xl">
            Matches the shifted seasonal climate vector of {district} (+{tempShift.toFixed(1)} &deg;C, {(precipShift * 100).toFixed(0)}% rainfall) against observed climatology of 23 Maharashtra agricultural districts and inspects their dominant cultivated crops.
          </p>
        </div>

        {/* District & Perturbation controls */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-1.5 text-xs">
            <label htmlFor="analog-dist" className="font-mono text-[#5A564F]">Target:</label>
            <select
              id="analog-dist"
              value={district}
              onChange={(e) => updateParam('district', e.target.value)}
              className="border border-hairline bg-white px-2 py-1 font-medium text-[#1B1A17] focus:outline-none focus:border-[#1E5144]"
            >
              {DISTRICTS.map((d) => (
                <option key={d} value={d}>{d}</option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-1.5 text-xs">
            <label htmlFor="temp-shift" className="font-mono text-[#5A564F]">Warming:</label>
            <select
              id="temp-shift"
              value={tempShift.toString()}
              onChange={(e) => updateParam('temp', e.target.value)}
              className="border border-hairline bg-white px-2 py-1 font-medium text-[#1B1A17] focus:outline-none focus:border-[#1E5144]"
            >
              <option value="1.0">+1.0 &deg;C</option>
              <option value="2.0">+2.0 &deg;C</option>
              <option value="3.0">+3.0 &deg;C</option>
              <option value="4.0">+4.0 &deg;C</option>
            </select>
          </div>

          <div className="flex items-center gap-1.5 text-xs">
            <label htmlFor="precip-shift" className="font-mono text-[#5A564F]">Rainfall:</label>
            <select
              id="precip-shift"
              value={precipShift.toString()}
              onChange={(e) => updateParam('precip', e.target.value)}
              className="border border-hairline bg-white px-2 py-1 font-medium text-[#1B1A17] focus:outline-none focus:border-[#1E5144]"
            >
              <option value="-0.30">-30% Deficit</option>
              <option value="-0.20">-20% Deficit</option>
              <option value="-0.10">-10% Deficit</option>
              <option value="0.0">0% Normal</option>
              <option value="0.10">+10% Surplus</option>
            </select>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 border border-[#993404] bg-[#FDF6F0] text-[#993404] text-xs">
          {error}
        </div>
      )}

      {/* Prominent Agronomic Disclaimer */}
      {data && (
        <div className="p-4 border border-[#B86B1B] bg-[#FFFBF5] text-xs text-[#1B1A17] flex items-start gap-3">
          <Info size={17} className="text-[#B86B1B] shrink-0 mt-0.5" />
          <div>
            <span className="font-bold">Agronomic Scope Notice: </span>
            <span>{data.disclaimer}</span>
          </div>
        </div>
      )}

      {loading && !data ? (
        <div className="h-72 border border-hairline bg-[#FAF8F2] flex items-center justify-center text-[#5A564F] text-sm">
          Searching Maharashtra climatological analog pool...
        </div>
      ) : data ? (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {data.analogs.map((item, idx) => (
              <div key={item.district} className="bg-[#FAF8F2] border border-hairline p-5 space-y-4">
                <div className="flex justify-between items-start border-b border-hairline pb-2.5">
                  <div>
                    <span className="text-xs font-mono text-[#5A564F]">Analog Match #{idx + 1}</span>
                    <h3 className="font-heading text-xl font-bold text-[#1B1A17]">{item.district}</h3>
                    <span className="text-xs text-[#5A564F]">{item.subregion}, Maharashtra</span>
                  </div>
                  <div className="px-2.5 py-1 bg-white border border-hairline font-mono text-xs font-bold text-[#1E5144]">
                    Distance: {item.climate_distance}
                  </div>
                </div>

                {/* Climate comparison */}
                <div className="grid grid-cols-2 gap-3 text-xs font-mono bg-white p-3 border border-hairline">
                  <div>
                    <span className="text-[#5A564F] block">Season Rainfall:</span>
                    <span className="font-bold text-[#1B1A17]">{item.current_climate.season_rainfall_mm} mm</span>
                  </div>
                  <div>
                    <span className="text-[#5A564F] block">Mean Tmax:</span>
                    <span className="font-bold text-[#1B1A17]">{item.current_climate.tmax_mean_c} &deg;C</span>
                  </div>
                  <div>
                    <span className="text-[#5A564F] block">Heat Days (&gt;38 &deg;C):</span>
                    <span className="font-bold text-[#1B1A17]">{item.current_climate.heat_days_38} days</span>
                  </div>
                  <div>
                    <span className="text-[#5A564F] block">Rainfall CV:</span>
                    <span className="font-bold text-[#1B1A17]">{(item.current_climate.rainfall_cv * 100).toFixed(0)}%</span>
                  </div>
                </div>

                {/* Dominant crops currently grown in this analog district */}
                <div className="space-y-1.5">
                  <span className="text-xs font-medium text-[#1B1A17] block">
                    Dominant Crops Cultivated Today (from ICRISAT DLD):
                  </span>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    {item.dominant_crops.map((c) => (
                      <div key={c.crop} className="p-2 bg-white border border-hairline flex justify-between items-center">
                        <span className="font-medium text-[#1B1A17]">{c.crop}</span>
                        <span className="font-mono text-[#5A564F] text-[11px]">{c.area_share_pct}% area</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
};
