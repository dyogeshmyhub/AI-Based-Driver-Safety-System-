import { formatDuration } from '../utils/formatDuration';

export default function SessionCard({ session }) {
  const sessionState = session?.active == null ? 'WAITING' : session.active ? 'ACTIVE' : 'INACTIVE';
  return <section className="card session-card"><div className="section-title"><span className="section-kicker">04</span><h2>Session</h2></div><div className="session-status"><span className={`status-dot ${session?.active ? 'on' : ''}`} /> {sessionState}</div><div className="session-time">{formatDuration(session?.duration_seconds)}</div><div className="session-stats"><div><span>Average score</span><strong>{session?.average_score == null ? 'Loading...' : Math.round(session.average_score)}</strong></div><div><span>Minimum score</span><strong>{session?.minimum_score == null ? 'Loading...' : Math.round(session.minimum_score)}</strong></div><div><span>Alerts</span><strong>{session?.alerts ?? 'Loading...'}</strong></div><div><span>Drowsiness events</span><strong>{session?.drowsiness_events ?? 'Loading...'}</strong></div><div><span>Yawns</span><strong>{session?.yawns ?? 'Loading...'}</strong></div></div></section>;
}
