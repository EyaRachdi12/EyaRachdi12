"use client";
import { useState, useEffect } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface AIStat {
  label: string;
  value: number;
  icon: string;
  color: string;
}

interface MonthlyData {
  month: string;
  plans: number;
  videos: number;
  clients: number;
}

interface ModelUsage {
  label: string;
  pct: number;
  color: string;
}

interface TopProject {
  name: string;
  activity: number;
  color: string;
}

interface AnalyticsData {
  ai_stats: AIStat[];
  monthly_data: MonthlyData[];
  model_usage: ModelUsage[];
  top_projects: TopProject[];
  summary: {
    total_clients: number;
    total_projects: number;
    active_projects: number;
    total_messages: number;
  };
}

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`${API_URL}/api/analytics`)
      .then(r => r.json())
      .then(d => {
        setData(d);
        setLoading(false);
      })
      .catch(() => {
        setError("Impossible de charger les analytics. Vérifiez que le backend est démarré.");
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div style={{ maxWidth: 1100 }}>
        <div style={{ textAlign: "center", padding: 60, color: "var(--text-muted)" }}>
          <div style={{ fontSize: 32, marginBottom: 12 }}>📊</div>
          Chargement des analytics...
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div style={{ maxWidth: 1100 }}>
        <div style={{ padding: "12px 16px", background: "#eb575718", border: "1px solid #eb5757", borderRadius: "var(--radius)", marginBottom: 20, fontSize: 13, color: "#eb5757" }}>
          {error || "Erreur lors du chargement des données"}
        </div>
      </div>
    );
  }

  const maxPlans = Math.max(...data.monthly_data.map(d => d.plans), 1);

  return (
    <div style={{ maxWidth: 1100 }}>
      <div className="animate-fade-in" style={{ marginBottom: 32 }}>
        <h1 style={{ fontFamily: "'Playfair Display', serif", fontSize: 28, fontWeight: 700, color: "var(--text-primary)", marginBottom: 6 }}>
          Analytiques
        </h1>
        <p style={{ color: "var(--text-secondary)", fontSize: 15 }}>
          Suivi de votre activité et des performances IA · {data.summary.total_clients} clients · {data.summary.active_projects} projets actifs
        </p>
      </div>

      {/* AI Stats */}
      <div className="animate-fade-in delay-100" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 14, marginBottom: 28 }}>
        {data.ai_stats.map((stat) => (
          <div key={stat.label} className="card-hover" style={{
            background: "var(--surface)", border: "1px solid var(--border)",
            borderRadius: "var(--radius-lg)", padding: 20, textAlign: "center",
          }}>
            <div style={{ fontSize: 28, marginBottom: 8 }}>{stat.icon}</div>
            <div style={{ fontSize: 28, fontWeight: 700, color: stat.color, fontFamily: "'Playfair Display', serif" }}>
              {stat.value}
            </div>
            <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 4 }}>{stat.label}</div>
          </div>
        ))}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 340px", gap: 24 }}>
        {/* Bar chart */}
        <div className="animate-fade-in delay-200" style={{
          background: "var(--surface)", border: "1px solid var(--border)",
          borderRadius: "var(--radius-lg)", padding: 24,
        }}>
          <h2 style={{ fontSize: 16, fontWeight: 600, color: "var(--text-primary)", marginBottom: 24 }}>
            Activité mensuelle
          </h2>

          {/* Legend */}
          <div style={{ display: "flex", gap: 20, marginBottom: 20 }}>
            {[
              { label: "Plans analysés", color: "var(--accent)" },
              { label: "Vidéos 3D", color: "#bb6bd9" },
              { label: "Nouveaux clients", color: "#6fcf97" },
            ].map((l) => (
              <div key={l.label} style={{ display: "flex", gap: 6, alignItems: "center" }}>
                <div style={{ width: 10, height: 10, borderRadius: 2, background: l.color }} />
                <span style={{ fontSize: 12, color: "var(--text-muted)" }}>{l.label}</span>
              </div>
            ))}
          </div>

          {/* Bars */}
          <div style={{ display: "flex", gap: 16, alignItems: "flex-end", height: 200 }}>
            {data.monthly_data.map((d) => (
              <div key={d.month} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: 4 }}>
                <div style={{ width: "100%", display: "flex", gap: 3, alignItems: "flex-end", height: 160 }}>
                  {/* Plans bar */}
                  <div style={{
                    flex: 1, borderRadius: "4px 4px 0 0",
                    background: "var(--accent)",
                    height: `${(d.plans / maxPlans) * 100}%`,
                    transition: "height 0.5s ease",
                    minHeight: 4,
                  }} />
                  {/* Videos bar */}
                  <div style={{
                    flex: 1, borderRadius: "4px 4px 0 0",
                    background: "#bb6bd9",
                    height: `${(d.videos / maxPlans) * 100}%`,
                    transition: "height 0.5s ease",
                    minHeight: 4,
                  }} />
                  {/* Clients bar */}
                  <div style={{
                    flex: 1, borderRadius: "4px 4px 0 0",
                    background: "#6fcf97",
                    height: `${(d.clients / maxPlans) * 100}%`,
                    transition: "height 0.5s ease",
                    minHeight: 4,
                  }} />
                </div>
                <span style={{ fontSize: 11, color: "var(--text-muted)" }}>{d.month}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Right column */}
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          {/* Model usage */}
          <div className="animate-fade-in delay-300" style={{
            background: "var(--surface)", border: "1px solid var(--border)",
            borderRadius: "var(--radius-lg)", padding: 24,
          }}>
            <h2 style={{ fontSize: 16, fontWeight: 600, color: "var(--text-primary)", marginBottom: 16 }}>
              Utilisation des modèles IA
            </h2>
            {data.model_usage.map((m) => (
              <div key={m.label} style={{ marginBottom: 14 }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                  <span style={{ fontSize: 13, color: "var(--text-secondary)" }}>{m.label}</span>
                  <span style={{ fontSize: 13, fontWeight: 600, color: m.color }}>{m.pct}%</span>
                </div>
                <div className="progress-bar">
                  <div style={{ height: "100%", width: `${m.pct}%`, background: m.color, borderRadius: 2, transition: "width 0.5s ease" }} />
                </div>
              </div>
            ))}
          </div>

          {/* Top projects */}
          <div className="animate-fade-in delay-400" style={{
            background: "var(--surface)", border: "1px solid var(--border)",
            borderRadius: "var(--radius-lg)", padding: 24,
          }}>
            <h2 style={{ fontSize: 16, fontWeight: 600, color: "var(--text-primary)", marginBottom: 16 }}>
              Projets les plus actifs
            </h2>
            {data.top_projects.map((p) => (
              <div key={p.name} style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 12 }}>
                <div style={{ width: 8, height: 8, borderRadius: "50%", background: p.color, flexShrink: 0 }} />
                <span style={{ flex: 1, fontSize: 13, color: "var(--text-secondary)" }}>{p.name}</span>
                <span style={{ fontSize: 13, fontWeight: 600, color: p.color }}>{p.activity} actions</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
