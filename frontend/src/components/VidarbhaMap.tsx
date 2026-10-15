import React, { useMemo } from 'react';
import * as d3Geo from 'd3-geo';
import type { RiskDistrictRecord } from '../api/client';
import { getRiskColor, getRiskLabel } from '../utils/risk';

interface VidarbhaMapProps {
  geojson: any;
  districtsData: RiskDistrictRecord[];
  selectedDistrict: string;
  onSelectDistrict: (districtId: string) => void;
  width?: number;
  height?: number;
}

export const VidarbhaMap: React.FC<VidarbhaMapProps> = ({
  geojson,
  districtsData,
  selectedDistrict,
  onSelectDistrict,
  width = 640,
  height = 420
}) => {
  const dataMap = useMemo(() => {
    const map = new Map<string, RiskDistrictRecord>();
    for (const d of districtsData) {
      map.set(d.district, d);
    }
    return map;
  }, [districtsData]);

  const { paths } = useMemo(() => {
    if (!geojson || !geojson.features || geojson.features.length === 0) {
      return { paths: [] };
    }

    const projection = d3Geo.geoMercator().fitSize([width, height], geojson);
    const pathGenerator = d3Geo.geoPath().projection(projection);

    const projectedPaths = geojson.features.map((feature: any) => {
      const name = feature.properties?.district || feature.properties?.name || '';
      const d = pathGenerator(feature);
      const centroid = pathGenerator.centroid(feature);
      return {
        name,
        d,
        centroid: isNaN(centroid[0]) ? null : centroid,
        properties: feature.properties
      };
    });

    return { paths: projectedPaths, bounds: null };
  }, [geojson, width, height]);

  if (!geojson || paths.length === 0) {
    return (
      <div className="w-full h-80 flex items-center justify-center border border-hairline bg-[#FAF8F2] text-[#5A564F]">
        Loading boundary geometries...
      </div>
    );
  }

  return (
    <div className="w-full flex flex-col gap-3">
      <div className="relative border border-hairline bg-[#FAF8F2] p-2 overflow-hidden">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="w-full h-auto block"
          style={{ maxHeight: '460px' }}
        >
          {paths.map((p: any) => {
            const distInfo = dataMap.get(p.name);
            const prob = distInfo?.predicted_shortfall_prob ?? null;
            const fillColor = getRiskColor(prob);
            const isSelected = selectedDistrict.toLowerCase() === p.name.toLowerCase();

            return (
              <g key={p.name}>
                <path
                  d={p.d}
                  fill={fillColor}
                  stroke={isSelected ? '#1B1A17' : '#706B63'}
                  strokeWidth={isSelected ? 2.5 : 1.0}
                  className="cursor-pointer hover:opacity-85 transition-opacity"
                  onClick={() => onSelectDistrict(p.name)}
                >
                  <title>
                    {p.name}
                    {prob !== null
                      ? `: ${(prob * 100).toFixed(1)}% shortfall risk (${getRiskLabel(prob)})`
                      : ': No active acreage'}
                  </title>
                </path>
                {p.centroid && (
                  <text
                    x={p.centroid[0]}
                    y={p.centroid[1]}
                    textAnchor="middle"
                    dominantBaseline="central"
                    fill={prob !== null && prob >= 0.50 ? '#FFFFFF' : '#1B1A17'}
                    className="text-[10px] md:text-[11px] font-sans font-medium pointer-events-none select-none"
                    style={{ textShadow: prob !== null && prob >= 0.50 ? '0 1px 2px rgba(0,0,0,0.6)' : 'none' }}
                  >
                    {p.name}
                  </text>
                )}
              </g>
            );
          })}
        </svg>

        {/* Legend */}
        <div className="mt-2 pt-2 border-t border-hairline flex flex-wrap items-center justify-between text-xs text-[#5A564F]">
          <span className="font-medium text-[#1B1A17]">PMFBY Shortfall Risk:</span>
          <div className="flex flex-wrap items-center gap-2">
            <div className="flex items-center gap-1">
              <span className="w-3.5 h-3.5 inline-block border border-hairline" style={{ backgroundColor: '#FFFFD4' }}></span>
              <span>&lt;20%</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="w-3.5 h-3.5 inline-block border border-hairline" style={{ backgroundColor: '#FED98E' }}></span>
              <span>20-35%</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="w-3.5 h-3.5 inline-block border border-hairline" style={{ backgroundColor: '#FE9929' }}></span>
              <span>35-50%</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="w-3.5 h-3.5 inline-block border border-hairline" style={{ backgroundColor: '#D95F0E' }}></span>
              <span>50-70%</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="w-3.5 h-3.5 inline-block border border-hairline" style={{ backgroundColor: '#993404' }}></span>
              <span>&gt;70%</span>
            </div>
          </div>
        </div>
      </div>
      <div className="text-[11px] text-[#5A564F] flex justify-between items-center px-1">
        <span>Click any district polygon to inspect historical yield series and out-of-sample backtest.</span>
        <span className="font-mono">1966 Parent Units</span>
      </div>
    </div>
  );
};
