const stateRows = [
  ['Face', (data) => {
    const value = data?.driver?.face_detected ?? data?.face?.detected;
    if (value == null) return null;
    return value ? 'DETECTED' : 'NOT DETECTED';
  }],
  ['Eyes', (data) => data?.driver?.eyes ?? data?.eyes?.status],
  ['Drowsiness', (data) => data?.driver?.drowsiness ?? data?.drowsiness?.status],
  ['Attention', (data) => data?.driver?.attention ?? data?.attention?.status],
  ['Head', (data) => data?.driver?.head_pose ?? data?.head?.direction],
  ['Mouth', (data) => data?.driver?.mouth ?? data?.mouth?.status],
];

export default function DriverStateCard({ data }) {
  return <section className="card"><div className="section-title"><span className="section-kicker">01</span><h2>Driver state</h2></div><div className="state-list">{stateRows.map(([label, getValue]) => <div className="state-row" key={label}><span>{label}</span><strong>{getValue(data) || 'Loading...'}</strong></div>)}</div></section>;
}
