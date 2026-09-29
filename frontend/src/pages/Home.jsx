import React, { useEffect, useState, useRef, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import "./Home.css";

/* ─── Ashoka Emblem SVG (inline) ─── */
function AshokaEmblem({ size = 40, color = "currentColor" }) {
  return (
    <svg width={size} height={size} viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="50" cy="50" r="48" stroke={color} strokeWidth="2" fill="none" />
      <circle cx="50" cy="50" r="38" stroke={color} strokeWidth="1.5" fill="none" />
      {/* Ashoka Chakra – 24 spokes */}
      {Array.from({ length: 24 }).map((_, i) => {
        const angle = (i * 15 * Math.PI) / 180;
        const x2 = 50 + 36 * Math.cos(angle);
        const y2 = 50 + 36 * Math.sin(angle);
        return <line key={i} x1="50" y1="50" x2={x2} y2={y2} stroke={color} strokeWidth="1" />;
      })}
      <circle cx="50" cy="50" r="8" fill={color} />
      {/* Four lions silhouette simplified */}
      <text x="50" y="26" textAnchor="middle" fill={color} fontSize="10" fontWeight="700" fontFamily="serif">☸</text>
      <text x="50" y="88" textAnchor="middle" fill={color} fontSize="7" fontWeight="600" fontFamily="serif">सत्यमेव जयते</text>
    </svg>
  );
}

/* ─── Government Agency Logo Bar ─── */
const GOV_AGENCIES = [
  { name: "MeitY", sub: "Ministry of Electronics & IT" },
  { name: "NIC", sub: "National Informatics Centre" },
  { name: "myGov", sub: "Citizen Engagement" },
  { name: "india.gov.in", sub: "National Portal" },
  { name: "Digital India", sub: "Power to Empower" },
  { name: "UMANG", sub: "Unified Mobile App" },
  { name: "DigiLocker", sub: "Digital Documents" },
];

/* ─── Static data ─── */
const STATS = [
  { value: "12,500+", label: "Scholarships Processed", icon: "🎓" },
  { value: "₹420 Cr", label: "Funds Disbursed", icon: "💰" },
  { value: "28", label: "States & UTs Covered", icon: "🗺️" },
  { value: "98.7%", label: "Accuracy Rate", icon: "✅" },
];

const OFFERS = [
  { icon: "🤖", title: "AI-Powered Scrutiny", desc: "Automated document verification using OCR, NLP, and deep-learning models to detect inconsistencies and fraudulent submissions in real-time." },
  { icon: "📊", title: "Intelligent Dashboard", desc: "Comprehensive analytics with live status tracking, scheme-wise breakdowns, and risk heat-maps for informed decision-making." },
  { icon: "🔗", title: "DigiLocker Integration", desc: "Seamlessly verify academic certificates, income proof, and identity documents through official government digital repositories." },
  { icon: "🛡️", title: "Policy Rule Engine", desc: "Configurable rule engine that encodes NFST and NOS eligibility criteria, ensuring 100% policy compliance before officer review." },
  { icon: "⚡", title: "Real-Time Processing", desc: "End-to-end pipeline from application intake to PFMS disbursement, reducing processing time from months to days." },
  { icon: "📑", title: "Audit Trail & Transparency", desc: "Complete immutable audit log of every action, ensuring accountability and enabling RTI compliance at every stage." },
];

const RESULTS_STATE = [
  { state: "Jharkhand", applications: 3240, approved: 2890, rejected: 210, pending: 140, disbursed: "₹48.2 Cr" },
  { state: "Madhya Pradesh", applications: 2810, approved: 2510, rejected: 180, pending: 120, disbursed: "₹42.1 Cr" },
  { state: "Odisha", applications: 2150, approved: 1920, rejected: 130, pending: 100, disbursed: "₹32.4 Cr" },
  { state: "Chhattisgarh", applications: 1890, approved: 1690, rejected: 110, pending: 90, disbursed: "₹28.7 Cr" },
  { state: "Rajasthan", applications: 1520, approved: 1380, rejected: 80, pending: 60, disbursed: "₹23.1 Cr" },
  { state: "Maharashtra", applications: 1340, approved: 1200, rejected: 90, pending: 50, disbursed: "₹20.5 Cr" },
  { state: "Andhra Pradesh", applications: 980, approved: 870, rejected: 60, pending: 50, disbursed: "₹14.8 Cr" },
  { state: "Gujarat", applications: 870, approved: 780, rejected: 50, pending: 40, disbursed: "₹13.2 Cr" },
];

const RESULTS_SCHEME = [
  { scheme: "NFST (Fellowship)", total: 5420, approved: 4870, avgDays: 12, satisfaction: "94%" },
  { scheme: "NOS (Overseas)", total: 3180, approved: 2840, avgDays: 18, satisfaction: "91%" },
  { scheme: "Pre-Matric", total: 8940, approved: 8120, avgDays: 8, satisfaction: "96%" },
  { scheme: "Post-Matric", total: 7260, approved: 6580, avgDays: 10, satisfaction: "93%" },
];

const TEAM = [
  { name: "Aarav", role: "Lead Developer & Architect", photo: "/images/team1.jpg", bio: "Full-stack architect specializing in AI/ML pipelines and government digital infrastructure systems." },
  { name: "Kamesh", role: "Backend Engineer", photo: "/images/team3.jpg", bio: "Expert in scalable microservices, API design, and database architecture for high-throughput government platforms." },
  { name: "Shreya", role: "Data Scientist", photo: "/images/team2.jpg", bio: "Specializes in NLP, OCR systems, and fraud detection algorithms for document verification workflows." },
  { name: "Kunal", role: "ML Engineer", photo: "/images/team5.jpg", bio: "Builds production-grade machine learning models for automated scrutiny and risk assessment pipelines." },
  { name: "Jasmine", role: "Project Manager", photo: "/images/team4.jpg", bio: "Agile project lead with expertise in govtech delivery, stakeholder management, and compliance frameworks." },
  { name: "Tushika", role: "UI/UX Designer", photo: "/images/team6.jpg", bio: "Creates accessible, user-centered interfaces with a focus on WCAG compliance and government design standards." },
];

const NAV_LINKS = [
  { id: "hero", label: "Home" },
  { id: "idea", label: "The Idea" },
  { id: "offer", label: "What We Offer" },
  { id: "results", label: "Results" },
  { id: "team", label: "Team" },
];

/* ─── hook: animated counter ─── */
function useCounter(target, duration = 2000, startCounting) {
  const [count, setCount] = useState(0);
  const numericTarget = parseInt(String(target).replace(/[^0-9]/g, ""), 10) || 0;

  useEffect(() => {
    if (!startCounting) return;
    let start = 0;
    const increment = numericTarget / (duration / 16);
    const timer = setInterval(() => {
      start += increment;
      if (start >= numericTarget) {
        setCount(numericTarget);
        clearInterval(timer);
      } else {
        setCount(Math.floor(start));
      }
    }, 16);
    return () => clearInterval(timer);
  }, [startCounting, numericTarget, duration]);

  return count;
}

/* ─── hook: intersection observer ─── */
function useInView() {
  const ref = useRef(null);
  const [inView, setInView] = useState(false);

  useEffect(() => {
    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) {
        setInView(true);
        observer.disconnect();
      }
    }, { threshold: 0.15 });

    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);

  return [ref, inView];
}

