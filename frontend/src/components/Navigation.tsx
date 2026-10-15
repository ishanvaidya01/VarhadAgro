import React, { useState } from 'react';
import { NavLink, Link } from 'react-router-dom';
import { Menu, X, ShieldCheck } from 'lucide-react';

const NAV_ITEMS = [
  { label: 'Risk Map', path: '/' },
  { label: 'District Detail', path: '/district' },
  { label: 'Season Tracker', path: '/early-warning' },
  { label: 'Scenario Lab', path: '/scenario' },
  { label: 'Crop Reliability', path: '/reliability' },
  { label: 'Climate Analogs', path: '/analogs' },
  { label: 'Evidence', path: '/evidence' },
];

export const Navigation: React.FC = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <header className="border-b border-hairline bg-[#FAF8F2] sticky top-0 z-40">
      {/* Top bulletin rule */}
      <div className="bg-[#1E5144] text-[#F3EFE6] px-4 py-1.5 text-xs flex justify-between items-center font-sans">
        <div className="flex items-center gap-2">
          <ShieldCheck size={14} className="text-[#FED98E]" />
          <span>Observed Evidence: ICRISAT DLD (1966-2017) and NASA POWER (1981-2023)</span>
        </div>
        <div className="hidden sm:block text-[11px] font-mono opacity-90">
          Spatial Unit: 1966 Parent Districts (Vidarbha)
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6">
        <div className="flex items-center justify-between h-14">
          {/* Brand */}
          <Link to="/" className="flex items-baseline gap-2.5">
            <span className="font-heading text-xl sm:text-2xl font-bold tracking-tight text-[#1B1A17]">
              VarhadCrop
            </span>
            <span className="text-xs uppercase tracking-wider text-[#5A564F] font-mono border-l border-hairline pl-2.5 hidden xs:inline">
              Vidarbha
            </span>
          </Link>

          {/* Desktop Nav */}
          <nav className="hidden lg:flex items-center space-x-1">
            {NAV_ITEMS.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `px-3 py-1.5 text-sm font-medium transition-colors border-b-2 ${
                    isActive
                      ? 'border-[#1E5144] text-[#1E5144] bg-[#F3EFE6]'
                      : 'border-transparent text-[#5A564F] hover:text-[#1B1A17] hover:border-[#D6CFBF]'
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>

          {/* Mobile hamburger */}
          <div className="lg:hidden flex items-center">
            <button
              type="button"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-1.5 text-[#5A564F] hover:text-[#1B1A17] border border-hairline bg-[#F3EFE6]"
              aria-label="Toggle navigation menu"
            >
              {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
          </div>
        </div>

        {/* Mobile menu dropdown */}
        {mobileMenuOpen && (
          <div className="lg:hidden border-t border-hairline py-2 bg-[#FAF8F2]">
            <nav className="flex flex-col space-y-1">
              {NAV_ITEMS.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  onClick={() => setMobileMenuOpen(false)}
                  className={({ isActive }) =>
                    `px-3 py-2 text-sm font-medium border-l-2 ${
                      isActive
                        ? 'border-[#1E5144] text-[#1E5144] bg-[#F3EFE6]'
                        : 'border-transparent text-[#5A564F] hover:text-[#1B1A17]'
                    }`
                  }
                >
                  {item.label}
                </NavLink>
              ))}
            </nav>
          </div>
        )}
      </div>
    </header>
  );
};
