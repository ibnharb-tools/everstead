const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

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
  // --- Assessment + marketplace (real backend) ---
  assess: (inputs) => req('/assess', { method: 'POST', body: inputs }),
  marketplace: (technology) => req(`/marketplace/${technology}`),

  // --- Auth ---
  signup: (name, email, password) => req('/auth/signup', { method: 'POST', body: { name, email, password } }),
  login: (email, password) => req('/auth/login', { method: 'POST', body: { email, password } }),
  me: (token) => req('/auth/me', { token }),
  forgotPassword: (email) => req('/auth/forgot-password', { method: 'POST', body: { email } }),
  oauth: (provider) => req('/auth/oauth', { method: 'POST', body: { provider } }),

  // --- Saved homes (scoped to user) ---
  listRetrofits: (token) => req('/retrofits', { token }),
  getRetrofit: (id, token) => req(`/retrofits/${id}`, { token }),
  saveRetrofit: (assessment, label, token) =>
    req('/retrofits', { method: 'POST', body: { assessment, label }, token }),
  deleteRetrofit: (id, token) => req(`/retrofits/${id}`, { method: 'DELETE', token }),
};