/* ─── stat card with counter ─── */
function StatCard({ stat, inView }) {
  const count = useCounter(stat.value, 2000, inView);
  const prefix = stat.value.startsWith("₹") ? "₹" : "";
  const suffix = stat.value.includes("+") ? "+" : stat.value.includes("%") ? "%" : stat.value.includes("Cr") ? " Cr" : "";

  return (
    <div className="hp-stat-card">
      <div className="hp-stat-icon">{stat.icon}</div>
      <div className="hp-stat-value">{prefix}{count.toLocaleString("en-IN")}{suffix}</div>
      <div className="hp-stat-label">{stat.label}</div>
    </div>
  );
}

/* ═══════════════════════ MAIN COMPONENT ═══════════════════════ */
export default function Home() {
  const navigate = useNavigate();
  const [scrolled, setScrolled] = useState(false);
  const [activeSection, setActiveSection] = useState("hero");
  const [theme, setTheme] = useState(() => localStorage.getItem("sankalp_theme") || "light");
  const [textSize, setTextSize] = useState(() => localStorage.getItem("sankalp_textsize") || "md");

  const [statsRef, statsInView] = useInView();
  const [ideaRef, ideaInView] = useInView();
  const [offerRef, offerInView] = useInView();
  const [resultsRef, resultsInView] = useInView();
  const [teamRef, teamInView] = useInView();

  /* ─── Accessibility: theme ─── */
  const cycleTheme = useCallback(() => {
    const order = ["light", "dark", "high-contrast"];
    const next = order[(order.indexOf(theme) + 1) % order.length];
    setTheme(next);
    localStorage.setItem("sankalp_theme", next);
  }, [theme]);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);

  /* ─── Accessibility: text size ─── */
  const changeTextSize = useCallback((dir) => {
    const sizes = ["sm", "md", "lg", "xl"];
    const idx = sizes.indexOf(textSize);
    const next = dir === "+" ? Math.min(idx + 1, 3) : Math.max(idx - 1, 0);
    setTextSize(sizes[next]);
    localStorage.setItem("sankalp_textsize", sizes[next]);
  }, [textSize]);

  useEffect(() => {
    document.body.className = document.body.className.replace(/text-(sm|md|lg|xl)/g, "");
    document.body.classList.add(`text-${textSize}`);
  }, [textSize]);

  /* ─── Scroll tracking ─── */
  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 60);
      const sections = NAV_LINKS.map((l) => document.getElementById(l.id));
      for (let i = sections.length - 1; i >= 0; i--) {
        const s = sections[i];
        if (s && s.getBoundingClientRect().top <= 150) {
          setActiveSection(NAV_LINKS[i].id);
          break;
        }
      }
    };
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const scrollTo = (id) => document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });

  const themeLabel = theme === "light" ? "☀️ Light" : theme === "dark" ? "🌙 Dark" : "🔳 High Contrast";

  return (
    <div className="hp-root">
      {/* ─── SKIP LINK (Accessibility) ─── */}
      <a href="#main-content" className="skip-link">Skip to Main Content</a>

      {/* ─── ACCESSIBILITY TOOLBAR (NSP-style) ─── */}
      <div className="a11y-toolbar" role="toolbar" aria-label="Accessibility controls">
        <div className="a11y-left">
          <span>Government of India</span>
          <span>|</span>
          <span>Ministry of Tribal Affairs</span>
        </div>
        <div className="a11y-right">
          <button className="a11y-btn" onClick={() => changeTextSize("-")} title="Decrease text size" aria-label="Decrease text size">A-</button>
          <button className="a11y-btn" onClick={() => { setTextSize("md"); localStorage.setItem("sankalp_textsize", "md"); }} title="Reset text size" aria-label="Reset text size">A</button>
          <button className="a11y-btn" onClick={() => changeTextSize("+")} title="Increase text size" aria-label="Increase text size">A+</button>
          <div className="a11y-divider" />
          <button className={`a11y-btn ${theme !== "light" ? "active" : ""}`} onClick={cycleTheme} title="Toggle theme" aria-label={`Current theme: ${theme}. Click to change.`}>
            {themeLabel}
          </button>
          <div className="a11y-divider" />
          <button className="a11y-btn" onClick={() => { const lang = document.documentElement.lang === "en" ? "hi" : "en"; document.documentElement.lang = lang; }} title="Toggle language" aria-label="Toggle language">
            हिं / En
          </button>
        </div>
      </div>

      {/* ─── NAVBAR ─── */}
      <nav className={`hp-nav ${scrolled ? "hp-nav--scrolled" : ""}`} role="navigation" aria-label="Main navigation">
        <div className="hp-nav-brand" onClick={() => scrollTo("hero")}>
          <div className="hp-emblem">
            <AshokaEmblem size={36} color={theme === "high-contrast" ? "#ffff00" : "#f97316"} />
          </div>
          <div className="hp-brand-text">
            <span className="hp-logo-text">MoTA<span className="hp-logo-accent"> SANKALP</span></span>
            <span className="hp-logo-sub">Ministry of Tribal Affairs</span>
          </div>
        </div>
        <div className="hp-nav-links">
          {NAV_LINKS.map((l) => (
            <button key={l.id} className={`hp-nav-link ${activeSection === l.id ? "active" : ""}`} onClick={() => scrollTo(l.id)}>
              {l.label}
            </button>
          ))}
        </div>
        <button className="hp-nav-login" onClick={() => navigate("/login")}>
          Officer Login →
        </button>
      </nav>

      {/* ─── HERO ─── */}
      <header className="hp-hero" id="hero">
        <div className="hp-hero-bg">
          <div className="hp-hero-orb hp-hero-orb--1" />
          <div className="hp-hero-orb hp-hero-orb--2" />
          <div className="hp-hero-grid" />
        </div>
        <div className="hp-hero-content">
          <div className="hp-hero-emblem">
            <AshokaEmblem size={64} color="rgba(255,255,255,0.8)" />
          </div>
          <div className="hp-hero-badge">Ministry of Tribal Affairs · Government of India</div>
          <h1 className="hp-hero-title">
            Scholarship Administration,<br />
            <span className="hp-hero-gradient">Reimagined with AI</span>
          </h1>
          <p className="hp-hero-sub">
            SANKALP — Scheme Administration, Network & Knowledge Automated Lifecycle Platform.
            AI-powered scrutiny for NFST and NOS scholarships that extracts, detects, compares, and explains.
          </p>
          <div className="hp-hero-actions">
            <button className="hp-btn-primary" onClick={() => scrollTo("idea")}>Explore the Platform</button>
            <button className="hp-btn-outline" onClick={() => navigate("/login")}>Officer Portal</button>
          </div>
        </div>
        <div className="hp-hero-scroll-hint">
          <span>Scroll to explore</span>
          <div className="hp-scroll-arrow" />
        </div>
      </header>

      {/* ─── STATS ─── */}
      <section className="hp-stats" ref={statsRef} aria-label="Key statistics">
        {STATS.map((s, i) => (
          <StatCard key={i} stat={s} inView={statsInView} />
        ))}
      </section>

      {/* ─── GOVERNMENT AGENCY LOGOS ─── */}
      <section className="hp-gov-strip" aria-label="Government partner agencies">
        <div className="hp-gov-strip-inner">
          {GOV_AGENCIES.map((a, i) => (
            <div className="hp-gov-logo" key={i}>
              <div className="hp-gov-logo-icon">
                <AshokaEmblem size={22} color={theme === "high-contrast" ? "#ffff00" : "#71717a"} />
              </div>
              <div className="hp-gov-logo-text">
                <strong>{a.name}</strong>
                <span>{a.sub}</span>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ─── MAIN CONTENT ─── */}
      <main id="main-content">

        {/* ─── THE IDEA ─── */}
        <section className={`hp-section hp-section--light ${ideaInView ? "hp-visible" : ""}`} id="idea" ref={ideaRef}>
          <div className="hp-section-inner">
            <div className="hp-section-header">
              <span className="hp-section-tag">The Vision</span>
              <h2 className="hp-section-title">The Idea Behind SANKALP</h2>
              <div className="hp-section-divider" />
            </div>
            <div className="hp-idea-grid">
              <div className="hp-idea-card">
                <div className="hp-idea-num">01</div>
                <h3>The Problem</h3>
                <p>Scholarship applications for tribal students under NFST and NOS are manually scrutinised, leading to months-long delays, human error, and inconsistent decision-making. Duplicate and fraudulent submissions go undetected.</p>
              </div>
              <div className="hp-idea-card">
                <div className="hp-idea-num">02</div>
                <h3>Our Approach</h3>
                <p>SANKALP digitises the entire lifecycle — from application intake through AI-powered document verification, policy rule checking, officer review, and PFMS disbursement. Every document is OCR-processed and cross-verified.</p>
              </div>
              <div className="hp-idea-card">
                <div className="hp-idea-num">03</div>
                <h3>The Outcome</h3>
                <p>Processing time reduced from 3–6 months to under 2 weeks. Officers receive AI-generated explanations for every flagged application, enabling faster, more transparent, and fairer decisions.</p>
              </div>
            </div>
          </div>
        </section>

        {/* ─── WHAT WE OFFER ─── */}
        <section className={`hp-section hp-section--subtle ${offerInView ? "hp-visible" : ""}`} id="offer" ref={offerRef}>
          <div className="hp-section-inner">
            <div className="hp-section-header">
              <span className="hp-section-tag">Capabilities</span>
              <h2 className="hp-section-title">What We Offer</h2>
              <div className="hp-section-divider" />
            </div>
            <div className="hp-offer-grid">
              {OFFERS.map((o, i) => (
                <div className="hp-offer-card" key={i} style={{ animationDelay: `${i * 0.1}s` }}>
                  <div className="hp-offer-icon">{o.icon}</div>
                  <h3>{o.title}</h3>
                  <p>{o.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ─── RESULTS ─── */}
        <section className={`hp-section hp-section--light ${resultsInView ? "hp-visible" : ""}`} id="results" ref={resultsRef}>
          <div className="hp-section-inner">
            <div className="hp-section-header">
              <span className="hp-section-tag">Impact & Data</span>
              <h2 className="hp-section-title">Results & Performance</h2>
              <div className="hp-section-divider" />
            </div>

            <div className="hp-table-block">
              <h3 className="hp-table-title">State-wise Scholarship Distribution</h3>
              <div className="hp-table-wrap">
                <table className="hp-table">
                  <thead>
                    <tr>
                      <th>State</th>
                      <th className="num">Applications</th>
                      <th className="num">Approved</th>
                      <th className="num">Rejected</th>
                      <th className="num">Pending</th>
                      <th className="num">Disbursed</th>
                    </tr>
                  </thead>
                  <tbody>
                    {RESULTS_STATE.map((r, i) => (
                      <tr key={i}>
                        <td>{r.state}</td>
                        <td className="num">{r.applications.toLocaleString("en-IN")}</td>
                        <td className="num hp-cell-good">{r.approved.toLocaleString("en-IN")}</td>
                        <td className="num hp-cell-bad">{r.rejected}</td>
                        <td className="num hp-cell-warn">{r.pending}</td>
                        <td className="num hp-cell-accent">{r.disbursed}</td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot>
                    <tr>
                      <td><strong>Total</strong></td>
                      <td className="num"><strong>{RESULTS_STATE.reduce((a, r) => a + r.applications, 0).toLocaleString("en-IN")}</strong></td>
                      <td className="num"><strong>{RESULTS_STATE.reduce((a, r) => a + r.approved, 0).toLocaleString("en-IN")}</strong></td>
                      <td className="num"><strong>{RESULTS_STATE.reduce((a, r) => a + r.rejected, 0)}</strong></td>
                      <td className="num"><strong>{RESULTS_STATE.reduce((a, r) => a + r.pending, 0)}</strong></td>
                      <td className="num"><strong>₹223 Cr</strong></td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            </div>

            <div className="hp-table-block">
              <h3 className="hp-table-title">Scheme-wise Performance Metrics</h3>
              <div className="hp-table-wrap">
                <table className="hp-table">
                  <thead>
                    <tr>
                      <th>Scheme</th>
                      <th className="num">Total Applications</th>
                      <th className="num">Approved</th>
                      <th className="num">Avg. Processing (Days)</th>
                      <th className="num">Satisfaction Rate</th>
                    </tr>
                  </thead>
                  <tbody>
                    {RESULTS_SCHEME.map((r, i) => (
                      <tr key={i}>
                        <td><strong>{r.scheme}</strong></td>
                        <td className="num">{r.total.toLocaleString("en-IN")}</td>
                        <td className="num hp-cell-good">{r.approved.toLocaleString("en-IN")}</td>
                        <td className="num">{r.avgDays}</td>
                        <td className="num hp-cell-accent">{r.satisfaction}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="hp-metrics-row">
              <div className="hp-metric">
                <div className="hp-metric-bar"><div className="hp-metric-fill" style={{ width: "94%" }} /></div>
                <span className="hp-metric-label">94% On-time Disbursement</span>
              </div>
              <div className="hp-metric">
                <div className="hp-metric-bar"><div className="hp-metric-fill hp-metric-fill--green" style={{ width: "98%" }} /></div>
                <span className="hp-metric-label">98.7% Verification Accuracy</span>
              </div>
              <div className="hp-metric">
                <div className="hp-metric-bar"><div className="hp-metric-fill hp-metric-fill--amber" style={{ width: "87%" }} /></div>
                <span className="hp-metric-label">87% Reduction in Processing Time</span>
              </div>
            </div>
          </div>
        </section>

        {/* ─── TEAM ─── */}
        <section className={`hp-section hp-section--dark ${teamInView ? "hp-visible" : ""}`} id="team" ref={teamRef}>
          <div className="hp-section-inner">
            <div className="hp-section-header hp-section-header--light">
              <span className="hp-section-tag">Our People</span>
              <h2 className="hp-section-title">Meet the Team</h2>
              <div className="hp-section-divider" />
            </div>
            <div className="hp-team-grid">
              {TEAM.map((m, i) => (
                <div className="hp-team-card" key={i} style={{ animationDelay: `${i * 0.1}s` }}>
                  <div className="hp-team-photo-wrap">
                    <img src={m.photo} alt={m.name} className="hp-team-photo" loading="lazy" />
                  </div>
                  <h3 className="hp-team-name">{m.name}</h3>
                  <span className="hp-team-role">{m.role}</span>
                  <p className="hp-team-bio">{m.bio}</p>
                </div>
              ))}
            </div>
          </div>
        </section>
      </main>

      {/* ─── FOOTER ─── */}
      <footer className="hp-footer" role="contentinfo">
        <div className="hp-footer-inner">
          <div className="hp-footer-brand">
            <div className="hp-footer-logo">
              <AshokaEmblem size={28} color="#f97316" />
              <span className="hp-logo-text hp-logo-text--sm">MoTA<span className="hp-logo-accent"> SANKALP</span></span>
            </div>
            <p className="hp-footer-desc">
              Scheme Administration, Network & Knowledge Automated Lifecycle Platform.
              A project under the Ministry of Tribal Affairs, Government of India.
            </p>
          </div>
          <div className="hp-footer-links">
            <h4>Quick Links</h4>
            <a href="#idea" onClick={(e) => { e.preventDefault(); scrollTo("idea"); }}>The Idea</a>
            <a href="#offer" onClick={(e) => { e.preventDefault(); scrollTo("offer"); }}>What We Offer</a>
            <a href="#results" onClick={(e) => { e.preventDefault(); scrollTo("results"); }}>Results</a>
            <a href="#team" onClick={(e) => { e.preventDefault(); scrollTo("team"); }}>Team</a>
          </div>
          <div className="hp-footer-links">
            <h4>Resources</h4>
            <a href="https://tribal.nic.in" target="_blank" rel="noreferrer">MoTA Official Site</a>
            <a href="https://scholarships.gov.in" target="_blank" rel="noreferrer">National Scholarship Portal</a>
            <a href="https://pfms.nic.in" target="_blank" rel="noreferrer">PFMS Portal</a>
            <a href="https://digilocker.gov.in" target="_blank" rel="noreferrer">DigiLocker</a>
          </div>
          <div className="hp-footer-links">
            <h4>Contact</h4>
            <span>Ministry of Tribal Affairs</span>
            <span>Shastri Bhawan, New Delhi – 110001</span>
            <span>sankalp@tribal.gov.in</span>
            <span>+91 11 2338 1141</span>
          </div>
        </div>

        {/* Gov agency strip in footer */}
        <div className="hp-footer-agencies">
          {GOV_AGENCIES.map((a, i) => (
            <div className="hp-footer-agency" key={i}>
              <AshokaEmblem size={16} color="#71717a" />
              <span>{a.name}</span>
            </div>
          ))}
        </div>

        <div className="hp-footer-bottom">
          <div className="hp-tricolor" />
          <p>© {new Date().getFullYear()} Ministry of Tribal Affairs, Government of India. All rights reserved. | Built with ❤️ for Digital India</p>
        </div>
      </footer>
    </div>
  );
}
