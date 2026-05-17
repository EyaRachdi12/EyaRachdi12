"use client";
import { createContext, useContext, useState, useEffect, ReactNode } from "react";

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

interface UserContextValue {
  user:    User | null;
  loading: boolean;
  setUser: (user: User | null) => void;
  logout:  () => void;
}

const UserContext = createContext<UserContextValue>({
  user:    null,
  loading: true,
  setUser: () => {},
  logout:  () => {},
});

export function UserProvider({ children }: { children: ReactNode }) {
  const [user,    setUserState] = useState<User | null>(null);
  const [loading, setLoading]   = useState(true);

  useEffect(() => {
    try {
      const stored = localStorage.getItem("archi_user");
      if (stored) setUserState(JSON.parse(stored));
    } catch {}
    setLoading(false);
  }, []);

  const setUser = (u: User | null) => {
    setUserState(u);
    if (u) {
      localStorage.setItem("archi_user", JSON.stringify(u));
    } else {
      localStorage.removeItem("archi_user");
    }
  };

  const logout = () => {
    localStorage.removeItem("archi_user");
    setUserState(null);
    window.location.href = "/auth/login";
  };

  return (
    <UserContext.Provider value={{ user, loading, setUser, logout }}>
      {children}
    </UserContext.Provider>
  );
}

export function useUserContext(): UserContextValue {
  return useContext(UserContext);
}
