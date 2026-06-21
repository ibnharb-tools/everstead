import React, { createContext, useContext, useEffect, useState } from 'react';
import { everstead } from '../api/everstead';

const AuthContext = createContext(null);
const TOKEN_KEY = 'everstead_token';

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY));
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    (async () => {
      const stored = localStorage.getItem(TOKEN_KEY);
      if (stored) {
        try {
          const { user: u } = await everstead.me(stored);
          if (active) setUser(u);
        } catch {
          localStorage.removeItem(TOKEN_KEY);
          if (active) setToken(null);
        }
      }
      if (active) setLoading(false);
    })();
    return () => {
      active = false;
    };
  }, []);

  const login = async (email, password) => {
    const { token: t, user: u } = await everstead.login(email, password);
    localStorage.setItem(TOKEN_KEY, t);
    setToken(t);
    setUser(u);
    return u;
  };

  const signup = async (name, email, password) => {
    const { token: t, user: u } = await everstead.signup(name, email, password);
    localStorage.setItem(TOKEN_KEY, t);
    setToken(t);
    setUser(u);
    return u;
  };

  const logout = () => {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ token, user, loading, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
