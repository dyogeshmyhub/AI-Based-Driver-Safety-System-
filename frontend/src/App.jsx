import { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { api } from './services/api';
import { MonitoringSocket } from './services/websocket';
import { formatDuration } from './utils/formatDuration';
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
  camera: { online: false, status: 'offline', width: 0, height: 0, resolution: null, fps: null },
  face: { detected: null, faces: null },
  driver: {
    face_detected: null,
    faces: null,
    eyes: null,
    left_ear: null,
    right_ear: null,
    average_ear: null,
    blink_count: null,
    mouth: null,
    yawn_count: null,
    head_pose: null,
    attention: null,
    drowsiness: null,
  },
  eyes: { left_ear: null, right_ear: null, average_ear: null, status: null, blink_count: null },
  mouth: { status: null, yawn_count: null },
  head: { direction: null },
  attention: { status: null },
  drowsiness: { status: null },
  safety: { score: null, risk_level: null, status: null, active_risks: [] },
  alert: null,
  session: { active: null, duration_seconds: null, alerts: null, average_score: null, minimum_score: null, drowsiness_events: null, yawns: null },
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
  const [theme, setTheme] = useState(() => (
    window.localStorage.getItem('driver-safety-theme') === 'light' ? 'light' : 'dark'
  ));
  const socketRef = useRef(null);

  useLayoutEffect(() => {
    window.scrollTo(0, 0);
  }, [view]);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    window.localStorage.setItem('driver-safety-theme', theme);
  }, [theme]);

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

  const renderDashboard = () => <div className="cockpit-layout">
    <div className={`cockpit-grid ${monitoring?.monitoring ? 'monitoring-active' : ''}`}>
      <section className="card camera-card cockpit-camera" aria-label="Live camera monitoring">
        <div className="card-heading">
          <div className="camera-heading">
            <span className="card-label">DRIVER MONITORING</span>
            <strong>{monitoring?.monitoring ? 'Live cabin view' : 'Cabin view'}</strong>
          </div>
          <span className={`live-tag ${monitoring?.camera?.online ? 'active' : ''}`}>{monitoring?.camera?.online ? 'CAMERA READY' : monitoring?.camera?.status === 'error' ? 'UNAVAILABLE' : monitoring?.monitoring ? 'INITIALIZING' : 'STANDBY'}</span>
        </div>
        <div className={`camera-visual ${cameraFrame ? 'has-feed' : 'no-feed'}`}>
          <img src={cameraFrame || undefined} alt="Live driver camera" hidden={!cameraFrame} />
          <div className="camera-empty" hidden={Boolean(cameraFrame)}>
            <span className="camera-icon" aria-hidden="true">◉</span>
            <strong>{monitoring?.camera?.status === 'error' ? 'Camera unavailable' : monitoring?.monitoring ? 'Initializing camera' : 'Monitoring on standby'}</strong>
            <span>{monitoring?.error || (monitoring?.monitoring ? 'Waiting for a camera frame.' : 'Start monitoring to begin driver observation.')}</span>
          </div>
          <div className="camera-overlay" hidden={!cameraFrame}>
            <b>{monitoring?.driver?.face_detected == null ? 'FACE STATUS UNAVAILABLE' : monitoring.driver.face_detected ? 'FACE DETECTED' : 'NO FACE DETECTED'}</b>
            <span>EYES {monitoring?.driver?.eyes || '—'}</span>
            <span>ATTENTION {monitoring?.driver?.attention || '—'}</span>
            <span>DROWSINESS {monitoring?.driver?.drowsiness || '—'}</span>
          </div>
        </div>
        <div className="camera-footer">
          <span><i className={monitoring?.camera?.online ? 'state-on' : ''} />{monitoring?.camera?.online ? 'Camera connected' : monitoring?.camera?.status === 'error' ? 'Camera unavailable' : 'Camera inactive'}</span>
          <span>{monitoring?.driver?.face_detected == null ? 'Face: awaiting data' : monitoring.driver.face_detected ? 'Face detected' : 'No face detected'}</span>
          <span>{monitoring?.camera?.online && Number.isFinite(monitoring.camera.fps) ? `${monitoring.camera.fps} FPS` : 'FPS —'}</span>
        </div>
        <div className="vehicle-visual" aria-label="Decorative vehicle outline; no vehicle sensor data is connected">
          <span className="vehicle-caption">CABIN MONITORING <small>CAMERA-BASED</small></span>
          <svg viewBox="0 0 260 72" role="img" aria-hidden="true">
            <path d="M44 47h-9a7 7 0 0 1-7-7v-7a7 7 0 0 1 6-7l17-4 17-13a14 14 0 0 1 9-3h67a18 18 0 0 1 12 5l17 15 29 5a8 8 0 0 1 7 8v8h-9" />
            <path d="M60 47h112M78 17l-7 12h53V8H84a9 9 0 0 0-6 2l-9 7m62-9v21h55l-14-13a14 14 0 0 0-10-4z" />
            <circle cx="58" cy="48" r="10" /><circle cx="190" cy="48" r="10" />
          </svg>
          <span className="vehicle-caption-end">NO VEHICLE SENSORS CONNECTED</span>
        </div>
      </section>

      <section className="cockpit-safety" aria-label="Driver safety">
        <div className="cockpit-column-heading"><span>SAFETY SYSTEM</span><span className={`monitoring-indicator ${monitoring?.monitoring ? 'active' : ''}`}><i />{monitoring?.monitoring ? 'MONITORING' : 'STANDBY'}</span></div>
        <SafetyScoreCard safety={monitoring?.safety} monitoring={Boolean(monitoring?.monitoring)} backendOnline={backendOnline} />
        <section className={`card risk-card ${monitoring?.safety?.risk_level?.toLowerCase() || 'unknown'}`}>
          <span className="card-label">CURRENT RISK</span>
          <strong>{monitoring?.safety?.risk_level || 'Awaiting data'}</strong>
          <p>{monitoring?.safety?.risk_level ? monitoring.safety.active_risks?.length ? monitoring.safety.active_risks.join(' / ') : 'No active risk signals' : 'Risk status is unavailable.'}</p>
        </section>
        <DriverStateCard data={monitoring} backendOnline={backendOnline} />
      </section>

      <section className="cockpit-analytics" aria-label="AI analytics">
        <AIMetricsCard data={monitoring} backendOnline={backendOnline} />
        <section className="card distraction-panel">
          <div className="section-title"><span className="section-kicker">LIVE</span><h2>Distraction analysis</h2></div>
          <div className="signal-list">
            {[
              ['Face detection', monitoring?.driver?.face_detected == null ? (backendOnline ? 'Awaiting data' : 'N/A') : monitoring.driver.face_detected ? 'Detected' : 'Not detected', monitoring?.driver?.face_detected == null ? 'unknown' : monitoring.driver.face_detected ? 'normal' : 'warning'],
              ['Driver attention', monitoring?.driver?.attention || (backendOnline ? 'Awaiting data' : 'N/A'), monitoring?.driver?.attention ? (String(monitoring.driver.attention).toLowerCase().includes('distract') ? 'warning' : 'normal') : 'unknown'],
              ['Drowsiness', monitoring?.driver?.drowsiness || (backendOnline ? 'Awaiting data' : 'N/A'), monitoring?.driver?.drowsiness ? (/(drows|warn|high)/i.test(monitoring.driver.drowsiness) ? 'warning' : 'normal') : 'unknown'],
              ['Eye state', monitoring?.driver?.eyes || (backendOnline ? 'Awaiting data' : 'N/A'), monitoring?.driver?.eyes ? (/closed/i.test(monitoring.driver.eyes) ? 'warning' : 'normal') : 'unknown'],
              ['Head orientation', monitoring?.driver?.head_pose || (backendOnline ? 'Awaiting data' : 'N/A'), monitoring?.driver?.head_pose ? 'neutral' : 'unknown'],
              ['Mouth / yawn', monitoring?.driver?.mouth || (backendOnline ? 'Awaiting data' : 'N/A'), monitoring?.driver?.mouth ? 'neutral' : 'unknown'],
            ].map(([label, value, state]) => <div className={`signal-row ${state}`} key={label}><span className="signal-label">{label}</span><span className="signal-track" aria-hidden="true"><i /></span><strong>{value}</strong></div>)}
          </div>
        </section>
      </section>

      <section className="cockpit-gauge" aria-label="Driver attention and recent alerts">
        <section className="card categorical-gauge">
          <div className="section-title"><span className="section-kicker">STATUS</span><h2>Attention level</h2></div>
          <div className={`attention-gauge ${monitoring?.driver?.attention ? (/distract/i.test(monitoring.driver.attention) ? 'warning' : 'normal') : 'unknown'}`}>
            <div><span>ATTENTION</span><strong>{monitoring?.driver?.attention || (backendOnline ? 'Awaiting data' : 'N/A')}</strong></div>
          </div>
          <p className="gauge-note">Live attention classification. No numeric distraction score is available.</p>
          <AlertPanel data={monitoring} />
          <EventsTable events={events} error={backendError} limit={3} />
        </section>
      </section>
    </div>

    <section className="cockpit-support" aria-label="Session and system information">
      <SessionCard session={monitoring?.session} />
      <SystemStatus data={monitoring} backendOnline={backendOnline} connection={connection} backendError={backendError} />
    </section>
  </div>;

  return (
    <main className="app-shell">
      <section className={`content ${view === 'dashboard' ? 'dashboard-content' : ''}`}>
        <Header data={monitoring} backendOnline={backendOnline} connection={connection} monitoring={Boolean(monitoring?.monitoring)} onStart={handleStart} onStop={handleStop} busy={busy} theme={theme} onToggleTheme={() => setTheme((current) => current === 'light' ? 'dark' : 'light')} />
        {(actionError || backendError) && <div className="notice">{actionError || (connection === 'RECONNECTING' ? 'Real-time connection lost. Reconnecting...' : 'Backend connection unavailable.')}</div>}
        {view === 'dashboard' && renderDashboard()}
        {view === 'live' && <LiveMonitoringPage data={monitoring} backendOnline={backendOnline} cameraFrame={cameraFrame} connection={connection} backendError={backendError} />}
        {view === 'history' && <SessionHistoryPage sessions={sessions} loading={sessionsLoading} error={backendError} onDelete={handleDeleteSession} onView={setSelectedSession} />}
        {view === 'events' && <SafetyEventsPage events={events || []} filter={eventsFilter} onFilter={setEventsFilter} loading={!events} error={backendError} />}
        {selectedSession && <div className="modal-backdrop" role="presentation" onClick={() => setSelectedSession(null)}><section className="session-modal" role="dialog" aria-modal="true" aria-labelledby="session-detail-title" onClick={(event) => event.stopPropagation()}><div className="card-heading"><div><span className="card-label">SESSION DETAIL</span><h2 id="session-detail-title">{selectedSession.id.slice(0, 12)}</h2></div><button className="icon-button" aria-label="Close session details" onClick={() => setSelectedSession(null)}>×</button></div><div className="detail-grid"><span>Start<strong>{new Date(selectedSession.start_time).toLocaleString()}</strong></span><span>End<strong>{selectedSession.end_time ? new Date(selectedSession.end_time).toLocaleString() : 'Active'}</strong></span><span>Average score<strong>{Math.round(selectedSession.average_safety_score)} / 100</strong></span><span>Minimum score<strong>{Math.round(selectedSession.minimum_safety_score)} / 100</strong></span><span>Alerts<strong>{selectedSession.total_alerts}</strong></span><span>Drowsiness events<strong>{selectedSession.total_drowsiness_events}</strong></span><span>Yawns<strong>{selectedSession.total_yawns}</strong></span><span>Blinks<strong>{selectedSession.total_blinks}</strong></span></div></section></div>}
      </section>
      <aside className="infotainment-bar" aria-label="Application controls">
        <nav className="nav" aria-label="Main navigation">
          {[['dashboard', '⌂', 'Dashboard'], ['live', '◉', 'Live monitoring'], ['history', '◷', 'Sessions'], ['events', '≋', 'Safety events']].map(([key, icon, label]) => <button className={view === key ? 'active' : ''} key={key} onClick={() => setView(key)} aria-current={view === key ? 'page' : undefined}><i aria-hidden="true">{icon}</i><span>{label}</span></button>)}
        </nav>
        <div className="dock-session"><i className={monitoring?.session?.active ? 'active' : ''} /><span>{monitoring?.session?.active ? 'SESSION ACTIVE' : 'NO ACTIVE SESSION'}</span>{monitoring?.session?.duration_seconds != null && <strong>{formatDuration(monitoring.session.duration_seconds)}</strong>}</div>
      </aside>
    </main>
  );
}
