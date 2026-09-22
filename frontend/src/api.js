export const API_BASE = "http://127.0.0.1:8000/api/v1";
export const API_ROOT = "http://127.0.0.1:8000";

export function getToken() {
  return localStorage.getItem("mota_token");
}

export function getUser() {
  try {
    return JSON.parse(localStorage.getItem("mota_user") || "null");
  } catch {
    return null;
  }
}

export function logout() {
  localStorage.removeItem("mota_token");
  localStorage.removeItem("mota_user");
  window.location.href = "/login";
}

async function request(path, { method = "GET", body, form } = {}) {
  const headers = {};
  const token = getToken();
  if (token) headers.Authorization = "Bearer " + token;
  let payload;
  if (form) payload = form;
  else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }
  const res = await fetch(API_BASE + path, { method, headers, body: payload });
  if (res.status === 401 && !path.startsWith("/auth/login")) {
    logout();
    throw new Error("Session expired");
  }
  const text = await res.text();
  const data = text ? JSON.parse(text) : null;
  if (!res.ok) {
    const detail = data && data.detail;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail || data));
  }
  return data;
}

export async function login(email, password) {
  const data = await request("/auth/login", { method: "POST", body: { email, password } });
  localStorage.setItem("mota_token", data.access_token);
  localStorage.setItem("mota_user", JSON.stringify(data.user));
  return data;
}

export async function openProtectedFile(url) {
  // url is an absolute API path like /api/v1/sanctions/1/pdf
  const res = await fetch(API_ROOT + url, { headers: { Authorization: "Bearer " + getToken() } });
  if (!res.ok) throw new Error("Could not open file");
  const blob = await res.blob();
  window.open(URL.createObjectURL(blob), "_blank");
}

export const api = {
  stats: () => request("/dashboard/stats"),
  schemes: () => request("/schemes"),
  listApplications: (params = {}) => {
    const qs = new URLSearchParams(Object.entries(params).filter(([, v]) => v)).toString();
    return request("/applications" + (qs ? "?" + qs : ""));
  },
  getApplication: (id) => request(`/applications/${id}`),
  createApplication: (body) => request("/applications", { method: "POST", body }),
  uploadDocument: (id, docType, file) => {
    const form = new FormData();
    form.append("doc_type", docType);
    form.append("file", file);
    return request(`/applications/${id}/documents`, { method: "POST", form });
  },
  runScrutiny: (id) => request(`/applications/${id}/scrutiny`, { method: "POST" }),
  approve: (id, reason) => request(`/applications/${id}/approve`, { method: "POST", body: { reason } }),
  reject: (id, reason) => request(`/applications/${id}/reject`, { method: "POST", body: { reason } }),
  manualReview: (id, reason) => request(`/applications/${id}/manual-review`, { method: "POST", body: { reason } }),
  sanction: (id) => request(`/applications/${id}/sanction`, { method: "POST" }),
  pay: (sanctionId) => request(`/sanctions/${sanctionId}/payment`, { method: "POST" }),
  audit: (id) => request(`/applications/${id}/audit`),
  nspImport: (count = 2) => request("/integrations/nsp/import", { method: "POST", body: { count } }),
  nspSync: () => request("/integrations/nsp/status-sync", { method: "POST" }),
  digilocker: (applicantId) => request(`/integrations/digilocker/${applicantId}`),
};
