import React, { useState } from 'react';
import { ShieldAlert, AlertCircle } from 'lucide-react';
import SearchBar from './components/SearchBar';
import RiskGauge from './components/RiskGauge';
import ArticleTable from './components/ArticleTable';
import ExplainabilityPanel from './components/ExplainabilityPanel';
import Timeline from './components/Timeline';
import HumanReview from './components/HumanReview';
import DeviceInfo from './components/DeviceInfo';
import AuditLog from './components/AuditLog';
import { screenEntity } from './api/client';

export default function App() {
  const [isSearching, setIsSearching] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [auditTrigger, setAuditTrigger] = useState(0);

  const handleSearch = async (query, useLiveWeb) => {
    setIsSearching(true);
    setError(null);
    try {
      const res = await screenEntity({ entity_name: query, top_k: 10, threshold: 0.15, use_live_web: useLiveWeb });
      setResult(res);
    } catch (err) {
      setError(err.message || 'An error occurred during screening');
      setResult(null);
    } finally {
      setIsSearching(false);
    }
  };

  const handleActionComplete = () => {
    setAuditTrigger(prev => prev + 1);
  };

  return (
    <div className="min-h-screen p-4 md:p-8">
      {/* Header */}
      <header className="max-w-6xl mx-auto mb-12 text-center animate-fade-in">
        <div className="inline-flex items-center justify-center p-3 bg-indigo-500/10 rounded-2xl mb-4 border border-indigo-500/20">
          <ShieldAlert className="text-indigo-400" size={32} />
        </div>
        <h1 className="text-3xl md:text-5xl font-bold tracking-tight text-slate-100 mb-4">
          Adverse Media <span className="gradient-text">Copilot</span>
        </h1>
        <p className="text-slate-400 max-w-2xl mx-auto text-sm md:text-base">
          AI-powered entity screening with AMD ROCm vector similarity and explainable risk scoring.
        </p>
      </header>

      {/* Main Container */}
      <main className="max-w-6xl mx-auto space-y-8 animate-slide-up">
        
        {/* Search Section */}
        <section>
          <SearchBar onSearch={handleSearch} isSearching={isSearching} />
          {error && (
            <div className="mt-4 p-4 rounded-xl bg-red-900/20 border border-red-500/30 text-red-400 flex items-center justify-center gap-2 max-w-2xl mx-auto">
              <AlertCircle size={18} />
              {error}
            </div>
          )}
        </section>

        {/* Results Section */}
        {result && (
          <div className="space-y-6 animate-fade-in">
            {/* Resolution Banner */}
            <div className="card p-4 flex flex-col md:flex-row justify-between items-center gap-4 text-sm">
              <div className="flex flex-col">
                <span className="text-slate-400">Queried: <span className="text-slate-200">{result.entity.original_name}</span></span>
                <span className="text-slate-400">Resolved to: <span className="text-indigo-300 font-semibold">{result.entity.resolved_name}</span> (Confidence: {(result.entity.confidence * 100).toFixed(1)}%)</span>
              </div>
              <div className="flex gap-2 flex-wrap">
                {result.entity.aliases?.map(a => (
                  <span key={a} className="px-2 py-1 bg-slate-800 rounded text-xs text-slate-400 border border-slate-700">
                    {a}
                  </span>
                ))}
              </div>
            </div>

            {/* Main Dash Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              <div className="lg:col-span-4">
                <RiskGauge 
                  score={result.risk_score} 
                  category={result.risk_category} 
                  breakdown={result.risk_breakdown}
                  confidence={result.confidence_score}
                />
              </div>
              <div className="lg:col-span-8">
                <ExplainabilityPanel report={result.explainability} />
              </div>
            </div>

            {/* Articles and Timeline */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              <div className="lg:col-span-8">
                <ArticleTable articles={result.articles} />
              </div>
              <div className="lg:col-span-4 space-y-6">
                <Timeline articles={result.articles} />
                <HumanReview 
                  screeningId={result.screening_id}
                  entityName={result.entity.resolved_name}
                  riskScore={result.risk_score}
                  riskCategory={result.risk_category}
                  onActionComplete={handleActionComplete}
                />
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-12 pt-8 border-t border-slate-800/60">
          <DeviceInfo />
          <div className="lg:flex lg:justify-end">
            <div className="w-full lg:w-[400px]">
              <AuditLog refreshTrigger={auditTrigger} />
            </div>
          </div>
        </div>

      </main>
    </div>
  );
}
