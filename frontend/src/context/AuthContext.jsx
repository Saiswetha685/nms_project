import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('sla_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState(() => localStorage.getItem('sla_token') || null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function checkAuth() {
      if (token) {
        try {
          const res = await api.get('/auth/me');
          setUser(res.data);
          localStorage.setItem('sla_user', JSON.stringify(res.data));
        } catch {
          setUser(null);
          setToken(null);
          localStorage.removeItem('sla_token');
          localStorage.removeItem('sla_user');
        }
      }
      setLoading(false);
    }
    checkAuth();
  }, [token]);

  const login = async (email, password) => {
    const res = await api.post('/auth/login', { email, password });
    const { access_token, user: loggedUser } = res.data;
    setToken(access_token);
    setUser(loggedUser);
    localStorage.setItem('sla_token', access_token);
    localStorage.setItem('sla_user', JSON.stringify(loggedUser));
    return loggedUser;
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('sla_token');
    localStorage.removeItem('sla_user');
  };

  const value = {
    user,
    token,
    isAuthenticated: !!token && !!user,
    isAdmin: user?.role === 'admin',
    isOperator: user?.role === 'operator' || user?.role === 'admin',
    login,
    logout,
    loading
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider');
  return ctx;
}
