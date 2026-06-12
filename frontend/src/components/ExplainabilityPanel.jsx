import React from 'react';
import { Info, BarChart3, AlertCircle } from 'lucide-react';

export default function ExplainabilityPanel({ report }) {
  if (!report) return null;

  return (
    <div className="card p-6 h-full flex flex-col">
      <div className="flex items-center gap-2 mb-4">
        <Info className="text-indigo-400" size={20} />
        <h2 className="text-lg font-semibold text-slate-200">Executive Summary</h2>
      </div>

      {/* AI Summary */}
      <div className="mb-6 p-4 rounded-xl bg-gradient-to-br from-indigo-900/20 to-slate-800/40 border border-indigo-500/20 leading-relaxed text-slate-300 text-sm">
        {report.summary}
      </div>

      <div className="space-y-6 flex-grow">
        {/* Key Risk Factors */}
        <div>
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2">
            <AlertCircle size={14} /> Key Risk Factors
          </h3>
          <ul className="space-y-2">
            {report.key_risk_factors.map((factor, i) => (
              <li key={i} className="text-sm text-slate-300 flex items-start gap-2">
                <span className="text-slate-600 mt-0.5">•</span>
                <span>{factor.replace(/^[^\w\s]+\s/, '')}</span> {/* Strips the emoji if we want to render it custom, but we leave it as is here by keeping the string */}
              </li>
            ))}
          </ul>
        </div>

        {/* Global Keywords */}
        <div>
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2">
            <BarChart3 size={14} /> Top Keywords
          </h3>
          <div className="flex flex-wrap gap-2">
            {report.top_keywords.map((kw, i) => (
              <span key={i} className="px-2 py-1 bg-slate-800/80 rounded text-xs text-indigo-300 border border-slate-700">
                {kw}
              </span>
            ))}
          </div>
        </div>
      </div>
      
      <div className="mt-6 pt-4 border-t border-slate-800 text-xs text-slate-500 flex justify-between">
        <span>{report.timeline_analysis}</span>
      </div>
    </div>
  );
}
