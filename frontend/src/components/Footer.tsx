import React from 'react';
import { Link } from 'react-router-dom';
import { Logo } from './brand';

interface FooterProps {
  onOpenDisclaimer: () => void;
}

export const Footer: React.FC<FooterProps> = ({ onOpenDisclaimer }) => (
  <footer className="mt-20 border-t border-slate-200 bg-white">
    <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <div className="flex flex-col gap-8 md:flex-row md:items-start md:justify-between">
        <div className="max-w-sm">
          <Logo />
          <p className="mt-3 text-sm leading-relaxed text-slate-500">
            Evidence-based nutrition guidance from your lab reports, built on ICMR-NIN food data.
          </p>
        </div>
        <nav aria-label="Footer" className="flex flex-wrap gap-x-8 gap-y-2 text-sm">
          <Link to="/" className="text-slate-600 hover:text-slate-900">
            Analyze a report
          </Link>
          <Link to="/history" className="text-slate-600 hover:text-slate-900">
            My reports
          </Link>
          <button type="button" onClick={onOpenDisclaimer} className="text-slate-600 hover:text-slate-900">
            Safety &amp; privacy
          </button>
        </nav>
      </div>
      <div className="mt-5 flex flex-col gap-3 border-t border-slate-100 pt-4 text-xs leading-relaxed text-slate-500 md:flex-row md:items-center md:justify-between">
        <p>© {new Date().getFullYear()} NutriLens</p>
        <p className="max-w-2xl md:text-right">
          NutriLens is an educational nutrition tool. It does not provide medical diagnosis or treatment.
          Consult a qualified healthcare professional before changing your diet or supplements.
        </p>
      </div>
    </div>
  </footer>
);
