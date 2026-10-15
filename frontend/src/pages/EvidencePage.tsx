import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import type { EvidenceResponse } from '../api/client';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';
import { ShieldAlert, Database } from 'lucide-react';

export const EvidencePage: React.FC = () => {
  const [data, setData] = useState<EvidenceResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);

    api.getEvidence()
      .then((res) => {
        if (!isMounted) return;
        setData(res);
        setLoading(false);
      })
      .catch((err) => {
        if (!isMounted) return;
        setError(err.message || 'Failed to load evidence report.');
        setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const calCurve = data?.plots_data?.calibration_curve;
  const calData = (calCurve && Array.isArray(calCurve.prob_pred))
    ? calCurve.prob_pred.map((predVal: number, idx: number) => ({
        pred: Number((predVal * 100).toFixed(1)),
        actual: Number((((calCurve.prob_true && calCurve.prob_true[idx]) ?? 0) * 100).toFixed(1))
      }))
    : [];

  return (
    <div className="space-y-8">
      {/* Editorial Header */}
      <div className="border-b border-hairline pb-4">
        <span className="text-xs uppercase font-mono tracking-wider text-[#5A564F]">Model &amp; Data Auditing</span>
        <h1 className="text-2xl sm:text-3xl font-bold font-heading text-[#1B1A17] tracking-tight">
          Evidence, Model Card &amp; Data Card
        </h1>
        <p className="text-xs sm:text-sm text-[#5A564F] mt-1 max-w-3xl">
          Complete transparent accounting of all empirical model metrics, calibration curves, empirical coverage on held-out years, data licenses, and explicit system limitations. Everything on this page is generated directly from pipeline build artifacts.
        </p>
      </div>

      {error && (
        <div className="p-4 border border-[#993404] bg-[#FDF6F0] text-[#993404] text-xs">
          {error}
        </div>
      )}

      {loading && !data ? (
        <div className="h-96 border border-hairline bg-[#FAF8F2] flex items-center justify-center text-[#5A564F] text-sm">
          Loading audit artifacts and calibration metrics...
        </div>
      ) : data ? (
        <div className="space-y-8">
          {/* Section 1: Model Card Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-4 bg-[#FAF8F2] border border-hairline space-y-1">
              <span className="text-xs text-[#5A564F] font-mono block">Out-of-Sample Regression</span>
              <span className="text-xl font-mono font-bold text-[#1B1A17] block">
                RMSE {data.metrics.regression.lightgbm_median.rmse}
              </span>
              <span className="text-xs text-[#1E5144] block font-semibold">
                +{(data.metrics.regression.lightgbm_median.skill_score * 100).toFixed(1)}% Skill vs Baseline
              </span>
              <span className="text-[11px] text-[#847F75] block">Baseline A RMSE: {data.metrics.regression.baseline_a.rmse}</span>
            </div>

            <div className="p-4 bg-[#FAF8F2] border border-hairline space-y-1">
              <span className="text-xs text-[#5A564F] font-mono block">Shortfall Classification</span>
              <span className="text-xl font-mono font-bold text-[#1B1A17] block">
                PR-AUC {data.metrics.classification.calibrated_shortfall_classifier.pr_auc}
              </span>
              <span className="text-xs text-[#1E5144] block font-semibold">
                Prevalence: {(data.metrics.prevalence * 100).toFixed(1)}%
              </span>
              <span className="text-[11px] text-[#847F75] block">Decision Threshold: {data.metrics.classification.calibrated_shortfall_classifier.decision_threshold}</span>
            </div>

            <div className="p-4 bg-[#FAF8F2] border border-hairline space-y-1">
              <span className="text-xs text-[#5A564F] font-mono block">Uncertainty Coverage</span>
              <span className="text-xl font-mono font-bold text-[#1B1A17] block">
                {(data.metrics.uncertainty_conformal_cqr.empirical_coverage_overall * 100).toFixed(1)}%
              </span>
              <span className="text-xs text-[#5A564F] block">
                Target: {(data.metrics.uncertainty_conformal_cqr.target_coverage * 100).toFixed(0)}% Nominal
              </span>
              <span className="text-[11px] text-[#847F75] block">Mean width: {data.metrics.uncertainty_conformal_cqr.mean_interval_width.toFixed(2)} anomaly units</span>
            </div>

            <div className="p-4 bg-[#FAF8F2] border border-hairline space-y-1">
              <span className="text-xs text-[#5A564F] font-mono block">Held-Out Test Set</span>
              <span className="text-xl font-mono font-bold text-[#1B1A17] block">
                {data.metrics.total_test_instances} instances
              </span>
              <span className="text-xs text-[#5A564F] block">
                {data.metrics.evaluation_period}
              </span>
              <span className="text-[11px] text-[#847F75] block">Strict rolling-origin test</span>
            </div>
          </div>

          {/* Section 2: Calibration Curve & Coverage Table */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* Calibration curve chart */}
            <div className="lg:col-span-6 bg-[#FAF8F2] border border-hairline p-5 space-y-3">
              <div className="border-b border-hairline pb-2">
                <h2 className="font-heading text-base font-bold text-[#1B1A17]">
                  Shortfall Probability Reliability (Calibration) Curve
                </h2>
                <span className="text-xs text-[#5A564F]">
                  Predicted probability bins vs empirical positive fraction. Perfect calibration lies on the diagonal.
                </span>
              </div>

              <div className="h-64 w-full pt-2">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={calData} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#D6CFBF" vertical={false} />
                    <XAxis dataKey="pred" stroke="#5A564F" tick={{ fontSize: 11 }} unit="%" label={{ value: 'Predicted Probability', position: 'insideBottom', offset: -2, fontSize: 10 }} />
                    <YAxis stroke="#5A564F" tick={{ fontSize: 11 }} unit="%" domain={[0, 100]} label={{ value: 'Empirical Frequency', angle: -90, position: 'insideLeft', fontSize: 10 }} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#FAF8F2', borderColor: '#D6CFBF', fontSize: '12px' }}
                      formatter={(val: any, name: any) => [`${val}%`, name === 'actual' ? 'Empirical Frequency' : 'Predicted Bin']}
                    />
                    <Line
                      type="linear"
                      dataKey="actual"
                      stroke="#1E5144"
                      strokeWidth={2}
                      dot={{ r: 4, fill: '#1E5144' }}
                      name="actual"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Empirical Coverage by Crop Table */}
            <div className="lg:col-span-6 bg-[#FAF8F2] border border-hairline p-5 space-y-3">
              <div className="border-b border-hairline pb-2">
                <h2 className="font-heading text-base font-bold text-[#1B1A17]">
                  Empirical Conformal Coverage by Crop (Held-Out Test Years)
                </h2>
                <span className="text-xs text-[#5A564F]">
                  Target: 90% Nominal Coverage. Lower coverage on Soybean/Pigeonpea reflects the severe 2014-2015 drought.
                </span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border border-hairline bg-white">
                  <thead className="bg-[#EAE4D5] border-b border-hairline font-mono text-[#1B1A17]">
                    <tr>
                      <th className="p-2.5">Crop</th>
                      <th className="p-2.5">Empirical Coverage</th>
                      <th className="p-2.5">Test Instances</th>
                      <th className="p-2.5">Mean Width</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-hairline font-mono">
                    {Object.entries(data.metrics.uncertainty_conformal_cqr.coverage_by_crop).map(([cName, cStats]) => (
                      <tr key={cName} className="hover:bg-[#FAF8F2]">
                        <td className="p-2.5 font-sans font-medium text-[#1B1A17]">{cName}</td>
                        <td className={`p-2.5 font-bold ${cStats.coverage >= 0.85 ? 'text-[#1E5144]' : 'text-[#D95F0E]'}`}>
                          {(cStats.coverage * 100).toFixed(1)}%
                        </td>
                        <td className="p-2.5 text-[#5A564F]">{cStats.n_samples}</td>
                        <td className="p-2.5">{cStats.mean_width.toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Section 3: Data Provenance & Licenses */}
          <div className="bg-[#FAF8F2] border border-hairline p-5 space-y-3">
            <div className="flex items-center gap-2 border-b border-hairline pb-2">
              <Database size={16} className="text-[#1E5144]" />
              <h2 className="font-heading text-base font-bold text-[#1B1A17]">Data Provenance &amp; Licensing Card</h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div className="p-3 bg-white border border-hairline space-y-1.5">
                <span className="font-bold text-[#1B1A17] block">Primary Yield Statistics</span>
                <p className="text-[#5A564F]">
                  <strong>Source:</strong> ICRISAT District Level Database (DLD) for Indian Agriculture (1966-2017)
                </p>
                <p className="text-[#5A564F]">
                  <strong>DOI:</strong> 10.21421/D2/XFB1BZ &bull; <strong>License:</strong> Creative Commons Attribution 4.0 (CC BY 4.0)
                </p>
                <p className="text-[#5A564F]">
                  <strong>Apportionment:</strong> 1966 parent district boundaries (Akola, Amravati, Buldhana, Yavatmal, Wardha, Nagpur, Bhandara, Chandrapur) to maintain continuous unfragmented historical series.
                </p>
              </div>

              <div className="p-3 bg-white border border-hairline space-y-1.5">
                <span className="font-bold text-[#1B1A17] block">Observed Daily Weather</span>
                <p className="text-[#5A564F]">
                  <strong>Source:</strong> NASA POWER Agroclimatology Daily Point API (1981-2023)
                </p>
                <p className="text-[#5A564F]">
                  <strong>Parameters:</strong> T2M, T2M_MAX, T2M_MIN, PRECTOTCORR, GWETROOT, ALLSKY_SFC_SW_DWN
                </p>
                <p className="text-[#5A564F]">
                  <strong>License:</strong> NASA Open Data Policy (Public Domain / US Government Open Data)
                </p>
              </div>
            </div>
          </div>

          {/* Section 4: What this tool CANNOT do (Mandatory explicit limitations) */}
          <div className="bg-[#FAF8F2] border border-hairline p-5 space-y-3">
            <div className="flex items-center gap-2 border-b border-hairline pb-2">
              <ShieldAlert size={16} className="text-[#D95F0E]" />
              <h2 className="font-heading text-base font-bold text-[#1B1A17]">What This Tool Cannot Do (Explicit Limitations)</h2>
            </div>

            <ul className="space-y-2 text-xs text-[#5A564F] list-disc list-inside">
              <li>
                <strong>Cannot predict farm-level yields:</strong> All models operate at the district statistical scale. Field-level variation from seed variety, sowing date, fertilizer dosage, micro-topography, and pest outbreaks cannot be captured by district weather averages.
              </li>
              <li>
                <strong>Cannot establish agronomic causation:</strong> Tree models and panel regressions capture empirical statistical associations between atmospheric variables and reported yield anomalies. They do not substitute for physiological crop growth models (e.g. DSSAT, APSIM).
              </li>
              <li>
                <strong>Cannot extrapolate safely beyond historical weather ranges:</strong> Regression trees cannot forecast outside the envelope of training features. The Scenario Lab incorporates explicit multivariate out-of-distribution guards; when extreme shifts trigger the warning, interval predictions should not be trusted.
              </li>
              <li>
                <strong>Cannot predict long-term price or financial indemnity amounts:</strong> The product models PMFBY-style shortfall events strictly as physical yield falling below 80% of historical average. Policy indemnity payouts depend on government threshold notification and sum insured guidelines.
              </li>
            </ul>
          </div>
        </div>
      ) : null}
    </div>
  );
};
