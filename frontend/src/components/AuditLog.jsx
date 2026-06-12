import React from 'react';
import { History, Shield, ShieldAlert, ShieldCheck } from 'lucide-react';
import { fetchAuditLog } from '../api/client';

export default function AuditLog({ refreshTrigger }) {
  const [logs, setLogs] = React.useState([]);

  React.useEffect(() => {
    fetchAuditLog(10).then(setLogs).catch(console.error);
  }, [refreshTrigger]);

  if (logs.length === 0) return null;

  return (
    <div className="card p-6">
      <div className="flex items-center gap-2 mb-4">
        <History className="text-indigo-400" size={20} />
        <h2 className="text-lg font-semibold text-slate-200">Recent Decisions</h2>
      </div>
      
      <div className="space-y-3">
        {logs.map((log, i) => {
          const isApprove = log.action === 'APPROVE';
          const isReject = log.action === 'REJECT';
          const isEscalate = log.action === 'ESCALATE';
          
          let Icon = Shield;
          let colorClass = 'text-slate-400';
          
          if (isApprove) { Icon = ShieldCheck; colorClass = 'text-emerald-400'; }
          if (isReject) { Icon = ShieldAlert; colorClass = 'text-red-400'; }
          if (isEscalate) { Icon = ShieldAlert; colorClass = 'text-amber-400'; }

          const d = new Date(log.timestamp);

          return (
            <div key={i} className="card-inner p-3 flex flex-col sm:flex-row gap-3 sm:items-center justify-between text-sm">
              <div className="flex items-center gap-3">
                <div className={`p-1.5 rounded bg-slate-800 ${colorClass}`}>
                  <Icon size={16} />
                </div>
                <div>
                  <div className="font-semibold text-slate-200">{log.entity_name}</div>
                  <div className="text-xs text-slate-500">
                    Risk: {log.risk_score.toFixed(1)} ({log.risk_category})
                  </div>
                </div>
              </div>
              
              <div className="flex flex-col sm:items-end gap-1 text-xs">
                <div className="font-medium text-slate-300">
                  {log.action}
                </div>
                <div className="text-slate-500">
                  {d.toLocaleDateString()} {d.toLocaleTimeString()}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
