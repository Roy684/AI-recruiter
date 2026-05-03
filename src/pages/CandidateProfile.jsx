import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend,
} from 'recharts';
import {
  ArrowLeft, UserCircle, Mail, Cpu, Star, CheckCircle, XCircle,
} from 'lucide-react';

const COLORS = ['#4f46e5', '#0ea5e9', '#10b981'];

const RADIAN = Math.PI / 180;
const renderCustomLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }) => {
  if (percent < 0.05) return null;
  const radius = innerRadius + (outerRadius - innerRadius) * 0.55;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);
  return (
    <text x={x} y={y} fill="white" textAnchor="middle" dominantBaseline="central"
      fontSize={12} fontWeight="bold">
      {`${(percent * 100).toFixed(0)}%`}
    </text>
  );
};

function ScoreRing({ value, label, color }) {
  const r = 36;
  const circ = 2 * Math.PI * r;
  const offset = circ - (value / 100) * circ;
  return (
    <div style={{ textAlign: 'center' }}>
      <svg width="90" height="90" viewBox="0 0 90 90">
        <circle cx="45" cy="45" r={r} fill="none" stroke="#1e293b" strokeWidth="8" />
        <circle
          cx="45" cy="45" r={r} fill="none"
          stroke={color} strokeWidth="8"
          strokeDasharray={circ} strokeDashoffset={offset}
          strokeLinecap="round"
          transform="rotate(-90 45 45)"
          style={{ transition: 'stroke-dashoffset 1s ease' }}
        />
        <text x="45" y="49" textAnchor="middle" fill="white" fontSize="14" fontWeight="bold">
          {value}%
        </text>
      </svg>
      <p style={{ color: '#94a3b8', fontSize: '12px', marginTop: '4px' }}>{label}</p>
    </div>
  );
}

