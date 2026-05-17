"use client";
import { useState, useEffect } from "react";
import { useUser } from "@/hooks/useUser";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Project {
  id:          string;
  name:        string;
  client_name: string;
  client_id:   string;
  status:      string;
  progress:    number;
  type:        string;
  date:        string;
  area:        string;
  budget:      string;
  architect_id: string;
}

interface Client {
  id:   string;
  name: string;
}

const STATUS_COLOR: Record<string, string> = {
  "En cours":   "#c9a96e",
  "Analyse IA": "#56b4d3",
  "Terminé":    "#6fcf97",
  "En attente": "#9c9590",
};

const PROJECT_TYPES = ["Résidentiel", "Rénovation", "Commercial", "Intérieur", "Durable"];
const PROJECT_STATUSES = ["En cours", "En attente", "Analyse IA", "Terminé"];

export default function ProjectsPage() {
  const { user } = useUser();
  const [projects, setProjects] = useState<Project[]>([]);
  const [clients,  setClients]  = useState<Client[]>([]);
  const [loading,  setLoading]  = useState(true);
  const [filter,   setFilter]   = useState("all");
  const [search,   setSearch]   = useState("");
  const [showModal, setShowModal] = useState(false);
  const [saving,    setSaving]    = useState(false);

  // New project form state
  const [form, setForm] = useState({
    name:        "",
    client_id:   "",
    client_name: "",
    type:        "Résidentiel",
    area:        "",
    budget:      "",
    status:      "En cours",
  });

  const archId = user?.id || "arch_1";

  const loadProjects = () => {
    fetch(`${API_URL}/api/projects?architect_id=${archId}`)
      .then(r => r.json())
      .then(d => { setProjects(d.projects || []); setLoading(false); })
      .catch(() => setLoading(false));
  };

  useEffect(() => {
    loadProjects();
    // Load clients for the dropdown
    fetch(`${API_URL}/api/clients`)
      .then(r => r.json())
      .then(d => setClients(d.clients || []))
      .catch(() => {});
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [archId]);

  const handleClientChange = (clientId: string) => {
    const client = clients.find(c => c.id === clientId);
    setForm(f => ({
      ...f,
      client_id:   clientId,
      client_name: client?.name || "",
    }));
  };

  const handleCreate = async () => {
    if (!form.name.trim()) return;
    setSaving(true);
    try {
      const res = await fetch(`${API_URL}/api/projects`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ ...form, architect_id: archId }),
      });
      if (res.ok) {
        setShowModal(false);
        setForm({ name: "", client_id: "", client_name: "", type: "Résidentiel", area: "", budget: "", status: "En cours" });
        loadProjects();
      }
    } catch {}
    setSaving(false);
  };

  const filters = ["all", "En cours", "Analyse IA", "Terminé", "En attente"];

  const filtered = projects.filter(p => {
    const matchFilter = filter === "all" || p.status === filter;
    const matchSearch = p.name.toLowerCase().includes(search.toLowerCase()) ||
      (p.client_name || "").toLowerCase().includes(search.toLowerCase());
    return matchFilter && matchSearch;
  });

  return (
    <div style={{ maxWidth: 1100 }}>
      <div className="animate-fade-in" style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 32, flexWrap: "wrap", gap: 16 }}>
        <div>
          <h1 style={{ fontFamily: "'Playfair Display', serif", fontSize: 28, fontWeight: 700, color: "var(--text-primary)", marginBottom: 6 }}>
            Mes Projets
          </h1>
          <p style={{ color: "var(--text-secondary)", fontSize: 15 }}>
            {projects.length} projet{projects.length !== 1 ? "s" : ""} · {projects.filter(p => p.status === "En cours").length} en cours
          </p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowModal(true)}>
          ➕ Nouveau projet
        </button>
      </div>

      {/* Filters & Search */}
      <div className="animate-fade-in delay-100" style={{ display: "flex", gap: 12, marginBottom: 24, flexWrap: "wrap", alignItems: "center" }}>
        <input
          className="input"
          placeholder="Rechercher un projet ou client..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          style={{ maxWidth: 280 }}
        />
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
          {filters.map(f => (
            <button key={f} onClick={() => setFilter(f)} style={{
              padding: "6px 14px", borderRadius: 999,
              border: `1px solid ${filter === f ? "var(--accent)" : "var(--border)"}`,
              background: filter === f ? "var(--accent-light)" : "var(--bg-secondary)",
              color: filter === f ? "var(--accent-dark)" : "var(--text-secondary)",
              fontSize: 13, fontWeight: filter === f ? 600 : 400, cursor: "pointer",
              transition: "all 0.2s ease",
            }}>
              {f === "all" ? "Tous" : f}
              {f !== "all" && (
                <span style={{ marginLeft: 6, fontSize: 11, opacity: 0.7 }}>
                  ({projects.filter(p => p.status === f).length})
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Projects grid */}
      {loading ? (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: 16 }}>
          {Array(4).fill(0).map((_, i) => (
            <div key={i} className="skeleton" style={{ height: 200, borderRadius: "var(--radius-lg)" }} />
          ))}
        </div>
      ) : (
        <div className="animate-fade-in delay-200" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: 16 }}>
          {filtered.map(project => (
            <div key={project.id} className="card-hover" style={{
              background: "var(--surface)", border: "1px solid var(--border)",
              borderRadius: "var(--radius-lg)", padding: 20, cursor: "pointer",
            }}>
              {/* Header */}
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12 }}>
                <div style={{ flex: 1 }}>
                  <h3 style={{ fontSize: 15, fontWeight: 600, color: "var(--text-primary)", marginBottom: 4 }}>
                    {project.name}
                  </h3>
                  <div style={{ fontSize: 13, color: "var(--text-muted)" }}>{project.client_name || "—"}</div>
                </div>
                <span style={{
                  fontSize: 11, fontWeight: 600,
                  color: STATUS_COLOR[project.status] || "#9c9590",
                  background: `${STATUS_COLOR[project.status] || "#9c9590"}18`,
                  padding: "3px 8px", borderRadius: 999, whiteSpace: "nowrap",
                }}>
                  {project.status}
                </span>
              </div>

              {/* Progress */}
              <div className="progress-bar" style={{ marginBottom: 6 }}>
                <div className="progress-fill" style={{ width: `${project.progress}%` }} />
              </div>
              <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 14, textAlign: "right" }}>
                {project.progress}%
              </div>

              {/* Meta */}
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 14 }}>
                {[project.type, project.area, project.budget].filter(Boolean).map(m => (
                  <span key={m} style={{
                    fontSize: 11, color: "var(--text-muted)",
                    background: "var(--bg-secondary)", padding: "3px 8px",
                    borderRadius: 999, border: "1px solid var(--border)",
                  }}>
                    {m}
                  </span>
                ))}
              </div>

              {/* Footer */}
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", paddingTop: 12, borderTop: "1px solid var(--border)" }}>
                <span style={{ fontSize: 12, color: "var(--text-muted)" }}>{project.date}</span>
                <div style={{ display: "flex", gap: 6 }}>
                  <button 
                    onClick={() => window.location.href = '/architect/upload'}
                    className="btn btn-ghost" 
                    style={{ fontSize: 12, padding: "4px 10px" }}
                  >
                    📐 Plan
                  </button>
                  <button 
                    onClick={() => window.location.href = '/architect/messages'}
                    className="btn btn-secondary" 
                    style={{ fontSize: 12, padding: "4px 10px" }}
                  >
                    Ouvrir →
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {!loading && filtered.length === 0 && (
        <div style={{ textAlign: "center", padding: 60, color: "var(--text-muted)" }}>
          <div style={{ fontSize: 40, marginBottom: 12 }}>🔍</div>
          <div style={{ fontSize: 16 }}>
            {projects.length === 0 ? "Aucun projet — créez votre premier projet" : "Aucun projet trouvé"}
          </div>
          {projects.length === 0 && (
            <button className="btn btn-primary" style={{ marginTop: 16 }} onClick={() => setShowModal(true)}>
              ➕ Créer un projet
            </button>
          )}
        </div>
      )}

      {/* Create project modal */}
      {showModal && (
        <div style={{
          position: "fixed", inset: 0, zIndex: 200,
          background: "rgba(0,0,0,0.5)", backdropFilter: "blur(4px)",
          display: "flex", alignItems: "center", justifyContent: "center", padding: 24,
        }} onClick={e => { if (e.target === e.currentTarget) setShowModal(false); }}>
          <div style={{
            background: "var(--surface)", borderRadius: "var(--radius-lg)",
            border: "1px solid var(--border)", padding: 32, width: "100%", maxWidth: 520,
            boxShadow: "0 20px 60px rgba(0,0,0,0.3)",
          }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
              <h2 style={{ fontFamily: "'Playfair Display', serif", fontSize: 20, fontWeight: 700, color: "var(--text-primary)" }}>
                Nouveau projet
              </h2>
              <button className="btn btn-ghost" style={{ padding: 8 }} onClick={() => setShowModal(false)}>✕</button>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
              <div>
                <label style={{ fontSize: 13, fontWeight: 600, color: "var(--text-primary)", display: "block", marginBottom: 6 }}>
                  Nom du projet *
                </label>
                <input
                  className="input"
                  placeholder="Ex: Villa Moderne — Dupont"
                  value={form.name}
                  onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                />
              </div>

              <div>
                <label style={{ fontSize: 13, fontWeight: 600, color: "var(--text-primary)", display: "block", marginBottom: 6 }}>
                  Client
                </label>
                <select
                  className="input"
                  value={form.client_id}
                  onChange={e => handleClientChange(e.target.value)}
                  style={{ cursor: "pointer" }}
                >
                  <option value="">— Sélectionner un client —</option>
                  {clients.map(c => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                <div>
                  <label style={{ fontSize: 13, fontWeight: 600, color: "var(--text-primary)", display: "block", marginBottom: 6 }}>
                    Type
                  </label>
                  <select
                    className="input"
                    value={form.type}
                    onChange={e => setForm(f => ({ ...f, type: e.target.value }))}
                    style={{ cursor: "pointer" }}
                  >
                    {PROJECT_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: 13, fontWeight: 600, color: "var(--text-primary)", display: "block", marginBottom: 6 }}>
                    Statut
                  </label>
                  <select
                    className="input"
                    value={form.status}
                    onChange={e => setForm(f => ({ ...f, status: e.target.value }))}
                    style={{ cursor: "pointer" }}
                  >
                    {PROJECT_STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                <div>
                  <label style={{ fontSize: 13, fontWeight: 600, color: "var(--text-primary)", display: "block", marginBottom: 6 }}>
                    Surface
                  </label>
                  <input
                    className="input"
                    placeholder="Ex: 120 m²"
                    value={form.area}
                    onChange={e => setForm(f => ({ ...f, area: e.target.value }))}
                  />
                </div>
                <div>
                  <label style={{ fontSize: 13, fontWeight: 600, color: "var(--text-primary)", display: "block", marginBottom: 6 }}>
                    Budget
                  </label>
                  <input
                    className="input"
                    placeholder="Ex: 350 000 €"
                    value={form.budget}
                    onChange={e => setForm(f => ({ ...f, budget: e.target.value }))}
                  />
                </div>
              </div>
            </div>

            <div style={{ display: "flex", gap: 10, marginTop: 24, justifyContent: "flex-end" }}>
              <button className="btn btn-ghost" onClick={() => setShowModal(false)}>Annuler</button>
              <button
                className="btn btn-primary"
                onClick={handleCreate}
                disabled={!form.name.trim() || saving}
                style={{ opacity: !form.name.trim() || saving ? 0.6 : 1 }}
              >
                {saving ? "Création..." : "✅ Créer le projet"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
