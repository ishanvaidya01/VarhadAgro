import React from 'react';
import { useSearchParams } from 'react-router-dom';

const CROPS = ['Cotton', 'Soybean', 'Pigeonpea', 'Sorghum', 'Rice', 'Wheat', 'Chickpea'];

const CROP_CUTOFFS: Record<string, Array<{ value: string; label: string }>> = {
  Cotton: [
    { value: '07-15', label: '15 Jul (Sowing / Onset)' },
    { value: '08-15', label: '15 Aug (Vegetative)' },
    { value: '09-15', label: '15 Sep (Pod Fill / Boll)' },
    { value: '10-31', label: 'End of Season (Harvest)' }
  ],
  Soybean: [
    { value: '07-15', label: '15 Jul (Sowing / Onset)' },
    { value: '08-15', label: '15 Aug (Vegetative)' },
    { value: '09-15', label: '15 Sep (Pod Fill)' },
    { value: '10-15', label: 'End of Season (Harvest)' }
  ],
  Pigeonpea: [
    { value: '07-15', label: '15 Jul (Sowing / Onset)' },
    { value: '08-15', label: '15 Aug (Vegetative)' },
    { value: '09-15', label: '15 Sep (Pod Fill / Boll)' },
    { value: '10-31', label: 'End of Season (Harvest)' }
  ],
  Sorghum: [
    { value: '07-15', label: '15 Jul (Sowing / Onset)' },
    { value: '08-15', label: '15 Aug (Vegetative)' },
    { value: '09-15', label: '15 Sep (Grain Fill)' },
    { value: '10-31', label: 'End of Season (Harvest)' }
  ],
  Rice: [
    { value: '07-15', label: '15 Jul (Sowing / Onset)' },
    { value: '08-15', label: '15 Aug (Vegetative)' },
    { value: '09-15', label: '15 Sep (Panicle / Grain)' },
    { value: '10-31', label: 'End of Season (Harvest)' }
  ],
  Wheat: [
    { value: '12-15', label: '15 Dec (Vegetative)' },
    { value: '01-15', label: '15 Jan (Flowering)' },
    { value: '02-15', label: '15 Feb (Grain Filling)' },
    { value: '03-31', label: 'End of Season (Harvest)' }
  ],
  Chickpea: [
    { value: '11-30', label: '30 Nov (Sowing / Emergence)' },
    { value: '12-31', label: '31 Dec (Vegetative)' },
    { value: '01-31', label: '31 Jan (Podding)' },
    { value: '03-15', label: 'End of Season (Harvest)' }
  ]
};

const BACKTEST_YEARS = [2017, 2016, 2015, 2014, 2013, 2012, 2011, 2010, 2009, 2008];

export const ControlsBar: React.FC<{ showYear?: boolean }> = ({ showYear = true }) => {
  const [searchParams, setSearchParams] = useSearchParams();

  const currentCrop = searchParams.get('crop') || 'Cotton';
  const cutoffOptions = CROP_CUTOFFS[currentCrop] || CROP_CUTOFFS['Cotton'];
  const defaultCutoff = cutoffOptions[cutoffOptions.length - 1].value;
  const currentCutoffParam = searchParams.get('cutoff');
  const isValidCutoff = cutoffOptions.some((o) => o.value === currentCutoffParam);
  const currentCutoff = isValidCutoff ? currentCutoffParam! : defaultCutoff;
  const currentYear = searchParams.get('year') || '2017';

  const updateParam = (key: string, value: string) => {
    const next = new URLSearchParams(searchParams);
    next.set(key, value);
    // If crop changed, reset cutoff to that crop's end-of-season
    if (key === 'crop') {
      const nextCutoffs = CROP_CUTOFFS[value] || CROP_CUTOFFS['Cotton'];
      next.set('cutoff', nextCutoffs[nextCutoffs.length - 1].value);
    }
    setSearchParams(next);
  };

  return (
    <div className="bg-[#FAF8F2] border border-hairline p-3 mb-6 flex flex-wrap items-center justify-between gap-4 text-sm">
      <div className="flex flex-wrap items-center gap-4">
        {/* Crop Selector */}
        <div className="flex items-center gap-2">
          <label htmlFor="crop-select" className="text-xs uppercase font-mono tracking-wider text-[#5A564F]">
            Crop:
          </label>
          <select
            id="crop-select"
            value={currentCrop}
            onChange={(e) => updateParam('crop', e.target.value)}
            className="border border-hairline bg-[#FFFFFF] px-2.5 py-1 text-sm font-medium text-[#1B1A17] focus:outline-none focus:border-[#1E5144]"
          >
            {CROPS.map((c) => (
              <option key={c} value={c}>
                {c} {c === 'Wheat' || c === 'Chickpea' ? '(Rabi)' : '(Kharif)'}
              </option>
            ))}
          </select>
        </div>

        {/* Cutoff / Lead Time Selector */}
        <div className="flex items-center gap-2">
          <label htmlFor="cutoff-select" className="text-xs uppercase font-mono tracking-wider text-[#5A564F]">
            Stage:
          </label>
          <select
            id="cutoff-select"
            value={currentCutoff}
            onChange={(e) => updateParam('cutoff', e.target.value)}
            className="border border-hairline bg-[#FFFFFF] px-2.5 py-1 text-sm font-medium text-[#1B1A17] focus:outline-none focus:border-[#1E5144]"
          >
            {cutoffOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        {/* Backtest Year Selector (Optional) */}
        {showYear && (
          <div className="flex items-center gap-2">
            <label htmlFor="year-select" className="text-xs uppercase font-mono tracking-wider text-[#5A564F]">
              Test Year:
            </label>
            <select
              id="year-select"
              value={currentYear}
              onChange={(e) => updateParam('year', e.target.value)}
              className="border border-hairline bg-[#FFFFFF] px-2.5 py-1 text-sm font-medium text-[#1B1A17] focus:outline-none focus:border-[#1E5144]"
            >
              {BACKTEST_YEARS.map((y) => (
                <option key={y} value={y.toString()}>
                  {y} {y === 2014 || y === 2015 ? '(Severe Drought)' : ''}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      <div className="text-xs font-mono text-[#5A564F] hidden md:block">
        Indemnity Level: 80% (PMFBY Operational Standard)
      </div>
    </div>
  );
};
