import { useEffect, useRef, useState } from 'react';
import { api } from './services/api';
import { MonitoringSocket } from './services/websocket';
import {
  AIMetricsCard,
  AlertPanel,
  DriverStateCard,
  EventsTable,
  Header,
  LiveMonitoringPage,
  SafetyEventsPage,
  SafetyScoreCard,
  SessionHistoryPage,
  SessionCard,
  SystemStatus,
} from './components';

const createInitialMonitoringState = () => ({
  connected: false,
  monitoring: false,
  timestamp: new Date().toISOString(),
  camera: { online: false, status: 'offline', width: 0, height: 0, resolution: '0x0', fps: 0 },
  face: { detected: false, faces: 0 },
  driver: {
    face_detected: false,
    faces: 0,
    eyes: 'OPEN',
    left_ear: 0.0,
    right_ear: 0.0,
    average_ear: 0.0,
    blink_count: 0,
    mouth: 'CLOSED',
    yawn_count: 0,
    head_pose: 'FORWARD',
    attention: 'ATTENTIVE',
    drowsiness: 'ALERT',
  },
  eyes: { left_ear: 0.0, right_ear: 0.0, average_ear: 0.0, status: 'OPEN', blink_count: 0 },
  mouth: { status: 'CLOSED', yawn_count: 0 },
  head: { direction: 'FORWARD' },
  attention: { status: 'ATTENTIVE' },
  drowsiness: { status: 'ALERT' },
  safety: { score: 100, risk_level: 'LOW', status: 'SAFE', active_risks: [] },
  alert: { level: 'INFO', message: 'Waiting for backend connection…', alarm_active: false },
  session: { active: false, duration_seconds: 0, alerts: 0, average_score: 100, minimum_score: 100, drowsiness_events: 0, yawns: 0 },
  error: null,
});

