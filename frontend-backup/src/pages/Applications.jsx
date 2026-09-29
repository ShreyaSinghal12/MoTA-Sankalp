import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api.js";
import Badge from "../components/Badge.jsx";

const STATUSES = ["", "RECEIVED", "UNDER_SCRUTINY", "SCRUTINY_COMPLETED", "AI_FLAGGED", "MANUAL_REVIEW", "APPROVED", "REJECTED", "SANCTIONED", "PAID"];
const EMPTY = { full_name: "", scheme_id: "NFST", gender: "F", state: "Jharkhand", age: 25, tribe: "",
  annual_income: 300000, marks_percentage: 76.5, claimed_fee: 444000, course: "Ph.D", institution: "", is_pvtg: false };

export default function Applications() {
  const nav = useNavigate();
  const [rows, setRows] = useState([]);
  const [filters, setFilters] = useState({ status: "", scheme_id: "", q: "" });
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState(EMPTY);
  const [msg, setMsg] = useState("");
  const [error, setError] = useState("");

  const load = () => api.listApplications(filters).then(setRows).catch((e) => setError(e.message));
  useEffect(() => { load(); }, [filters.status, filters.scheme_id]);

  async function create(e) {
    e.preventDefault();
    setError("");
    try {
      const body = { ...form, age: Number(form.age), annual_income: Number(form.annual_income),
        marks_percentage: Number(form.marks_percentage), claimed_fee: Number(form.claimed_fee) };
      const app = await api.createApplication(body);
      nav(`/applications/${app.id}`);
    } catch (err) {
      setError(err.message);
    }
  }

  async function nspImport() {
    try {
      const r = await api.nspImport(2);
      setMsg(`NSP (mock): imported ${r.imported} applications - ${r.applications.map((a) => a.full_name).join(", ")}`);
      load();
    } catch (err) { setError(err.message); }
  }

  async function nspSync() {
    try {
      const r = await api.nspSync();
      setMsg(`NSP (mock): status of ${r.accepted} applications synced at ${new Date(r.synced_at).toLocaleTimeString()}`);
    } catch (err) { setError(err.message); }
  }

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.type === "checkbox" ? e.target.checked : e.target.value });

  return (
    <div>
      <div className="page-head">
        <div>
          <div className="kicker">NFST | NOS</div>
          <h1>Applications</h1>
        </div>
        <div className="row-gap">
          <button className="btn ghost" onClick={nspSync}>NSP status sync</button>
          <button className="btn ghost" onClick={nspImport}>Import from NSP</button>
          <button className="btn primary" onClick={() => setShowCreate(!showCreate)}>{showCreate ? "Close" : "New application"}</button>
        </div>
      </div>

      {msg && <div className="notice">{msg}</div>}
      {error && <div className="error">{error}</div>}

      {showCreate && (
        <form className="panel form-grid" onSubmit={create}>
          <label>Full name<input required value={form.full_name} onChange={set("full_name")} placeholder="Priya Soren" /></label>
          <label>Scheme<select value={form.scheme_id} onChange={set("scheme_id")}><option>NFST</option><option>NOS</option></select></label>
          <label>Gender<select value={form.gender} onChange={set("gender")}><option>F</option><option>M</option><option>O</option></select></label>
          <label>State<input value={form.state} onChange={set("state")} /></label>
          <label>Tribe<input value={form.tribe} onChange={set("tribe")} /></label>
          <label>Age<input type="number" value={form.age} onChange={set("age")} /></label>
          <label>Annual income (Rs)<input type="number" value={form.annual_income} onChange={set("annual_income")} /></label>
          <label>Marks %<input type="number" step="0.1" value={form.marks_percentage} onChange={set("marks_percentage")} /></label>
          <label>Claimed amount (Rs)<input type="number" value={form.claimed_fee} onChange={set("claimed_fee")} /></label>
          <label>Course<input value={form.course} onChange={set("course")} /></label>
          <label>Institution<input value={form.institution} onChange={set("institution")} /></label>
          <label className="check"><input type="checkbox" checked={form.is_pvtg} onChange={set("is_pvtg")} /> PVTG applicant</label>
          <div className="form-actions"><button className="btn primary">Create and open</button></div>
        </form>
      )}

      <div className="filters">
        <input placeholder="Search name or application no." value={filters.q}
          onChange={(e) => setFilters({ ...filters, q: e.target.value })} onKeyDown={(e) => e.key === "Enter" && load()} />
        <select value={filters.scheme_id} onChange={(e) => setFilters({ ...filters, scheme_id: e.target.value })}>
          <option value="">All schemes</option><option>NFST</option><option>NOS</option>
        </select>
        <select value={filters.status} onChange={(e) => setFilters({ ...filters, status: e.target.value })}>
          {STATUSES.map((s) => <option key={s} value={s}>{s || "All statuses"}</option>)}
        </select>
        <button className="btn ghost" onClick={load}>Search</button>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr><th>ID</th><th>Application No</th><th>Name</th><th>Scheme</th><th>State</th><th className="num">Income</th>
              <th className="num">Marks</th><th>Status</th><th>Risk</th><th>Source</th><th /></tr>
          </thead>
          <tbody>
            {rows.map((a) => (
              <tr key={a.id}>
                <td className="mono">{a.id}</td>
                <td className="mono">{a.application_number}</td>
                <td>{a.full_name}{a.is_pvtg && <span className="tag">PVTG</span>}</td>
                <td>{a.scheme_id}</td>
                <td>{a.state}</td>
                <td className="num">{Number(a.annual_income).toLocaleString("en-IN")}</td>
                <td className="num">{a.marks_percentage}</td>
                <td><Badge value={a.status} /></td>
                <td><Badge value={a.risk_level} /></td>
                <td className="tiny muted">{a.source}</td>
                <td><Link className="btn small" to={`/applications/${a.id}`}>View</Link></td>
              </tr>
            ))}
            {rows.length === 0 && <tr><td colSpan={11} className="muted">No applications match.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}
