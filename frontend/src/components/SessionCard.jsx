function formatDuration(seconds) {
  if (seconds == null) return 'Loading...';
  const value = Math.max(0, Number(seconds));
  const hours = Math.floor(value / 3600);
  const minutes = Math.floor((value % 3600) / 60);
  const remaining = value % 60;
  return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(remaining).padStart(2, '0')}`;
}

export default function SessionCard({ session }) {
  return <section className="card session-card"><div className="section-title"><span className="section-kicker">04</span><h2>Session</h2></div><div className="session-status"><span className={`status-dot ${session?.active ? 'on' : ''}`} /> {session?.active ? 'ACTIVE' : 'INACTIVE'}</div><div className="session-time">{formatDuration(session?.duration_seconds)}</div><div className="session-stats"><div><span>Average score</span><strong>{session?.average_score == null ? 'Loading...' : Math.round(session.average_score)}</strong></div><div><span>Minimum score</span><strong>{session?.minimum_score == null ? 'Loading...' : Math.round(session.minimum_score)}</strong></div><div><span>Alerts</span><strong>{session?.alerts ?? 'Loading...'}</strong></div><div><span>Drowsiness events</span><strong>{session?.drowsiness_events ?? 'Loading...'}</strong></div><div><span>Yawns</span><strong>{session?.yawns ?? 'Loading...'}</strong></div></div></section>;
}
