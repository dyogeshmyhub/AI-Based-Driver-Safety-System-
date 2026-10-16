export default function SafetyScoreCard({ safety }) {
  const score = safety?.score;
  const risk = safety?.risk_level;
  return (
    <section className="card score-card">
      <div className="card-heading"><span className="card-label">SAFETY SCORE</span><span className="live-tag">LIVE</span></div>
      <div className="score-value">{score == null ? 'Loading...' : `${score} / 100`}</div>
      <div className="score-track"><span style={{ width: `${score == null ? 0 : score}%` }} /></div>
      <span className={`risk-badge ${risk?.toLowerCase() || 'loading'}`}>{risk || 'Loading...'}</span>
    </section>
  );
}
