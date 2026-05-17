"use client";
import { useState, useEffect } from "react";
import { useUser } from "@/hooks/useUser";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function SettingsPage() {
  const { user, setUser, logout } = useUser();
  const [form, setForm] = useState({
    name:      "",
    email:     "",
    city:      "",
    specialty: "",
    phone:     "",
  });
  const [saving,   setSaving]   = useState(false);
  const [saved,    setSaved]    = useState(false);
  const [pwForm,   setPwForm]   = useState({ current: "", newPw: "", confirm: "" });
  const [pwSaving, setPwSaving] = useState(false);
  const [pwMsg,    setPwMsg]    = useState("");

  useEffect(() => {
    if (user) {
      setForm({
        name:      user.name      || "",
        email:     user.email     || "",
        city:      user.city      || "",
        specialty: user.specialty || "",
        phone:     "",
      });
    }
  }, [user]);

  const handleSave = async () => {
    setSaving(true);
    setSaved(false);
    try {
      // Update localStorage
      const updated = { ...user, ...form };
      setUser(updated as typeof user);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch {}
    setSaving(false);
  };

  const handlePasswordChange = async () => {
    if (pwForm.newPw !== pwForm.confirm) {
      setPwMsg("Les mots de passe ne correspondent pas.");
      return;
    }
    if (pwForm.newPw.length < 8) {
      setPwMsg("Le mot de passe doit faire au moins 8 caractères.");
      return;
    }
    setPwSaving(true);
    setPwMsg("");
    // In a real app, call API to change password
    setTimeout(() => {
      setPwMsg("✅ Mot de passe modifié avec succès.");
      setPwForm({ current: "", newPw: "", confirm: "" });
      setPwSaving(false);
    }, 800);
  };

  if (!user) {
    return (
      <div style={{ maxWidth: 600, padding: 40, textAlign: "center", color: "var(--text-muted)" }}>
        <div style={{ fontSize: 40, marginBottom: 12 }}>🔒</div>
        <div>Vous devez être connecté pour accéder aux paramètres.</div>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 700 }}>
      <div className="animate-fade-in" style={{ marginBottom: 32 }}>
        <h1 style={{ fontFamily: "'Playfair Display', serif", fontSize: 28, fontWeight: 700, color: "var(--text-primary)", marginBottom: 6 }}>
          Paramètres
        </h1>
        <p style={{ color: "var(--text-secondary)", fontSize: 15 }}>
          Gérez votre profil et vos préférences.
        </p>
      </div>

      {/* Profile section */}
      <div className="animate-fade-in delay-100" style={{
        background: "var(--surface)", border: "1px solid var(--border)",
        borderRadius: "var(--radius-lg)", padding: 28, marginBottom: 20,
      }}>
        <div style={{ display: "flex", gap: 20, alignItems: "center", marginBottom: 24 }}>
          <div style={{
            width: 72, height: 72, borderRadius: "50%",
            background: "linear-gradient(135deg, var(--accent), #e8c98e)",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 28, fontWeight: 700, color: "white",
          }}>
            {user.name?.[0]?.toUpperCase() || "?"}
          </div>
          <div>
            <div style={{ fontSize: 18, fontWeight: 700, color: "var(--text-primary)" }}>{user.name}</div>
            <div style={{ fontSize: 13, color: "var(--text-muted)" }}>{user.email}</div>
            <span className="badge badge-gold" style={{ marginTop: 6, display: "inline-block" }}>
              {user.role === "architect" ? "🏛️ Architecte" : "👤 Client"}
            </span>
          </div>
        </div>

        <h2 style={{ fontSize: 15, fontWeight: 600, color: "var(--text-primary)", marginBottom: 16 }}>
          Informations personnelles
        </h2>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14, marginBottom: 20 }}>
          {[
            { label: "Nom complet",  key: "name",      type: "text",  placeholder: "Jean Dupont" },
            { label: "Email",        key: "email",     type: "email", placeholder: "vous@exemple.com" },
            { label: "Ville",        key: "city",      type: "text",  placeholder: "Paris" },
            { label: "Téléphone",    key: "phone",     type: "tel",   placeholder: "+33 6 00 00 00 00" },
          ].map(f => (
            <div key={f.key}>
              <label style={{ fontSize: 12, fontWeight: 500, color: "var(--text-secondary)", display: "block", marginBottom: 5 }}>
                {f.label}
              </label>
              <input
                type={f.type}
                className="input"
                placeholder={f.placeholder}
                value={(form as Record<string, string>)[f.key]}
                onChange={e => setForm(prev => ({ ...prev, [f.key]: e.target.value }))}
                style={{ fontSize: 13 }}
              />
            </div>
          ))}
          {user.role === "architect" && (
            <div style={{ gridColumn: "1 / -1" }}>
              <label style={{ fontSize: 12, fontWeight: 500, color: "var(--text-secondary)", display: "block", marginBottom: 5 }}>
                Spécialité
              </label>
              <select
                className="input"
                value={form.specialty}
                onChange={e => setForm(prev => ({ ...prev, specialty: e.target.value }))}
                style={{ fontSize: 13 }}
              >
                <option value="">Choisir une spécialité</option>
                <option>Architecture résidentielle</option>
                <option>Architecture commerciale</option>
                <option>Architecture d&apos;intérieur</option>
                <option>Urbanisme</option>
                <option>Architecture durable</option>
              </select>
            </div>
          )}
        </div>

        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <button
            onClick={handleSave}
            disabled={saving}
            className="btn btn-primary"
            style={{ fontSize: 13 }}
          >
            {saving ? "Sauvegarde..." : "💾 Sauvegarder les modifications"}
          </button>
          {saved && (
            <span style={{ fontSize: 13, color: "#6fcf97", fontWeight: 500 }}>
              ✅ Modifications sauvegardées
            </span>
          )}
        </div>
      </div>

      {/* Password section */}
      <div className="animate-fade-in delay-200" style={{
        background: "var(--surface)", border: "1px solid var(--border)",
        borderRadius: "var(--radius-lg)", padding: 28, marginBottom: 20,
      }}>
        <h2 style={{ fontSize: 15, fontWeight: 600, color: "var(--text-primary)", marginBottom: 16 }}>
          🔒 Changer le mot de passe
        </h2>
        <div style={{ display: "flex", flexDirection: "column", gap: 12, maxWidth: 400 }}>
          {[
            { label: "Mot de passe actuel", key: "current", placeholder: "••••••••" },
            { label: "Nouveau mot de passe", key: "newPw",  placeholder: "Min. 8 caractères" },
            { label: "Confirmer",            key: "confirm", placeholder: "Répétez le nouveau mot de passe" },
          ].map(f => (
            <div key={f.key}>
              <label style={{ fontSize: 12, fontWeight: 500, color: "var(--text-secondary)", display: "block", marginBottom: 5 }}>
                {f.label}
              </label>
              <input
                type="password"
                className="input"
                placeholder={f.placeholder}
                value={(pwForm as Record<string, string>)[f.key]}
                onChange={e => setPwForm(prev => ({ ...prev, [f.key]: e.target.value }))}
                style={{ fontSize: 13 }}
              />
            </div>
          ))}
          {pwMsg && (
            <div style={{
              fontSize: 13, padding: "8px 12px", borderRadius: "var(--radius)",
              background: pwMsg.startsWith("✅") ? "#6fcf9718" : "#eb575718",
              color: pwMsg.startsWith("✅") ? "#6fcf97" : "#eb5757",
              border: `1px solid ${pwMsg.startsWith("✅") ? "#6fcf97" : "#eb5757"}`,
            }}>
              {pwMsg}
            </div>
          )}
          <button
            onClick={handlePasswordChange}
            disabled={pwSaving || !pwForm.current || !pwForm.newPw}
            className="btn btn-secondary"
            style={{ fontSize: 13, alignSelf: "flex-start" }}
          >
            {pwSaving ? "Modification..." : "Modifier le mot de passe"}
          </button>
        </div>
      </div>

      {/* Danger zone */}
      <div className="animate-fade-in delay-300" style={{
        background: "var(--surface)", border: "1px solid #eb5757",
        borderRadius: "var(--radius-lg)", padding: 24,
      }}>
        <h2 style={{ fontSize: 15, fontWeight: 600, color: "#eb5757", marginBottom: 8 }}>
          ⚠️ Zone dangereuse
        </h2>
        <p style={{ fontSize: 13, color: "var(--text-secondary)", marginBottom: 16 }}>
          La déconnexion vous redirigera vers la page de connexion.
        </p>
        <button
          onClick={logout}
          className="btn"
          style={{
            background: "#eb575718", color: "#eb5757",
            border: "1px solid #eb5757", fontSize: 13,
          }}
        >
          🚪 Se déconnecter
        </button>
      </div>
    </div>
  );
}
