function formatDate(value) {
  if (!value) return '—';
  return new Date(value).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' });
}

function formatDuration(seconds) {
  const value = Math.max(0, Math.round(Number(seconds) || 0));
  const hours = Math.floor(value / 3600);
  const minutes = Math.floor((value % 3600) / 60);
  const remaining = value % 60;
  return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(remaining).padStart(2, '0')}`;
}

export default function SessionHistoryPage({ sessions, loading, error, onDelete, onView }) {
  return <section className="page-panel">
    <div className="page-heading"><div><p className="eyebrow">ARCHIVE / SESSIONS</p><h2>Session history</h2><p>Review completed monitoring runs and their measured safety outcomes.</p></div><span className="record-count">{sessions.length} RECORDS</span></div>
    {error && <div className="notice">{error}</div>}
    {loading ? <p className="muted">Loading session archive...</p> : sessions.length === 0 ? <div className="empty-state"><strong>No completed sessions yet</strong><span>Start monitoring to create the first session record.</span></div> : <div className="table-wrap"><table className="data-table"><thead><tr><th>Session ID</th><th>Start</th><th>End</th><th>Duration</th><th>Avg score</th><th>Min score</th><th>Alerts</th><th>Drowsiness</th><th>Yawns</th><th>Actions</th></tr></thead><tbody>{sessions.map((session) => <tr key={session.id}><td><code>{session.id.slice(0, 8)}</code></td><td>{formatDate(session.start_time)}</td><td>{formatDate(session.end_time)}</td><td>{formatDuration(session.duration)}</td><td><strong>{Math.round(session.average_safety_score)}</strong></td><td><strong>{Math.round(session.minimum_safety_score)}</strong></td><td>{session.total_alerts}</td><td>{session.total_drowsiness_events}</td><td>{session.total_yawns}</td><td className="row-actions"><button className="text-button" onClick={() => onView(session)}>View</button><button className="text-button danger-text" onClick={() => onDelete(session)}>Delete</button></td></tr>)}</tbody></table></div>}
  </section>;
}
