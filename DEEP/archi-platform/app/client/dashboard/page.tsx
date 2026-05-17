"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import { useUser } from "@/hooks/useUser";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Project {
  id: string; name: string; status: string; progress: number;
  client_name: string; date: string; type: string;
}

interface Brief {
  description: string; caption: string; total_area: number;
  style: string; rooms: { name: string; area: number }[];
}

export default function ClientDashboard() {
  const { user } = useUser();
  const [projects, setProjects] = useState<Project[]>([]);
  const [brief,    setBrief]    = useState<Brief | null>(null);
  const [unread,   setUnread]   = useState(0);
  const [loading,  setLoading]  = useState(true);

  useEffect(() => {
    if (!user) return;

    // Load projects for this client
    fetch(`${API_URL}/api/projects?client_id=${user.id}`)
      .then(r => r.json())
      .then(d => setProjects(d.projects || []))
      .catch(() => {});

    // Load brief
    fetch(`${API_URL}/api/briefs/${user.id}`)
      .then(r => r.json())
      .then(d => { if (d.brief) setBrief(d.brief); })
      .catch(() => {});

    // Load unread messages
    fetch(`${API_URL}/api/conversations`)
      .then(r => r.json())
      .then(d => {
        const convs = d.conversations || [];
        const myConv = convs.find((c: { client_id: string; unread_client: number }) => c.client_id === user.id);
        if (myConv) setUnread(myConv.unread_client || 0);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [user]);

  const greeting = () => {
    const h = new Date().getHours();
    if (h < 12) return "Bonjour";
    if (h < 18) return "Bon après-midi";
    return "Bonsoir";
  };

  const activeProject = projects.find(p => p.status === "En cours") || projects[0];

  return (
    <div style={{ maxWidth: 1100 }}>
      <div className="animate-fade-in" style={{ marginBottom: 32 }}>
        <h1 style={{ fontFamily: "'Playfair Display', serif", fontSize: 28, fontWeight: 700, color: "var(--text-primary)", marginBottom: 6 }}>
          {greeting()}, {user?.name?.split(" ")[0] || "Client"} 👋
        </h1>
        <p style={{ color: "var(--text-secondary)", fontSize: 15 }}>
          {brief ? "Votre brief est enregistré." : "Commencez par décrire votre projet."}
        </p>
      </div>

      {/* Active project */}
      {activeProject ? (
        <div className="animate-fade-in delay-100" style={{
          background: "linear-gradient(135deg, var(--accent-light), var(--surface))",
          border: "1px solid var(--accent)", borderRadius: "var(--radius-lg)",
          padding: 28, marginBottom: 24,
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 16, marginBottom: 16 }}>
            <div>
              <span className="badge badge-gold" style={{ marginBottom: 8, display: "inline-block" }}>Projet actif</span>
              <h2 style={{ fontSize: 20, fontWeight: 700, color: "var(--text-primary)", marginBottom: 4 }}>{activeProject.name}</h2>
              <p style={{ fontSize: 14, color: "var(--text-secondary)" }}>Démarré le {activeProject.date}</p>
            </div>
            <div style={{ textAlign: "right" }}>
              <div style={{ fontSize: 36, fontWeight: 700, color: "var(--accent)", fontFamily: "'Playfair Display', serif" }}>
                {activeProject.progress}%
              </div>
              <div style={{ fontSize: 12, color: "var(--text-muted)" }}>Avancement</div>
            </div>
          </div>
          <div className="progress-bar" style={{ marginBottom: 8 }}>
            <div className="progress-fill" style={{ width: `${activeProject.progress}%` }} />
          </div>
          <div style={{ display: "flex", justifyContent: "flex-end" }}>
            <Link href="/client/projects" className="btn btn-primary" style={{ fontSize: 13, padding: "8px 16px" }}>
              Voir le projet →
            </Link>
          </div>
        </div>
      ) : (
        <div className="animate-fade-in delay-100" style={{
          background: "var(--surface)", border: "1px dashed var(--border)",
          borderRadius: "var(--radius-lg)", padding: 32, marginBottom: 24, textAlign: "center",
        }}>
          <div style={{ fontSize: 40, marginBottom: 12 }}>🏗️</div>
          <div style={{ fontSize: 16, fontWeight: 600, color: "var(--text-primary)", marginBottom: 8 }}>Aucun projet actif</div>
          <p style={{ fontSize: 14, color: "var(--text-secondary)", marginBottom: 16 }}>
            Décrivez votre projet pour commencer
          </p>
          <Link href="/client/brief" className="btn btn-primary">✍️ Créer mon brief</Link>
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "1fr 300px", gap: 24 }}>
        {/* Quick actions */}
        <div className="animate-fade-in delay-200" style={{
          background: "var(--surface)", border: "1px solid var(--border)",
          borderRadius: "var(--radius-lg)", padding: 24,
        }}>
          <h2 style={{ fontSize: 16, fontWeight: 600, color: "var(--text-primary)", marginBottom: 16 }}>
            Que voulez-vous faire ?
          </h2>
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {[
              { label: brief ? "Modifier mon brief" : "Créer mon brief", href: "/client/brief",    icon: "✍️" },
              { label: "Poser une question sur le plan",                  href: "/client/vqa",      icon: "❓" },
              { label: "Voir les esquisses IA",                           href: "/client/sketches", icon: "🎨" },
              { label: `Messages${unread > 0 ? ` (${unread} non lu${unread > 1 ? "s" : ""})` : ""}`, href: "/client/messages", icon: "💬" },
            ].map(action => (
              <Link key={action.label} href={action.href} style={{
                display: "flex", alignItems: "center", gap: 12,
                padding: "12px 14px", background: "var(--bg-secondary)",
                borderRadius: "var(--radius)", border: "1px solid var(--border)",
                textDecoration: "none", color: "var(--text-primary)",
                fontSize: 14, fontWeight: 500, transition: "all 0.2s ease",
              }}>
                <span style={{ fontSize: 18 }}>{action.icon}</span>
                {action.label}
                <span style={{ marginLeft: "auto", color: "var(--text-muted)" }}>→</span>
              </Link>
            ))}
          </div>
        </div>

        {/* Brief summary */}
        <div className="animate-fade-in delay-300" style={{
          background: "var(--surface)", border: "1px solid var(--border)",
          borderRadius: "var(--radius-lg)", padding: 20,
        }}>
          <h2 style={{ fontSize: 15, fontWeight: 600, color: "var(--text-primary)", marginBottom: 14 }}>
            Mon Brief
          </h2>
          {brief ? (
            <div>
              <div style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.6, marginBottom: 12 }}>
                {brief.caption}
              </div>
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 12 }}>
                <span className="badge badge-gold">{brief.total_area} m²</span>
                <span className="badge badge-gold">{brief.style}</span>
                <span className="badge badge-gold">{brief.rooms?.length} pièces</span>
              </div>
              <Link href="/client/brief" className="btn btn-secondary" style={{ width: "100%", justifyContent: "center", fontSize: 13 }}>
                ✏️ Modifier
              </Link>
            </div>
          ) : (
            <div style={{ textAlign: "center", padding: "20px 0" }}>
              <div style={{ fontSize: 32, marginBottom: 8 }}>📝</div>
              <div style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 12 }}>
                Pas encore de brief
              </div>
              <Link href="/client/brief" className="btn btn-primary" style={{ fontSize: 13 }}>
                Créer mon brief →
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
