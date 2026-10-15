import React from 'react';

export const Terms: React.FC = () => {
  return (
    <div className="py-8 max-w-3xl mx-auto space-y-6">
      <div className="border-b border-hairline pb-3">
        <h1 className="text-2xl sm:text-3xl font-bold font-heading text-[#1B1A17]">Terms and Conditions</h1>
        <span className="text-xs text-[#5A564F] font-mono">Last updated: 2026-10-14</span>
      </div>

      <div className="bg-[#FAF8F2] border border-hairline p-6 text-sm text-[#1B1A17] space-y-4">
        <div>
          <h2 className="font-bold text-base mb-1">Operator Details</h2>
          <p className="text-xs text-[#5A564F]">
            <strong>Operator:</strong> Ishan Vaidya
          </p>
          <p className="text-xs text-[#5A564F]">
            <strong>Jurisdiction:</strong> Pune, India
          </p>
          <p className="text-xs text-[#5A564F]">
            <strong>Contact:</strong> ishan.vaidya01@gmail.com
          </p>
        </div>

        <div>
          <h2 className="font-bold text-base mb-1">Scientific &amp; Demonstration Purpose</h2>
          <p className="text-xs text-[#5A564F] leading-relaxed">
            VarhadCrop is an academic and empirical research platform intended for district-level risk benchmarking, climate stress-testing, and methodological auditing.
          </p>
        </div>

        <div>
          <h2 className="font-bold text-base mb-1">Disclaimer of Advisory Warranties</h2>
          <p className="text-xs text-[#5A564F] leading-relaxed">
            The platform outputs represent statistical associations derived from historical data. This tool does not constitute individualized agronomic, financial, insurance underwriting, or legal advice. Operators, agriculturalists, and insurers must independently verify local soil profiles, hydrological conditions, and official PMFBY notifications before making operational commitments.
          </p>
        </div>
      </div>
    </div>
  );
};