export default function CandidateProfile() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [candidate, setCandidate] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch(`https://ai-recruiter-ne55.onrender.com/api/candidates/${id}`)
      .then(res => res.json())
      .then(data => {
        if (data.success && data.data) {
          setCandidate(data.data);
        } else {
          setError('Candidate not found.');
        }
      })
      .catch(() => setError('Failed to load candidate data.'))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '60vh' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{
            width: '48px', height: '48px', border: '4px solid #334155',
            borderTopColor: '#4f46e5', borderRadius: '50%',
            animation: 'spin 0.8s linear infinite', margin: '0 auto 16px',
          }} />
          <p style={{ color: '#94a3b8' }}>Loading profile...</p>
        </div>
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  if (error || !candidate) {
    return (
      <div style={{ textAlign: 'center', padding: '80px 20px' }}>
        <XCircle style={{ width: 48, height: 48, color: '#ef4444', margin: '0 auto 16px' }} />
        <p style={{ color: '#f8fafc', fontSize: '18px' }}>{error || 'Candidate not found.'}</p>
        <button onClick={() => navigate('/dashboard')} style={backBtnStyle}>
          ← Back to Dashboard
        </button>
      </div>
    );
  }

  const tfidf    = Math.round((candidate.tfidf_sim   ?? 0) * 100);
  const sbert    = Math.round((candidate.sbert_sim    ?? 0) * 100);
  const skillPct = Math.round((candidate.skill_match  ?? 0) * 100);
  const overall  = candidate.score ?? 0;

  const pieData = [
    { name: 'TF-IDF Similarity', value: tfidf    || 1 },
    { name: 'Semantic Match',     value: sbert    || 1 },
    { name: 'Skill Overlap',      value: skillPct || 1 },
  ];

  const fitLabel =
    overall >= 90 ? 'Excellent' :
    overall >= 80 ? 'Strong' :
    overall >= 70 ? 'Good' :
    overall >= 60 ? 'Fair' : 'Weak';

  const fitColor =
    overall >= 90 ? '#10b981' :
    overall >= 80 ? '#0ea5e9' :
    overall >= 70 ? '#f59e0b' : '#ef4444';

  const matchedSkills  = candidate.matched_skills  ?? [];
  const allSkills      = candidate.skills          ?? [];
  const unmatchedSkills = allSkills.filter(s => !matchedSkills.map(m => m.toLowerCase()).includes(s.toLowerCase()));

  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto', padding: '40px 24px' }}>
      {/* Back button */}
      <button onClick={() => navigate('/dashboard')} style={backBtnStyle}>
        <ArrowLeft style={{ width: 16, height: 16 }} />
        Back to Dashboard
      </button>

      {/* Header card */}
      <div style={cardStyle}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '24px', flexWrap: 'wrap' }}>
          <div style={{
            width: '80px', height: '80px', borderRadius: '50%',
            background: 'linear-gradient(135deg, #4f46e5, #0ea5e9)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
          }}>
            <UserCircle style={{ width: 48, height: 48, color: 'white' }} />
          </div>
          <div style={{ flex: 1 }}>
            <h1 style={{ fontSize: '28px', fontWeight: 800, color: '#f8fafc', margin: 0 }}>
              {candidate.name || 'Unknown Candidate'}
            </h1>
            {candidate.email && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '6px', color: '#94a3b8' }}>
                <Mail style={{ width: 14, height: 14 }} />
                <span style={{ fontSize: '14px' }}>{candidate.email}</span>
              </div>
            )}
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{
              fontSize: '40px', fontWeight: 900,
              background: 'linear-gradient(135deg, #4f46e5, #0ea5e9)',
              WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
            }}>{overall}%</div>
            <span style={{
              padding: '4px 12px', borderRadius: '999px', fontSize: '12px', fontWeight: 700,
              background: fitColor + '22', color: fitColor,
            }}>{fitLabel} Match</span>
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px', marginTop: '20px' }}>
        {/* Pie chart card */}
        <div style={{ ...cardStyle, gridColumn: 'span 1' }}>
          <h2 style={sectionTitle}>Score Breakdown</h2>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%" cy="50%"
                outerRadius={80}
                dataKey="value"
                labelLine={false}
                label={renderCustomLabel}
              >
                {pieData.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px', color: '#f8fafc' }}
                formatter={(value) => [`${value}%`, '']}
              />
              <Legend
                wrapperStyle={{ color: '#94a3b8', fontSize: '12px', paddingTop: '8px' }}
              />
            </PieChart>
          </ResponsiveContainer>

          {/* Mini ring scores */}
          <div style={{ display: 'flex', justifyContent: 'space-around', marginTop: '16px' }}>
            <ScoreRing value={tfidf}    label="TF-IDF"    color="#4f46e5" />
            <ScoreRing value={sbert}    label="Semantic"  color="#0ea5e9" />
            <ScoreRing value={skillPct} label="Skills"    color="#10b981" />
          </div>
        </div>

        {/* Skills card */}
        <div style={cardStyle}>
          <h2 style={sectionTitle}>
            <Cpu style={{ width: 16, height: 16, display: 'inline', marginRight: '6px' }} />
            Skills
          </h2>

          {matchedSkills.length > 0 && (
            <>
              <p style={{ color: '#10b981', fontSize: '12px', fontWeight: 700, marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                <CheckCircle style={{ width: 12, height: 12, display: 'inline', marginRight: '4px' }} />
                Matched Skills
              </p>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '16px' }}>
                {matchedSkills.map(skill => (
                  <span key={skill} style={skillTag('#10b981')}>{skill}</span>
                ))}
              </div>
            </>
          )}

          {unmatchedSkills.length > 0 && (
            <>
              <p style={{ color: '#94a3b8', fontSize: '12px', fontWeight: 700, marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Other Skills
              </p>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                {unmatchedSkills.map(skill => (
                  <span key={skill} style={skillTag('#4f46e5')}>{skill}</span>
                ))}
              </div>
            </>
          )}

          {allSkills.length === 0 && (
            <p style={{ color: '#94a3b8', fontSize: '14px' }}>No skills extracted.</p>
          )}

          {/* Overall bar */}
          <div style={{ marginTop: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
              <span style={{ color: '#94a3b8', fontSize: '13px' }}>Overall Match</span>
              <span style={{ color: '#f8fafc', fontWeight: 700 }}>{overall}%</span>
            </div>
            <div style={{ height: '8px', background: '#0f172a', borderRadius: '9999px', overflow: 'hidden' }}>
              <div style={{
                height: '100%', borderRadius: '9999px',
                background: 'linear-gradient(90deg, #4f46e5, #0ea5e9)',
                width: `${overall}%`, transition: 'width 1s ease',
              }} />
            </div>
          </div>

          {candidate.status && (
            <div style={{ marginTop: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ color: '#94a3b8', fontSize: '13px' }}>Status:</span>
              <span style={{
                padding: '2px 10px', borderRadius: '999px', fontSize: '12px', fontWeight: 700,
                background: candidate.status === 'reviewed' ? '#10b98122' : '#f59e0b22',
                color: candidate.status === 'reviewed' ? '#10b981' : '#f59e0b',
              }}>
                {candidate.status}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Uploaded at */}
      {candidate.uploaded_at && (
        <p style={{ color: '#475569', fontSize: '12px', marginTop: '20px', textAlign: 'right' }}>
          Uploaded: {new Date(candidate.uploaded_at).toLocaleString()}
        </p>
      )}
    </div>
  );
}

// ── Inline styles ──────────────────────────────────────────────────────────────

const cardStyle = {
  background: '#1e293b',
  border: '1px solid #334155',
  borderRadius: '16px',
  padding: '24px',
};

const sectionTitle = {
  fontSize: '16px',
  fontWeight: 700,
  color: '#f8fafc',
  marginTop: 0,
  marginBottom: '16px',
  display: 'flex',
  alignItems: 'center',
};

const backBtnStyle = {
  display: 'inline-flex', alignItems: 'center', gap: '6px',
  padding: '8px 16px', marginBottom: '24px',
  background: '#1e293b', border: '1px solid #334155',
  borderRadius: '10px', color: '#94a3b8',
  cursor: 'pointer', fontSize: '14px', fontWeight: 600,
  transition: 'color 0.2s',
};

const skillTag = (color) => ({
  padding: '4px 12px', borderRadius: '999px',
  background: color + '22', color: color,
  fontSize: '12px', fontWeight: 600,
  border: `1px solid ${color}44`,
});
