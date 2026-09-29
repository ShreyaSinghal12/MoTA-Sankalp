import { NavLink, Link } from "react-router-dom";
import { getUser, logout } from "../api.js";

export default function Layout({ children }) {
  const user = getUser();
  return (
    <div className="shell">
      <aside className="rail">
        <div className="brand">
          <div className="brand-mark">MoTA</div>
          <div className="brand-name">SANKALP</div>
          <div className="brand-sub">Scheme Administration, Network &amp; Knowledge Automated Lifecycle Platform</div>
        </div>
        <nav>
  <NavLink to="/dashboard">Dashboard</NavLink>
  <NavLink to="/applications">Applications</NavLink>
  <NavLink to="/documents">Document Analyzer</NavLink>
  <a href="http://127.0.0.1:8000/docs" target="_blank" rel="noreferrer">API Docs</a>
</nav>
        <div className="rail-foot">
          <div className="who">{user ? user.full_name : ""}</div>
          <div className="role">{user ? user.role : ""}</div>
          <button className="btn ghost small" onClick={logout}>Sign out</button>
        </div>
      </aside>
      <main className="content">{children}</main>
    </div>
  );
}
