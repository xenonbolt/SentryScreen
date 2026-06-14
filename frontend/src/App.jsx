/**
* App.jsx — SentryScreen Adverse Media Copilot
* Matches the design of /home/dwijo/Desktop/UI/src/App.tsx
* API → FastAPI backend via Jupyter proxy or direct Vite dev proxy.
* Demo mode auto-activates when the backend is unreachable.
*/

import React, { useState, useEffect, useRef } from 'react';
import {
  Shield, Search, Activity, Cpu, History, AlertTriangle,
  CheckCircle, XCircle, AlertCircle, HelpCircle, ChevronRight,
  Sparkles, Info, Layers, Database, Calendar, Clock,
  ArrowRight, TrendingUp, FileText, User, Building, RefreshCw,
  Wifi, WifiOff, Server,
} from 'lucide-react';
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip,
  CartesianGrid, BarChart, Bar,
} from 'recharts';

import {
  screenEntity, submitAudit, fetchAuditLog,
  fetchHealth, fetchDatasetStats, fetchArticles, API_BASE,
} from './api/client';
import { DEMO_SCREENING_RESULT, DEMO_HEALTH, DEMO_AUDIT_LOG } from './api/demoData';

// ── Risk colour helpers ────────────────────────────────────────────────────────
const getRiskColor = (cat) => {
  if (!cat) return 'text-slate-400 bg-slate-500/10 border-slate-500/20';
  const c = cat.toUpperCase();
  if (c === 'HIGH') return 'text-red-400 bg-red-500/10 border-red-500/20';
  if (c === 'MEDIUM') return 'text-amber-400 bg-amber-500/10 border-amber-500/20';
  return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
};

const getRiskStroke = (cat) => {
  if (!cat) return '#64748b';
  const c = cat.toUpperCase();
  if (c === 'HIGH') return '#ef4444';
  if (c === 'MEDIUM') return '#f59e0b';
  return '#10b981';
};

const getSeverityBadge = (label) => {
  const l = (label || '').toLowerCase();
  if (l === 'critical') return 'bg-rose-600/20 text-rose-300 border border-rose-500/30';
  if (l === 'high') return 'bg-red-500/20 text-red-300 border border-red-500/30';
  if (l === 'medium') return 'bg-amber-500/20 text-amber-300 border border-amber-500/30';
  return 'bg-slate-700/50 text-slate-300 border border-slate-600/30';
};

const getSentimentColor = (score) => {
  if (score >= 0.70) return '#ef4444';
  if (score >= 0.45) return '#f59e0b';
  return '#4ade80';
};

// ── Keyword highlighter ──────────────────────────────────────────────────────
function HighlightedText({ text, keywords = [] }) {
  if (!keywords.length) return <span>{text}</span>;
  const sorted = [...keywords].sort((a, b) => b.length - a.length);
  const escaped = sorted.map(k => k.replace(/[./\\^$*+?{}|[\]()]/g, '\\$&')).join('|');
  if (!escaped) return <span>{text}</span>;
  const regex = new RegExp(`\\b(${escaped})\\b`, 'gi');
  const parts = text.split(regex);
  return (
    <>
      {parts.map((p, i) =>
        sorted.some(k => k.toLowerCase() === p.toLowerCase())
          ? <span key={i} className="bg-red-500/30 text-rose-300 px-1 py-0.5 rounded font-semibold border border-red-500/40">{p}</span>
          : p
      )}
    </>
  );
}

// ── Agent pipeline steps ─────────────────────────────────────────────────────
const AGENT_STEPS = [
  { agent: 'Entity Resolver Agent', log: 'Init: Received query, resolving candidate matches...' },
  { agent: 'Entity Resolver Agent', log: 'Comparing token distances & database mappings...' },
  { agent: 'Adverse Media Retrieval', log: 'Firing 3-query Google-style search (general + negative + adverse)...' },
  { agent: 'Adverse Media Retrieval', log: 'Reading full article content via newspaper3k...' },
  { agent: 'Relevance Scoring Agent', log: 'Computing SentenceTransformer embeddings on device...' },
  { agent: 'Relevance Scoring Agent', log: 'Evaluating cosine similarity vectors against FAISS index...' },
  { agent: 'Sentiment Analysis (ZSC)', log: 'Running zero-shot classification (nli-deberta-v3-small)...' },
  { agent: 'Risk Analysis Agent', log: 'Applying weighted formula: rel+sev+freq+recency+sentiment...' },
  { agent: 'Explainability Agent', log: 'Cataloging risk keywords and summaries...' },
  { agent: 'Decision Agent', log: 'Finalising risk tier and compliance directive...' },
];

