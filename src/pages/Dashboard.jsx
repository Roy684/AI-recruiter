import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  BarChart3, Star, UserCircle, ExternalLink, Trash2, ChevronDown,
} from 'lucide-react';

// ── helpers ────────────────────────────────────────────────────────────────────
const fitLabel = (score) =>
  score >= 80 ? 'Excellent' :
    score >= 60 ? 'Strong' :
      score >= 40 ? 'Good' :
        score >= 20 ? 'Fair' : 'Weak';

const fitColors = (score) =>
  score >= 80 ? 'bg-green-500/20 text-green-400' :
    score >= 60 ? 'bg-blue-500/20 text-blue-400' :
      score >= 40 ? 'bg-yellow-500/20 text-yellow-400' :
        'bg-red-500/20 text-red-400';

export default function Dashboard() {
  const navigate = useNavigate();

  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [scoring, setScoring] = useState(false);
  const [deleting, setDeleting] = useState(null);   // id being deleted

  // JD dropdown state
  const [jdList, setJdList] = useState([]);
  const [selectedJd, setSelectedJd] = useState(null);  // full JD object
  const [jdOpen, setJdOpen] = useState(false);

  // ── Fetch all JDs ──────────────────────────────────────────────────────────
  useEffect(() => {
    fetch('http://localhost:5000/api/job-descriptions')
      .then(r => r.json())
      .then(data => {
        if (data.success && data.data?.job_descriptions) {
          const list = data.data.job_descriptions;
          setJdList(list);
          if (list.length > 0) setSelectedJd(list[0]); // default: newest
        }
      })
      .catch(console.error);
  }, []);

  // ── Fetch candidates ───────────────────────────────────────────────────────
  const fetchCandidates = useCallback(() => {
    setLoading(true);
    fetch('http://localhost:5000/api/candidates')
      .then(r => r.json())
      .then(data => {
        if (data.success && data.data?.candidates) {
          setCandidates(data.data.candidates);
        }
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { fetchCandidates(); }, [fetchCandidates]);

  // ── Run AI Scoring against selected JD ────────────────────────────────────
  const handleScoreCandidates = async () => {
    if (!selectedJd) return;
    setScoring(true);
    try {
      const res = await fetch('http://localhost:5000/api/score-all', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ jd_id: selectedJd.id }),
      });
      const data = await res.json();
      if (data.success) {
        fetchCandidates();
      } else {
        alert('Error: ' + data.message);
      }
    } catch {
      alert('Failed to trigger scoring.');
    } finally {
      setScoring(false);
    }
  };

  // ── Delete candidate ───────────────────────────────────────────────────────
  const handleDelete = async (id, name) => {
    if (!window.confirm(`Delete "${name}"? This cannot be undone.`)) return;
    setDeleting(id);
    try {
      const res = await fetch(`http://localhost:5000/api/candidates/${id}`, { method: 'DELETE' });
      const data = await res.json();
      if (data.success) {
        setCandidates(prev => prev.filter(c => c.id !== id));
      } else {
        alert('Delete failed: ' + data.message);
      }
    } catch {
      alert('Failed to delete candidate.');
    } finally {
      setDeleting(null);
    }
  };

  // ── Loading / empty states ─────────────────────────────────────────────────
  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '50vh', gap: '16px' }}>
        <div style={{
          width: '48px', height: '48px', border: '4px solid #334155',
          borderTopColor: '#4f46e5', borderRadius: '50%',
          animation: 'spin 0.8s linear infinite',
        }} />
        <p style={{ color: '#94a3b8' }}>Loading candidates…</p>
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  const topCandidate = candidates[0];

  return (
    <div className="max-w-6xl mx-auto p-6 md:p-10 space-y-8">

      {/* ── Header ── */}
      <div className="flex flex-col md:flex-row md:items-start gap-4 md:gap-0 md:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-text-main">Candidate Rankings</h1>
          <p className="text-text-muted mt-1">
            AI-powered match results for:&nbsp;
            <span className="font-semibold text-text-main">
              {selectedJd ? selectedJd.jobTitle : 'No JD selected'}
            </span>
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* JD Dropdown */}
          <div style={{ position: 'relative' }}>
            <button
              onClick={() => setJdOpen(o => !o)}
              style={{
                display: 'flex', alignItems: 'center', gap: '8px',
                padding: '8px 14px', background: '#1e293b',
                border: '1px solid #334155', borderRadius: '12px',
                color: '#f8fafc', fontSize: '14px', fontWeight: 600,
                cursor: 'pointer', minWidth: '200px', justifyContent: 'space-between',
              }}
            >
              <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '160px' }}>
                {selectedJd ? selectedJd.jobTitle : 'Select Job Description'}
              </span>
              <ChevronDown style={{ width: 16, height: 16, color: '#94a3b8', flexShrink: 0, transform: jdOpen ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }} />
            </button>

            {jdOpen && (
              <div style={{
                position: 'absolute', top: 'calc(100% + 6px)', right: 0,
                background: '#1e293b', border: '1px solid #334155',
                borderRadius: '12px', minWidth: '240px', zIndex: 50,
                boxShadow: '0 16px 40px rgba(0,0,0,0.5)',
                overflow: 'hidden',
              }}>
                {jdList.length === 0 ? (
                  <p style={{ padding: '12px 16px', color: '#94a3b8', fontSize: '13px' }}>
                    No job descriptions found.
                  </p>
                ) : (
                  jdList.map(jd => (
                    <button
                      key={jd.id}
                      onClick={() => { setSelectedJd(jd); setJdOpen(false); }}
                      style={{
                        display: 'block', width: '100%', textAlign: 'left',
                        padding: '10px 16px', background: selectedJd?.id === jd.id ? '#4f46e522' : 'transparent',
                        color: selectedJd?.id === jd.id ? '#818cf8' : '#f8fafc',
                        fontSize: '14px', border: 'none', cursor: 'pointer',
                        borderBottom: '1px solid #334155',
                        transition: 'background 0.15s',
                      }}
                      onMouseEnter={e => { if (selectedJd?.id !== jd.id) e.currentTarget.style.background = '#334155'; }}
                      onMouseLeave={e => { if (selectedJd?.id !== jd.id) e.currentTarget.style.background = 'transparent'; }}
                    >
                      <div style={{ fontWeight: 600 }}>{jd.jobTitle}</div>
                      <div style={{ fontSize: '11px', color: '#64748b', marginTop: '2px' }}>
                        {new Date(jd.created_at).toLocaleDateString()}
                      </div>
                    </button>
                  ))
                )}
              </div>
            )}
          </div>

          {/* Score button */}
          <button
            onClick={handleScoreCandidates}
            disabled={scoring || !selectedJd || candidates.length === 0}
            className="px-4 py-2 bg-primary hover:bg-primary-hover text-white rounded-xl font-semibold transition-colors shadow-lg disabled:opacity-50"
          >
            {scoring ? 'Scoring…' : 'Run AI Scoring'}
          </button>

          {/* Count badge */}
          <div className="flex items-center gap-2 px-4 py-2 bg-surface border border-surface-hover rounded-xl">
            <BarChart3 className="w-5 h-5 text-secondary" />
            <span className="font-medium">{candidates.length} Candidates</span>
          </div>
        </div>
      </div>

      {/* ── Empty state ── */}
      {candidates.length === 0 && (
        <div style={{ textAlign: 'center', padding: '60px 20px', color: '#94a3b8' }}>
          <UserCircle style={{ width: 56, height: 56, margin: '0 auto 16px', opacity: 0.4 }} />
          <p style={{ fontSize: '18px' }}>No candidates yet. Upload some resumes!</p>
        </div>
      )}

      {candidates.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

          {/* ── Top Match card ── */}
          <div className="md:col-span-1 bg-gradient-to-br from-primary/20 to-secondary/10 border border-primary/30 rounded-2xl p-6 relative overflow-hidden">
            <div className="absolute top-0 right-0 p-4">
              <Star className="w-8 h-8 text-yellow-400 fill-yellow-400" />
            </div>
            <h2 className="text-sm font-semibold text-primary uppercase tracking-wider mb-4">Top Match</h2>
            <div className="flex items-center gap-4 mb-6">
              <div className="w-16 h-16 bg-surface rounded-full flex items-center justify-center border-2 border-primary">
                <UserCircle className="w-10 h-10 text-primary" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-text-main">{topCandidate.name}</h3>
                <p className="text-2xl font-black text-transparent bg-clip-text bg-gradient-to-r from-primary to-secondary">
                  {topCandidate.score}% Match
                </p>
              </div>
            </div>
            <button
              onClick={() => navigate(`/candidate/${topCandidate.id}`)}
              className="w-full py-3 bg-surface hover:bg-surface-hover text-text-main rounded-xl font-semibold transition-colors border border-surface-hover flex items-center justify-center gap-2"
            >
              View Full Profile
              <ExternalLink className="w-4 h-4" />
            </button>
          </div>

          {/* ── Candidate table ── */}
          <div className="md:col-span-2 bg-surface border border-surface-hover rounded-2xl overflow-hidden shadow-xl">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-surface-hover/50 text-text-muted text-sm uppercase tracking-wider border-b border-surface-hover">
                    <th className="px-6 py-4 font-medium">Candidate</th>
                    <th className="px-6 py-4 font-medium">Match Score</th>
                    <th className="px-6 py-4 font-medium">Fit</th>
                    <th className="px-6 py-4 font-medium text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-surface-hover">
                  {candidates.map((c) => (
                    <tr key={c.id} className="hover:bg-surface-hover/30 transition-colors">
                      {/* Name */}
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <UserCircle className="w-8 h-8 text-text-muted flex-shrink-0" />
                          <span className="font-semibold text-text-main">{c.name}</span>
                        </div>
                      </td>

                      {/* Score bar */}
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <div className="bg-background rounded-full h-2.5 w-24">
                            <div
                              className="bg-gradient-to-r from-primary to-secondary h-2.5 rounded-full"
                              style={{ width: `${c.score}%` }}
                            />
                          </div>
                          <span className="font-bold text-text-main">{c.score}%</span>
                        </div>
                      </td>

                      {/* Fit badge */}
                      <td className="px-6 py-4">
                        <span className={`px-3 py-1 rounded-full text-xs font-bold ${fitColors(c.score)}`}>
                          {c.match || fitLabel(c.score)}
                        </span>
                      </td>

                      {/* Actions */}
                      <td className="px-6 py-4">
                        <div className="flex items-center justify-end gap-3">
                          <button
                            onClick={() => navigate(`/candidate/${c.id}`)}
                            className="text-primary hover:text-primary-hover font-medium text-sm transition-colors flex items-center gap-1"
                          >
                            Review
                            <ExternalLink className="w-3 h-3" />
                          </button>
                          <button
                            onClick={() => handleDelete(c.id, c.name)}
                            disabled={deleting === c.id}
                            style={{
                              background: 'none', border: 'none', cursor: 'pointer',
                              color: '#ef4444', opacity: deleting === c.id ? 0.4 : 0.7,
                              padding: '4px', borderRadius: '6px',
                              transition: 'opacity 0.2s',
                              display: 'flex', alignItems: 'center',
                            }}
                            onMouseEnter={e => { if (deleting !== c.id) e.currentTarget.style.opacity = 1; }}
                            onMouseLeave={e => { if (deleting !== c.id) e.currentTarget.style.opacity = 0.7; }}
                            title="Delete candidate"
                          >
                            <Trash2 style={{ width: 16, height: 16 }} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
