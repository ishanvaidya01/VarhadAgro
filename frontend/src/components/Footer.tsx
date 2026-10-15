import React from 'react';
import { Link } from 'react-router-dom';

export const Footer: React.FC = () => {
  return (
    <footer className="border-t border-hairline bg-[#FAF8F2] mt-16 py-8 text-xs text-[#5A564F]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div className="space-y-1">
          <p className="font-medium text-[#1B1A17]">VarhadCrop Platform</p>
          <p>
            Statistical models trained on ICRISAT DLD (1966-2017) and NASA POWER (1981-2023).
          </p>
          <p className="text-[11px] text-[#847F75]">
            Notice: All model outputs represent empirical statistical associations, not agronomic causation.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row sm:items-center gap-4 sm:gap-8">
          <div>
            <span>Operator: <strong>Ishan Vaidya</strong> (Pune, India)</span>
            <span className="mx-2 hidden sm:inline">|</span>
            <span>Contact: <a href="mailto:ishan.vaidya01@gmail.com" className="underline hover:text-[#1B1A17]">ishan.vaidya01@gmail.com</a></span>
          </div>

          <div className="flex gap-4">
            <Link to="/privacy" className="underline hover:text-[#1B1A17]">Privacy Policy</Link>
            <Link to="/terms" className="underline hover:text-[#1B1A17]">Terms and Conditions</Link>
          </div>
        </div>
      </div>
    </footer>
  );
};
