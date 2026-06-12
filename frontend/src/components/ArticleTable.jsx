import React from 'react';
import { ExternalLink, Calendar, AlertTriangle } from 'lucide-react';
import clsx from 'clsx';

export default function ArticleTable({ articles }) {
  const [expandedId, setExpandedId] = React.useState(null);

  if (!articles || articles.length === 0) return null;

  const toggleExpand = (id) => {
    setExpandedId(expandedId === id ? null : id);
  };

  const severityClass = (sev) => {
    switch (sev.toLowerCase()) {
      case 'critical': return 'badge-critical';
      case 'high': return 'badge-high';
      case 'medium': return 'badge-medium';
      case 'low': return 'badge-low';
      default: return 'badge-low';
    }
  };

  const highlightText = (text, keywords) => {
    if (!keywords || keywords.length === 0) return text;
    // Simple naive highlighting: regex replace ignoring case
    // We escape regex chars in keywords
    const regex = new RegExp(`(${keywords.map(k => k.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')})`, 'gi');
    
    // Split text and map
    const parts = text.split(regex);
    return parts.map((part, i) => {
      if (keywords.some(k => k.toLowerCase() === part.toLowerCase())) {
        return <span key={i} className="keyword-highlight">{part}</span>;
      }
      return part;
    });
  };

  return (
    <div className="card overflow-hidden">
      <div className="px-6 py-4 border-b border-slate-800/60 flex justify-between items-center bg-slate-800/20">
        <h2 className="text-lg font-semibold text-slate-200">Adverse Media Findings</h2>
        <span className="text-sm font-medium text-slate-400">{articles.length} articles</span>
      </div>
      
      <div className="divide-y divide-slate-800/60 max-h-[600px] overflow-y-auto">
        {articles.map((art) => (
          <div 
            key={art.id} 
            className="p-5 hover:bg-slate-800/30 transition-colors cursor-pointer group"
            onClick={() => toggleExpand(art.id)}
          >
            <div className="flex justify-between items-start gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                  <span className={severityClass(art.severity_label)}>
                    {art.severity_label.toUpperCase()}
                  </span>
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-800 text-slate-300 border border-slate-700">
                    {art.category.replace('_', ' ')}
                  </span>
                  <span className="text-xs font-medium text-slate-500 flex items-center gap-1 ml-auto">
                    <Calendar size={12} />
                    {art.published_date}
                  </span>
                </div>
                
                <h3 className="text-base font-semibold text-slate-200 group-hover:text-indigo-400 transition-colors mb-1 truncate">
                  {art.article_title}
                </h3>
                
                <div className="text-sm text-slate-500 flex items-center gap-2">
                  <span className="font-medium text-slate-400">{art.source}</span>
                  <span>•</span>
                  <span>Rel: {art.relevance_score.toFixed(2)}</span>
                  <span>•</span>
                  <span className="flex items-center gap-1">
                    <AlertTriangle size={14} className="text-amber-500/70" />
                    +{(art.risk_contribution).toFixed(1)} pts
                  </span>
                </div>
              </div>
            </div>

            {/* Expanded Content */}
            <div className={clsx(
              "grid transition-all duration-300 ease-in-out",
              expandedId === art.id ? "grid-rows-[1fr] opacity-100 mt-4" : "grid-rows-[0fr] opacity-0"
            )}>
              <div className="overflow-hidden">
                <div className="card-inner p-4 text-sm text-slate-300 leading-relaxed space-y-4">
                  <div className="p-3 bg-indigo-500/10 border border-indigo-500/20 rounded-lg text-indigo-200">
                    <strong>Why Flagged:</strong> {art.why_flagged}
                  </div>
                  
                  <div>
                    <h4 className="font-semibold text-slate-400 mb-1 text-xs uppercase tracking-wider">Article Excerpt</h4>
                    <p className="whitespace-pre-wrap">
                      {highlightText(art.article_text, art.keywords)}
                    </p>
                  </div>
                  
                  {art.keywords?.length > 0 && (
                    <div>
                      <h4 className="font-semibold text-slate-400 mb-2 text-xs uppercase tracking-wider">Extracted Keywords</h4>
                      <div className="flex flex-wrap gap-2">
                        {art.keywords.map((kw, i) => (
                          <span key={i} className="px-2 py-1 bg-slate-800 rounded text-xs text-amber-200 border border-amber-500/20">
                            {kw}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
