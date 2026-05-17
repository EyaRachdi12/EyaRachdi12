"use client";
import { useState } from "react";
import Link from "next/link";
import ThemeToggle from "@/components/ThemeToggle";

export default function LoginPage() {
  const [role, setRole] = useState<"architect" | "client">("architect");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${API_URL}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, role }),
      });

      if (!res.ok) {
        const err = await res.json();
        alert(err.detail || "Email ou mot de passe incorrect");
        setLoading(false);
        return;
      }

      const user = await res.json();
      localStorage.setItem("archi_user", JSON.stringify(user));
      window.location.href = role === "architect" ? "/architect/dashboard" : "/client/dashboard";
    } catch {
      // Fallback for demo
      window.location.href = role === "architect" ? "/architect/dashboard" : "/client/dashboard";
    }
  };

  return (
    <div style={{
      minHeight: "100vh",
      display: "flex",
      background: "var(--bg)",
    }}>
      {/* Left panel — decorative */}
      <div style={{
        flex: 1,
        background: "linear-gradient(135deg, #1a1714 0%, #2a2318 50%, #1a1714 100%)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: 48,
        position: "relative",
        overflow: "hidden",
      }} className="hidden-mobile">
        {/* Grid */}
        <div style={{
          position: "absolute",
          inset: 0,
          backgroundImage: `linear-gradient(rgba(201,169,110,0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(201,169,110,0.08) 1px, transparent 1px)`,
          backgroundSize: "40px 40px",
        }} />

        {/* Floating plan mockup */}
        <div className="animate-float" style={{
          position: "relative",
          width: 320,
          height: 320,
          background: "rgba(201,169,110,0.05)",
          border: "1px solid rgba(201,169,110,0.2)",
          borderRadius: 20,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          marginBottom: 40,
        }}>
          <svg width="200" height="200" viewBox="0 0 200 200" fill="none">
            {/* Floor plan sketch */}
            <rect x="20" y="20" width="160" height="160" stroke="rgba(201,169,110,0.6)" strokeWidth="2" fill="none"/>
            <line x1="20" y1="90" x2="100" y2="90" stroke="rgba(201,169,110,0.4)" strokeWidth="1.5"/>
            <line x1="100" y1="20" x2="100" y2="160" stroke="rgba(201,169,110,0.4)" strokeWidth="1.5"/>
            <line x1="100" y1="130" x2="180" y2="130" stroke="rgba(201,169,110,0.4)" strokeWidth="1.5"/>
            {/* Door arcs */}
            <path d="M100 90 Q115 90 115 105" stroke="rgba(201,169,110,0.5)" strokeWidth="1" fill="none"/>
            <path d="M100 130 Q115 130 115 145" stroke="rgba(201,169,110,0.5)" strokeWidth="1" fill="none"/>
            {/* Labels */}
            <text x="50" y="60" fill="rgba(201,169,110,0.7)" fontSize="10" textAnchor="middle">Salon</text>
            <text x="50" y="125" fill="rgba(201,169,110,0.7)" fontSize="10" textAnchor="middle">Cuisine</text>
            <text x="145" y="80" fill="rgba(201,169,110,0.7)" fontSize="10" textAnchor="middle">Chambre</text>
            <text x="145" y="150" fill="rgba(201,169,110,0.7)" fontSize="10" textAnchor="middle">SDB</text>
          </svg>

          {/* AI badge */}
          <div style={{
            position: "absolute",
            top: -12,
            right: -12,
            background: "var(--accent)",
            borderRadius: 999,
            padding: "4px 12px",
            fontSize: 11,
            fontWeight: 700,
            color: "white",
          }}>
            IA Active
          </div>
        </div>

        <h2 style={{
          fontFamily: "'Playfair Display', serif",
          fontSize: 28,
          fontWeight: 700,
          color: "white",
          textAlign: "center",
          marginBottom: 12,
        }}>
          Bienvenue sur ArchiVision
        </h2>
        <p style={{ color: "rgba(255,255,255,0.5)", textAlign: "center", fontSize: 14, maxWidth: 280 }}>
          La plateforme qui transforme vos plans en expériences immersives.
        </p>
      </div>

      {/* Right panel — form */}
      <div style={{
        width: "100%",
        maxWidth: 480,
        display: "flex",
        flexDirection: "column",
        padding: "40px 48px",
        justifyContent: "center",
        position: "relative",
      }}>
        {/* Top bar */}
        <div style={{ position: "absolute", top: 24, right: 24, display: "flex", gap: 8, alignItems: "center" }}>
          <ThemeToggle />
        </div>

        {/* Logo */}
        <Link href="/" style={{ textDecoration: "none", display: "flex", alignItems: "center", gap: 10, marginBottom: 40 }}>
          <div style={{ width: 32, height: 32, background: "var(--accent)", borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5">
              <polygon points="3 9 12 2 21 9 21 20 3 20 3 9"/>
              <rect x="9" y="14" width="6" height="6"/>
            </svg>
          </div>
          <span style={{ fontFamily: "'Playfair Display', serif", fontWeight: 700, fontSize: 18, color: "var(--text-primary)" }}>
            Archi<span style={{ color: "var(--accent)" }}>Guide</span>
          </span>
        </Link>

        <h1 style={{ fontSize: 26, fontWeight: 700, marginBottom: 8, color: "var(--text-primary)" }}>
          Connexion
        </h1>
        <p style={{ color: "var(--text-secondary)", fontSize: 14, marginBottom: 32 }}>
          Pas encore de compte ?{" "}
          <Link href="/auth/register" style={{ color: "var(--accent)", textDecoration: "none", fontWeight: 500 }}>
            S&apos;inscrire
          </Link>
        </p>

        {/* Role selector */}
        <div style={{
          display: "flex",
          background: "var(--bg-secondary)",
          borderRadius: 10,
          padding: 4,
          marginBottom: 28,
          border: "1px solid var(--border)",
        }}>
          {(["architect", "client"] as const).map((r) => (
            <button
              key={r}
              type="button"
              onClick={() => setRole(r)}
              style={{
                flex: 1,
                padding: "12px 10px",
                borderRadius: 8,
                border: "none",
                cursor: "pointer",
                fontSize: 14,
                fontWeight: 600,
                transition: "all 0.2s ease",
                background: role === r ? "var(--accent)" : "var(--surface)",
                color: role === r ? "#ffffff" : "var(--text-primary)",
                boxShadow: role === r ? "0 2px 8px rgba(201,169,110,0.35)" : "none",
                outline: "none",
              }}
            >
              {r === "architect" ? "🏛️ Architecte" : "👤 Client"}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <div>
            <label style={{ fontSize: 13, fontWeight: 500, color: "var(--text-secondary)", display: "block", marginBottom: 6 }}>
              Email
            </label>
            <input
              type="email"
              className="input"
              placeholder="vous@exemple.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div>
            <label style={{ fontSize: 13, fontWeight: 500, color: "var(--text-secondary)", display: "block", marginBottom: 6 }}>
              Mot de passe
            </label>
            <input
              type="password"
              className="input"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            <div style={{ textAlign: "right", marginTop: 6 }}>
              <Link href="/auth/forgot" style={{ fontSize: 12, color: "var(--accent)", textDecoration: "none" }}>
                Mot de passe oublié ?
              </Link>
            </div>
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading}
            style={{ width: "100%", justifyContent: "center", padding: "14px", fontSize: 15, marginTop: 8 }}
          >
            {loading ? (
              <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <svg className="animate-spin-slow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
                </svg>
                Connexion...
              </span>
            ) : "Se connecter →"}
          </button>
        </form>

        {/* Divider */}
        <div style={{ display: "flex", alignItems: "center", gap: 12, margin: "24px 0" }}>
          <div className="divider" style={{ flex: 1, margin: 0 }} />
          <span style={{ fontSize: 12, color: "var(--text-muted)" }}>ou continuer avec</span>
          <div className="divider" style={{ flex: 1, margin: 0 }} />
        </div>

        {/* Social */}
        <div style={{ display: "flex", gap: 12 }}>
          {["Google", "GitHub"].map((provider) => (
            <button key={provider} className="btn btn-secondary" style={{ flex: 1, justifyContent: "center", fontSize: 13 }}>
              {provider === "Google" ? "🔵" : "⚫"} {provider}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
