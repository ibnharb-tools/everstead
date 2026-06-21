import { mockAssessment, mockMarketplace } from '../mock/mockData';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const delay = (ms = 700) => new Promise((r) => setTimeout(r, ms));

async function req(path, { method = 'GET', body, token } = {}) {
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(`${API}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  let data = {};
  try {
    data = await res.json();
  } catch {
    data = {};
  }
  if (!res.ok) {
    const err = data && data.error ? data.error : { message: 'Something went wrong. Please try again.' };
    throw { ...err, status: res.status };
  }
  return data;
}

export const everstead = {
  // --- Assessment + marketplace come from the local mock (engine built separately) ---
  async assess(_inputs) {
    await delay(1400);
    return JSON.parse(JSON.stringify(mockAssessment));
  },
  async marketplace(_technology) {
    await delay(400);
    return mockMarketplace;
  },

  // --- Auth (real backend) ---
  signup: (name, email, password) => req('/auth/signup', { method: 'POST', body: { name, email, password } }),
  login: (email, password) => req('/auth/login', { method: 'POST', body: { email, password } }),
  me: (token) => req('/auth/me', { token }),
  forgotPassword: (email) => req('/auth/forgot-password', { method: 'POST', body: { email } }),
  oauth: (provider) => req('/auth/oauth', { method: 'POST', body: { provider } }),

  // --- Saved homes (real backend, scoped to user) ---
  listRetrofits: (token) => req('/retrofits', { token }),
  getRetrofit: (id, token) => req(`/retrofits/${id}`, { token }),
  saveRetrofit: (assessment, label, token) =>
    req('/retrofits', { method: 'POST', body: { assessment, label }, token }),
  deleteRetrofit: (id, token) => req(`/retrofits/${id}`, { method: 'DELETE', token }),
};
