import React from 'react';
import { ShieldAlert, ShieldCheck, Shield } from 'lucide-react';

export default function RiskGauge({ score, category, breakdown, confidence }) {
  // Determine colours and icons based on category
  const isHigh = category === 'HIGH';
  const isMed = category === 'MEDIUM';
  const isLow = category === 'LOW';

  const colorClass = isHigh ? 'text-risk-high' : isMed ? 'text-risk-med' : 'text-risk-low';
  const bgClass = isHigh ? 'bg-risk-high/10' : isMed ? 'bg-risk-med/10' : 'bg-risk-low/10';
  const borderClass = isHigh ? 'border-risk-high/30' : isMed ? 'border-risk-med/30' : 'border-risk-low/30';
  
  const Icon = isHigh ? ShieldAlert : isMed ? Shield : ShieldCheck;

  // SVG arc calculation (0 to 180 degrees)
  const radius = 80;
  const strokeWidth = 12;
  const circumference = radius * Math.PI; // semi-circle
  const strokeDashoffset = circumference - (score / 100) * circumference;

  return (
    <div className="card p-6 flex flex-col items-center justify-between h-full relative overflow-hidden">
      {/* Background glow */}
      <div className={`absolute -top-10 -right-10 w-40 h-40 blur-3xl opacity-20 rounded-full ${isHigh ? 'bg-risk-high' : isMed ? 'bg-risk-med' : 'bg-risk-low'}`} />

      <h2 className="text-lg font-semibold text-slate-300 w-full mb-4">Risk Assessment</h2>
      
      <div className="relative flex flex-col items-center">
        {/* SVG Gauge */}
        <svg width="200" height="110" viewBox="0 0 200 110" className="overflow-visible">
          <defs>
            <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#10b981" />
              <stop offset="50%" stopColor="#f59e0b" />
              <stop offset="100%" stopColor="#ef4444" />
            </linearGradient>
          </defs>
          {/* Background Arc */}
          <path
            d="M 20 100 A 80 80 0 0 1 180 100"
            fill="none"
            stroke="currentColor"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            className="text-slate-800"
          />
          {/* Foreground Arc */}
          <path
            d="M 20 100 A 80 80 0 0 1 180 100"
            fill="none"
            stroke="url(#gaugeGradient)"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            className="transition-all duration-1000 ease-out"
          />
        </svg>

        {/* Score Display */}
        <div className="absolute bottom-0 flex flex-col items-center transform translate-y-4">
          <div className={`text-4xl font-bold tracking-tight ${colorClass}`}>
            {score.toFixed(1)}
          </div>
          <div className={`mt-1 flex items-center gap-1.5 px-3 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider border ${bgClass} ${colorClass} ${borderClass}`}>
            <Icon size={12} />
            {category}
          </div>
        </div>
      </div>

      {/* Breakdown */}
      <div className="w-full mt-10 grid grid-cols-2 gap-3 text-xs">
        <div className="card-inner p-3">
          <div className="text-slate-400 mb-1">Relevance</div>
          <div className="font-medium text-slate-200">{breakdown.relevance_component.toFixed(1)} / 35</div>
        </div>
        <div className="card-inner p-3">
          <div className="text-slate-400 mb-1">Severity</div>
          <div className="font-medium text-slate-200">{breakdown.severity_component.toFixed(1)} / 25</div>
        </div>
        <div className="card-inner p-3">
          <div className="text-slate-400 mb-1">Frequency</div>
          <div className="font-medium text-slate-200">{breakdown.frequency_component.toFixed(1)} / 25</div>
        </div>
        <div className="card-inner p-3">
          <div className="text-slate-400 mb-1">Recency</div>
          <div className="font-medium text-slate-200">{breakdown.recency_component.toFixed(1)} / 15</div>
        </div>
      </div>

      <div className="w-full mt-4 text-xs text-center text-slate-500 font-medium">
        Confidence Score: {(confidence * 100).toFixed(1)}%
      </div>
    </div>
  );
}
