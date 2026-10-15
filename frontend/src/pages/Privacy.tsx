import React from 'react';

export const Privacy: React.FC = () => {
  return (
    <div className="py-8 max-w-3xl mx-auto space-y-6">
      <div className="border-b border-hairline pb-3">
        <h1 className="text-2xl sm:text-3xl font-bold font-heading text-[#1B1A17]">Privacy Policy</h1>
        <span className="text-xs text-[#5A564F] font-mono">Last updated: 2026-10-14</span>
      </div>

      <div className="bg-[#FAF8F2] border border-hairline p-6 text-sm text-[#1B1A17] space-y-4">
        <div>
          <h2 className="font-bold text-base mb-1">Operator and Contact Information</h2>
          <p className="text-xs text-[#5A564F]">
            <strong>Operator:</strong> Ishan Vaidya
          </p>
          <p className="text-xs text-[#5A564F]">
            <strong>Contact Email:</strong> ishan.vaidya01@gmail.com
          </p>
          <p className="text-xs text-[#5A564F]">
            <strong>Jurisdiction:</strong> Pune, Maharashtra, India
          </p>
        </div>

        <div>
          <h2 className="font-bold text-base mb-1">Data Collection and Analytics</h2>
          <p className="text-xs text-[#5A564F] leading-relaxed">
            No personal data tracking, persistent profiling cookies, or invasive behavioral tracking is performed by this platform. 
            All simulations, queries, and stress tests process public empirical weather and agricultural statistics.
          </p>
        </div>

        <div>
          <h2 className="font-bold text-base mb-1">Server Logs</h2>
          <p className="text-xs text-[#5A564F] leading-relaxed">
            Standard HTTP request metadata (IP address, user agent, request path) may be momentarily recorded in volatile server logs for operational security, rate limiting, and debugging purposes only.
          </p>
        </div>
      </div>
    </div>
  );
};
