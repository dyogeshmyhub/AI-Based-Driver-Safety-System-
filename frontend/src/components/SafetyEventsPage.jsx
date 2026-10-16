const filters = ['ALL', 'INFO', 'WARNING', 'HIGH', 'CRITICAL'];

function formatDate(value) {
  return value ? new Date(value).toLocaleString([], { dateStyle: 'medium', timeStyle: 'medium' }) : '—';
}

export default function SafetyEventsPage({ events, filter, onFilter, loading, error }) {
  const visibleEvents = filter === 'ALL' ? events : events.filter((event) => {
    const severity = event.severity.toUpperCase();
    return severity === filter || (filter === 'HIGH' && severity === 'DANGER');
  });
  return <section className="page-panel">
    <div className="page-heading"><div><p className="eyebrow">AUDIT / SAFETY EVENTS</p><h2>Safety events</h2><p>Signals written by the live SafetyEngine and persisted to SQLite.</p></div><div className="filter-bar" role="group" aria-label="Filter safety events">{filters.map((value) => <button key={value} className={`filter-button ${filter === value ? 'selected' : ''}`} onClick={() => onFilter(value)}>{value}</button>)}</div></div>
    {error && <div className="notice">{error}</div>}
    {loading ? <p className="muted">Loading event stream...</p> : visibleEvents.length === 0 ? <div className="empty-state"><strong>No matching events</strong><span>Safety signals will appear here while monitoring is active.</span></div> : <div className="event-timeline">{visibleEvents.map((event) => <article className="timeline-item" key={event.id}><span className={`timeline-marker ${event.severity.toLowerCase()}`} /><div className="timeline-copy"><div className="timeline-meta"><time>{formatDate(event.timestamp)}</time><span className={`severity ${event.severity.toLowerCase()}`}>{event.severity}</span></div><h3>{event.event_type.replaceAll('_', ' ')}</h3><p>{event.message}</p><small>Session {event.session_id?.slice(0, 8) || '—'} · score {event.safety_score}</small></div></article>)}</div>}
  </section>;
}
