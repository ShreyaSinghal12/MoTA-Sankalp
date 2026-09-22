import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api.js";
import Badge from "../components/Badge.jsx";

const CARDS = [
  ["total_applications", "Total Applications"],
  ["pending", "Pending (Received)"],
  ["under_scrutiny", "Under Scrutiny"],
  ["ai_flagged", "AI Flagged"],
  ["manual_review", "Manual Review"],
  ["approved", "Approved"],
  ["rejected", "Rejected"],
  ["sanctioned", "Sanctioned"],
  ["paid", "Paid (PFMS)"],
];

export default function Dashboard() {
  const [s, setS] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.stats().then(setS).catch((e) => setError(e.message));
  }, []);

  if (error) return <div className="error">{error}</div>;
  if (!s) return <div className="loading">Loading dashboard...</div>;

  const maxScheme = Math.max(1, ...Object.values(s.by_scheme));
  return (
    <div>
      <div className="page-head">
        <div>
          <div className="kicker">Administrator cockpit</div>
          <h1>Dashboard</h1>
        </div>
        <Link className="btn primary" to="/applications">Open applications</Link>
      </div>

      <div className="cards">
        {CARDS.map(([k, label]) => (
          <div key={k} className={"card" + (k === "ai_flagged" && s[k] ? " card-alert" : "")}>
            <div className="card-v">{s[k]}</div>
            <div className="card-l">{label}</div>
          </div>
        ))}
        <div className="card card-wide">
          <div className="card-v">Rs {Number(s.amount_disbursed).toLocaleString("en-IN")}</div>
          <div className="card-l">Disbursed via PFMS (mock)</div>
        </div>
      </div>

      <div className="grid2">
        <div className="panel">
          <h3>Applications by scheme</h3>
          {Object.entries(s.by_scheme).map(([k, v]) => (
            <div key={k} className="bar-row">
              <span className="bar-label">{k}</span>
              <span className="bar"><span style={{ width: (v / maxScheme) * 100 + "%" }} /></span>
              <span className="bar-v">{v}</span>
            </div>
          ))}
          <h3 style={{ marginTop: 24 }}>By status</h3>
          <div className="chips">
            {Object.entries(s.by_status).map(([k, v]) => (
              <span key={k} className="chip"><Badge value={k} /> {v}</span>
            ))}
          </div>
          <h3 style={{ marginTop: 24 }}>By risk</h3>
          <div className="chips">
            {Object.entries(s.by_risk).map(([k, v]) => (
              <span key={k} className="chip"><Badge value={k} /> {v}</span>
            ))}
          </div>
        </div>
        <div className="panel">
          <h3>Recent activity</h3>
          <ul className="activity">
            {s.recent_activity.map((a) => (
              <li key={a.id}>
                <span className="mono">{a.action}</span>
                <span className="muted"> by {a.actor}</span>
                {a.application_id && <Link to={`/applications/${a.application_id}`}> #{a.application_id}</Link>}
                <div className="tiny muted">{new Date(a.created_at).toLocaleString()}</div>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
