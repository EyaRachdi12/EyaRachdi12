"use client";
import { useState, useRef, useCallback } from "react";
import dynamic from "next/dynamic";

const FloorPlan3DViewer = dynamic(
  () => import("@/components/FloorPlan3DViewer"),
  { ssr: false }
);

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type Stage = "input" | "parsing" | "viewer";

interface RoomData {
  name: string;
  area: number;
  windows: number;
}

const STYLES = ["contemporain", "haussmannien", "industriel", "méditerranéen", "bioclimatique", "scandinave"];

const EXAMPLES = [
  "Une villa contemporaine avec un grand salon lumineux de 35m², une cuisine ouverte, 3 chambres dont une suite parentale, une terrasse avec vue sur jardin.",
  "Un appartement haussmannien rénové avec salon de 30m², cuisine équipée, 2 chambres, salle de bain, couloir d'entrée.",
  "Une maison bioclimatique avec salon ouvert sur terrasse de 20m², cuisine, 3 chambres, salle de bain, bureau, garage.",
];

export default function VisualizePage() {
  const [stage,       setStage]       = useState<Stage>("input");
  const [description, setDescription] = useState("");
  const [style,       setStyle]       = useState("contemporain");
  const [imageFile,   setImageFile]   = useState<File | null>(null);
  const [imagePreview,setImagePreview]= useState<string>("");
  const [rooms,       setRooms]       = useState<RoomData[]>([]);
  const [parsedInfo,  setParsedInfo]  = useState<{total_area:number;has_garden:boolean;has_pool:boolean;has_terrace:boolean} | null>(null);
  const [error,       setError]       = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setImageFile(f);
    const reader = new FileReader();
    reader.onload = ev => setImagePreview(ev.target?.result as string);
    reader.readAsDataURL(f);
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const f = e.dataTransfer.files?.[0];
    if (!f || !f.type.startsWith("image/")) return;
    setImageFile(f);
    const reader = new FileReader();
    reader.onload = ev => setImagePreview(ev.target?.result as string);
    reader.readAsDataURL(f);
  }, []);

  const handleGenerate = async () => {
    if (description.trim().length < 10) return;
    setStage("parsing");
    setError("");
    try {
      // Use multipart form data if image is provided
      if (imageFile) {
        const formData = new FormData();
        formData.append("description", description);
        formData.append("style", style);
        formData.append("image", imageFile);
        
        const res = await fetch(`${API_URL}/api/parse-description-with-image`, {
          method: "POST",
          body: formData,
        });
        if (!res.ok) throw new Error(`Erreur ${res.status}`);
        const data = await res.json();
        setRooms(data.rooms);
        setParsedInfo({
          total_area:  data.total_area,
          has_garden:  data.has_garden,
          has_pool:    data.has_pool,
          has_terrace: data.has_terrace,
        });
        setStage("viewer");
      } else {
        // Text-only mode
        const res = await fetch(`${API_URL}/api/parse-description`, {
          method:  "POST",
          headers: { "Content-Type": "application/json" },
          body:    JSON.stringify({ description, style }),
        });
        if (!res.ok) throw new Error(`Erreur ${res.status}`);
        const data = await res.json();
        setRooms(data.rooms);
        setParsedInfo({
          total_area:  data.total_area,
          has_garden:  data.has_garden,
          has_pool:    data.has_pool,
          has_terrace: data.has_terrace,
        });
        setStage("viewer");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur inconnue");
      setStage("input");
    }
  };

  const reset = () => {
    setStage("input");
    setRooms([]);
    setParsedInfo(null);
    setError("");
  };

  // ── INPUT STAGE ────────────────────────────────────────────────────────────
  if (stage === "input" || stage === "parsing") {
    return (
      <div style={{ maxWidth: 960 }}>
        {/* Header */}
        <div className="animate-fade-in" style={{ marginBottom: 28 }}>
          <h1 style={{ fontFamily: "'Playfair Display', serif", fontSize: 28, fontWeight: 700, color: "var(--text-primary)", marginBottom: 6 }}>
            Visualisation 3D Interactive
          </h1>
          <p style={{ color: "var(--text-secondary)", fontSize: 15 }}>
            Uploadez le plan 2D et décrivez le projet — ArchiGuide génère une visite 3D interactive.
          </p>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>

          {/* LEFT — Image upload */}
          <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
            <div
              onDrop={handleDrop}
              onDragOver={e => e.preventDefault()}
              onClick={() => fileRef.current?.click()}
              style={{
                background: "var(--surface)", border: `2px dashed ${imageFile ? "var(--accent)" : "var(--border)"}`,
                borderRadius: "var(--radius-lg)", padding: 24, cursor: "pointer",
                transition: "all 0.2s ease", minHeight: 280,
                display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
              }}
            >
              <input ref={fileRef} type="file" accept="image/*" style={{ display: "none" }} onChange={handleImageChange} />
              {imagePreview ? (
                <div style={{ width: "100%", textAlign: "center" }}>
                  <img src={imagePreview} alt="Plan" style={{ maxWidth: "100%", maxHeight: 220, borderRadius: 8, objectFit: "contain" }} />
                  <div style={{ fontSize: 12, color: "var(--accent)", marginTop: 8, fontWeight: 600 }}>
                    ✅ {imageFile?.name}
                  </div>
                  <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 4 }}>
                    Cliquez pour changer
                  </div>
                </div>
              ) : (
                <>
                  <div style={{ fontSize: 48, marginBottom: 12 }}>🏗️</div>
                  <div style={{ fontSize: 14, fontWeight: 600, color: "var(--text-primary)", marginBottom: 6 }}>
                    Uploadez le plan de masse
                  </div>
                  <div style={{ fontSize: 12, color: "var(--text-muted)", textAlign: "center" }}>
                    Glissez-déposez ou cliquez<br />PNG, JPG, WEBP
                  </div>
                </>
              )}
            </div>

            {/* Style selector */}
            <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "var(--radius-lg)", padding: 20 }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: "var(--text-primary)", marginBottom: 12 }}>🎨 Style architectural</div>
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                {STYLES.map(s => (
                  <button key={s} onClick={() => setStyle(s)} style={{
                    padding: "6px 14px", borderRadius: 999,
                    border: `1px solid ${style === s ? "var(--accent)" : "var(--border)"}`,
                    background: style === s ? "var(--accent-light)" : "var(--bg-secondary)",
                    color: style === s ? "var(--accent-dark)" : "var(--text-secondary)",
                    fontSize: 12, fontWeight: style === s ? 600 : 400,
                    cursor: "pointer", transition: "all 0.2s ease", textTransform: "capitalize",
                  }}>
                    {s}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* RIGHT — Description */}
          <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
            <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "var(--radius-lg)", padding: 24, flex: 1 }}>
              <label style={{ fontSize: 13, fontWeight: 600, color: "var(--text-primary)", display: "block", marginBottom: 10 }}>
                ✍️ Description du projet
              </label>
              <textarea
                className="input"
                style={{ minHeight: 180, resize: "vertical", fontFamily: "inherit", lineHeight: 1.7, fontSize: 13 }}
                placeholder="Ex: Un appartement avec salon de 30m², cuisine ouverte, 2 chambres dont une suite parentale, salle de bain, couloir d'entrée. Style contemporain avec grandes fenêtres..."
                value={description}
                onChange={e => setDescription(e.target.value)}
              />
              <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 6 }}>
                {description.length} caractères — mentionnez les pièces et leurs surfaces (ex: salon 30m²)
              </div>
            </div>

            {/* Examples */}
            <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "var(--radius-lg)", padding: 16 }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: "var(--text-primary)", marginBottom: 10 }}>💡 Exemples</div>
              {EXAMPLES.map((ex, i) => (
                <button key={i} onClick={() => setDescription(ex)} style={{
                  width: "100%", textAlign: "left", padding: "8px 10px",
                  background: "var(--bg-secondary)", border: "1px solid var(--border)",
                  borderRadius: "var(--radius)", fontSize: 11, color: "var(--text-secondary)",
                  cursor: "pointer", marginBottom: 6, lineHeight: 1.5, transition: "all 0.2s ease",
                }}>
                  {ex.substring(0, 90)}...
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div style={{ marginTop: 16, padding: "12px 16px", background: "rgba(235,87,87,0.1)", border: "1px solid #eb5757", borderRadius: "var(--radius)", fontSize: 13, color: "#eb5757" }}>
            ❌ {error}
          </div>
        )}

        {/* Info banner */}
        <div style={{
          marginTop: 20, padding: "12px 16px", background: "var(--accent-light)",
          border: "1px solid var(--accent)", borderRadius: "var(--radius)",
          fontSize: 13, color: "var(--accent-dark)", display: "flex", gap: 10, alignItems: "center",
        }}>
          <span style={{ fontSize: 18 }}>ℹ️</span>
          <div>
            <strong>Visualisation 3D interactive</strong> — Le positionnement des pièces est généré automatiquement pour une exploration immersive. 
            Utilisez les contrôles pour visiter l'espace en 3D.
          </div>
        </div>

        {/* CTA */}
        <div style={{ marginTop: 20, display: "flex", gap: 12, alignItems: "center" }}>
          <button
            onClick={handleGenerate}
            disabled={description.trim().length < 10 || stage === "parsing"}
            className="btn btn-primary"
            style={{ fontSize: 15, padding: "14px 32px", opacity: description.trim().length < 10 ? 0.5 : 1 }}
          >
            {stage === "parsing" ? "⏳ Analyse en cours..." : "🏗️ Générer la visualisation 3D →"}
          </button>
          {!imageFile && (
            <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
              (Le plan image est optionnel)
            </span>
          )}
        </div>
      </div>
    );
  }

  // ── VIEWER STAGE ───────────────────────────────────────────────────────────
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      {/* Header bar */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 12 }}>
        <div>
          <h1 style={{ fontFamily: "'Playfair Display', serif", fontSize: 22, fontWeight: 700, color: "var(--text-primary)", marginBottom: 2 }}>
            Visualisation 3D Interactive
          </h1>
          <p style={{ color: "var(--text-secondary)", fontSize: 13 }}>
            {rooms.length} pièces · {parsedInfo?.total_area}m² · Style {style}
            {parsedInfo?.has_terrace && " · Terrasse"}
            {parsedInfo?.has_garden && " · Jardin"}
            {parsedInfo?.has_pool && " · Piscine"}
          </p>
        </div>
        <button onClick={reset} className="btn btn-ghost" style={{ fontSize: 13 }}>
          ← Nouvelle visualisation
        </button>
      </div>

      {/* Main layout: 3D viewer + side panel */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 280px", gap: 16, height: "calc(100vh - 200px)", minHeight: 520 }}>

        {/* 3D Viewer */}
        <div style={{
          background: "#1a1714", borderRadius: "var(--radius-lg)",
          overflow: "hidden", border: "1px solid var(--border)", position: "relative",
        }}>
          <FloorPlan3DViewer rooms={rooms} autoTour={false} />
        </div>

        {/* Side panel */}
        <div style={{ display: "flex", flexDirection: "column", gap: 12, overflowY: "auto" }}>

          {/* Floor plan image reference */}
          {imagePreview && (
            <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "var(--radius-lg)", padding: 14 }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: "var(--text-primary)", marginBottom: 8 }}>📐 Plan de référence</div>
              <img src={imagePreview} alt="Plan" style={{ width: "100%", borderRadius: 6, objectFit: "contain", maxHeight: 160 }} />
            </div>
          )}

          {/* Room list */}
          <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "var(--radius-lg)", padding: 14 }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: "var(--text-primary)", marginBottom: 10 }}>
              🏠 Pièces détectées ({rooms.length})
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              {rooms.map((r, i) => (
                <div key={i} style={{
                  display: "flex", justifyContent: "space-between", alignItems: "center",
                  padding: "6px 10px", background: "var(--bg-secondary)",
                  borderRadius: "var(--radius)", fontSize: 12,
                }}>
                  <span style={{ color: "var(--text-primary)", fontWeight: 500 }}>{r.name}</span>
                  <span style={{ color: "var(--accent)", fontWeight: 600 }}>{r.area}m²</span>
                </div>
              ))}
            </div>
            <div style={{ marginTop: 10, paddingTop: 10, borderTop: "1px solid var(--border)", fontSize: 12, color: "var(--text-secondary)", display: "flex", justifyContent: "space-between" }}>
              <span>Surface totale</span>
              <span style={{ fontWeight: 700, color: "var(--text-primary)" }}>{parsedInfo?.total_area}m²</span>
            </div>
          </div>

          {/* Controls help */}
          <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "var(--radius-lg)", padding: 14 }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: "var(--text-primary)", marginBottom: 8 }}>🎮 Contrôles</div>
            {[
              ["🖱 Glisser", "Tourner la caméra"],
              ["⚙ Molette", "Zoom avant/arrière"],
              ["▶ Visite", "Tour automatique"],
              ["🔴 Rec", "Enregistrer en vidéo"],
            ].map(([key, val]) => (
              <div key={key} style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "var(--text-secondary)", marginBottom: 5 }}>
                <span style={{ fontWeight: 600, color: "var(--text-primary)" }}>{key}</span>
                <span>{val}</span>
              </div>
            ))}
          </div>

          {/* Description recap */}
          <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "var(--radius-lg)", padding: 14 }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: "var(--text-primary)", marginBottom: 6 }}>📝 Description</div>
            <p style={{ fontSize: 11, color: "var(--text-secondary)", lineHeight: 1.6, fontStyle: "italic", margin: 0 }}>
              &ldquo;{description.substring(0, 180)}{description.length > 180 ? "..." : ""}&rdquo;
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
