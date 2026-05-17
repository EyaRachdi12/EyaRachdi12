
"use client";
import { useState, useEffect } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface FloorPlan {
  id: string;
  title: string;
  type: string;
  rooms: number;
  surface: number;
  style: string;
  image_file?: string;
  description: string;
  features: string[];
}

export default function ExplorerPage() {
  const router = useRouter();
  const [selectedType, setSelectedType] = useState("all");
  const [selectedStyle, setSelectedStyle] = useState("all");
  const [floorPlans, setFloorPlans] = useState<FloorPlan[]>([]);
  const [loading, setLoading] = useState(true);

  // Fetch floor plans from backend
  useEffect(() => {
    const fetchPlans = async () => {
      try {
        const res = await fetch(`${API_URL}/api/floor-plans`);
        if (res.ok) {
          const data = await res.json();
          setFloorPlans(data.plans);
        }
      } catch (error) {
        console.error("Failed to fetch floor plans:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchPlans();
  }, []);

  const planTypes = ["all", "Studio", "T2", "T3", "T4", "Loft"];
  const styles = ["all", "Contemporain", "Minimaliste"];

  const filteredPlans = floorPlans.filter(plan => {
    const typeMatch = selectedType === "all" || plan.type === selectedType;
    const styleMatch = selectedStyle === "all" || plan.style === selectedStyle;
    return typeMatch && styleMatch;
  });

  const handleAnalyze = (planId: string) => {
    // Redirect to VQA page with plan ID
    router.push(`/client/vqa?plan=${planId}`);
  };

  const handleDownload = async (planId: string) => {
    try {
      // Download the floor plan image
      const link = document.createElement('a');
      link.href = `${API_URL}/api/floor-plans/${planId}/download`;
      link.download = '';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (error) {
      console.error("Download failed:", error);
      alert("Erreur lors du téléchargement");
    }
  };

  return (
    <div style={{ maxWidth: 1200 }}>
      {/* Header */}
      <div className="animate-fade-in" style={{ marginBottom: 32 }}>
        <h1 style={{ fontFamily: "'Playfair Display', serif", fontSize: 32, fontWeight: 700, color: "var(--text-primary)", marginBottom: 8 }}>
          📐 Explorer les Plans
        </h1>
        <p style={{ color: "var(--text-secondary)", fontSize: 16 }}>
          Découvrez notre bibliothèque de plans architecturaux types — Analysez-les avec l&apos;IA
        </p>
      </div>

      {/* Filters */}
      <div className="animate-fade-in delay-100" style={{
        background: "var(--surface)", border: "1px solid var(--border)",
        borderRadius: "var(--radius-lg)", padding: 24, marginBottom: 32,
      }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}>
          {/* Type Filter */}
          <div>
            <h3 style={{ fontSize: 14, fontWeight: 600, color: "var(--text-primary)", marginBottom: 12 }}>
              Type de logement
            </h3>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              {planTypes.map(type => (
                <button
                  key={type}
                  onClick={() => setSelectedType(type)}
                  style={{
                    padding: "6px 14px", borderRadius: 999,
                    border: `1px solid ${selectedType === type ? "var(--accent)" : "var(--border)"}`,
                    background: selectedType === type ? "var(--accent-light)" : "var(--bg-secondary)",
                    color: selectedType === type ? "var(--accent-dark)" : "var(--text-secondary)",
                    fontSize: 13, fontWeight: selectedType === type ? 600 : 400,
                    cursor: "pointer", transition: "all 0.2s ease",
                  }}
                >
                  {type === "all" ? "Tous" : type}
                </button>
              ))}
            </div>
          </div>

          {/* Style Filter */}
          <div>
            <h3 style={{ fontSize: 14, fontWeight: 600, color: "var(--text-primary)", marginBottom: 12 }}>
              Style architectural
            </h3>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              {styles.map(style => (
                <button
                  key={style}
                  onClick={() => setSelectedStyle(style)}
                  style={{
                    padding: "6px 14px", borderRadius: 999,
                    border: `1px solid ${selectedStyle === style ? "var(--accent)" : "var(--border)"}`,
                    background: selectedStyle === style ? "var(--accent-light)" : "var(--bg-secondary)",
                    color: selectedStyle === style ? "var(--accent-dark)" : "var(--text-secondary)",
                    fontSize: 13, fontWeight: selectedStyle === style ? 600 : 400,
                    cursor: "pointer", transition: "all 0.2s ease",
                  }}
                >
                  {style === "all" ? "Tous" : style}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Results count */}
        <div style={{ marginTop: 16, paddingTop: 16, borderTop: "1px solid var(--border)" }}>
          <span style={{ fontSize: 13, color: "var(--text-muted)" }}>
            {filteredPlans.length} plan{filteredPlans.length > 1 ? 's' : ''} trouvé{filteredPlans.length > 1 ? 's' : ''}
          </span>
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div style={{
          textAlign: "center",
          padding: 60,
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: "var(--radius-lg)",
        }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>⏳</div>
          <p style={{ fontSize: 14, color: "var(--text-secondary)" }}>
            Chargement des plans...
          </p>
        </div>
      )}

      {/* Plans Grid */}
      {!loading && (
        <div className="animate-scale-in" style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))",
          gap: 20,
        }}>
          {filteredPlans.map(plan => (
          <div
            key={plan.id}
            className="card-hover"
            style={{
              background: "var(--surface)",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius-lg)",
              overflow: "hidden",
              transition: "all 0.3s ease",
            }}
          >
            {/* Image */}
            <div style={{
              height: 220,
              background: "#f5f5f5",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              position: "relative",
              overflow: "hidden",
            }}>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={`${API_URL}/api/floor-plans/${plan.id}/image`}
                alt={plan.title}
                loading="lazy"
                style={{
                  width: "100%",
                  height: "100%",
                  objectFit: "contain",
                }}
              />
              
              {/* Badges */}
              <div style={{
                position: "absolute",
                top: 12,
                left: 12,
                display: "flex",
                gap: 8,
              }}>
                <div style={{
                  background: "var(--accent)",
                  color: "white",
                  fontSize: 11,
                  fontWeight: 600,
                  padding: "4px 10px",
                  borderRadius: 999,
                }}>
                  {plan.type}
                </div>
                <div style={{
                  background: "rgba(0,0,0,0.6)",
                  color: "white",
                  fontSize: 11,
                  padding: "4px 10px",
                  borderRadius: 999,
                  backdropFilter: "blur(4px)",
                }}>
                  {plan.surface} m²
                </div>
              </div>
            </div>

            {/* Content */}
            <div style={{ padding: 20 }}>
              <h3 style={{
                fontSize: 16,
                fontWeight: 600,
                color: "var(--text-primary)",
                marginBottom: 6,
              }}>
                {plan.title}
              </h3>

              <p style={{
                fontSize: 13,
                color: "var(--text-secondary)",
                marginBottom: 12,
                lineHeight: 1.5,
              }}>
                {plan.description}
              </p>

              {/* Stats */}
              <div style={{
                display: "flex",
                gap: 16,
                marginBottom: 12,
                paddingBottom: 12,
                borderBottom: "1px solid var(--border)",
              }}>
                <div>
                  <div style={{ fontSize: 11, color: "var(--text-muted)" }}>Pièces</div>
                  <div style={{ fontSize: 15, fontWeight: 600, color: "var(--accent)" }}>
                    {plan.rooms}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: 11, color: "var(--text-muted)" }}>Surface</div>
                  <div style={{ fontSize: 15, fontWeight: 600, color: "var(--accent)" }}>
                    {plan.surface} m²
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: 11, color: "var(--text-muted)" }}>Style</div>
                  <div style={{ fontSize: 15, fontWeight: 600, color: "var(--accent)" }}>
                    {plan.style}
                  </div>
                </div>
              </div>

              {/* Features */}
              <div style={{ marginBottom: 16 }}>
                <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 6 }}>
                  Caractéristiques:
                </div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                  {plan.features.slice(0, 3).map(feature => (
                    <span
                      key={feature}
                      style={{
                        fontSize: 11,
                        padding: "3px 8px",
                        background: "var(--bg-secondary)",
                        border: "1px solid var(--border)",
                        borderRadius: 999,
                        color: "var(--text-secondary)",
                      }}
                    >
                      {feature}
                    </span>
                  ))}
                  {plan.features.length > 3 && (
                    <span style={{
                      fontSize: 11,
                      padding: "3px 8px",
                      color: "var(--text-muted)",
                    }}>
                      +{plan.features.length - 3}
                    </span>
                  )}
                </div>
              </div>

              {/* Actions */}
              <div style={{ display: "flex", gap: 8 }}>
                <button
                  onClick={() => handleAnalyze(plan.id)}
                  className="btn btn-primary"
                  style={{
                    flex: 1,
                    justifyContent: "center",
                    fontSize: 13,
                    padding: "8px 12px",
                  }}
                >
                  🤖 Analyser avec IA
                </button>
                <button
                  onClick={() => handleDownload(plan.id)}
                  className="btn btn-secondary"
                  style={{
                    fontSize: 13,
                    padding: "8px 12px",
                  }}
                >
                  ⬇️
                </button>
              </div>
            </div>
          </div>
          ))}
        </div>
      )}

      {/* Empty State */}
      {!loading && filteredPlans.length === 0 && (
        <div style={{
          textAlign: "center",
          padding: 60,
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: "var(--radius-lg)",
        }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>🔍</div>
          <h3 style={{
            fontSize: 18,
            fontWeight: 600,
            color: "var(--text-primary)",
            marginBottom: 8,
          }}>
            Aucun plan trouvé
          </h3>
          <p style={{ fontSize: 14, color: "var(--text-secondary)" }}>
            Essayez de modifier vos filtres
          </p>
        </div>
      )}

      {/* Info Banner */}
      <div style={{
        marginTop: 32,
        padding: 20,
        background: "var(--accent-light)",
        border: "1px solid var(--accent)",
        borderRadius: "var(--radius-lg)",
        display: "flex",
        gap: 16,
        alignItems: "center",
      }}>
        <span style={{ fontSize: 32 }}>💡</span>
        <div style={{ flex: 1 }}>
          <h4 style={{
            fontSize: 14,
            fontWeight: 600,
            color: "var(--accent-dark)",
            marginBottom: 4,
          }}>
            Analysez les plans avec l&apos;IA
          </h4>
          <p style={{ fontSize: 13, color: "var(--text-secondary)" }}>
            Cliquez sur &quot;Analyser avec IA&quot; pour poser des questions sur n&apos;importe quel plan — 
            localisation des pièces, surfaces, orientation, et plus encore!
          </p>
        </div>
      </div>
    </div>
  );
}
