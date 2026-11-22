import { clearAuthentication, getAccessToken } from "../auth/cognito";

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function requestJson(path, options = {}) {
  const token = await getAccessToken();
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
  });

  let data = {};
  try {
    data = await response.json();
  } catch {
    data = {};
  }

  if (!response.ok) {
    if (response.status === 401 || response.status === 403) await clearAuthentication();
    const message = data?.detail || "Request failed";
    throw new Error(message);
  }

  return data;
}
export function getJson(path) {
  return requestJson(path);
}

export function postJson(path, body) {
  return requestJson(path, { method: "POST", body: JSON.stringify(body) });
}
