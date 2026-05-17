"use client";
import { useState, useEffect } from "react";

interface Client {
  id: string;
  name: string;
  email: string;
  project: string;
  city: string;
  phone: string;
  status: string;
  project_type: string;
  since: string;
  projects: number;
  avatar: string;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const STATUS_COLOR: Record<string, string> = {
  "Actif":      "#6fcf97",
  "Terminé":    "#9c9590",
  "En attente": "#c9a96e",
};

export default function ClientsPage() {
  const [clients,  setClients]  = useState<Client[]>([]);
  const [loading,  setLoading]  = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [search,   setSearch]   = useState("");
  const [selectedClient, setSelectedClient] = useState<Client | null>(null);
  const [form, setForm] = useState({
    name: "", email: "", project: "", city: "",
    phone: "", status: "Actif", project_type: "Maison individuelle",
  });
  const [saving, setSaving] = useState(false);
  const [error,  setError]  = useState("");

  // Load clients
  useEffect(() => {
    fetch(`${API_URL}/api/clients`)
      .then(r => r.json())
      .then(data => {
        // API returns { clients: [...], total: N }
        const list = Array.isArray(data) ? data : (data.clients || []);
        setClients(list);
        setLoading(false);
      })
      .catch(() => { setLoading(false); setError("Backend non disponible — démarrez le serveur sur le port 8000"); });
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      const r = await fetch(`${API_URL}/api/clients`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      if (!r.ok) throw new Error();
      const newClient = await r.json();
      setClients(prev => [...prev, newClient]);
      setShowForm(false);
      setForm({ name:"", email:"", project:"", city:"", phone:"", status:"Actif", project_type:"Maison individuelle" });
    } catch {
      setError("Erreur lors de la création");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Supprimer ce client ?")) return;
    await fetch(`${API_URL}/api/clients/${id}`, { method: "DELETE" });
    setClients(prev => prev.filter(c => c.id !== id));
  };

  const filtered = clients.filter(c =>
    c.name.toLowerCase().includes(search.toLowerCase()) ||
    c.email.toLowerCase().includes(search.toLowerCase()) ||
    c.project.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div style={{ maxWidth: 1000 }}>
      {/* Header */}
      <div className="animate-fade-in" style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start", marginBottom:32, flexWrap:"wrap", gap:16 }}>
        <div>
          <h1 style={{ fontFamily:"'Playfair Display', serif", fontSize:28, fontWeight:700, color:"var(--text-primary)", marginBottom:6 }}>
            Mes Clients
          </h1>
          <p style={{ color:"var(--text-secondary)", fontSize:15 }}>
            {clients.length} client{clients.length !== 1 ? "s" : ""} · {clients.filter(c=>c.status==="Actif").length} actifs
          </p>
        </div>
        <button onClick={() => setShowForm(true)} className="btn btn-primary">
          + Ajouter un client
        </button>
      </div>

      {/* Error */}
      {error && (
        <div style={{ padding:"12px 16px", background:"#eb575718", border:"1px solid #eb5757", borderRadius:"var(--radius)", marginBottom:20, fontSize:13, color:"#eb5757" }}>
          {error} — <button onClick={() => setError("")} style={{ background:"none", border:"none", color:"#eb5757", cursor:"pointer", textDecoration:"underline" }}>Fermer</button>
        </div>
      )}

      {/* Search */}
      <div className="animate-fade-in delay-100" style={{ marginBottom:20 }}>
        <input
          className="input"
          placeholder="Rechercher un client, email, projet..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          style={{ maxWidth: 360 }}
        />
      </div>

      {/* Add form */}
      {showForm && (
        <div className="animate-scale-in" style={{
          background:"var(--surface)", border:"1px solid var(--accent)",
          borderRadius:"var(--radius-lg)", padding:24, marginBottom:24,
        }}>
          <h2 style={{ fontSize:16, fontWeight:600, color:"var(--text-primary)", marginBottom:20 }}>
            Nouveau client
          </h2>
          <form onSubmit={handleCreate}>
            <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:14, marginBottom:14 }}>
              {[
                { label:"Nom complet *",  key:"name",    type:"text",  placeholder:"Jean Dupont" },
                { label:"Email *",        key:"email",   type:"email", placeholder:"jean@exemple.com" },
                { label:"Projet",         key:"project", type:"text",  placeholder:"Villa Moderne" },
                { label:"Ville",          key:"city",    type:"text",  placeholder:"Paris" },
                { label:"Téléphone",      key:"phone",   type:"tel",   placeholder:"+33 6 00 00 00 00" },
              ].map(f => (
                <div key={f.key}>
                  <label style={{ fontSize:12, fontWeight:500, color:"var(--text-secondary)", display:"block", marginBottom:5 }}>
                    {f.label}
                  </label>
                  <input
                    type={f.type}
                    className="input"
                    placeholder={f.placeholder}
                    value={(form as Record<string,string>)[f.key]}
                    onChange={e => setForm(prev => ({ ...prev, [f.key]: e.target.value }))}
                    required={f.label.includes("*")}
                    style={{ fontSize:13 }}
                  />
                </div>
              ))}
              <div>
                <label style={{ fontSize:12, fontWeight:500, color:"var(--text-secondary)", display:"block", marginBottom:5 }}>
                  Type de projet
                </label>
                <select className="input" style={{ fontSize:13 }}
                  value={form.project_type}
                  onChange={e => setForm(prev => ({ ...prev, project_type: e.target.value }))}>
                  <option>Maison individuelle</option>
                  <option>Appartement</option>
                  <option>Local commercial</option>
                  <option>Rénovation</option>
                  <option>Extension</option>
                  <option>Villa</option>
                </select>
              </div>
            </div>
            <div style={{ display:"flex", gap:10 }}>
              <button type="submit" className="btn btn-primary" disabled={saving} style={{ fontSize:13 }}>
                {saving ? "Enregistrement..." : "✅ Créer le client"}
              </button>
              <button type="button" onClick={() => setShowForm(false)} className="btn btn-ghost" style={{ fontSize:13 }}>
                Annuler
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div style={{ textAlign:"center", padding:60, color:"var(--text-muted)" }}>
          <div style={{ fontSize:32, marginBottom:12 }}>⏳</div>
          Chargement des clients...
        </div>
      )}

      {/* Empty state */}
      {!loading && filtered.length === 0 && (
        <div style={{ textAlign:"center", padding:60, color:"var(--text-muted)" }}>
          <div style={{ fontSize:40, marginBottom:12 }}>👥</div>
          <div style={{ fontSize:16, marginBottom:8 }}>
            {search ? "Aucun client trouvé" : "Aucun client pour l'instant"}
          </div>
          {!search && (
            <button onClick={() => setShowForm(true)} className="btn btn-primary" style={{ marginTop:12 }}>
              + Ajouter votre premier client
            </button>
          )}
        </div>
      )}

      {/* Clients list */}
      {!loading && filtered.length > 0 && (
        <div className="animate-fade-in delay-100" style={{ display:"flex", flexDirection:"column", gap:12 }}>
          {filtered.map(client => (
            <div key={client.id} className="card-hover" style={{
              background:"var(--surface)", border:"1px solid var(--border)",
              borderRadius:"var(--radius-lg)", padding:20,
              display:"flex", gap:16, alignItems:"center", flexWrap:"wrap",
            }}>
              {/* Avatar */}
              <div style={{
                width:48, height:48, borderRadius:"50%",
                background:"linear-gradient(135deg, var(--accent), #e8c98e)",
                display:"flex", alignItems:"center", justifyContent:"center",
                fontSize:18, fontWeight:700, color:"white", flexShrink:0,
              }}>
                {client.avatar}
              </div>

              {/* Info */}
              <div style={{ flex:1, minWidth:180 }}>
                <div style={{ fontSize:15, fontWeight:600, color:"var(--text-primary)", marginBottom:3 }}>
                  {client.name}
                </div>
                <div style={{ fontSize:13, color:"var(--text-muted)" }}>{client.email}</div>
                {client.phone && (
                  <div style={{ fontSize:12, color:"var(--text-muted)" }}>{client.phone}</div>
                )}
              </div>

              {/* Project */}
              <div style={{ minWidth:160 }}>
                <div style={{ fontSize:11, color:"var(--text-muted)", marginBottom:3 }}>Projet</div>
                <div style={{ fontSize:13, fontWeight:500, color:"var(--accent)" }}>
                  {client.project || "—"}
                </div>
                {client.city && (
                  <div style={{ fontSize:11, color:"var(--text-muted)" }}>📍 {client.city}</div>
                )}
              </div>

              {/* Stats */}
              <div style={{ display:"flex", gap:20 }}>
                <div style={{ textAlign:"center" }}>
                  <div style={{ fontSize:18, fontWeight:700, color:"var(--text-primary)" }}>{client.projects}</div>
                  <div style={{ fontSize:11, color:"var(--text-muted)" }}>Projets</div>
                </div>
                <div style={{ textAlign:"center" }}>
                  <div style={{ fontSize:12, color:"var(--text-muted)" }}>Depuis</div>
                  <div style={{ fontSize:13, fontWeight:500, color:"var(--text-primary)" }}>{client.since}</div>
                </div>
              </div>

              {/* Status */}
              <span style={{
                fontSize:12, fontWeight:600,
                color: STATUS_COLOR[client.status] || "var(--text-muted)",
                background: `${STATUS_COLOR[client.status] || "#9c9590"}18`,
                padding:"4px 12px", borderRadius:999,
              }}>
                {client.status}
              </span>

              {/* Actions */}
              <div style={{ display:"flex", gap:8 }}>
                <a href="/architect/messages" className="btn btn-ghost" style={{ fontSize:12, padding:"6px 12px" }} title="Envoyer un message">
                  💬
                </a>
                <button
                  onClick={() => handleDelete(client.id)}
                  className="btn btn-ghost"
                  style={{ fontSize:12, padding:"6px 12px", color:"#eb5757" }}
                  title="Supprimer le client"
                >
                  🗑
                </button>
                <button 
                  onClick={() => setSelectedClient(client)}
                  className="btn btn-secondary" 
                  style={{ fontSize:12, padding:"6px 12px" }}
                >
                  Voir →
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Client Details Modal */}
      {selectedClient && (
        <div 
          style={{
            position: "fixed", top: 0, left: 0, right: 0, bottom: 0,
            background: "rgba(0,0,0,0.6)", display: "flex",
            alignItems: "center", justifyContent: "center", zIndex: 1000,
            padding: 20,
          }}
          onClick={() => setSelectedClient(null)}
        >
          <div 
            className="animate-scale-in"
            style={{
              background: "var(--surface)", borderRadius: "var(--radius-lg)",
              border: "1px solid var(--border)", maxWidth: 600, width: "100%",
              maxHeight: "90vh", overflowY: "auto",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div style={{
              padding: "20px 24px", borderBottom: "1px solid var(--border)",
              display: "flex", alignItems: "center", gap: 16,
            }}>
              <div style={{
                width: 56, height: 56, borderRadius: "50%",
                background: "linear-gradient(135deg, var(--accent), #e8c98e)",
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: 24, fontWeight: 700, color: "white",
              }}>
                {selectedClient.avatar}
              </div>
              <div style={{ flex: 1 }}>
                <h2 style={{ fontSize: 20, fontWeight: 700, color: "var(--text-primary)", marginBottom: 4 }}>
                  {selectedClient.name}
                </h2>
                <div style={{ fontSize: 13, color: "var(--text-muted)" }}>
                  Client depuis {selectedClient.since}
                </div>
              </div>
              <button
                onClick={() => setSelectedClient(null)}
                className="btn btn-ghost"
                style={{ padding: "8px 12px" }}
              >
                ✕
              </button>
            </div>

            {/* Content */}
            <div style={{ padding: 24 }}>
              {/* Contact Info */}
              <div style={{ marginBottom: 24 }}>
                <h3 style={{ fontSize: 14, fontWeight: 600, color: "var(--text-primary)", marginBottom: 12 }}>
                  Informations de contact
                </h3>
                <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <span style={{ fontSize: 16 }}>📧</span>
                    <a href={`mailto:${selectedClient.email}`} style={{ fontSize: 14, color: "var(--accent)", textDecoration: "none" }}>
                      {selectedClient.email}
                    </a>
                  </div>
                  {selectedClient.phone && (
                    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                      <span style={{ fontSize: 16 }}>📱</span>
                      <a href={`tel:${selectedClient.phone}`} style={{ fontSize: 14, color: "var(--accent)", textDecoration: "none" }}>
                        {selectedClient.phone}
                      </a>
                    </div>
                  )}
                  {selectedClient.city && (
                    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                      <span style={{ fontSize: 16 }}>📍</span>
                      <span style={{ fontSize: 14, color: "var(--text-secondary)" }}>
                        {selectedClient.city}
                      </span>
                    </div>
                  )}
                </div>
              </div>

              {/* Project Info */}
              <div style={{ marginBottom: 24 }}>
                <h3 style={{ fontSize: 14, fontWeight: 600, color: "var(--text-primary)", marginBottom: 12 }}>
                  Projet en cours
                </h3>
                <div style={{
                  background: "var(--bg-secondary)", border: "1px solid var(--border)",
                  borderRadius: "var(--radius)", padding: 16,
                }}>
                  <div style={{ fontSize: 15, fontWeight: 600, color: "var(--accent)", marginBottom: 6 }}>
                    {selectedClient.project || "Aucun projet"}
                  </div>
                  {selectedClient.project_type && (
                    <div style={{ fontSize: 13, color: "var(--text-muted)" }}>
                      Type : {selectedClient.project_type}
                    </div>
                  )}
                </div>
              </div>

              {/* Stats */}
              <div style={{ marginBottom: 24 }}>
                <h3 style={{ fontSize: 14, fontWeight: 600, color: "var(--text-primary)", marginBottom: 12 }}>
                  Statistiques
                </h3>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                  <div style={{
                    background: "var(--bg-secondary)", border: "1px solid var(--border)",
                    borderRadius: "var(--radius)", padding: 16, textAlign: "center",
                  }}>
                    <div style={{ fontSize: 24, fontWeight: 700, color: "var(--accent)", marginBottom: 4 }}>
                      {selectedClient.projects}
                    </div>
                    <div style={{ fontSize: 12, color: "var(--text-muted)" }}>
                      Projet{selectedClient.projects !== 1 ? "s" : ""}
                    </div>
                  </div>
                  <div style={{
                    background: "var(--bg-secondary)", border: "1px solid var(--border)",
                    borderRadius: "var(--radius)", padding: 16, textAlign: "center",
                  }}>
                    <div style={{
                      fontSize: 14, fontWeight: 600,
                      color: STATUS_COLOR[selectedClient.status] || "var(--text-muted)",
                      marginBottom: 4,
                    }}>
                      {selectedClient.status}
                    </div>
                    <div style={{ fontSize: 12, color: "var(--text-muted)" }}>
                      Statut
                    </div>
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div style={{ display: "flex", gap: 10 }}>
                <a 
                  href="/architect/messages" 
                  className="btn btn-primary" 
                  style={{ flex: 1, justifyContent: "center" }}
                >
                  💬 Envoyer un message
                </a>
                <a 
                  href="/architect/projects" 
                  className="btn btn-secondary" 
                  style={{ flex: 1, justifyContent: "center" }}
                >
                  📐 Voir les projets
                </a>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
