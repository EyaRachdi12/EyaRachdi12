"use client";
import { useState, useEffect } from "react";
import Link from "next/link";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Document {
  id: string;
  name: string;
  type: string;
  date: string;
  size: string;
  status: string;
  file_path?: string;
}

export default function ClientProjectsPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);

  const project = {
    id: "28e84b10",
    name: "Villa Moderne — Famille Dupont",
    architect: "Jean-Marc Leblanc",
    status: "En cours",
    progress: 65,
    startDate: "28 Avr 2026",
    estimatedEnd: "15 Juil 2026",
    budget: "380 000 €",
    area: "99 m²",
    style: "Contemporain minimaliste",
    rooms: 6,
  };

  useEffect(() => {
    // Load project documents
    fetch(`${API_URL}/api/projects/${project.id}/documents`)
      .then(r => r.json())
      .then(data => {
        const docs = data.documents || [];
        
        // Add static documents that don't have files yet
        const staticDocs = [
          { id: "brief", name: "Brief client structuré", type: "DOC", date: "29 Avr", size: "0.5 MB", status: "Actif", file_path: null },
          { id: "sketches", name: "Esquisses IA — Lot 1", type: "ZIP", date: "29 Avr", size: "15 MB", status: "Actif", file_path: null },
          { id: "video", name: "Vidéo 3D — Walkthrough", type: "MP4", date: "1 Mai", size: "45 MB", status: "Nouveau", file_path: null },
        ];
        
        setDocuments([...docs, ...staticDocs]);
        setLoading(false);
      })
      .catch(() => {
        setLoading(false);
      });
  }, []);

  const handleDownload = (doc: Document) => {
    if (!doc.file_path) {
      alert(`Le téléchargement de "${doc.name}" n'est pas encore disponible. Ce document sera ajouté prochainement.`);
      return;
    }

    // Télécharger le fichier
    const downloadUrl = `${API_URL}/api/projects/${project.id}/documents/${doc.id}/download`;
    
    // Ouvrir dans un nouvel onglet pour déclencher le téléchargement
    window.open(downloadUrl, '_blank');
  };

  return (
    <div style={{ maxWidth: 1000 }}>
      <div className="animate-fade-in" style={{ marginBottom: 32 }}>
        <h1 style={{ fontFamily: "'Playfair Display', serif", fontSize: 28, fontWeight: 700, color: "var(--text-primary)", marginBottom: 6 }}>
          Mon Projet
        </h1>
      </div>

      {/* Project header */}
      <div className="animate-fade-in delay-100" style={{
        background: "linear-gradient(135deg, var(--accent-light), var(--surface))",
        border: "1px solid var(--accent)",
        borderRadius: "var(--radius-lg)",
        padding: 28,
        marginBottom: 24,
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 16, marginBottom: 20 }}>
          <div>
            <h2 style={{ fontSize: 22, fontWeight: 700, color: "var(--text-primary)", marginBottom: 6 }}>
              {project.name}
            </h2>
            <p style={{ fontSize: 14, color: "var(--text-secondary)" }}>
              Architecte : <strong style={{ color: "var(--accent)" }}>{project.architect}</strong>
            </p>
          </div>
          <span className="badge badge-gold" style={{ fontSize: 13, padding: "6px 14px" }}>
            {project.status}
          </span>
        </div>

        <div className="progress-bar" style={{ marginBottom: 8 }}>
          <div className="progress-fill" style={{ width: `${project.progress}%` }} />
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, color: "var(--text-muted)" }}>
          <span>Démarré le {project.startDate}</span>
          <span style={{ fontWeight: 600, color: "var(--accent)" }}>{project.progress}%</span>
          <span>Fin estimée : {project.estimatedEnd}</span>
        </div>

        {/* Meta */}
        <div style={{ display: "flex", gap: 20, marginTop: 20, flexWrap: "wrap" }}>
          {[
            { label: "Budget", value: project.budget },
            { label: "Surface", value: project.area },
            { label: "Style", value: project.style },
            { label: "Pièces", value: `${project.rooms} pièces` },
          ].map((m) => (
            <div key={m.label}>
              <div style={{ fontSize: 11, color: "var(--text-muted)" }}>{m.label}</div>
              <div style={{ fontSize: 14, fontWeight: 600, color: "var(--text-primary)" }}>{m.value}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Quick actions */}
      <div className="animate-fade-in delay-200" style={{ display: "flex", gap: 12, marginBottom: 24, flexWrap: "wrap" }}>
        {[
          { label: "❓ Questions sur le plan", href: "/client/vqa" },
          { label: "🎨 Voir les esquisses", href: "/client/sketches" },
          { label: "💬 Contacter l'architecte", href: "/client/messages" },
          { label: "✏️ Modifier le brief", href: "/client/brief" },
        ].map((action) => (
          <Link key={action.label} href={action.href} className="btn btn-secondary" style={{ fontSize: 13 }}>
            {action.label}
          </Link>
        ))}
      </div>

      {/* Documents */}
      <div className="animate-fade-in delay-300" style={{
        background: "var(--surface)", border: "1px solid var(--border)",
        borderRadius: "var(--radius-lg)", padding: 24,
      }}>
        <h2 style={{ fontSize: 16, fontWeight: 600, color: "var(--text-primary)", marginBottom: 16 }}>
          Documents du projet
        </h2>
        
        {loading ? (
          <div style={{ textAlign: "center", padding: 40, color: "var(--text-muted)" }}>
            Chargement des documents...
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {documents.map((doc) => (
              <div key={doc.id} style={{
                display: "flex", gap: 14, alignItems: "center",
                padding: "12px 16px",
                background: "var(--bg-secondary)",
                borderRadius: "var(--radius)",
                border: "1px solid var(--border)",
              }}>
                <div style={{
                  width: 36, height: 36, borderRadius: 8,
                  background: doc.type === "PDF" || doc.type === "PNG" ? "#eb575718" : doc.type === "MP4" ? "#bb6bd918" : "var(--accent-light)",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: 16,
                }}>
                  {doc.type === "PDF" || doc.type === "PNG" ? "📄" : doc.type === "MP4" ? "🎬" : doc.type === "ZIP" ? "🗜️" : "📝"}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 14, fontWeight: 500, color: "var(--text-primary)" }}>{doc.name}</div>
                  <div style={{ fontSize: 12, color: "var(--text-muted)" }}>{doc.date} · {doc.size}</div>
                </div>
                <span style={{
                  fontSize: 11, fontWeight: 600,
                  color: doc.status === "Nouveau" ? "var(--accent)" : doc.status === "Actif" ? "#6fcf97" : "var(--text-muted)",
                  background: doc.status === "Nouveau" ? "var(--accent-light)" : doc.status === "Actif" ? "#6fcf9718" : "var(--bg-secondary)",
                  padding: "3px 8px", borderRadius: 999,
                }}>
                  {doc.status}
                </span>
                <button 
                  onClick={() => handleDownload(doc)}
                  className="btn btn-ghost" 
                  style={{ fontSize: 12, padding: "6px 10px", cursor: "pointer" }}
                  title={doc.file_path ? "Télécharger" : "Pas encore disponible"}
                >
                  ⬇️
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