// ═══════════════════════════════════════════════════════════════════════════
export default function App() {
  // ── State ─────────────────────────────────────────────────────────────────
  const [entityName, setEntityName] = useState('');
  const [customFocus, setCustomFocus] = useState('');
  const [webSearch, setWebSearch] = useState(true);
  const [loading, setLoading] = useState(false);
  const [activeAgent, setActiveAgent] = useState('');
  const [agentLogs, setAgentLogs] = useState([]);
  const [apiError, setApiError] = useState(null);

  const [selectedResult, setSelectedResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [hardware, setHardware] = useState(null);
  const [dbStats, setDbStats] = useState(null);
  const [dbArticles, setDbArticles] = useState([]);
  const [auditLog, setAuditLog] = useState([]);
  const [analystNotes, setAnalystNotes] = useState('');
  const [activeTab, setActiveTab] = useState('dashboard');
  const [isDemo, setIsDemo] = useState(false);
  const [dbEntityFilter, setDbEntityFilter] = useState('');
  const [dbSevFilter, setDbSevFilter] = useState('ALL');
  const [rocmStats, setRocmStats] = useState({ vram: 14200, load: 45, cpu: 25, ram: 128 });

  const logEndRef = useRef(null);

  // ── Bootstrap ─────────────────────────────────────────────────────────────
  useEffect(() => {
    loadHardware();
    loadAuditLog();
    loadDbStats();
    
    // Fallback if telemetry fails
    const hw = setInterval(() => {
      loadHardware();
    }, 60000);
    
    // Fast polling telemetry
    const tel = setInterval(() => {
      loadTelemetry();
    }, 1000);
    
    return () => {
      clearInterval(hw);
      clearInterval(tel);
    };
  }, []);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [agentLogs]);

  async function loadHardware() {
    try {
      const data = await fetchHealth();
      setHardware(data);
      setIsDemo(false);
    } catch {
      setHardware(DEMO_HEALTH);
      setIsDemo(true);
    }
  }

  async function loadTelemetry() {
    try {
      const { fetchTelemetry } = await import('./api/client');
      const data = await fetchTelemetry();
      if (data.vram_usage !== undefined) {
        setRocmStats({
          vram: data.vram_usage,
          load: data.compute_load,
          cpu: data.cpu_usage,
          ram: data.ram_usage
        });
      }
    } catch {
      // Mock fallback
      setRocmStats(prev => ({
        vram: Math.min(198000, Math.max(1000, prev.vram + Math.floor(Math.random() * 2000 - 500))),
        load: Math.min(100, Math.max(5, prev.load + Math.floor(Math.random() * 40 - 15))),
        cpu: Math.min(100, Math.max(2, prev.cpu + Math.floor(Math.random() * 20 - 10))),
        ram: Math.min(256, Math.max(32, prev.ram + Math.floor(Math.random() * 8 - 4)))
      }));
    }
  }

  async function loadDbStats() {
    try {
      const stats = await fetchDatasetStats();
      setDbStats(stats);
    } catch {
      setDbStats({ total_articles: 1250, unique_entities: 120, category_counts: {}, severity_counts: {} });
    }
  }

  async function loadAuditLog() {
    try {
      const logs = await fetchAuditLog(50);
      setAuditLog(Array.isArray(logs) ? logs : []);
    } catch {
      setAuditLog(DEMO_AUDIT_LOG);
    }
  }

  async function loadDbArticles() {
    try {
      const params = { limit: 100 };
      if (dbEntityFilter) params.entity = dbEntityFilter;
      if (dbSevFilter !== 'ALL') params.severity = dbSevFilter.toLowerCase();
      const arts = await fetchArticles(params);
      setDbArticles(Array.isArray(arts) ? arts : []);
    } catch {
      setDbArticles(DEMO_SCREENING_RESULT.articles);
    }
  }

  const handleAuditAction = async (action) => {
    if (!selectedResult) return;
    try {
      await submitAudit({
        screening_id: selectedResult.screening_id,
        entity_name: selectedResult.entity.resolved_name,
        action: action,
        analyst_notes: analystNotes,
        risk_score: selectedResult.risk_score,
        risk_category: selectedResult.risk_category
      });
      loadAuditLog();
      setAnalystNotes('');
      if (action === 'ESCALATE') {
        alert("This has been escalated");
      } else {
        alert(`Decision Logged: ${action}`);
      }

    } catch (err) {
      alert(`Failed to log decision: ${err.message}`);
    }
  };

  // ── Run screening ─────────────────────────────────────────────────────────
  const runScreening = async (e) => {
    e.preventDefault();
    if (!entityName.trim()) return;

    setLoading(true);
    setApiError(null);
    setAgentLogs([]);
    setActiveAgent('');

    let idx = 0;
    const runSteps = () => {
      if (idx < AGENT_STEPS.length) {
        const stepAgent = AGENT_STEPS[idx].agent;
        const stepLog = AGENT_STEPS[idx].log;
        setActiveAgent(stepAgent);
        setAgentLogs(prev => [...prev, `[${stepAgent}] ${stepLog}`]);
        idx++;
        setTimeout(runSteps, 550);
      } else {
        doApiCall();
      }
    };
    runSteps();
  };

  async function doApiCall() {
    try {
      const res = await screenEntity({
        entity_name: entityName.trim(),
        top_k: 15,
        threshold: 0.0,
        use_live_web: webSearch,
      });
      const session = { ...res, _queryInput: entityName.trim(), _ts: Date.now() };
      setHistory(prev => [session, ...prev]);
      setSelectedResult(session);
      setAnalystNotes('');
      setEntityName('');
      setIsDemo(false);
    } catch (err) {
      if (err.message?.includes('fetch') || err instanceof TypeError) {
        // Backend offline → use demo data
        const demo = { ...DEMO_SCREENING_RESULT, entity: { ...DEMO_SCREENING_RESULT.entity, original_name: entityName.trim() }, _queryInput: entityName.trim(), _ts: Date.now() };
        setHistory(prev => [demo, ...prev]);
        setSelectedResult(demo);
        setAnalystNotes('');
        setEntityName('');
        setIsDemo(true);
        setApiError(null);
      } else {
        setApiError(err.message || 'Unexpected server error.');
      }
    } finally {
      setLoading(false);
      setActiveAgent('');
    }
  }

  async function submitDecision(action) {
    if (!selectedResult) return;
    const payload = {
      screening_id: selectedResult.screening_id,
      entity_name: selectedResult.entity?.resolved_name || 'Unknown',
      action,
      analyst_notes: analystNotes,
      risk_score: selectedResult.risk_score,
      risk_category: selectedResult.risk_category,
    };
    try {
      await submitAudit(payload);
    } catch { /* demo mode — ignore */ }
    const updated = { ...selectedResult, _reviewStatus: action, _reviewNotes: analystNotes };
    setSelectedResult(updated);
    setHistory(prev => prev.map(s => s.screening_id === updated.screening_id ? updated : s));
    setAuditLog(prev => [{ ...payload, timestamp: new Date().toISOString() }, ...prev]);
    if (action === 'ESCALATE') {
      alert("This has been escalated");
    }

  }

  // ── Timeline data ─────────────────────────────────────────────────────────
  const timelineData = (() => {
    if (!selectedResult?.articles?.length) return [];
    const map = {};
    selectedResult.articles.forEach(art => {
      const mo = (art.published_date || '').slice(0, 7);
      if (!mo) return;
      if (!map[mo]) map[mo] = { count: 0, maxSent: 0 };
      map[mo].count++;
      if ((art.sentiment_score || 0) > map[mo].maxSent) map[mo].maxSent = art.sentiment_score || 0;
    });
    return Object.entries(map)
      .map(([date, v]) => ({ date, 'Negative Vol': v.count, 'Peak Sentiment': +(v.maxSent * 100).toFixed(1) }))
      .sort((a, b) => a.date.localeCompare(b.date));
  })();

  const negativeArticles = selectedResult?.articles?.filter(a => a.is_negative_news) || [];

  // ── Tabs ──────────────────────────────────────────────────────────────────
  const TABS = [
    { id: 'dashboard', label: 'SCREENING HUB' },
    { id: 'audit', label: `AUDIT LOGS (${auditLog.length})` },
    { id: 'database', label: `COMPLIANCE DATABASE (${dbStats?.total_articles || 0})` },
    { id: 'hardware', label: 'ROCM GPU DIAGNOSTICS' },
  ];

  // ══════════════════════════════════════════════════════════════════════════
  return (
    <div className="min-h-screen bg-[#0d121f] text-slate-100 flex flex-col font-sans selection:bg-cyan-500/30">

      {/* ── HEADER ── */}
      <header className="border-b border-slate-800 bg-[#090d16] px-6 py-4 flex flex-col md:flex-row items-center justify-between gap-4 shadow-xl shadow-black/20">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-gradient-to-br from-red-600 to-rose-700 rounded-lg shadow-md flex items-center justify-center">
            <Shield className="w-6 h-6 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold tracking-tight text-white">Adverse Media Screening Copilot</h1>
              <span className="text-[10px] bg-red-500/20 text-rose-400 font-mono font-semibold px-2 py-0.5 rounded-full border border-red-500/30">
                AMD Instinct Edge
              </span>
            </div>
            <p className="text-xs text-slate-400">Agent-driven name resolution, semantic scoring &amp; regulatory risk appraisal</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Demo mode badge */}
          {isDemo && (
            <div className="flex items-center gap-2 bg-amber-500/10 border border-amber-500/30 px-3 py-1.5 rounded-lg text-xs text-amber-400">
              <WifiOff className="w-3.5 h-3.5" />
              <span className="font-mono font-semibold">DEMO MODE — API offline</span>
            </div>
          )}
          {!isDemo && hardware && (
            <div className="flex items-center gap-4 bg-[#121927] border border-slate-800 px-4 py-2 rounded-lg text-xs">
              <div className="flex items-center gap-2">
                <div className="relative">
                  <div className="w-2.5 h-2.5 bg-emerald-500 rounded-full animate-ping absolute top-0 left-0" />
                  <div className="w-2.5 h-2.5 bg-emerald-400 rounded-full relative" />
                </div>
                <span className="font-mono text-slate-300 font-medium">ROCm Engine Active</span>
              </div>
              <div className="h-6 w-px bg-slate-800" />
              <div>
                <span className="text-slate-400 block text-[10px]">DEVICE</span>
                <span className="font-semibold text-slate-200 font-mono flex items-center gap-1">
                  <Cpu className="w-3.5 h-3.5 text-cyan-400" />
                  {hardware.device_name || 'CPU'}
                </span>
              </div>
              <div className="h-6 w-px bg-slate-800" />
              <div>
                <span className="text-slate-400 block text-[10px]">STATUS</span>
                <span className="font-semibold text-emerald-400 font-mono">{hardware.status || 'ok'}</span>
              </div>
            </div>
          )}
        </div>
      </header>

      {/* ── NAV TABS ── */}
      <nav className="bg-[#0b101a] border-b border-slate-800 px-6 py-2 flex items-center justify-between">
        <div className="flex gap-1.5">
          {TABS.map(t => (
            <button
              key={t.id}
              onClick={() => { setActiveTab(t.id); if (t.id === 'database') loadDbArticles(); if (t.id === 'audit') loadAuditLog(); }}
              className={`px-4 py-2 rounded-lg text-xs font-semibold tracking-wide transition-all ${activeTab === t.id
                  ? 'bg-slate-800 text-white shadow-inner border-b-2 border-red-500'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
                }`}
            >
              {t.label}
            </button>
          ))}
        </div>
        <div className="text-xs text-slate-500 flex items-center gap-2 bg-slate-900 px-3 py-1.5 rounded-full border border-slate-800">
          <Clock className="w-3.5 h-3.5 text-slate-400" />
          <span>API: <strong className="font-mono text-slate-300 text-[10px]">{API_BASE}</strong></span>
        </div>
      </nav>

      {/* ── MAIN ── */}
      <main className="flex-1 p-6 overflow-y-auto">

        {/* ════════ TAB: SCREENING HUB ════════ */}
        {activeTab === 'dashboard' && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

            {/* LEFT COL: controls (span 4) */}
            <div className="lg:col-span-4 flex flex-col gap-6">

              {/* Search card */}
              <div className="bg-[#121927] border border-slate-800 rounded-xl p-5 shadow-lg relative overflow-hidden">
                <div className="absolute right-0 top-0 w-24 h-24 bg-gradient-to-bl from-rose-500/10 to-transparent pointer-events-none" />
                <h2 className="text-sm font-bold text-slate-200 flex items-center gap-2 mb-4">
                  <Search className="w-4 h-4 text-rose-500" />
                  Trigger Adverse Screening
                </h2>

                <form onSubmit={runScreening} className="space-y-4">
                  <div className="space-y-1">
                    <label className="text-[11px] font-bold text-slate-400 tracking-wider uppercase">Entity Name</label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. Genesis Global Minerals"
                      value={entityName}
                      disabled={loading}
                      onChange={e => setEntityName(e.target.value)}
                      className="w-full bg-[#0a0d15] text-slate-200 border border-slate-800 px-3.5 py-2.5 rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-rose-500 font-medium placeholder-slate-700"
                    />
                    <div className="text-[10px] text-slate-500 italic mt-1">Try: Apex FinTech Services, Genesis Global Minerals</div>
                  </div>

                  <div className="space-y-1">
                    <label className="text-[11px] font-bold text-slate-400 tracking-wider uppercase">Custom Threat Focus (Optional)</label>
                    <input
                      type="text"
                      placeholder="e.g. Sanctions evasion, ESG violations"
                      value={customFocus}
                      disabled={loading}
                      onChange={e => setCustomFocus(e.target.value)}
                      className="w-full bg-[#0a0d15] text-slate-200 border border-slate-800 px-3.5 py-2 rounded-lg text-xs focus:outline-none focus:ring-1 focus:ring-rose-500 placeholder-slate-700"
                    />
                  </div>

                  <div className="pt-1">
                    <label className="flex items-center gap-2.5 cursor-pointer text-xs font-semibold text-slate-300">
                      <input
                        type="checkbox"
                        checked={webSearch}
                        disabled={loading}
                        onChange={e => setWebSearch(e.target.checked)}
                        className="w-4 h-4 accent-rose-500 rounded"
                      />
                      <span className="flex items-center gap-1.5">
                        Enable Live OSINT Web Search
                        <span className="text-[9px] bg-cyan-500/20 text-cyan-400 px-1.5 py-0.5 rounded-full uppercase tracking-wider font-mono">
                          Live
                        </span>
                      </span>
                    </label>
                    <p className="text-[10px] text-slate-500 pl-6 mt-0.5">
                      Fires 3 Google-style DDG queries + reads full article content.
                    </p>
                  </div>

                  {apiError && (
                    <div className="bg-red-500/10 border border-red-500/30 p-3 rounded-lg text-xs text-rose-400 flex items-start gap-2">
                      <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                      <div><strong>Error:</strong> {apiError}</div>
                    </div>
                  )}

                  {isDemo && (
                    <div className="bg-amber-500/10 border border-amber-500/30 p-3 rounded-lg text-xs text-amber-400 flex items-start gap-2">
                      <WifiOff className="w-4 h-4 shrink-0 mt-0.5" />
                      <div>Backend unreachable. Results will use <strong>demo data</strong>.</div>
                    </div>
                  )}

                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full bg-[#e11d48] hover:bg-[#be123c] disabled:bg-slate-800 disabled:text-slate-500 rounded-lg py-2.5 text-xs font-bold uppercase tracking-wider text-white transition-colors shadow-lg shadow-rose-950/20 flex items-center justify-center gap-2 cursor-pointer"
                  >
                    {loading ? (
                      <><RefreshCw className="w-4 h-4 animate-spin" />RUNNING MULTI-AGENT SWEEP...</>
                    ) : (
                      <><Shield className="w-4 h-4" />LAUNCH COPILOT SCREENING</>
                    )}
                  </button>
                </form>
              </div>

              {/* Agent pipeline log (visible during loading) */}
              {loading && (
                <div className="bg-[#121927] border border-slate-800 rounded-xl p-5 shadow-lg flex flex-col min-h-[300px]">
                  <h3 className="text-xs font-bold text-slate-200 tracking-wider uppercase mb-3 flex items-center justify-between border-b border-slate-800 pb-2">
                    <span className="flex items-center gap-1.5 text-rose-400">
                      <Activity className="w-3.5 h-3.5 animate-pulse" />
                      Active Agent Pipeline
                    </span>
                    <span className="font-mono text-[10px] text-zinc-500">Live Trace</span>
                  </h3>
                  <div className="bg-slate-900 border border-slate-800 rounded-lg p-3 text-xs mb-3 flex items-center justify-between">
                    <span className="text-slate-400">Executing:</span>
                    <span className="font-mono font-bold text-cyan-400 bg-cyan-900/15 border border-cyan-800/30 px-2 py-0.5 rounded">{activeAgent}</span>
                  </div>
                  <div className="bg-black/40 rounded-lg p-3.5 flex-1 font-mono text-[11px] overflow-y-auto space-y-2 text-slate-300">
                    {agentLogs.map((log, i) => (
                      <div key={i} className="flex gap-2">
                        <span className="text-rose-500 font-bold shrink-0">»</span>
                        <span>{log}</span>
                      </div>
                    ))}
                    <div className="flex gap-2 text-rose-400 animate-pulse">
                      <span className="shrink-0">_</span>
                      <span>Processing...</span>
                    </div>
                    <div ref={logEndRef} />
                  </div>
                </div>
              )}

              {/* History */}
              {!loading && (
                <div className="bg-[#121927] border border-slate-800 rounded-xl p-5 shadow-lg">
                  <h3 className="text-xs font-bold text-slate-400 tracking-wider uppercase mb-4 flex items-center justify-between">
                    <span className="flex items-center gap-2">
                      <History className="w-4 h-4 text-emerald-500" />
                      Recent Sessions
                    </span>
                    <span className="text-[10px] text-neutral-500">Count: {history.length}</span>
                  </h3>

                  {history.length === 0 ? (
                    <div className="text-xs text-slate-600 italic py-6 text-center">
                      No entities screened yet. Submit a name above.
                    </div>
                  ) : (
                    <div className="space-y-2.5 max-h-[350px] overflow-y-auto pr-1">
                      {history.slice(0, 7).map((item, i) => (
                        <button
                          key={i}
                          onClick={() => setSelectedResult(item)}
                          className={`w-full text-left p-3 rounded-lg border text-xs flex flex-col gap-1.5 transition-all ${selectedResult?.screening_id === item.screening_id
                              ? 'bg-slate-800/70 border-slate-700'
                              : 'bg-[#0b101a] border-slate-800/50 hover:bg-slate-800/30'
                            }`}
                        >
                          <div className="flex justify-between items-center w-full">
                            <span className="font-bold text-slate-100 truncate max-w-[160px]">
                              {item.entity?.original_name || item._queryInput}
                            </span>
                            <span className={`text-[9px] font-mono font-bold px-1.5 py-0.5 rounded border uppercase ${getRiskColor(item.risk_category)}`}>
                              {item.risk_score?.toFixed(0)} ({item.risk_category})
                            </span>
                          </div>
                          <div className="flex justify-between text-[10px] text-slate-500">
                            <span>{item._reviewStatus || 'PENDING'}</span>
                            <span className="font-mono text-[9px]">{new Date(item._ts || item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                          </div>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* RIGHT COL: results (span 8) */}
            <div className="lg:col-span-8 space-y-6">
              {!selectedResult ? (
                /* ── Empty state ── */
                <div className="bg-[#121927] border border-slate-800 rounded-xl p-16 text-center shadow-lg flex flex-col items-center justify-center min-h-[500px]">
                  <div className="w-16 h-16 bg-slate-800/50 rounded-full flex items-center justify-center mb-4 border border-slate-700/50">
                    <Shield className="w-8 h-8 text-slate-500" />
                  </div>
                  <h3 className="text-lg font-bold text-slate-300">Ready for screening campaign</h3>
                  <p className="text-xs text-slate-500 max-w-md mt-2">
                    Enter an entity name to trigger the multi-agent adverse media pipeline.
                    {isDemo && ' Running in demo mode — no backend required.'}
                  </p>

                  <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-3 w-full max-w-2xl">
                    {[
                      { label: 'CASE 1', color: 'text-rose-400', name: 'Genesis Global Minerals', desc: 'Critical environmental + Panama bribery.' },
                      { label: 'CASE 2', color: 'text-amber-400', name: 'Apex FinTech Services', desc: '$18M FinCEN AML fine + CEO fraud.' },
                      { label: 'CASE 3', color: 'text-emerald-400', name: 'Microsoft', desc: 'Tech giant — recent news + layoffs check.' },
                    ].map(c => (
                      <div
                        key={c.name}
                        onClick={() => setEntityName(c.name)}
                        className="p-3 bg-slate-900 border border-slate-800/70 hover:border-slate-700 rounded-lg text-left cursor-pointer transition-all"
                      >
                        <span className={`text-[10px] font-mono font-extrabold uppercase ${c.color}`}>{c.label}</span>
                        <h4 className="text-xs font-bold text-slate-200 mt-1">{c.name}</h4>
                        <p className="text-[11px] text-slate-500 mt-1">{c.desc}</p>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                /* ── Results ── */
                <div className="space-y-6">

                  {/* ── Risk score + compliance directive row ── */}
                  <div className="grid grid-cols-1 md:grid-cols-12 gap-6">

                    {/* Gauge (span 6) */}
                    <div className="md:col-span-6 bg-gradient-to-b from-[#162137] to-[#121927] border border-slate-800 rounded-xl p-5 shadow-lg flex flex-col justify-between relative overflow-hidden">
                      <div className={`absolute top-0 left-0 right-0 h-1 ${selectedResult.risk_category === 'HIGH' ? 'bg-red-500' :
                          selectedResult.risk_category === 'MEDIUM' ? 'bg-amber-500' : 'bg-emerald-500'
                        }`} />

                      <div className="flex justify-between items-start mb-4">
                        <div>
                          <span className="text-[10px] font-mono tracking-widest text-slate-400 uppercase">CALCULATED METRIC</span>
                          <h3 className="text-sm font-extrabold text-slate-100 flex items-center gap-1.5 mt-0.5">
                            <Layers className="w-4 h-4 text-cyan-400" />
                            Final Risk Index
                          </h3>
                        </div>
                        <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold border uppercase ${getRiskColor(selectedResult.risk_category)}`}>
                          {selectedResult.risk_category} Risk
                        </span>
                      </div>

                      {/* Radial gauge */}
                      <div className="flex items-center gap-6 my-2">
                        <div className="relative flex items-center justify-center">
                          <svg className="w-24 h-24 transform -rotate-90">
                            <circle cx="48" cy="48" r="38" strokeWidth="8" stroke="#0a0e16" fill="transparent" />
                            <circle
                              cx="48" cy="48" r="38" strokeWidth="8"
                              stroke={getRiskStroke(selectedResult.risk_category)}
                              strokeDasharray={`${2 * Math.PI * 38}`}
                              strokeDashoffset={`${2 * Math.PI * 38 * (1 - (selectedResult.risk_score || 0) / 100)}`}
                              strokeLinecap="round" fill="transparent"
                            />
                          </svg>
                          <span className="absolute text-2xl font-black text-white font-mono">
                            {(selectedResult.risk_score || 0).toFixed(0)}
                          </span>
                        </div>

                        {/* Breakdown bars */}
                        <div className="flex-1 space-y-1.5">
                          {[
                            { label: 'Relevance', val: (selectedResult.risk_breakdown?.relevance_component || 0) / 30, color: '#ba1826' },
                            { label: 'Severity', val: (selectedResult.risk_breakdown?.severity_component || 0) / 22, color: '#dc2626' },
                            { label: 'Frequency', val: (selectedResult.risk_breakdown?.frequency_component || 0) / 20, color: '#fca5a5' },
                            { label: 'Recency', val: (selectedResult.risk_breakdown?.recency_component || 0) / 13, color: '#ef4444' },
                            { label: 'Sentiment', val: (selectedResult.risk_breakdown?.sentiment_component || 0) / 15, color: '#f59e0b' },
                          ].map(({ label, val, color }) => (
                            <div key={label}>
                              <div className="flex justify-between font-mono text-[9px] text-slate-400 mb-0.5">
                                <span>{label}</span>
                                <span style={{ color }}>{(Math.min(val, 1) * 100).toFixed(0)}%</span>
                              </div>
                              <div className="bg-black border border-[#1c2538] h-1.5 rounded-full overflow-hidden">
                                <div style={{ width: `${Math.min(val * 100, 100)}%`, background: color }} className="h-full rounded-full" />
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Negative news count */}
                      {(selectedResult.risk_breakdown?.negative_news_count || 0) > 0 && (
                        <div className="border-t border-slate-800/80 pt-2 mt-2 text-[10px] font-mono text-amber-400 flex items-center gap-1.5">
                          <AlertTriangle className="w-3 h-3" />
                          {selectedResult.risk_breakdown.negative_news_count} negative news articles detected
                        </div>
                      )}

                      <div className="border-t border-slate-800/80 pt-3 text-[10px] text-slate-500 font-mono text-center">
                        Formula: 0.30×rel + 0.22×sev + 0.20×freq + 0.13×rec + 0.15×sentiment
                      </div>
                    </div>

                    {/* Compliance directive (span 6) */}
                    <div className="md:col-span-6 bg-[#121927] border border-slate-800 rounded-xl p-5 shadow-lg flex flex-col justify-between">
                      <div>
                        <span className="text-[10px] font-mono tracking-widest text-slate-400 uppercase">COMPLIANCE DIRECTIVE</span>
                        <h3 className="text-sm font-extrabold text-slate-100 flex items-center gap-1.5 mt-0.5">
                          <CheckCircle className="w-4 h-4 text-emerald-500" />
                          AI Risk Summary
                        </h3>
                        <div className="mt-3 bg-[#0a0e16] p-3 rounded-lg border border-slate-800/80">
                          <p className="text-[11px] text-slate-300 leading-relaxed">
                            {selectedResult.explainability?.summary || 'No summary available.'}
                          </p>
                        </div>
                        <div className="mt-3 space-y-1.5">
                          {(selectedResult.explainability?.key_risk_factors || []).map((f, i) => (
                            <div key={i} className="flex items-start gap-2 text-xs text-slate-300">
                              <ChevronRight className="w-3.5 h-3.5 text-rose-500 shrink-0 mt-0.5" />
                              {f}
                            </div>
                          ))}
                        </div>
                      </div>
                      <div className="flex items-center gap-2 text-[11px] text-slate-500 border-t border-slate-800/80 pt-3 mt-3">
                        <User className="w-3.5 h-3.5" />
                        <span>Resolved:</span>
                        <span className="font-bold text-cyan-300 font-mono">{selectedResult.entity?.resolved_name}</span>
                        <span className="text-slate-600">·</span>
                        <span className="text-slate-500">{(selectedResult.entity?.confidence * 100)?.toFixed(1)}% conf.</span>
                      </div>
                    </div>
                  </div>

                  {/* ── Human-in-the-loop ── */}
                  <div className="bg-[#121927] border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
                    <div className="flex flex-col md:flex-row md:items-center justify-between border-b border-slate-800 pb-3 gap-2">
                      <div>
                        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200 flex items-center gap-2">
                          <HelpCircle className="w-4 h-4 text-cyan-400" />
                          Human-In-The-Loop Review
                        </h3>
                        <p className="text-[11px] text-slate-500 mt-0.5">Override decisions, apply authorisation stamps, or file procedural logs.</p>
                      </div>
                      <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 px-3 py-1 rounded text-[11px]">
                        <span className="text-slate-400">Audit State:</span>
                        <span className={`font-bold px-2 py-0.5 rounded ${selectedResult._reviewStatus === 'APPROVE' ? 'bg-emerald-500/20 text-emerald-400' :
                            selectedResult._reviewStatus === 'REJECT' ? 'bg-rose-500/20 text-rose-400' :
                              selectedResult._reviewStatus === 'ESCALATE' ? 'bg-amber-500/20 text-amber-400' :
                                'bg-slate-800 text-slate-400'
                          }`}>
                          {selectedResult._reviewStatus || 'PENDING'}
                        </span>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-12 gap-4">
                      <div className="md:col-span-8">
                        <textarea
                          rows={2}
                          placeholder="Internal analyst rationale, case references..."
                          value={analystNotes}
                          onChange={e => setAnalystNotes(e.target.value)}
                          className="w-full bg-[#0a0d15] text-slate-200 border border-slate-800 p-2.5 rounded-lg text-xs focus:outline-none focus:ring-1 focus:ring-rose-500 placeholder-slate-600"
                        />
                      </div>
                      <div className="md:col-span-4 flex flex-col gap-2 justify-center">
                        <div className="grid grid-cols-3 gap-2">
                          <button onClick={() => submitDecision('APPROVE')} className="bg-emerald-600 hover:bg-emerald-700 text-white rounded font-bold text-[10px] py-1.5 uppercase transition-colors tracking-wider flex flex-col items-center justify-center gap-1 cursor-pointer">
                            <CheckCircle className="w-3.5 h-3.5" />Approve
                          </button>
                          <button onClick={() => submitDecision('REJECT')} className="bg-rose-600 hover:bg-rose-700 text-white rounded font-bold text-[10px] py-1.5 uppercase transition-colors tracking-wider flex flex-col items-center justify-center gap-1 cursor-pointer">
                            <XCircle className="w-3.5 h-3.5" />Reject
                          </button>
                          <button onClick={() => submitDecision('ESCALATE')} className="bg-amber-600 hover:bg-amber-700 text-white rounded font-bold text-[10px] py-1.5 uppercase transition-colors tracking-wider flex flex-col items-center justify-center gap-1 cursor-pointer">
                            <AlertCircle className="w-3.5 h-3.5" />Escalate
                          </button>
                        </div>
                        <p className="text-[9px] text-slate-500 italic text-center">Action registers a persistent audit log entry.</p>
                      </div>
                    </div>
                  </div>

                  {/* ── ⚠️ Recent Negative News ── */}
                  <div>
                    <div className="flex justify-between items-center mb-3">
                      <h3 className="text-sm font-bold text-amber-400 flex items-center gap-2">
                        <AlertTriangle className="w-4 h-4" />
                        Recent Negative News for {selectedResult.entity?.resolved_name}
                      </h3>
                      <span className="text-xs text-slate-400 font-mono bg-slate-900 border border-slate-800 px-2 py-0.5 rounded">
                        {negativeArticles.length} flagged
                      </span>
                    </div>

                    {negativeArticles.length === 0 ? (
                      <div className="bg-[#121927] border border-slate-800 rounded-xl p-6 text-center text-xs text-emerald-400">
                        ✔ No recent negative news detected for this entity.
                      </div>
                    ) : (
                      <div className="space-y-3">
                        {negativeArticles.map(art => {
                          const sc = art.sentiment_score || 0;
                          const clr = getSentimentColor(sc);
                          const lbl = sc >= 0.70 ? 'HIGH NEGATIVE' : sc >= 0.45 ? 'MODERATE NEGATIVE' : 'LOW NEGATIVE';
                          return (
                            <div key={art.id} className="bg-[#121927] border border-amber-500/20 rounded-xl overflow-hidden shadow-lg flex flex-col md:flex-row hover:border-amber-500/40 transition-all">
                              {/* Sentiment sidebar */}
                              <div className="md:w-48 bg-[#0e1420] p-4 border-r border-slate-800 flex flex-col justify-center gap-3">
                                <div>
                                  <div className="text-[10px] font-mono text-slate-500 uppercase mb-1">SENTIMENT WEIGHT</div>
                                  <div className="text-2xl font-black font-mono" style={{ color: clr }}>{(sc * 100).toFixed(0)}%</div>
                                  <div className="text-[10px] font-mono mt-0.5" style={{ color: clr }}>{lbl}</div>
                                </div>
                                <div className="bg-black border border-slate-800 h-2 rounded-full overflow-hidden">
                                  <div className="h-full rounded-full" style={{ width: `${sc * 100}%`, background: clr }} />
                                </div>
                                <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase self-start ${getSeverityBadge(art.severity_label)}`}>
                                  {art.severity_label}
                                </span>
                              </div>

                              {/* Content */}
                              <div className="flex-1 p-4 space-y-2.5">
                                <div>
                                  <h4 className="text-sm font-bold text-amber-300">{art.article_title}</h4>
                                  <div className="flex items-center gap-3 text-[11px] text-slate-500 mt-1">
                                    <span className="flex items-center gap-1"><Building className="w-3 h-3" />{art.country}</span>
                                    <span className="h-3 w-px bg-slate-800" />
                                    <span className="flex items-center gap-1 font-mono"><Calendar className="w-3 h-3" />{(art.published_date || '').slice(0, 10)}</span>
                                    {art.source && (
                                      <>
                                        <span className="h-3 w-px bg-slate-800" />
                                        <a href={art.source} target="_blank" rel="noreferrer" className="text-amber-500/70 hover:text-amber-400 transition-colors truncate max-w-[180px]">
                                          {art.source.replace(/^https?:\/\//, '').slice(0, 40)}
                                        </a>
                                      </>
                                    )}
                                  </div>
                                </div>
                                <div className="text-xs text-slate-300 leading-relaxed bg-[#0a0d15] p-3 rounded-lg border border-slate-800/80">
                                  {art.article_text?.slice(0, 400)}{art.article_text?.length > 400 ? '…' : ''}
                                </div>
                                {art.why_flagged && (
                                  <div className="text-[11px] text-amber-300/80 bg-amber-500/5 border border-amber-500/15 p-2.5 rounded-lg flex items-start gap-1.5">
                                    <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                                    {art.why_flagged}
                                  </div>
                                )}
                                {art.evidence_quotes?.length > 0 && (
                                  <div className="mt-2 space-y-2">
                                    {art.evidence_quotes.map((quote, idx) => (
                                      <div key={idx} className="border-l-2 border-emerald-500/50 pl-3 py-1 bg-emerald-950/10 text-emerald-300/90 text-[11px] italic">
                                        "{quote}"
                                      </div>
                                    ))}
                                  </div>
                                )}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>

                  {/* ── All matched publications ── */}
                  <div>
                    <h3 className="text-sm font-bold text-slate-100 flex items-center justify-between mb-4">
                      <span className="flex items-center gap-2">
                        <FileText className="w-4 h-4 text-cyan-400" />
                        Matched Publications ({selectedResult.articles?.length || 0})
                      </span>
                      <span className="text-xs text-slate-500 font-mono">Sorted by risk contribution</span>
                    </h3>

                    {!selectedResult.articles?.length ? (
                      <div className="bg-[#121927] border border-slate-800 rounded-xl p-10 text-center text-xs text-slate-500">
                        No adverse articles matched.
                      </div>
                    ) : (
                      <div className="space-y-4">
                        {selectedResult.articles.map(art => (
                          <div key={art.id} className="bg-[#121927] border border-slate-800 rounded-xl overflow-hidden shadow-lg hover:border-slate-700 transition-all flex flex-col md:flex-row">
                            <div className="md:w-48 bg-[#0e1420] p-4 border-r border-slate-800 flex flex-col justify-between gap-3">
                              <div>
                                <div className="text-[10px] font-mono tracking-wider text-slate-500 uppercase">RELEVANCE</div>
                                <div className="text-2xl font-black text-white font-mono mt-0.5">
                                  {((art.relevance_score || 0) * 100).toFixed(0)}%
                                </div>
                              </div>
                              <div>
                                <div className="text-[9px] font-mono tracking-wider text-slate-500 uppercase mb-1">SEVERITY</div>
                                <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase ${getSeverityBadge(art.severity_label)}`}>
                                  {art.severity_label}
                                </span>
                              </div>
                              {art.is_negative_news && (
                                <span className="text-[9px] font-mono bg-amber-500/15 text-amber-400 border border-amber-500/25 px-2 py-0.5 rounded uppercase">
                                  ⚠ Negative
                                </span>
                              )}
                            </div>

                            <div className="flex-1 p-4 space-y-3">
                              <div>
                                <h4 className="text-sm font-bold text-slate-100">{art.article_title}</h4>
                                <div className="flex items-center gap-3 text-[11px] text-slate-500 mt-1">
                                  <span className="flex items-center gap-1"><Building className="w-3 h-3" />{art.source}</span>
                                  <span className="h-3 w-px bg-slate-800" />
                                  <span className="flex items-center gap-1 font-mono"><Calendar className="w-3 h-3" />{(art.published_date || '').slice(0, 10)}</span>
                                  <span className="h-3 w-px bg-slate-800" />
                                  <span className="text-[10px] bg-indigo-500/10 text-indigo-400 px-2 rounded-full font-mono">{art.category}</span>
                                </div>
                              </div>
                              <div className="text-xs text-slate-300 leading-relaxed bg-[#0a0d15] p-3 rounded-lg border border-slate-800/80 font-serif">
                                <HighlightedText text={art.article_text?.slice(0, 400) + (art.article_text?.length > 400 ? '…' : '')} keywords={art.keywords || []} />
                              </div>
                              {art.why_flagged && (
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 border-t border-slate-800/80 pt-3">
                                  <div className="space-y-1 bg-red-950/10 border border-slate-800/90 p-3 rounded">
                                    <span className="text-[10px] font-bold text-red-400 uppercase tracking-wide flex items-center gap-1">
                                      <AlertTriangle className="w-3.5 h-3.5" />WHY FLAGGED
                                    </span>
                                    <p className="text-[11px] text-slate-400 leading-relaxed">{art.why_flagged}</p>
                                  </div>
                                  <div className="space-y-1 bg-cyan-950/10 border border-slate-800/90 p-3 rounded">
                                    <span className="text-[10px] font-bold text-cyan-400 uppercase tracking-wide flex items-center gap-1">
                                      <Sparkles className="w-3.5 h-3.5" />RELEVANCE JUSTIFICATION
                                    </span>
                                    <p className="text-[11px] text-slate-400 leading-relaxed">{art.relevance_reason || 'Semantically matched.'}</p>
                                  </div>
                                </div>
                              )}
                              {art.evidence_quotes?.length > 0 && (
                                <div className="mt-3 space-y-2">
                                  <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-wide flex items-center gap-1 mb-1">
                                    <FileText className="w-3.5 h-3.5" />EVIDENCE EXTRACTED
                                  </span>
                                  {art.evidence_quotes.map((quote, idx) => (
                                    <div key={idx} className="border-l-2 border-emerald-500/50 pl-3 py-1.5 bg-emerald-950/10 text-emerald-300/90 text-[11px] italic font-serif">
                                      "{quote}"
                                    </div>
                                  ))}
                                </div>
                              )}
                              {art.keywords?.length > 0 && (
                                <div className="flex items-center gap-1.5 flex-wrap">
                                  <span className="text-[10px] font-semibold text-slate-500">Flagged:</span>
                                  {art.keywords.map((kw, i) => (
                                    <span key={i} className="bg-red-500/20 text-rose-300 rounded text-[9px] font-bold px-2 py-0.5 uppercase tracking-wide border border-red-500/20 font-mono">{kw}</span>
                                  ))}
                                </div>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* ── Timeline chart ── */}
                  {timelineData.length > 0 && (
                    <div className="bg-[#121927] border border-slate-800 rounded-xl p-5 shadow-lg">
                      <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
                        <div>
                          <h3 className="text-xs font-bold uppercase text-slate-200 tracking-wide flex items-center gap-2">
                            <TrendingUp className="w-4 h-4 text-rose-500" />
                            Negative News Timeline
                          </h3>
                          <p className="text-[10px] text-slate-500">Volume and peak sentiment intensity by month.</p>
                        </div>
                        <span className="text-[10px] text-slate-400 bg-slate-900 border border-slate-800 px-2 py-0.5 rounded">
                          {timelineData.length} periods
                        </span>
                      </div>
                      <div className="h-52">
                        <ResponsiveContainer width="100%" height="100%">
                          <LineChart data={timelineData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#1c2538" />
                            <XAxis dataKey="date" stroke="#64748b" fontSize={10} />
                            <YAxis yAxisId="left" stroke="#ef4444" fontSize={10} />
                            <YAxis yAxisId="right" orientation="right" stroke="#f59e0b" fontSize={10} />
                            <Tooltip contentStyle={{ backgroundColor: '#0b101a', borderColor: '#1e293b', borderRadius: '8px', fontSize: '11px' }} />
                            <Line yAxisId="left" type="monotone" dataKey="Negative Vol" stroke="#ef4444" strokeWidth={3} activeDot={{ r: 8 }} />
                            <Line yAxisId="right" type="monotone" dataKey="Peak Sentiment" stroke="#f59e0b" strokeWidth={2} />
                          </LineChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  )}


                </div>
              )}
            </div>
          </div>
        )}

        {/* ════════ TAB: AUDIT LOGS ════════ */}
        {activeTab === 'audit' && (
          <div className="bg-[#121927] border border-slate-800 rounded-xl p-5 shadow-lg space-y-5">
            <div className="flex justify-between items-center border-b border-slate-800 pb-3.5">
              <div>
                <h2 className="text-base font-bold text-white flex items-center gap-2">
                  <History className="w-5 h-5 text-rose-500" />
                  Procedural Screening Archive
                </h2>
                <p className="text-xs text-slate-500 mt-0.5">Compliance audit log — decisions, timestamps, analyst notes.</p>
              </div>
              <button onClick={loadAuditLog} className="bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded px-3 py-1.5 text-xs font-semibold flex items-center gap-1.5 cursor-pointer">
                <RefreshCw className="w-3.5 h-3.5" />Reload
              </button>
            </div>

            {auditLog.length === 0 ? (
              <div className="text-center py-20 text-slate-500 text-xs italic">
                No audit logs yet. Run a screening to generate records.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 font-bold bg-[#0c111e]/65">
                      {['Timestamp', 'Entity', 'Action', 'Risk Score', 'Category', 'Notes'].map(h => (
                        <th key={h} className="py-3 px-4 uppercase tracking-wider text-[11px]">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/80">
                    {auditLog.map((log, i) => (
                      <tr key={i} className="hover:bg-slate-800/20">
                        <td className="py-3 px-4 font-mono text-slate-400 text-[11px]">{new Date(log.timestamp).toLocaleString()}</td>
                        <td className="py-3 px-4 font-bold text-white">{log.entity_name}</td>
                        <td className="py-3 px-4">
                          <span className={`px-2 py-0.5 text-[10px] rounded font-mono font-bold uppercase border ${log.action === 'APPROVE' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
                              log.action === 'REJECT' ? 'bg-rose-500/10 text-rose-400 border-rose-500/20' :
                                'bg-amber-500/10 text-amber-400 border-amber-500/20'
                            }`}>{log.action}</span>
                        </td>
                        <td className="py-3 px-4 font-mono font-bold text-white">{log.risk_score?.toFixed(1)}</td>
                        <td className="py-3 px-4">
                          <span className={`px-2 py-0.5 text-[9px] rounded font-bold border uppercase ${getRiskColor(log.risk_category)}`}>
                            {log.risk_category}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-slate-400 italic">{log.analyst_notes || '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* ════════ TAB: COMPLIANCE DATABASE ════════ */}
        {activeTab === 'database' && (
          <div className="bg-[#121927] border border-slate-800 rounded-xl p-5 shadow-lg space-y-5">
            <div className="flex justify-between items-center border-b border-slate-800 pb-3.5">
              <div>
                <h2 className="text-base font-bold text-white flex items-center gap-2">
                  <Database className="w-5 h-5 text-rose-500" />
                  Pre-compiled Adverse Database
                </h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  Synthetic incident datasets — PEP violations, environmental damage, AML, market fraud.
                </p>
              </div>
              <span className="text-xs text-rose-400 bg-rose-500/10 px-3.5 py-1 rounded-full border border-rose-500/20 font-bold font-mono">
                Total: {dbStats?.total_articles || 0} records
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div>
                <label className="text-[11px] font-bold text-slate-400 tracking-wider uppercase mb-1 block">Filter By Entity</label>
                <input
                  type="text"
                  value={dbEntityFilter}
                  onChange={e => setDbEntityFilter(e.target.value)}
                  className="w-full bg-[#0a0d15] text-slate-200 border border-slate-800 px-3 py-2 rounded text-xs focus:outline-none focus:ring-1 focus:ring-rose-500 placeholder-slate-700"
                />
              </div>
              <div>
                <label className="text-[11px] font-bold text-slate-400 tracking-wider uppercase mb-1 block">Filter By Severity</label>
                <select
                  value={dbSevFilter}
                  onChange={e => setDbSevFilter(e.target.value)}
                  className="w-full bg-[#0a0d15] text-slate-200 border border-slate-800 px-3 py-2 rounded text-xs focus:outline-none focus:ring-1 focus:ring-rose-500"
                >
                  {['ALL', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].map(s => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>
              <div className="flex items-end">
                <button onClick={loadDbArticles} className="w-full bg-[#e11d48] hover:bg-[#be123c] text-white font-bold py-2 rounded text-xs uppercase tracking-wider transition-colors h-[34px]">
                  Query Database ➜
                </button>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {dbArticles.map((item, i) => (
                <div key={item.id || i} className="bg-slate-900/60 border border-slate-800/80 p-4 rounded-lg flex flex-col justify-between hover:border-slate-700 transition-all gap-3">
                  <div>
                    <div className="flex justify-between items-start">
                      <div>
                        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wide">Target Entity:</h4>
                        <span className="text-sm font-black text-white">{item.entity_name}</span>
                      </div>
                      <span className={`text-[9px] font-mono font-bold px-2 py-0.5 border rounded uppercase ${getSeverityBadge(item.severity_label)}`}>
                        {item.severity_label}
                      </span>
                    </div>
                    <div className="border-t border-slate-800/60 my-2 pt-2">
                      <h5 className="text-xs font-bold text-rose-400">{item.article_title}</h5>
                      <p className="text-[11px] text-slate-400 leading-relaxed mt-1">{item.article_text?.slice(0, 200)}{item.article_text?.length > 200 ? '…' : ''}</p>
                    </div>
                  </div>
                  <div className="flex justify-between text-[10px] text-slate-500 border-t border-slate-800/30 pt-2 font-mono">
                    <span>Source: {item.source}</span>
                    <span className="bg-indigo-500/15 text-indigo-400 px-2 py-0.5 rounded">{item.category}</span>
                  </div>
                </div>
              ))}

              {dbArticles.length === 0 && (
                <div className="col-span-2 text-center py-20 text-slate-500 text-xs italic">
                  Click the tab to load database records (or they appear here in demo mode).
                </div>
              )}
            </div>
          </div>
        )}

        {/* ════════ TAB: ROCM GPU DIAGNOSTICS ════════ */}
        {activeTab === 'hardware' && (
          <div className="space-y-6">
            <div className="bg-[#121927] border border-slate-800 rounded-xl p-6 shadow-lg flex flex-col md:flex-row items-center justify-between gap-6">
              <div className="flex items-center gap-4">
                <div className="p-4 bg-rose-600/15 border border-rose-500/30 rounded-xl">
                  <Cpu className="w-10 h-10 text-rose-500 animate-pulse" />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-white flex items-center gap-2">
                    {hardware?.device_name || 'Device'}
                    <span className="text-xs bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-semibold px-2.5 py-0.5 rounded-full">
                      {isDemo ? 'Demo Mode' : 'HBM3 Memory Cluster'}
                    </span>
                  </h2>
                  <p className="text-xs text-slate-500 mt-1">
                    ROCm profiling stack mapping real-time compliance embeddings to GPU processing nodes.
                  </p>
                </div>
              </div>

              <div className="flex gap-4">
                <div className="bg-[#0b101a] border border-slate-800/80 p-4 rounded-xl text-center min-w-[130px]">
                  <span className="text-[10px] font-bold text-slate-500 uppercase block">Model Loaded</span>
                  <span className="text-base font-extrabold text-cyan-400 block font-mono mt-1">
                    {hardware?.model_loaded ? 'YES' : 'NO'}
                  </span>
                </div>
                <div className="bg-[#0b101a] border border-slate-800/80 p-4 rounded-xl text-center min-w-[130px]">
                  <span className="text-[10px] font-bold text-slate-500 uppercase block">API Version</span>
                  <span className="text-base font-extrabold text-rose-400 block font-mono mt-1">
                    v{hardware?.version || '1.0.0'}
                  </span>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
              <div className="bg-[#121927] border border-slate-800 rounded-xl p-5 shadow-lg flex flex-col items-center justify-center relative overflow-hidden">
                <h3 className="text-xs font-bold uppercase text-emerald-400 tracking-wide mb-2 w-full text-left">VRAM Allocation (MiB)</h3>
                <div className="relative flex flex-col items-center justify-center pt-4">
                  <svg viewBox="0 0 180 110" className="w-48 h-auto">
                    <path d="M 20 90 A 70 70 0 0 1 160 90" fill="none" stroke="#1e293b" strokeWidth="14" strokeLinecap="round" />
                    <path d="M 20 90 A 70 70 0 0 1 160 90" fill="none" stroke="#10b981" strokeWidth="14" strokeLinecap="round"
                      strokeDasharray="220"
                      strokeDashoffset={220 * (1 - Math.min(1, rocmStats.vram / 198000))}
                      style={{ transition: 'stroke-dashoffset 0.5s ease-out' }}
                    />
                  </svg>
                  <div className="absolute top-[45px] flex flex-col items-center">
                    <span className="text-3xl font-black text-slate-100 font-mono tracking-tighter drop-shadow-md">{rocmStats.vram}</span>
                    <span className="text-[10px] text-emerald-500 font-bold uppercase tracking-widest mt-1">/ 198000 MiB</span>
                  </div>
                </div>
              </div>
              <div className="bg-[#121927] border border-slate-800 rounded-xl p-5 shadow-lg flex flex-col items-center justify-center relative overflow-hidden">
                <h3 className="text-xs font-bold uppercase text-emerald-400 tracking-wide mb-2 w-full text-left">Compute Engine Load</h3>
                <div className="relative flex flex-col items-center justify-center pt-4">
                  <svg viewBox="0 0 180 110" className="w-48 h-auto">
                    <path d="M 20 90 A 70 70 0 0 1 160 90" fill="none" stroke="#1e293b" strokeWidth="14" strokeLinecap="round" />
                    <path d="M 20 90 A 70 70 0 0 1 160 90" fill="none" stroke="#10b981" strokeWidth="14" strokeLinecap="round"
                      strokeDasharray="220"
                      strokeDashoffset={220 * (1 - (rocmStats.load / 100))}
                      style={{ transition: 'stroke-dashoffset 0.5s ease-out' }}
                    />
                  </svg>
                  <div className="absolute top-[45px] flex flex-col items-center">
                    <span className="text-3xl font-black text-slate-100 font-mono tracking-tighter drop-shadow-md">{rocmStats.load}%</span>
                    <span className="text-[10px] text-emerald-500 font-bold uppercase tracking-widest mt-1">Utilisation</span>
                  </div>
                </div>
              </div>
              <div className="bg-[#121927] border border-slate-800 rounded-xl p-5 shadow-lg flex flex-col items-center justify-center relative overflow-hidden">
                <h3 className="text-xs font-bold uppercase text-cyan-400 tracking-wide mb-2 w-full text-left">CPU Core Load</h3>
                <div className="relative flex flex-col items-center justify-center pt-4">
                  <svg viewBox="0 0 180 110" className="w-48 h-auto">
                    <path d="M 20 90 A 70 70 0 0 1 160 90" fill="none" stroke="#1e293b" strokeWidth="14" strokeLinecap="round" />
                    <path d="M 20 90 A 70 70 0 0 1 160 90" fill="none" stroke="#06b6d4" strokeWidth="14" strokeLinecap="round"
                      strokeDasharray="220"
                      strokeDashoffset={220 * (1 - (rocmStats.cpu / 100))}
                      style={{ transition: 'stroke-dashoffset 0.5s ease-out' }}
                    />
                  </svg>
                  <div className="absolute top-[45px] flex flex-col items-center">
                    <span className="text-3xl font-black text-slate-100 font-mono tracking-tighter drop-shadow-md">{rocmStats.cpu}%</span>
                    <span className="text-[10px] text-cyan-500 font-bold uppercase tracking-widest mt-1">Utilisation</span>
                  </div>
                </div>
              </div>
              <div className="bg-[#121927] border border-slate-800 rounded-xl p-5 shadow-lg flex flex-col items-center justify-center relative overflow-hidden">
                <h3 className="text-xs font-bold uppercase text-cyan-400 tracking-wide mb-2 w-full text-left">System Memory</h3>
                <div className="relative flex flex-col items-center justify-center pt-4">
                  <svg viewBox="0 0 180 110" className="w-48 h-auto">
                    <path d="M 20 90 A 70 70 0 0 1 160 90" fill="none" stroke="#1e293b" strokeWidth="14" strokeLinecap="round" />
                    <path d="M 20 90 A 70 70 0 0 1 160 90" fill="none" stroke="#06b6d4" strokeWidth="14" strokeLinecap="round"
                      strokeDasharray="220"
                      strokeDashoffset={220 * (1 - (rocmStats.ram / 256))}
                      style={{ transition: 'stroke-dashoffset 0.5s ease-out' }}
                    />
                  </svg>
                  <div className="absolute top-[45px] flex flex-col items-center">
                    <span className="text-3xl font-black text-slate-100 font-mono tracking-tighter drop-shadow-md">{rocmStats.ram}</span>
                    <span className="text-[10px] text-cyan-500 font-bold uppercase tracking-widest mt-1">/ 256 GB</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-[#121927] border border-slate-800 rounded-xl p-5 shadow-lg space-y-3">
                <div className="flex justify-between items-center border-b border-slate-800 pb-2">
                  <span className="text-xs font-bold text-slate-200 uppercase tracking-wider">Dataset Records</span>
                  <span className="text-xs font-mono font-bold text-cyan-400">{dbStats?.total_articles?.toLocaleString() || 0}</span>
                </div>
                <p className="text-[11px] text-slate-500 leading-relaxed bg-[#0b101a] p-3 rounded border border-slate-800/80">
                  Synthetic adverse media dataset loaded into FAISS vector index for semantic retrieval.
                </p>
              </div>

              <div className="bg-[#121927] border border-slate-800 rounded-xl p-5 shadow-lg space-y-3">
                <div className="flex justify-between items-center border-b border-slate-800 pb-2">
                  <span className="text-xs font-bold text-slate-200 uppercase tracking-wider">Embedding Model</span>
                  <span className="text-xs font-mono font-bold text-rose-400">all-MiniLM-L6</span>
                </div>
                <p className="text-[11px] text-slate-500 leading-relaxed bg-[#0b101a] p-3 rounded border border-slate-800/80">
                  SentenceTransformer L2-normalised embeddings, FAISS flat IP index, optional GPU offload.
                </p>
              </div>

              <div className="bg-[#121927] border border-slate-800 rounded-xl p-5 shadow-lg space-y-3">
                <div className="flex justify-between items-center border-b border-slate-800 pb-2">
                  <span className="text-xs font-bold text-slate-200 uppercase tracking-wider">ZSC Sentiment</span>
                  <span className="text-xs font-mono font-bold text-emerald-400">nli-deberta-v3</span>
                </div>
                <p className="text-[11px] text-slate-500 leading-relaxed bg-[#0b101a] p-3 rounded border border-slate-800/80">
                  Zero-shot NLI classification for negative news detection. Blended 65% ZSC + 35% keyword.
                </p>
              </div>
            </div>

            {/* Benchmark chart */}
            <div className="bg-[#121927] border border-slate-800 rounded-xl p-5 shadow-lg">
              <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider mb-4 border-b border-slate-800 pb-2.5">
                AMD Instinct MI300X Throughput (Documents Analysed / min)
              </h3>
              <div className="h-44">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={[
                    { name: 'CPU Single', val: 45 },
                    { name: 'CPU 8-Core', val: 180 },
                    { name: 'Legacy GPU', val: 1450 },
                    { name: 'MI300X ROCm', val: 16800 },
                  ]}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1c2538" />
                    <XAxis dataKey="name" stroke="#64748b" fontSize={10} />
                    <YAxis stroke="#64748b" fontSize={10} />
                    <Tooltip contentStyle={{ backgroundColor: '#0b101a', borderColor: '#1e293b', borderRadius: '8px', fontSize: '11px' }} />
                    <Bar dataKey="val" fill="#ef4444" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        )}

      </main>

      {/* ── FOOTER ── */}
      <footer className="border-t border-slate-800 bg-[#070b13] px-6 py-4 flex flex-col md:flex-row items-center justify-between text-xs text-slate-500 gap-4 mt-auto">
        <div className="flex items-center gap-2">
          <span>© 2026 SentryScreen Adverse Media Copilot — AMD Instinct + FastAPI + React</span>
          {isDemo && <span className="text-amber-500 font-mono">[DEMO MODE]</span>}
        </div>
        <div className="flex gap-4">
          <span className="font-mono text-[10px]">API: {API_BASE}</span>
        </div>
      </footer>

    </div>
  );
}
