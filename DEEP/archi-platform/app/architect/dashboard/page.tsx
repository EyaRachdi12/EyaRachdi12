"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import { useUser } from "@/hooks/useUser";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ArchitectStats {
  total_projects:   number;
  active_projects:  number;
  total_clients:    number;
  plans_analyzed:   number;
  videos_generated: number;
  messages_unread:  number;
}

interface Project {
  id:          string;
  name:        string;
  client_name: string;
  status:      string;
  progress:    number;
  type:        string;
  date:        string;
}

const STATUS_COLOR: Record<string, string> = {
  "En cours":   "#c9a96e",
  "Analyse IA": "#56b4d3",
  "Terminé":    "#6fcf97",
  "En attente": "#9c9590",
};

const FALLBACK_STATS: ArchitectStats = {
  total_projects:   0,
  active_projects:  0,
  total_clients:    0,
  plans_analyzed:   0,
  videos_generated: 0,
  messages_unread:  0,
};

export default function ArchitectDashboard() {
  const { user } = useUser();
  const [stats,          setStats]          = useState<ArchitectStats>(FALLBACK_STATS);
  const [recentProjects, setRecentProjects] = useState<Project[]>([]);
  const [loading,        setLoading]        = useState(true);

  useEffect(() => {
    const archId = user?.id || "arch_1";

    Promise.all([
      fetch(`${API_URL}/api/stats/architect?architect_id=${archId}`)
        .then(r => r.json())
        .catch(() => FALLBACK_STATS),
      fetch(`${API_URL}/api/projects?architect_id=${archId}&limit=4`)
        .then(r => r.json())
        .catch(() => ({ projects: [] })),
    ]).then(([statsData, projData]) => {
      setStats(statsData as ArchitectStats);
      setRecentProjects((projData as { projects: Project[] }).projects || []);
      setLoading(false);
    });
  }, [user]);

  const greeting = () => {
    const h = new Date().getHours();
    if (h < 12) return "Bonjour";
    if (h < 18) return "Bon après-midi";
    return "Bonsoir";
  };

  const today = new Date().toLocaleDateString("fr-FR", {
    weekday: "long", day: "numeric", month: "long", year: "numeric",
  });

  return (
    <div style={{ maxWidth: 1200 }}>
      {/* Header */}
      <div className="animate-fade-in" style={{ marginBottom: 32 }}>
        <h1 style={{ fontFamily: "'Playfair Display', serif", fontSize: 28, fontWeight: 700, color: "var(--text-primary)", marginBottom: 6 }}>
          {greeting()}, {user?.name || "Architecte"} 👋
        </h1>
        <p style={{ color: "var(--text-secondary)", fontSize: 15 }}>
          {today.charAt(0).toUpperCase() + today.slice(1)}
        </p>
      </div>

      {/* Stats */}
      <div className="animate-fade-in delay-100" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 16, marginBottom: 32 }}>
        {loading ? (
          Array(4).fill(0).map((_, i) => (
            <div key={i} className="skeleton" style={{ height: 110, borderRadius: "var(--radius-lg)" }} />
          ))
        ) : [
          { label: "Projets actifs",  value: stats.active_projects,  change: "projets en cours",  icon: "📁", color: "#c9a96e" },
          { label: "Total projets",   value: stats.total_projects,   change: "tous statuts",       icon: "🏗️", color: "#56b4d3" },
          { label: "Clients",         value: stats.total_clients,    change: "inscrits",           icon: "👥", color: "#6fcf97" },
          { label: "Messages",        value: stats.messages_unread,  change: "non lus",            icon: "💬", color: "#bb6bd9" },
        ].map(stat => (
          <div key={stat.label} className="card-hover" style={{
            background: "var(--surface)", border: "1px solid var(--border)",
            borderRadius: "var(--radius-lg)", padding: 24,
          }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 16 }}>
              <span style={{ fontSize: 28 }}>{stat.icon}</span>
              <span style={{ fontSize: 11, fontWeight: 600, color: stat.color, background: `${stat.color}18`, padding: "3px 8px", borderRadius: 999 }}>
                {stat.change}
              </span>
            </div>
            <div style={{ fontSize: 32, fontWeight: 700, color: "var(--text-primary)", fontFamily: "'Playfair Display', serif" }}>
              {stat.value}
            </div>
            <div style={{ fontSize: 13, color: "var(--text-secondary)", marginTop: 4 }}>{stat.label}</div>
          </div>
        ))}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 320px", gap: 24 }}>
        {/* Recent projects */}
        <div className="animate-fade-in delay-200" style={{
          background: "var(--surface)", border: "1px solid var(--border)",
          borderRadius: "var(--radius-lg)", padding: 24,
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
            <h2 style={{ fontSize: 16, fontWeight: 600, color: "var(--text-primary)" }}>Projets récents</h2>
            <Link href="/architect/projects" style={{ fontSize: 13, color: "var(--accent)", textDecoration: "none" }}>Voir tout →</Link>
          </div>

          {loading ? (
            <div style={{ color: "var(--text-muted)", textAlign: "center", padding: 32 }}>Chargement...</div>
          ) : !recentProjects.length ? (
            <div style={{ textAlign: "center", padding: 40, color: "var(--text-muted)" }}>
              <div style={{ fontSize: 32, marginBottom: 8 }}>📁</div>
              <div>Aucun projet pour l&apos;instant</div>
              <Link href="/architect/projects" className="btn btn-primary" style={{ marginTop: 16, fontSize: 13 }}>
                + Créer un projet
              </Link>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              {recentProjects.map(project => (
                <div key={project.id} style={{
                  padding: 16, background: "var(--bg-secondary)",
                  borderRadius: "var(--radius)", border: "1px solid var(--border)",
                  cursor: "pointer",
                }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 10 }}>
                    <div>
                      <div style={{ fontSize: 14, fontWeight: 600, color: "var(--text-primary)", marginBottom: 3 }}>{project.name}</div>
                      <div style={{ fontSize: 12, color: "var(--text-muted)" }}>{project.client_name || "—"} · {project.date}</div>
                    </div>
                    <span style={{
                      fontSize: 11, fontWeight: 600,
                      color: STATUS_COLOR[project.status] || "#9c9590",
                      background: `${STATUS_COLOR[project.status] || "#9c9590"}18`,
                      padding: "3px 8px", borderRadius: 999,
                    }}>
                      {project.status}
                    </span>
                  </div>
                  <div className="progress-bar">
                    <div className="progress-fill" style={{ width: `${project.progress}%` }} />
                  </div>
                  <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 4, textAlign: "right" }}>{project.progress}%</div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right column */}
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          {/* Quick actions */}
          <div className="animate-fade-in delay-300" style={{
            background: "var(--surface)", border: "1px solid var(--border)",
            borderRadius: "var(--radius-lg)", padding: 24,
          }}>
            <h2 style={{ fontSize: 16, fontWeight: 600, color: "var(--text-primary)", marginBottom: 16 }}>Actions rapides</h2>
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {[
                { label: "Analyser un plan",    href: "/architect/upload",    icon: "📤", color: "var(--accent)" },
                { label: "Générer vidéo 3D",    href: "/architect/visualize", icon: "🎬", color: "#bb6bd9" },
                { label: "Nouveau projet",      href: "/architect/projects",  icon: "➕", color: "#6fcf97" },
                { label: "Voir les messages",   href: "/architect/messages",  icon: "💬", color: "#56b4d3" },
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

          {/* Profile card */}
          <div className="animate-fade-in delay-400" style={{
            background: "linear-gradient(135deg, var(--accent-light), var(--surface))",
            border: "1px solid var(--accent)", borderRadius: "var(--radius-lg)", padding: 20,
          }}>
            <div style={{ display: "flex", gap: 12, alignItems: "center", marginBottom: 12 }}>
              <div style={{
                width: 44, height: 44, borderRadius: "50%",
                background: "linear-gradient(135deg, var(--accent), #e8c98e)",
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: 18, fontWeight: 700, color: "white",
              }}>
                {user?.name ? user.name[0].toUpperCase() : "A"}
              </div>
              <div>
                <div style={{ fontSize: 14, fontWeight: 600, color: "var(--text-primary)" }}>{user?.name || "Architecte"}</div>
                <div style={{ fontSize: 12, color: "var(--text-muted)" }}>{user?.email || ""}</div>
              </div>
            </div>
            {user?.specialty && (
              <div style={{ fontSize: 12, color: "var(--accent-dark)", background: "var(--accent-light)", padding: "4px 10px", borderRadius: 999, display: "inline-block" }}>
                {user.specialty}
              </div>
            )}
            {user?.city && (
              <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 6 }}>📍 {user.city}</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
