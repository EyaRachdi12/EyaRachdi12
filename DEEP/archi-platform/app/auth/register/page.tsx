"use client";
import { useState, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import ThemeToggle from "@/components/ThemeToggle";

function RegisterForm() {
  const searchParams = useSearchParams();
  const defaultRole = (searchParams.get("role") as "architect" | "client") || "architect";
  const [role, setRole] = useState<"architect" | "client">(defaultRole);
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({ name: "", email: "", password: "", specialty: "", city: "" });

  const handleNext = async (e: React.FormEvent) => {
    e.preventDefault();
    if (step < 2) { setStep(2); return; }
    setLoading(true);

    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${API_URL}/api/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name:         form.name,
          email:        form.email,
          password:     form.password,
          role:         role,
          specialty:    form.specialty,
          city:         form.city,
          project_type: form.specialty,
        }),
      });

      if (!res.ok) {
        const err = await res.json();
        alert(err.detail || "Erreur lors de l'inscription");
        setLoading(false);
        return;
      }

      const user = await res.json();
      // Store user in localStorage
      localStorage.setItem("archi_user", JSON.stringify(user));
      window.location.href = role === "architect" ? "/architect/dashboard" : "/client/dashboard";
    } catch {
      // Fallback — redirect anyway for demo
      window.location.href = role === "architect" ? "/architect/dashboard" : "/client/dashboard";
    }
  };

  return (
    <div style={{ minHeight: "100vh", display: "flex", background: "var(--bg)" }}>
      {/* Left decorative */}
      <div style={{
        flex: 1,
        background: "linear-gradient(135deg, #0f0e0c 0%, #1e1c18 100%)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: 48,
        position: "relative",
        overflow: "hidden",
      }}>
        <div style={{
          position: "absolute", inset: 0,
          backgroundImage: `linear-gradient(rgba(201,169,110,0.06) 1px, transparent 1px), linear-gradient(90deg, rgba(201,169,110,0.06) 1px, transparent 1px)`,
          backgroundSize: "40px 40px",
        }} />

        {/* Steps visual */}
        <div style={{ position: "relative", zIndex: 1, width: "100%", maxWidth: 320 }}>
          {[
            { n: 1, title: "Informations de base", desc: "Nom, email, mot de passe" },
            { n: 2, title: "Profil professionnel", desc: "Spécialité, localisation" },
            { n: 3, title: "C&apos;est parti !", desc: "Accès à la plateforme" },
          ].map((s) => (
            <div key={s.n} style={{ display: "flex", gap: 16, marginBottom: 28, alignItems: "flex-start" }}>
              <div style={{
                width: 36,
                height: 36,
                borderRadius: "50%",
                background: step >= s.n ? "var(--accent)" : "rgba(201,169,110,0.15)",
                border: `2px solid ${step >= s.n ? "var(--accent)" : "rgba(201,169,110,0.3)"}`,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: 14,
                fontWeight: 700,
                color: step >= s.n ? "white" : "rgba(201,169,110,0.5)",
                flexShrink: 0,
                transition: "all 0.3s ease",
              }}>
                {step > s.n ? "✓" : s.n}
              </div>
              <div>
                <div style={{ fontSize: 14, fontWeight: 600, color: step >= s.n ? "white" : "rgba(255,255,255,0.3)" }}>
                  {s.title}
                </div>
                <div style={{ fontSize: 12, color: "rgba(255,255,255,0.3)", marginTop: 2 }}>{s.desc}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Right form */}
      <div style={{ width: "100%", maxWidth: 480, display: "flex", flexDirection: "column", padding: "40px 48px", justifyContent: "center", position: "relative" }}>
        <div style={{ position: "absolute", top: 24, right: 24 }}>
          <ThemeToggle />
        </div>

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
          Créer un compte
        </h1>
        <p style={{ color: "var(--text-secondary)", fontSize: 14, marginBottom: 28 }}>
          Déjà inscrit ?{" "}
          <Link href="/auth/login" style={{ color: "var(--accent)", textDecoration: "none", fontWeight: 500 }}>
            Se connecter
          </Link>
        </p>

        {/* Role selector */}
        <div style={{ display: "flex", background: "var(--bg-secondary)", borderRadius: 10, padding: 4, marginBottom: 28, border: "1px solid var(--border)" }}>
          {(["architect", "client"] as const).map((r) => (
            <button
              key={r}
              type="button"
              onClick={() => setRole(r)}
              style={{
                flex: 1, padding: "12px 10px", borderRadius: 8, border: "none", cursor: "pointer",
                fontSize: 14, fontWeight: 600, transition: "all 0.2s ease",
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

        {/* Progress */}
        <div className="progress-bar" style={{ marginBottom: 28 }}>
          <div className="progress-fill" style={{ width: `${(step / 2) * 100}%` }} />
        </div>

        <form onSubmit={handleNext} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {step === 1 && (
            <>
              <div>
                <label style={{ fontSize: 13, fontWeight: 500, color: "var(--text-secondary)", display: "block", marginBottom: 6 }}>
                  Nom complet
                </label>
                <input className="input" placeholder="Jean Dupont" value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })} required />
              </div>
              <div>
                <label style={{ fontSize: 13, fontWeight: 500, color: "var(--text-secondary)", display: "block", marginBottom: 6 }}>
                  Email
                </label>
                <input type="email" className="input" placeholder="vous@exemple.com" value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })} required />
              </div>
              <div>
                <label style={{ fontSize: 13, fontWeight: 500, color: "var(--text-secondary)", display: "block", marginBottom: 6 }}>
                  Mot de passe
                </label>
                <input type="password" className="input" placeholder="Min. 8 caractères" value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })} required minLength={8} />
              </div>
            </>
          )}

          {step === 2 && (
            <>
              {role === "architect" && (
                <div>
                  <label style={{ fontSize: 13, fontWeight: 500, color: "var(--text-secondary)", display: "block", marginBottom: 6 }}>
                    Spécialité
                  </label>
                  <select className="input" value={form.specialty}
                    onChange={(e) => setForm({ ...form, specialty: e.target.value })} required>
                    <option value="">Choisir une spécialité</option>
                    <option>Architecture résidentielle</option>
                    <option>Architecture commerciale</option>
                    <option>Architecture d&apos;intérieur</option>
                    <option>Urbanisme</option>
                    <option>Architecture durable</option>
                  </select>
                </div>
              )}
              <div>
                <label style={{ fontSize: 13, fontWeight: 500, color: "var(--text-secondary)", display: "block", marginBottom: 6 }}>
                  Ville
                </label>
                <input className="input" placeholder="Paris, Lyon, Marseille..." value={form.city}
                  onChange={(e) => setForm({ ...form, city: e.target.value })} required />
              </div>
              {role === "client" && (
                <div>
                  <label style={{ fontSize: 13, fontWeight: 500, color: "var(--text-secondary)", display: "block", marginBottom: 6 }}>
                    Type de projet
                  </label>
                  <select className="input">
                    <option>Maison individuelle</option>
                    <option>Appartement</option>
                    <option>Local commercial</option>
                    <option>Rénovation</option>
                    <option>Extension</option>
                  </select>
                </div>
              )}
            </>
          )}

          <button type="submit" className="btn btn-primary" disabled={loading}
            style={{ width: "100%", justifyContent: "center", padding: "14px", fontSize: 15, marginTop: 8 }}>
            {loading ? "Création du compte..." : step === 1 ? "Continuer →" : "Créer mon compte →"}
          </button>
        </form>

        {step === 2 && (
          <button onClick={() => setStep(1)} className="btn btn-ghost"
            style={{ width: "100%", justifyContent: "center", marginTop: 8, fontSize: 14 }}>
            ← Retour
          </button>
        )}
      </div>
    </div>
  );
}

export default function RegisterPage() {
  return (
    <Suspense>
      <RegisterForm />
    </Suspense>
  );
}
