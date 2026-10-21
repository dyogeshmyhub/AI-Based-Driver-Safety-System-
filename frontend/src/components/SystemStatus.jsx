export default function SystemStatus({ data, backendOnline, connection, backendError }) {
  const cameraState = data?.camera?.online ? 'ONLINE' : data?.camera?.status === 'error' ? 'ERROR' : 'OFFLINE';
  const rows = [
    ['Backend', backendOnline ? 'ONLINE' : connection === 'CONNECTING' ? 'CONNECTING' : 'OFFLINE'],
    ['AI Engine', data?.monitoring ? 'ACTIVE' : backendOnline ? 'STANDBY' : 'OFFLINE'],
    ['Camera', cameraState],
    ['WebSocket', connection],
  ];
  const statusClass = (value) => ['ONLINE', 'CONNECTED', 'ACTIVE'].includes(value) ? 'good' : ['ERROR', 'OFFLINE', 'DISCONNECTED', 'RECONNECTING'].includes(value) ? 'warn' : '';
  return <section className="card system-card"><div className="section-title"><span className="section-kicker">06</span><h2>System status</h2></div><div className="system-list">{rows.map(([label, value]) => <div key={label}><span>{label}</span><strong className={statusClass(value)}><i />{value}</strong></div>)}</div>{backendError && <p className="error-text">{backendError}</p>}</section>;
}
