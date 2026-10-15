import React from 'react';
import { Link } from 'react-router-dom';
import { Compass } from 'lucide-react';

export const NotFound: React.FC = () => {
  return (
    <div className="py-16 text-center max-w-lg mx-auto space-y-4">
      <div className="w-12 h-12 bg-[#FAF8F2] border border-hairline mx-auto flex items-center justify-center text-[#1E5144]">
        <Compass size={24} />
      </div>
      <h1 className="text-3xl font-bold font-heading text-[#1B1A17]">404 &bull; Page Not Found</h1>
      <p className="text-sm text-[#5A564F] leading-relaxed">
        The requested path does not exist on the VarhadCrop platform.
      </p>
      <div className="pt-2">
        <Link
          to="/"
          className="inline-block px-4 py-2 border border-[#1E5144] bg-[#1E5144] text-[#F3EFE6] text-xs font-medium hover:bg-[#153B31] transition-colors"
        >
          Return to Vidarbha Risk Map
        </Link>
      </div>
    </div>
  );
};
