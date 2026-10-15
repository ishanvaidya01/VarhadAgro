import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { api } from '../api/client';
import type { RiskMapResponse, RiskDistrictRecord } from '../api/client';
import { VidarbhaMap } from '../components/VidarbhaMap';
import { getRiskColor } from '../utils/risk';
import { ControlsBar } from '../components/ControlsBar';
import { AlertTriangle, ArrowRight, Info, CheckCircle2 } from 'lucide-react';

export const RiskMapPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const currentCrop = searchParams.get('crop') || 'Cotton';
  const currentCutoff = searchParams.get('cutoff') || undefined;
  const currentYearStr = searchParams.get('year') || '2017';
  const currentYear = parseInt(currentYearStr, 10);

  const [mapData, setMapData] = useState<RiskMapResponse | null>(null);
  const [geojson, setGeojson] = useState<any>(null);
  const [selectedDistrict, setSelectedDistrict] = useState<string>('Akola');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);

    Promise.all([
      api.getDistricts(),
      api.getRiskMap(currentCrop, currentCutoff, currentYear)
    ])
      .then(([distRes, riskRes]) => {
        if (!isMounted) return;
        setGeojson(distRes.geojson);
        setMapData(riskRes);
        setLoading(false);
      })
      .catch((err) => {
        if (!isMounted) return;
        setError(err.message || 'Failed to load risk map data.');
        setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [currentCrop, currentCutoff, currentYear]);

  const selectedRecord: RiskDistrictRecord | undefined = mapData?.districts.find(
    (d) => d.district.toLowerCase() === selectedDistrict.toLowerCase()
  );

  return (
    <div className="space-y-6">
      {/* Editorial lead */}
      <div className="border-b border-hairline pb-4">
        <h1 className="text-2xl sm:text-3xl font-bold font-heading text-[#1B1A17] tracking-tight">
          Vidarbha Crop Shortfall Risk Map
        </h1>
        <p className="text-sm text-[#5A564F] mt-1 max-w-3xl">
          Empirical district-level probability of agricultural yield falling below the 80% PMFBY indemnity threshold for {currentCrop}, calibrated on observed weather and historical government yield series.
        </p>
      </div>

      <ControlsBar showYear={true} />

      {error && (
        <div className="p-4 border border-[#993404] bg-[#FDF6F0] text-[#993404] text-sm flex items-start gap-3">
          <AlertTriangle size={18} className="shrink-0 mt-0.5" />
          <div>
            <p className="font-medium">Error loading risk distribution</p>
            <p className="text-xs mt-0.5">{error}</p>
          </div>
        </div>
      )}

      {loading && !mapData ? (
        <div className="h-96 border border-hairline bg-[#FAF8F2] flex items-center justify-center text-[#5A564F] text-sm">
          Loading district geometries and calibrated risk estimates...
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Main Map Canvas */}
          <div className="lg:col-span-7 bg-[#FAF8F2] border border-hairline p-4">
            <div className="flex items-center justify-between mb-3 text-xs text-[#5A564F] border-b border-hairline pb-2">
              <span className="font-mono">
                Season: {currentCrop === 'Wheat' || currentCrop === 'Chickpea' ? 'Rabi' : 'Kharif'} | Stage: {mapData?.cutoff}
              </span>
              <span className="font-mono">
                Decision Threshold: {(mapData?.decision_threshold ? mapData.decision_threshold * 100 : 21).toFixed(0)}%
              </span>
            </div>

            <VidarbhaMap
              geojson={geojson}
              districtsData={mapData?.districts || []}
              selectedDistrict={selectedDistrict}
              onSelectDistrict={(id) => setSelectedDistrict(id)}
            />
          </div>

          {/* District Detail Drawer / Panel */}
          <div className="lg:col-span-5 bg-[#FAF8F2] border border-hairline p-5 space-y-5">
            <div className="border-b border-hairline pb-3 flex justify-between items-start">
              <div>
                <span className="text-xs uppercase font-mono tracking-wider text-[#5A564F]">District Inspection</span>
                <h2 className="text-2xl font-bold font-heading text-[#1B1A17]">{selectedDistrict}</h2>
                <span className="text-xs text-[#5A564F]">{selectedRecord?.subregion || 'Vidarbha'}</span>
              </div>
              <div
                className="px-2.5 py-1 text-xs font-mono font-medium border border-hairline"
                style={{ backgroundColor: getRiskColor(selectedRecord?.predicted_shortfall_prob ?? null) }}
              >
                {selectedRecord?.predicted_shortfall_prob !== null && selectedRecord?.predicted_shortfall_prob !== undefined
                  ? `${(selectedRecord.predicted_shortfall_prob * 100).toFixed(1)}% Risk`
                  : 'No active area'}
              </div>
            </div>

            {selectedRecord && selectedRecord.predicted_shortfall_prob !== null ? (
              <div className="space-y-4 text-sm">
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 bg-white border border-hairline">
                    <span className="text-xs text-[#5A564F] block">Predicted Anomaly</span>
                    <span className="text-lg font-mono font-bold text-[#1B1A17]">
                      {selectedRecord.predicted_anomaly !== null
                        ? `${selectedRecord.predicted_anomaly >= 0 ? '+' : ''}${(selectedRecord.predicted_anomaly * 100).toFixed(1)}%`
                        : 'N/A'}
                    </span>
                    <span className="text-[11px] text-[#847F75] block mt-0.5">vs expanding trend</span>
                  </div>

                  <div className="p-3 bg-white border border-hairline">
                    <span className="text-xs text-[#5A564F] block">90% Prediction Band</span>
                    <span className="text-xs font-mono text-[#1B1A17] block mt-1 font-medium">
                      [{selectedRecord.ci_lower !== null ? `${(selectedRecord.ci_lower * 100).toFixed(0)}%` : ''} to{' '}
                      {selectedRecord.ci_upper !== null ? `+${(selectedRecord.ci_upper * 100).toFixed(0)}%` : ''}]
                    </span>
                    <span className="text-[11px] text-[#847F75] block mt-0.5">conformal calibrated</span>
                  </div>
                </div>

                {/* Backtest Test Year Outcome */}
                <div className="p-3 bg-white border border-hairline space-y-1.5">
                  <span className="text-xs font-medium text-[#1B1A17] block">
                    Held-Out Test Year ({currentYear}) Verification:
                  </span>
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-[#5A564F]">Actual Yield Anomaly:</span>
                    <span className="font-semibold text-[#1B1A17]">
                      {selectedRecord.actual_yield_anomaly !== null
                        ? `${selectedRecord.actual_yield_anomaly >= 0 ? '+' : ''}${(selectedRecord.actual_yield_anomaly * 100).toFixed(1)}%`
                        : 'N/A'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-[#5A564F]">Actual PMFBY Shortfall:</span>
                    <span
                      className={`font-semibold ${
                        selectedRecord.actual_shortfall_event === 1 ? 'text-[#993404]' : 'text-[#1E5144]'
                      }`}
                    >
                      {selectedRecord.actual_shortfall_event === 1 ? 'Yes (Loss Event)' : 'No (Normal / Surplus)'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-xs font-mono pt-1 border-t border-hairline">
                    <span className="text-[#5A564F]">Model Classification:</span>
                    <span className="font-semibold text-[#1B1A17]">
                      {selectedRecord.shortfall_pred_class === 1 ? 'Triggered Alert' : 'No Alert'}
                    </span>
                  </div>
                </div>

                {/* Plain language SHAP drivers */}
                <div className="p-3 bg-[#FAF8F2] border border-hairline">
                  <div className="flex items-center gap-1.5 text-xs font-medium text-[#1B1A17] mb-1">
                    <Info size={14} className="text-[#1E5144]" />
                    <span>Associated Weather Drivers (Statistical association):</span>
                  </div>
                  <p className="text-xs text-[#5A564F] leading-relaxed">
                    {selectedRecord.top_drivers}
                  </p>
                </div>

                {/* Action Link */}
                <div className="pt-2">
                  <Link
                    to={`/district?district=${encodeURIComponent(selectedDistrict)}&crop=${encodeURIComponent(currentCrop)}`}
                    className="inline-flex items-center justify-between w-full px-4 py-2.5 bg-[#1E5144] text-[#F3EFE6] text-xs font-medium hover:bg-[#153B31] transition-colors"
                  >
                    <span>Inspect 52-Year Yield Series &amp; Full Backtest</span>
                    <ArrowRight size={14} />
                  </Link>
                </div>
              </div>
            ) : (
              <div className="p-6 text-center text-sm text-[#5A564F] border border-dashed border-hairline">
                {selectedRecord?.message || 'Select a district polygon on the map to inspect risk factors.'}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Honesty Banner */}
      <div className="border border-hairline bg-[#FAF8F2] p-4 text-xs text-[#5A564F] flex items-start gap-3">
        <CheckCircle2 size={16} className="text-[#1E5144] shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-[#1B1A17]">Transparent Model Skill Notice: </span>
          <span>
            LightGBM and Panel Ridge models achieve +4.7% to +8.1% RMSE skill over baseline on held-out test years across Vidarbha. Weather associations alone explain moderate yield variance; soil vertisol depth and local canal irrigation explain residual differences.
          </span>
        </div>
      </div>
    </div>
  );
};
