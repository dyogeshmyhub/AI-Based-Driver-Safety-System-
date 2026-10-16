import AIMetricsCard from './AIMetricsCard';
import AlertPanel from './AlertPanel';
import DriverStateCard from './DriverStateCard';
import SafetyScoreCard from './SafetyScoreCard';
import SystemStatus from './SystemStatus';

export default function LiveMonitoringPage({ data, backendOnline, cameraFrame, connection, backendError }) {
  const driver = data?.driver || {};
  const camera = data?.camera || {};
  return <section className="live-page">
    <div className="page-heading"><div><p className="eyebrow">02 / LIVE MONITORING</p><h2>Driver watch</h2><p>Processed locally from the active webcam stream.</p></div><span className={`live-status ${data?.monitoring ? 'active' : ''}`}><i />{data?.monitoring ? 'MONITORING ACTIVE' : 'STANDBY'}</span></div>
    <div className="live-layout"><section className="card live-camera-card"><div className="card-heading"><span className="card-label">LIVE CAMERA / {camera.resolution || '0x0'}</span><span className="live-tag active">{camera.status || 'OFFLINE'} · {camera.fps || 0} FPS</span></div><div className="camera-visual large-camera"><img src={cameraFrame || undefined} alt="Live driver camera feed" hidden={!cameraFrame} /><span className="camera-crosshair" hidden={Boolean(cameraFrame)} /><div className="camera-overlay"><b>{driver.face_detected ? 'FACE DETECTED' : 'NO FACE DETECTED'}</b><span>EYES {driver.eyes || '—'}</span><span>ATTENTION: {driver.attention || '—'}</span><span>DROWSINESS: {driver.drowsiness || '—'}</span></div></div></section><SafetyScoreCard safety={data?.safety} /></div>
    <div className="content-grid live-cards"><DriverStateCard data={data} /><AIMetricsCard data={data} /><AlertPanel data={data} /><SystemStatus data={data} backendOnline={backendOnline} connection={connection} backendError={backendError} /></div>
  </section>;
}
