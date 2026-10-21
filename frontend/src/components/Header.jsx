export default function Header({ data, backendOnline, connection, monitoring, onStart, onStop, busy, theme, onToggleTheme }) {
  const indicators = [
    ['Backend', backendOnline ? 'Online' : connection === 'CONNECTING' ? 'Connecting' : 'Offline'],
    ['AI engine', monitoring ? 'Active' : backendOnline ? 'Standby' : connection === 'CONNECTING' ? 'Connecting' : 'Offline'],
    ['Camera', data?.camera?.online ? 'Active' : data?.camera?.status === 'error' ? 'Error' : backendOnline ? 'Offline' : connection === 'CONNECTING' ? 'Connecting' : 'Offline'],
    ['WebSocket', connection === 'CONNECTED' ? 'Connected' : connection === 'CONNECTING' ? 'Connecting' : connection === 'RECONNECTING' ? 'Reconnecting' : 'Disconnected'],
  ];
  return (
    <header className="topbar">
      <div>
        <p className="eyebrow">INTELLIGENT DRIVER MONITORING</p>
        <h1>Driver Safety</h1>
        <p className="subtitle">Intelligent driver monitoring, designed for safer journeys.</p>
        <div className="status-indicators" aria-label="System connection status">{indicators.map(([label, value]) => <span key={label} className={['Online', 'Active', 'Connected'].includes(value) ? 'online' : value === 'Error' ? 'error' : ''}><i />{label}<b>{value}</b></span>)}</div>
      </div>
      <div className="header-actions">
        <button className="theme-toggle" type="button" onClick={onToggleTheme} aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} appearance`} title={`Switch to ${theme === 'light' ? 'dark' : 'light'} appearance`}>
          <span aria-hidden="true">{theme === 'light' ? '◐' : '☼'}</span>{theme === 'light' ? 'Dark' : 'Light'} appearance
        </button>
        <span className={`connection-pill ${connection.toLowerCase()}`}><span className="status-dot" /> {connection}</span>
        {!monitoring ? <button className="button button-primary" onClick={onStart} disabled={busy} aria-busy={busy}>{busy ? 'Starting...' : 'Start monitoring'}</button> : <button className="button button-danger" onClick={onStop} disabled={busy} aria-busy={busy}>{busy ? 'Stopping...' : 'Stop monitoring'}</button>}
      </div>
    </header>
  );
}
