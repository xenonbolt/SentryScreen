import React from 'react';
import { Check, X, AlertTriangle, Loader2 } from 'lucide-react';
import { submitAudit } from '../api/client';

export default function HumanReview({ screeningId, entityName, riskScore, riskCategory, onActionComplete }) {
  const [notes, setNotes] = React.useState('');
  const [isSubmitting, setIsSubmitting] = React.useState(false);

  const handleAction = async (action) => {
    if (!screeningId) return;
    setIsSubmitting(true);
    try {
      await submitAudit({
        screening_id: screeningId,
        entity_name: entityName,
        action,
        analyst_notes: notes,
        risk_score: riskScore,
        risk_category: riskCategory
      });
      setNotes('');
      if (onActionComplete) onActionComplete(action);
    } catch (err) {
      console.error("Failed to submit audit log:", err);
      alert("Failed to submit decision. Please check backend connection.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="card p-6">
      <h2 className="text-lg font-semibold text-slate-200 mb-2">Human-in-the-Loop Review</h2>
      <p className="text-sm text-slate-400 mb-4">Record your final decision for the audit log.</p>
      
      <textarea
        className="input mb-4 h-24 resize-none"
        placeholder="Add analyst notes or rationale here..."
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
        disabled={isSubmitting}
      />
      
      <div className="flex flex-wrap gap-3">
        <button
          className="btn-approve flex-1"
          onClick={() => handleAction('APPROVE')}
          disabled={isSubmitting}
        >
          {isSubmitting ? <Loader2 className="animate-spin" size={16} /> : <Check size={16} />}
          Clear / False Positive
        </button>
        <button
          className="btn-escalate flex-1"
          onClick={() => handleAction('ESCALATE')}
          disabled={isSubmitting}
        >
          {isSubmitting ? <Loader2 className="animate-spin" size={16} /> : <AlertTriangle size={16} />}
          Escalate to EDD
        </button>
        <button
          className="btn-reject flex-1"
          onClick={() => handleAction('REJECT')}
          disabled={isSubmitting}
        >
          {isSubmitting ? <Loader2 className="animate-spin" size={16} /> : <X size={16} />}
          Reject / Block
        </button>
      </div>
    </div>
  );
}
