export default function AIMetricsCard({ data, backendOnline = false }) {
  const driver = data?.driver ?? {};
  const eyes = data?.driver ?? data?.eyes ?? {};
  const mouth = data?.driver ?? data?.mouth ?? {};
  const camera = data?.camera;
  const metric = (value, digits = 2) => value == null ? backendOnline ? 'Awaiting data' : 'N/A' : typeof value === 'number' ? value.toFixed(digits) : value;
  return <section className="card"><div className="section-title"><span className="section-kicker">02</span><h2>AI metrics</h2></div><div className="metrics-grid">
    <div><span>Left EAR</span><strong>{metric(eyes?.left_ear)}</strong></div><div><span>Right EAR</span><strong>{metric(eyes?.right_ear)}</strong></div><div><span>Average EAR</span><strong>{metric(eyes?.average_ear)}</strong></div><div><span>Blinks</span><strong>{metric(driver?.blink_count ?? eyes?.blink_count, 0)}</strong></div><div><span>Yawns</span><strong>{metric(driver?.yawn_count ?? mouth?.yawn_count, 0)}</strong></div><div><span>FPS</span><strong>{metric(camera?.fps, 0)}</strong></div>
  </div></section>;
}
