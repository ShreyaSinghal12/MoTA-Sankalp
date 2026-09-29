import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { login } from "../api.js";

export default function Login() {
  const nav = useNavigate();
  const [email, setEmail] = useState("admin@mota.gov.in");
  const [password, setPassword] = useState("admin123");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await login(email, password);
      nav("/dashboard");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login-wrap">
      <div className="login-art">
        <Link to="/home" className="login-back">← Back to Home</Link>
        <div className="login-kicker">Ministry of Tribal Affairs | Government of India</div>
        <h1>SANKALP</h1>
        <p>Scholarship and fellowship scrutiny for NFST and NOS. AI extracts, detects, compares and explains. The rule engine checks policy. The officer decides.</p>
        <div className="login-stripe" />
      </div>
      <form className="login-card" onSubmit={submit}>
        <h2>Officer sign-in</h2>
        <label>Email<input value={email} onChange={(e) => setEmail(e.target.value)} /></label>
        <label>Password<input type="password" value={password} onChange={(e) => setPassword(e.target.value)} /></label>
        {error && <div className="error">{error}</div>}
        <button className="btn primary" disabled={busy}>{busy ? "Signing in..." : "Sign in"}</button>
        <div className="demo-creds">
          Demo: admin@mota.gov.in / admin123<br />officer@mota.gov.in / officer123
        </div>
      </form>
    </div>
  );
}
