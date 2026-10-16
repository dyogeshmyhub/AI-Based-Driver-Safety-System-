export default function Header({ data, backendOnline, connection, monitoring, onStart, onStop, busy }) {
  const indicators = [
    ['BACKEND', backendOnline],
    ['AI ENGINE', monitoring],
    ['CAMERA', data?.camera?.online],
    ['WEBSOCKET', connection === 'CONNECTED'],
  ];
  return (
    <header className="topbar">
      <div>
        <p className="eyebrow">REAL-TIME CONTROL ROOM</p>
        <h1>Driver Safety AI</h1>
        <p className="subtitle">Real-Time Driver Monitoring System</p>
        <div className="status-indicators" aria-label="System connection status">{indicators.map(([label, online]) => <span key={label} className={online ? 'online' : ''}><i />{label} {online ? 'ONLINE' : 'OFFLINE'}</span>)}</div>
      </div>
      <div className="header-actions">
        <span className={`connection-pill ${connection.toLowerCase()}`}><span className="status-dot" /> {connection}</span>
        {!monitoring ? <button className="button button-primary" onClick={onStart} disabled={busy} aria-busy={busy}>{busy ? 'Starting...' : 'Start monitoring'}</button> : <button className="button button-danger" onClick={onStop} disabled={busy} aria-busy={busy}>{busy ? 'Stopping...' : 'Stop monitoring'}</button>}
      </div>
    </header>
  );
}
