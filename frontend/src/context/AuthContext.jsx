import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import api from '../api/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => localStorage.getItem('sif_token'));
  const [isLoading, setIsLoading] = useState(true);

  // On app load, if a token exists in localStorage, verify it against
  // /auth/me so a stale/expired token doesn't silently render the app
  // as "logged in" with no actual user data.
  const rehydrate = useCallback(async () => {
    const storedToken = localStorage.getItem('sif_token');
    if (!storedToken) {
      setIsLoading(false);
      return;
    }
    try {
      const res = await api.get('/auth/me');
      setUser(res.data);
      setToken(storedToken);
    } catch (err) {
      localStorage.removeItem('sif_token');
      setUser(null);
      setToken(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    rehydrate();
  }, [rehydrate]);

  const applyAuthResult = (data) => {
    localStorage.setItem('sif_token', data.access_token);
    setToken(data.access_token);
    setUser({
      user_id: data.user_id,
      name: data.name,
      email: data.email,
      role: data.role,
    });
  };

  const login = async (email, password) => {
    const res = await api.post('/auth/login', { email, password });
    applyAuthResult(res.data);
    return res.data;
  };

  const register = async (name, email, password, role) => {
    const res = await api.post('/auth/register', { name, email, password, role });
    applyAuthResult(res.data);
    return res.data;
  };

  const logout = () => {
    localStorage.removeItem('sif_token');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return ctx;
}