export default function App() {
  const [monitoring, setMonitoring] = useState(createInitialMonitoringState);
  const [events, setEvents] = useState(null);
  const [connection, setConnection] = useState('CONNECTING');
  const [backendOnline, setBackendOnline] = useState(false);
  const [backendError, setBackendError] = useState('');
  const [actionError, setActionError] = useState('');
  const [busy, setBusy] = useState(false);
  const [cameraFrame, setCameraFrame] = useState('');
  const [view, setView] = useState('dashboard');
  const [sessions, setSessions] = useState([]);
  const [sessionsLoading, setSessionsLoading] = useState(false);
  const [eventsFilter, setEventsFilter] = useState('ALL');
  const [selectedSession, setSelectedSession] = useState(null);
  const socketRef = useRef(null);

  useEffect(() => {
    let mounted = true;
    const loadStatus = async () => {
      try {
        const status = await api.getMonitoringStatus();
        if (mounted) {
          setMonitoring({ ...createInitialMonitoringState(), ...status, camera: { ...createInitialMonitoringState().camera, ...(status.camera || {}) }, safety: { ...createInitialMonitoringState().safety, ...(status.safety || {}) } });
          setBackendOnline(true);
          setBackendError('');
        }
      } catch (error) {
        if (mounted) { setBackendOnline(false); setBackendError(error.message || 'Backend unavailable'); }
      }
    };
    loadStatus();
    const socket = new MonitoringSocket({
      onState: (state) => {
        setMonitoring((previous) => ({ ...previous, ...state, camera: { ...previous.camera, ...(state.camera || {}) }, safety: { ...previous.safety, ...(state.safety || {}) } }));
        setBackendError(state.error || '');
      },
      onStatus: setConnection,
    });
    socketRef.current = socket;
    socket.connect();
    return () => {
      mounted = false;
      socket.disconnect();
    };
  }, []);

  useEffect(() => {
    let mounted = true;
    const loadSessions = async () => {
      setSessionsLoading(true);
      try {
        const recent = await api.getSessions();
        if (mounted) { setSessions(recent); setBackendOnline(true); }
      } catch (error) {
        if (mounted) { setBackendOnline(false); setBackendError(error.message || 'Session history unavailable'); }
      } finally {
        if (mounted) setSessionsLoading(false);
      }
    };
    loadSessions();
    const timer = window.setInterval(loadSessions, 10000);
    return () => {
      mounted = false;
      window.clearInterval(timer);
    };
  }, []);

  useEffect(() => {
    let mounted = true;
    const loadEvents = async () => {
      try {
        const recent = await api.getRecentEvents();
        if (mounted) {
          setEvents(recent);
          setBackendOnline(true);
          setBackendError('');
        }
      } catch (error) {
        if (mounted) { setBackendOnline(false); setBackendError(error.message || 'Backend unavailable'); }
      }
    };
    loadEvents();
    const timer = window.setInterval(loadEvents, 5000);
    return () => {
      mounted = false;
      window.clearInterval(timer);
    };
  }, []);

  useEffect(() => {
    let active = true;
    let objectUrl = '';

    const refreshCameraFrame = async () => {
      if (!monitoring?.monitoring) {
        setCameraFrame('');
        return;
      }
      try {
        const nextUrl = await api.getCameraFrame();
        if (!active) return;
        if (objectUrl) URL.revokeObjectURL(objectUrl);
        objectUrl = nextUrl;
        setCameraFrame(nextUrl);
      } catch {
        if (active) setCameraFrame('');
      }
    };

    refreshCameraFrame();
    const timer = window.setInterval(refreshCameraFrame, 250);
    return () => {
      active = false;
      window.clearInterval(timer);
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [monitoring?.monitoring]);

  const handleStart = async () => {
    setBusy(true);
    setActionError('');
    try {
      const result = await api.startMonitoring();
      if (!result.success) setActionError(result.message);
    } catch (error) {
      setActionError(error.message || 'Backend unavailable');
    } finally {
      setBusy(false);
    }
  };

  const handleStop = async () => {
    setBusy(true);
    setActionError('');
    try {
      await api.stopMonitoring();
    } catch (error) {
      setActionError(error.message || 'Backend unavailable');
    } finally {
      setBusy(false);
    }
  };

  const handleDeleteSession = async (session) => {
    if (!window.confirm(`Delete session ${session.id.slice(0, 8)} and its safety events?`)) return;
    try {
      await api.deleteSession(session.id);
      setSessions((current) => current.filter((item) => item.id !== session.id));
      setSelectedSession(null);
      setBackendError('');
    } catch (error) {
      setBackendError(error.message || 'Unable to delete session');
    }
  };

  const renderDashboard = () => <>
    <div className="hero-grid">
      <SafetyScoreCard safety={monitoring?.safety} />
      <section className="card camera-card"><div className="card-heading"><span className="card-label">CAMERA / MONITORING</span><span className={`live-tag ${monitoring?.camera?.online ? 'active' : ''}`}>{monitoring?.camera?.status || 'WAITING'}</span></div><div className="camera-visual"><img src={cameraFrame || undefined} alt="Live driver camera" hidden={!cameraFrame} /><span className="camera-crosshair" hidden={Boolean(cameraFrame)} /><div className="camera-overlay"><b>{monitoring?.driver?.face_detected ? 'FACE DETECTED' : 'NO FACE DETECTED'}</b><span>EYES {monitoring?.driver?.eyes || '—'}</span><span>ATTENTION: {monitoring?.driver?.attention || '—'}</span></div><span className="camera-caption">{monitoring?.camera?.online ? `${monitoring.camera.resolution} · ${monitoring.camera.fps} FPS` : 'Start monitoring to connect webcam'}</span></div></section>
      <section className="card risk-card"><span className="card-label">CURRENT RISK</span><strong>{monitoring?.safety?.risk_level || 'LOW'}</strong><p>{monitoring?.safety?.active_risks?.length ? monitoring.safety.active_risks.join(' / ') : 'No active risk signals'}</p></section>
    </div>
    <div className="content-grid"><DriverStateCard data={monitoring} /><AIMetricsCard data={monitoring} /><AlertPanel data={monitoring} /><SessionCard session={monitoring?.session} /><EventsTable events={events} error={backendError} /><SystemStatus data={monitoring} backendOnline={backendOnline} connection={connection} backendError={backendError} /></div>
  </>;

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand-lockup"><span className="brand-mark">DS</span><div><strong>Driver Safety</strong><span>AI control room</span></div></div>
        <nav className="nav" aria-label="Main navigation">
          {[['dashboard', '01', 'Dashboard'], ['live', '02', 'Live monitoring'], ['history', '03', 'Session history'], ['events', '04', 'Safety events']].map(([key, number, label]) => <button className={view === key ? 'active' : ''} key={key} onClick={() => setView(key)} aria-current={view === key ? 'page' : undefined}><b>{number}</b>{label}</button>)}
        </nav>
        <div className="sidebar-footer"><span className="status-dot on" /> Local processing<br /><small>Webcam data stays on this machine.</small></div>
      </aside>
      <section className="content">
        <Header data={monitoring} backendOnline={backendOnline} connection={connection} monitoring={Boolean(monitoring?.monitoring)} onStart={handleStart} onStop={handleStop} busy={busy} />
        {(actionError || backendError) && <div className="notice">{actionError || (connection === 'RECONNECTING' ? 'Real-time connection lost. Reconnecting...' : 'Backend connection unavailable.')}</div>}
        {view === 'dashboard' && renderDashboard()}
        {view === 'live' && <LiveMonitoringPage data={monitoring} backendOnline={backendOnline} cameraFrame={cameraFrame} connection={connection} backendError={backendError} />}
        {view === 'history' && <SessionHistoryPage sessions={sessions} loading={sessionsLoading} error={backendError} onDelete={handleDeleteSession} onView={setSelectedSession} />}
        {view === 'events' && <SafetyEventsPage events={events || []} filter={eventsFilter} onFilter={setEventsFilter} loading={!events} error={backendError} />}
        {selectedSession && <div className="modal-backdrop" role="presentation" onClick={() => setSelectedSession(null)}><section className="session-modal" role="dialog" aria-modal="true" aria-labelledby="session-detail-title" onClick={(event) => event.stopPropagation()}><div className="card-heading"><div><span className="card-label">SESSION DETAIL</span><h2 id="session-detail-title">{selectedSession.id.slice(0, 12)}</h2></div><button className="icon-button" aria-label="Close session details" onClick={() => setSelectedSession(null)}>×</button></div><div className="detail-grid"><span>Start<strong>{new Date(selectedSession.start_time).toLocaleString()}</strong></span><span>End<strong>{selectedSession.end_time ? new Date(selectedSession.end_time).toLocaleString() : 'Active'}</strong></span><span>Average score<strong>{Math.round(selectedSession.average_safety_score)} / 100</strong></span><span>Minimum score<strong>{Math.round(selectedSession.minimum_safety_score)} / 100</strong></span><span>Alerts<strong>{selectedSession.total_alerts}</strong></span><span>Drowsiness events<strong>{selectedSession.total_drowsiness_events}</strong></span><span>Yawns<strong>{selectedSession.total_yawns}</strong></span><span>Blinks<strong>{selectedSession.total_blinks}</strong></span></div></section></div>}
      </section>
    </main>
  );
}
