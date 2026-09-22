import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, openProtectedFile } from "../api.js";
import Badge from "../components/Badge.jsx";
import Section from "../components/Section.jsx";

const DOC_TYPES = ["ST_CERTIFICATE", "INCOME_CERTIFICATE", "MARKSHEET", "ADMISSION_LETTER", "ID_PROOF", "OTHER"];
const DET_LABELS = {
  official_seal: "Official seal", signature: "Signature", qr_code: "QR code",
  income_field: "Income field", st_certificate_field: "ST certificate field",
};
const FINAL = ["APPROVED", "REJECTED", "SANCTIONED", "PAID"];

function money(v) {
  return "Rs " + Number(v || 0).toLocaleString("en-IN");
}

function Json({ value }) {
  return <pre className="json">{JSON.stringify(value, null, 2)}</pre>;
}

export default function ApplicationDetail() {
  const { id } = useParams();
  const [d, setD] = useState(null);
  const [audit, setAudit] = useState([]);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [msg, setMsg] = useState("");
  const [reason, setReason] = useState("");
  const [docType, setDocType] = useState("ST_CERTIFICATE");
  const [file, setFile] = useState(null);
  const [locker, setLocker] = useState(null);

  async function load() {
    try {
      const [detail, a] = await Promise.all([api.getApplication(id), api.audit(id)]);
      setD(detail);
      setAudit(a);
    } catch (e) {
      setError(e.message);
    }
  }
  useEffect(() => { load(); }, [id]);

  async function run(label, fn, success) {
    setBusy(label);
    setError("");
    setMsg("");
    try {
      const r = await fn();
      if (success) setMsg(typeof success === "function" ? success(r) : success);
      await load();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy("");
    }
  }

  if (!d) return error ? <div className="error">{error}</div> : <div className="loading">Loading application...</div>;

  const a = d.application;
  const risk = Object.fromEntries(d.risk_results.map((r) => [r.check_type, r]));
  const scrutinized = d.rule_results.length > 0;
  const needReason = (fn) => () => {
    if (reason.trim().length < 3) { setError("Enter a reason (min 3 characters) before taking an officer action."); return; }
    fn();
  };

  return (
    <div className="detail">
      <div className="page-head">
        <div>
          <div className="kicker"><Link to="/applications">Applications</Link> / {a.application_number}</div>
          <h1>{a.full_name}</h1>
          <div className="row-gap">
            <Badge value={a.status} /> <Badge value={a.risk_level} /> <Badge value={a.ai_recommendation} />
            <span className="muted tiny">Scheme {a.scheme_id} | Source {a.source}</span>
          </div>
        </div>
        <div className="actions-bar">
          <button className="btn primary" disabled={!!busy || FINAL.includes(a.status)}
            onClick={() => run("scrutiny", () => api.runScrutiny(id), (r) => `Scrutiny complete: ${r.ai_recommendation}, ${r.discrepancies.length} discrepancies`)}>
            {busy === "scrutiny" ? "Running AI pipeline..." : "Run Scrutiny"}
          </button>
        </div>
      </div>

      {msg && <div className="notice">{msg}</div>}
      {error && <div className="error">{error}</div>}

      <div className="pipeline">
        {["Docs", "OCR", "Extract", "Detect", "Fuzzy", "pHash", "IForest", "Rules", "Twin", "Officer", "Sanction", "PFMS"].map((s, i) => {
          const done = (i < 9 && scrutinized) || (i === 9 && d.officer_actions.length) || (i === 10 && d.sanction) || (i === 11 && d.payment) || (i === 0 && d.documents.length);
          return <span key={s} className={"step" + (done ? " done" : "")}>{s}</span>;
        })}
      </div>

      <Section n={1} title="Applicant details">
        <div className="kv">
          {[["Applicant ID", a.applicant_id], ["Gender", a.gender], ["Category", a.category], ["Tribe", a.tribe],
            ["PVTG", a.is_pvtg ? "Yes" : "No"], ["State", a.state], ["Age", a.age], ["Course", a.course],
            ["Institution", a.institution], ["Annual income", money(a.annual_income)], ["Marks", a.marks_percentage + "%"],
            ["Claimed amount", money(a.claimed_fee)], ["Merit score", a.eligibility_score ?? "-"], ["Email", a.email]]
            .map(([k, v]) => <div key={k}><span>{k}</span><strong>{v ?? "-"}</strong></div>)}
        </div>
        <div className="row-gap" style={{ marginTop: 12 }}>
          <button className="btn ghost small" onClick={() => api.digilocker(a.applicant_id).then(setLocker).catch((e) => setError(e.message))}>
            Check DigiLocker (mock)
          </button>
        </div>
        {locker && (
          <table className="compact">
            <thead><tr><th>DigiLocker document</th><th>Issuer</th><th>Issued</th><th>Verified</th></tr></thead>
            <tbody>{locker.documents.map((x) => <tr key={x.doc_type}><td>{x.doc_type}</td><td>{x.issuer}</td><td>{x.issued_on}</td><td><Badge value={x.verified ? "PASS" : "FAIL"} /></td></tr>)}</tbody>
          </table>
        )}
      </Section>

      <Section n={2} title="Documents" hint="PNG / JPG / PDF, max 5 MB. Stored in backend/uploads/{application_id}/">
        <table className="compact">
          <thead><tr><th>#</th><th>Type</th><th>File</th><th>pHash</th><th>OCR engine</th><th /></tr></thead>
          <tbody>
            {d.documents.map((doc) => (
              <tr key={doc.id}>
                <td className="mono">{doc.id}</td><td>{doc.doc_type}</td><td>{doc.filename}</td>
                <td className="mono tiny">{doc.phash || "-"}</td><td>{doc.ocr_engine || "not processed"}</td>
                <td><button className="btn small ghost" onClick={() => openProtectedFile(doc.download_url).catch((e) => setError(e.message))}>View</button></td>
              </tr>
            ))}
            {d.documents.length === 0 && <tr><td colSpan={6} className="muted">No documents yet.</td></tr>}
          </tbody>
        </table>
        {!FINAL.includes(a.status) && (
          <div className="upload">
            <select value={docType} onChange={(e) => setDocType(e.target.value)}>{DOC_TYPES.map((t) => <option key={t}>{t}</option>)}</select>
            <input type="file" accept=".png,.jpg,.jpeg,.pdf" onChange={(e) => setFile(e.target.files[0])} />
            <button className="btn" disabled={!file || !!busy}
              onClick={() => run("upload", () => api.uploadDocument(id, docType, file), `${docType} uploaded`)}>Upload</button>
          </div>
        )}
      </Section>

      {!scrutinized && (
        <div className="panel empty-state">Scrutiny has not been run yet. Upload documents if needed, then click <b>Run Scrutiny</b>.</div>
      )}

      {scrutinized && (
        <>
          <Section n={3} title="OCR results & field extraction" hint="EasyOCR when installed; otherwise demo fallback reads the synthetic text layer">
            <div className="doc-grid">
              {d.documents.map((doc) => (
                <div key={doc.id} className="doc-card">
                  <div className="doc-card-head"><strong>{doc.doc_type}</strong><span className="tiny muted">{doc.ocr_engine} | conf {doc.ocr_confidence}</span></div>
                  <pre className="ocr">{doc.ocr_text || "(no text)"}</pre>
                  <table className="compact">
                    <tbody>{Object.entries(doc.extracted_fields || {}).map(([k, v]) => <tr key={k}><td className="muted">{k}</td><td><strong>{String(v)}</strong></td></tr>)}</tbody>
                  </table>
                </div>
              ))}
            </div>
          </Section>

          <Section n={4} title="YOLO document visual detection" hint="REAL_MODEL = YOLOv8n fine-tuned on real data (backend/models/document_detector.pt); otherwise DEMO_FALLBACK heuristics. Each cell shows its source.">
            <table className="compact">
              <thead><tr><th>Document</th><th>Mode</th>{Object.values(DET_LABELS).map((l) => <th key={l}>{l}</th>)}</tr></thead>
              <tbody>
                {d.documents.map((doc) => {
                  const det = (doc.detection || {}).detections || {};
                  return (
                    <tr key={doc.id}>
                      <td>{doc.doc_type}</td><td><Badge value={(doc.detection || {}).mode} /></td>
                      {Object.keys(DET_LABELS).map((k) => (
                        <td key={k}>
                          {det[k] && det[k].detected ? <span className="yes">Yes {det[k].confidence}</span> : <span className="no">No</span>}
                          {det[k] && det[k].source && <div className="tiny muted">{det[k].source}</div>}
                        </td>
                      ))}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </Section>

          <Section n={5} title="Rule evaluation" hint="Deterministic policy from configs/schemes/*.yaml (demo values)">
            <table className="compact">
              <thead><tr><th>Rule</th><th>Actual</th><th>Expected</th><th>Result</th><th>Reason</th></tr></thead>
              <tbody>{d.rule_results.map((r) => (
                <tr key={r.id}><td className="mono">{r.rule_id}</td><td>{r.actual_value}</td><td>{r.expected}</td>
                  <td><Badge value={r.passed ? "PASS" : "FAIL"} /></td><td>{r.reason}</td></tr>
              ))}</tbody>
            </table>
          </Section>

          <div className="grid3">
            <Section n={6} title="Entity matching" hint="RapidFuzz">
              {risk.NAME_MATCH && (risk.NAME_MATCH.details.comparisons || []).map((c) => (
                <div key={c.document_id} className="mini">
                  <div className="tiny muted">{c.doc_type}</div>
                  <div>{c.name_a} vs <b>{c.name_b}</b></div>
                  <div className="row-gap"><span className="big">{c.similarity}</span><Badge value={c.interpretation} /></div>
                  {c.initials_consistent && <div className="tiny">Initials consistent</div>}
                </div>
              ))}
            </Section>
            <Section n={7} title="Duplicate check" hint="pHash Hamming distance vs earlier documents">
              {risk.DUPLICATE && (risk.DUPLICATE.details.per_document || []).map((p) => (
                <div key={p.doc_type} className="mini">
                  <div className="row-gap"><b>{p.doc_type}</b><Badge value={p.possible_duplicate ? "FLAG" : "PASS"} /></div>
                  {(p.nearest || []).slice(0, 2).map((m) => (
                    <div key={m.document_id} className="tiny">doc #{m.document_id} (app #{m.application_id}) - distance {m.hamming_distance}</div>
                  ))}
                </div>
              ))}
              <div className="tiny muted">Near-identical images need verification; not proof of fraud.</div>
            </Section>
            <Section n={8} title="Anomaly check" hint="Isolation Forest">
              {risk.ANOMALY && (
                <div className="mini">
                  <div className="row-gap"><Badge value={risk.ANOMALY.details.label} /><span className="big">{risk.ANOMALY.details.anomaly_score}</span></div>
                  <div className="tiny muted">negative = more unusual</div>
                  {risk.ANOMALY.details.top_deviations.map((t) => (
                    <div key={t.feature} className="tiny">{t.feature}: {Number(t.value).toLocaleString("en-IN")} ({t.z_score > 0 ? "+" : ""}{t.z_score} SD)</div>
                  ))}
                </div>
              )}
            </Section>
          </div>

          <Section n={9} title="Discrepancies & MoTA-Twin resolution" hint="Deterministic agent proposes; officer reviews every proposal">
            {d.discrepancies.length === 0 && <div className="notice">No discrepancies. AI recommendation: approve.</div>}
            {d.discrepancies.map((x) => (
              <div key={x.id} className="twin">
                <div className="twin-issue">
                  <div className="row-gap"><span className="mono">{x.issue_type}</span><Badge value={x.severity} /></div>
                  <p>{x.description}</p>
                </div>
                {x.resolution && (
                  <div className="twin-res">
                    <div className="kicker">MoTA-Twin proposal | confidence {x.resolution.confidence} | officer review required</div>
                    <p><b>{x.resolution.proposed_resolution}</b></p>
                    <ol>{(x.resolution.reasoning.steps || []).map((s, i) => <li key={i}>{s}</li>)}</ol>
                    <div className="tiny muted">Recommended action: {x.resolution.reasoning.recommended_action}</div>
                  </div>
                )}
              </div>
            ))}
          </Section>
        </>
      )}

      <Section n={10} title="Officer actions" hint="Final decision is always the officer's. Reason is mandatory and audited.">
        {d.officer_actions.map((o) => (
          <div key={o.id} className="mini">
            <Badge value={o.action === "APPROVE" ? "APPROVED" : o.action === "REJECT" ? "REJECTED" : "MANUAL_REVIEW"} /> by {o.officer_email}: {o.reason}
            {o.overrode_ai && <span className="tag warn-tag">overrode AI ({o.ai_recommendation_at_decision})</span>}
          </div>
        ))}
        {!FINAL.includes(a.status) && (
          <>
            <textarea placeholder="Reason for decision (required)" value={reason} onChange={(e) => setReason(e.target.value)} />
            <div className="row-gap">
              <button className="btn good" disabled={!!busy || !scrutinized} onClick={needReason(() => run("approve", () => api.approve(id, reason), "Approved"))}>Approve</button>
              <button className="btn bad" disabled={!!busy || !scrutinized} onClick={needReason(() => run("reject", () => api.reject(id, reason), "Rejected"))}>Reject</button>
              <button className="btn ghost" disabled={!!busy} onClick={needReason(() => run("manual", () => api.manualReview(id, reason), "Sent to manual review"))}>Manual Review</button>
            </div>
          </>
        )}
      </Section>

      <div className="grid2">
        <Section n={11} title="Sanction">
          {d.sanction ? (
            <div className="mini">
              <div className="mono">{d.sanction.sanction_number}</div>
              <div className="big">{money(d.sanction.amount)}</div>
              <div className="tiny muted">{new Date(d.sanction.sanction_date).toLocaleString()} | {d.sanction.officer_email}</div>
              <button className="btn small" onClick={() => openProtectedFile(d.sanction.pdf_url).catch((e) => setError(e.message))}>Open sanction PDF</button>
            </div>
          ) : (
            <button className="btn primary" disabled={a.status !== "APPROVED" || !!busy}
              onClick={() => run("sanction", () => api.sanction(id), (r) => `Sanction ${r.sanction_number} generated`)}>Generate Sanction</button>
          )}
        </Section>
        <Section n={12} title="Payment (PFMS mock)">
          {d.payment ? (
            <div className="mini">
              <Badge value={d.payment.status} /> <span className="mono">{d.payment.payment_reference}</span>
              <div className="big">{money(d.payment.amount)}</div>
              <Json value={d.payment.response} />
            </div>
          ) : (
            <button className="btn primary" disabled={!d.sanction || !!busy}
              onClick={() => run("pay", () => api.pay(d.sanction.id), (r) => `PFMS: ${r.payment_reference} ${r.status}`)}>Send Payment</button>
          )}
        </Section>
      </div>

      <Section n={13} title="Audit timeline" hint="Every AI and human step is logged">
        <ol className="timeline">
          {audit.map((e) => (
            <li key={e.id}>
              <div className="t-dot" />
              <div>
                <div><span className="mono">{e.action}</span> <span className="muted">by {e.actor}</span></div>
                <div className="tiny muted">{new Date(e.created_at).toLocaleString()}</div>
                {e.details && Object.keys(e.details).length > 0 && (
                  <div className="tiny">{Object.entries(e.details).map(([k, v]) => `${k}: ${typeof v === "object" ? JSON.stringify(v) : v}`).join(" | ")}</div>
                )}
              </div>
            </li>
          ))}
        </ol>
      </Section>
    </div>
  );
}
