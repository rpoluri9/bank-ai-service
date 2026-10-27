// API helpers for the Bank AI Platform.
// Banking API (Spring Boot, :8080) is protected by HTTP Basic auth (local
// demo user — see the project README "Demo auth"). The AI service (:8081)
// has no auth of its own. Base URLs can be overridden with Vite env vars:
//   VITE_BANKING_URL, VITE_AI_URL

const BANKING_URL = import.meta.env.VITE_BANKING_URL || "http://localhost:8080";
const AI_URL = import.meta.env.VITE_AI_URL || "http://localhost:8081";

function authHeader(auth) {
  if (!auth || !auth.username) return {};
  return { Authorization: "Basic " + btoa(auth.username + ":" + auth.password) };
}

async function request(base, path, auth, options = {}) {
  const res = await fetch(base + path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...authHeader(auth),
      ...(options.headers || {}),
    },
  });
  const text = await res.text();
  let body = null;
  try {
    body = text ? JSON.parse(text) : null;
  } catch {
    body = { message: text };
  }
  if (!res.ok) {
    const err = new Error((body && body.message) || `Request failed (${res.status})`);
    err.status = res.status;
    throw err;
  }
  return body;
}

export const bankingApi = {
  listAccounts: (auth) => request(BANKING_URL, "/api/accounts", auth),
  getAccount: (auth, id) => request(BANKING_URL, `/api/accounts/${id}`, auth),
  createAccount: (auth, data) =>
    request(BANKING_URL, "/api/accounts", auth, {
      method: "POST",
      body: JSON.stringify(data),
    }),
  deposit: (auth, id, data) =>
    request(BANKING_URL, `/api/accounts/${id}/deposit`, auth, {
      method: "POST",
      body: JSON.stringify(data),
    }),
  withdraw: (auth, id, data) =>
    request(BANKING_URL, `/api/accounts/${id}/withdraw`, auth, {
      method: "POST",
      body: JSON.stringify(data),
    }),
  transfer: (auth, id, data) =>
    request(BANKING_URL, `/api/accounts/${id}/transfer`, auth, {
      method: "POST",
      body: JSON.stringify(data),
    }),
  transactions: (auth, id) =>
    request(BANKING_URL, `/api/accounts/${id}/transactions`, auth),
};

export const aiApi = {
  ask: (question, accountId) =>
    request(
      AI_URL,
      "/api/ask",
      null,
      {
        method: "POST",
        body: JSON.stringify({ question, account_id: accountId || undefined }),
      }
    ),
  health: () => request(AI_URL, "/api/health", null),
};
