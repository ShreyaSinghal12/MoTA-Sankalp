const TONES = {
  RECEIVED: "neutral", UNDER_SCRUTINY: "info", SCRUTINY_COMPLETED: "good", AI_FLAGGED: "warn",
  MANUAL_REVIEW: "warn", APPROVED: "good", REJECTED: "bad", SANCTIONED: "good", PAID: "good",
  LOW: "good", MEDIUM: "warn", HIGH: "bad", NOT_ASSESSED: "neutral",
  PASS: "good", FAIL: "bad", REVIEW: "warn", FLAG: "bad",
  RECOMMEND_APPROVE: "good", RECOMMEND_REJECT: "bad", NEEDS_OFFICER_REVIEW: "warn",
  REAL_MODEL: "good", DEMO_FALLBACK: "info", NORMAL: "good", NEEDS_REVIEW: "warn",
  MATCH: "good", PROBABLE_MATCH_REVIEW: "warn", MISMATCH: "bad",
};

export default function Badge({ value }) {
  if (value === null || value === undefined || value === "") return <span className="badge neutral">-</span>;
  const v = String(value);
  return <span className={"badge " + (TONES[v] || "neutral")}>{v.replaceAll("_", " ")}</span>;
}
