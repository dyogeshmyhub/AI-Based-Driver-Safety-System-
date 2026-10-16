export default function SystemStatus({ data, backendOnline, connection, backendError }) {
  const cameraState = data?.camera?.online ? 'ONLINE' : data?.camera?.status === 'error' ? 'ERROR' : 'OFFLINE';
  const rows = [
    ['Backend', backendOnline ? 'ONLINE' : 'OFFLINE'],
    ['AI Engine', data?.monitoring ? 'ONLINE' : 'OFFLINE'],
    ['Camera', cameraState],
    ['WebSocket', connection === 'CONNECTED' ? 'CONNECTED' : connection === 'RECONNECTING' ? 'RECONNECTING' : 'DISCONNECTED'],
    ['Database', backendError ? 'ERROR' : 'CONNECTED'],
  ];
  return <section className="card system-card"><div className="section-title"><span className="section-kicker">06</span><h2>System status</h2></div><div className="system-list">{rows.map(([label, value]) => <div key={label}><span>{label}</span><strong className={value === 'ONLINE' || value === 'CONNECTED' || value === 'READY' ? 'good' : 'warn'}><i />{value}</strong></div>)}</div>{backendError && <p className="error-text">Backend connection unavailable.</p>}</section>;
}
