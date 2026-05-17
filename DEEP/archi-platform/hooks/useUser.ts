"use client";
import { useState, useEffect } from "react";

export interface User {
  id:            string;
  name:          string;
  email:         string;
  role:          "architect" | "client";
  avatar:        string;
  city?:         string;
  specialty?:    string;
  project_type?: string;
  created_at?:   string;
  token?:        string;
}

export function useUser() {
  const [user, setUserState] = useState<User | null>(null);

  useEffect(() => {
    try {
      const stored = localStorage.getItem("archi_user");
      if (stored) setUserState(JSON.parse(stored));
    } catch {}
  }, []);

  const setUser = (u: User | null) => {
    setUserState(u);
    if (u) localStorage.setItem("archi_user", JSON.stringify(u));
    else localStorage.removeItem("archi_user");
  };

  const logout = () => {
    localStorage.removeItem("archi_user");
    setUserState(null);
    window.location.href = "/auth/login";
  };

  return { user, setUser, logout };
}
