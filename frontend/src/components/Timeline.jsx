import React from 'react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell
} from 'recharts';

export default function Timeline({ articles }) {
  if (!articles || articles.length === 0) return null;

  // Group articles by year
  const yearCounts = articles.reduce((acc, art) => {
    const year = art.published_date.substring(0, 4);
    if (!acc[year]) acc[year] = { year, count: 0, critical: 0, high: 0, medium: 0, low: 0 };
    acc[year].count += 1;
    acc[year][art.severity_label] += 1;
    return acc;
  }, {});

  const data = Object.values(yearCounts).sort((a, b) => a.year.localeCompare(b.year));

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const p = payload[0].payload;
      return (
        <div className="bg-slate-900 border border-slate-700 p-3 rounded-lg shadow-xl text-sm">
          <p className="font-bold text-slate-200 mb-1">{label}</p>
          <p className="text-slate-400 mb-2">Total Articles: {p.count}</p>
          <div className="space-y-1 text-xs">
            {p.critical > 0 && <div className="text-rose-400">Critical: {p.critical}</div>}
            {p.high > 0 && <div className="text-red-400">High: {p.high}</div>}
            {p.medium > 0 && <div className="text-amber-400">Medium: {p.medium}</div>}
            {p.low > 0 && <div className="text-emerald-400">Low: {p.low}</div>}
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="card p-6">
      <h2 className="text-lg font-semibold text-slate-200 mb-6">Adverse Media Timeline</h2>
      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <XAxis dataKey="year" stroke="#475569" fontSize={12} tickLine={false} axisLine={false} />
            <YAxis stroke="#475569" fontSize={12} tickLine={false} axisLine={false} />
            <Tooltip cursor={{ fill: '#1e293b', opacity: 0.5 }} content={<CustomTooltip />} />
            <Bar dataKey="count" radius={[4, 4, 0, 0]}>
              {data.map((entry, index) => {
                // Colour based on the most severe finding in that year
                let fill = '#64748b'; // default slate
                if (entry.critical > 0) fill = '#e11d48'; // rose-600
                else if (entry.high > 0) fill = '#ef4444'; // red-500
                else if (entry.medium > 0) fill = '#f59e0b'; // amber-500
                else if (entry.low > 0) fill = '#10b981'; // emerald-500
                
                return <Cell key={`cell-${index}`} fill={fill} />;
              })}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
