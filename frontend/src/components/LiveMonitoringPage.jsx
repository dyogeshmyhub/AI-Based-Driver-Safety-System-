import AIMetricsCard from './AIMetricsCard';
import AlertPanel from './AlertPanel';
import DriverStateCard from './DriverStateCard';
import SafetyScoreCard from './SafetyScoreCard';
import SystemStatus from './SystemStatus';

export default function LiveMonitoringPage({ data, backendOnline, cameraFrame, connection, backendError }) {
  const driver = data?.driver || {};
  const camera = data?.camera || {};
  return <section className="live-page">
    <div className="page-heading"><div><p className="eyebrow">02 / LIVE MONITORING</p><h2>Live monitoring</h2><p>Processed locally from the active webcam stream.</p></div><span className={`live-status ${data?.monitoring ? 'active' : ''}`}><i />{data?.monitoring ? 'MONITORING ACTIVE' : 'STANDBY'}</span></div>
    <div className="live-layout"><section className="card live-camera-card"><div className="card-heading"><span className="card-label">LIVE CAMERA{camera.resolution ? ` / ${camera.resolution}` : ''}</span><span className={`live-tag ${camera.online ? 'active' : ''}`}>{camera.status || 'OFFLINE'}{camera.online && Number.isFinite(camera.fps) ? ` · ${camera.fps} FPS` : ''}</span></div><div className={`camera-visual large-camera ${cameraFrame ? 'has-feed' : 'no-feed'}`}><img src={cameraFrame || undefined} alt="Live driver camera feed" hidden={!cameraFrame} /><div className="camera-empty" hidden={Boolean(cameraFrame)}><span className="camera-icon" aria-hidden="true">◉</span><strong>{data?.monitoring ? 'Waiting for camera image' : 'Camera is on standby'}</strong><span>{data?.monitoring ? 'The live feed will appear when a camera frame is available.' : 'Start monitoring to view the live camera feed.'}</span></div><div className="camera-overlay" hidden={!cameraFrame}><b>{driver.face_detected ? 'FACE DETECTED' : 'NO FACE DETECTED'}</b><span>EYES {driver.eyes || '—'}</span><span>ATTENTION: {driver.attention || '—'}</span><span>DROWSINESS: {driver.drowsiness || '—'}</span></div></div></section><SafetyScoreCard safety={data?.safety} /></div>
    <div className="content-grid live-cards"><DriverStateCard data={data} backendOnline={backendOnline} /><AIMetricsCard data={data} backendOnline={backendOnline} /><AlertPanel data={data} /><SystemStatus data={data} backendOnline={backendOnline} connection={connection} backendError={backendError} /></div>
  </section>;
}
