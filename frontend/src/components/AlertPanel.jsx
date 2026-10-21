export default function AlertPanel({ data }) {
  const alert = data?.alert;
  const risks = data?.safety?.active_risks || [];
  const level = alert?.level || 'INFO';
  const waiting = !alert;
  return <section className={`card alert-panel ${level.toLowerCase()}`}><div className="section-title"><span className="section-kicker">03</span><h2>Active alerts</h2></div><div className="alert-state"><span className="alert-mark">{waiting ? '…' : level === 'CRITICAL' ? '!' : level === 'INFO' ? 'OK' : '!'}</span><div><strong>{waiting ? 'Waiting for monitoring status' : level === 'INFO' ? 'No active alerts' : alert?.message}</strong><p>{risks.length ? risks.join(' / ') : waiting ? 'Alert status will appear when the backend responds.' : alert?.message || 'Driver monitoring is clear.'}</p></div></div></section>;
}
