import React from 'react';
import { Cpu, Server, Database } from 'lucide-react';
import { fetchHealth, fetchDatasetStats } from '../api/client';

export default function DeviceInfo() {
  const [health, setHealth] = React.useState(null);
  const [stats, setStats] = React.useState(null);

  React.useEffect(() => {
    const loadInfo = async () => {
      try {
        const [h, s] = await Promise.all([fetchHealth(), fetchDatasetStats()]);
        setHealth(h);
        setStats(s);
      } catch (err) {
        console.error("Could not load backend info", err);
      }
    };
    loadInfo();
  }, []);

  if (!health || !stats) return null;

  const isGpu = health.device === 'cuda';

  return (
    <div className="flex flex-wrap items-center gap-4 text-xs font-medium text-slate-500">
      <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-800/50 border border-slate-700/50">
        <Server size={14} className="text-slate-400" />
        Backend v{health.version}
      </div>
      <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-800/50 border border-slate-700/50">
        <Database size={14} className="text-indigo-400" />
        {stats.total_articles} Articles / {stats.unique_entities} Entities
      </div>
      <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-800/50 border border-slate-700/50">
        <Cpu size={14} className={isGpu ? 'text-emerald-400' : 'text-slate-400'} />
        {isGpu ? `GPU Detected: ${health.device_name}` : 'CPU Inference'}
      </div>
    </div>
  );
}
