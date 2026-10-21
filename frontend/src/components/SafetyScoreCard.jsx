export default function SafetyScoreCard({ safety, monitoring = false, backendOnline = true }) {
  const score = safety?.score;
  const risk = safety?.risk_level;
  const unavailable = backendOnline ? 'Awaiting data' : 'N/A';
  return (
    <section className="card score-card cockpit-score">
      <div className="card-heading"><span className="card-label">SAFETY SCORE</span><span className={`live-tag ${monitoring ? 'active' : ''}`}>{monitoring ? 'LIVE' : 'STANDBY'}</span></div>
      <div className="score-value">{score == null ? unavailable : `${score} / 100`}</div>
      <div className="score-track" aria-label={score == null ? 'Safety score unavailable' : `Safety score ${score} out of 100`}><span style={{ width: `${score == null ? 0 : Math.min(100, Math.max(0, score))}%` }} /></div>
      <span className={`risk-badge ${risk?.toLowerCase() || 'loading'}`}>{risk || unavailable}</span>
    </section>
  );
}
