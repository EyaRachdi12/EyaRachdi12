"use client";
import { useState, useEffect } from "react";
import Image from "next/image";
import { useUser } from "@/hooks/useUser";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Sketch {
  id:        number;
  title:     string;
  prompt:    string;
  image_b64: string | null;
  image_url: string | null;
  view_type: string;
  liked:     boolean;
}

export default function SketchesPage() {
  const { user } = useUser();
  
  // Form state
  const [useBrief, setUseBrief] = useState(true);
  const [selectedStyle, setSelectedStyle] = useState("contemporain");
  const [description, setDescription] = useState("");
  const [elements, setElements] = useState<string[]>(["terrasse", "grandes_fenetres"]);
  const [viewTypes, setViewTypes] = useState<string[]>(["facade", "interior_living", "interior_kitchen"]);
  
  // Generation state
  const [generating, setGenerating] = useState(false);
  const [sketches, setSketches] = useState<Sketch[]>([]);
  const [progress, setProgress] = useState(0);
  const [method, setMethod] = useState("");
  
  // UI state
  const [sharing, setSharing] = useState(false);
  const [shared, setShared] = useState(false);
  const [likedSketches, setLikedSketches] = useState<Set<number>>(new Set());

  const STYLES = [
    { id: "contemporain",  label: "Contemporain",  emoji: "🏙️" },
    { id: "minimaliste",   label: "Minimaliste",   emoji: "⬜" },
    { id: "industriel",    label: "Industriel",    emoji: "🏭" },
    { id: "scandinave",    label: "Scandinave",    emoji: "🌲" },
    { id: "mediterraneen", label: "Méditerranéen", emoji: "🌊" },
    { id: "bioclimatique", label: "Bioclimatique", emoji: "🌿" },
  ];

  const architecturalElements = [
    { id: "terrasse", label: "Terrasse", emoji: "🏡" },
    { id: "grandes_fenetres", label: "Grandes fenêtres", emoji: "🪟" },
    { id: "jardin", label: "Jardin", emoji: "🌳" },
    { id: "piscine", label: "Piscine", emoji: "🏊" },
    { id: "garage", label: "Garage", emoji: "🚗" },
    { id: "balcon", label: "Balcon", emoji: "🏢" },
  ];

  const viewOptions = [
    { id: "facade", label: "Façade principale", emoji: "🏠" },
    { id: "interior_living", label: "Vue intérieure (salon)", emoji: "🛋️" },
    { id: "interior_kitchen", label: "Vue intérieure (cuisine)", emoji: "🍳" },
    { id: "interior_bedroom", label: "Vue intérieure (chambre)", emoji: "🛏️" },
    { id: "aerial", label: "Vue aérienne", emoji: "🚁" },
    { id: "garden", label: "Vue jardin/terrasse", emoji: "🌿" },
  ];

  // Load brief on mount
  useEffect(() => {
    if (!user?.id || !useBrief) return;
    
    fetch(`${API_URL}/api/briefs/${user.id}`)
      .then(r => r.json())
      .then(d => {
        if (d.brief) {
          const brief = d.brief;
          // Auto-fill description from brief
          const briefDesc = `${brief.description || ''} Style ${brief.style || 'contemporain'}. ${brief.rooms?.length || 0} pièces pour une surface de ${brief.total_area || 0} m².`;
          setDescription(briefDesc);
          
          // Set style from brief
          if (brief.style) {
            const styleId = brief.style.toLowerCase();
            if (STYLES.some(s => s.id === styleId)) {
              setSelectedStyle(styleId);
            }
          }
        }
      })
      .catch(() => {});
  }, [user, useBrief]);

  const toggleElement = (id: string) => {
    setElements(prev => 
      prev.includes(id) ? prev.filter(e => e !== id) : [...prev, id]
    );
  };

  const toggleViewType = (id: string) => {
    setViewTypes(prev => 
      prev.includes(id) ? prev.filter(v => v !== id) : [...prev, id]
    );
  };

  const handleGenerate = async () => {
    if (viewTypes.length === 0) {
      alert("Veuillez sélectionner au moins un type de vue à générer");
      return;
    }

    setGenerating(true);
    setSketches([]);
    setProgress(0);
    setShared(false);

    // Animate progress
    const timer = setInterval(() => {
      setProgress(p => { if (p >= 85) { clearInterval(timer); return 85; } return p + 5; });
    }, 300);

    try {
      const res = await fetch(`${API_URL}/api/generate-sketches-ai`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          style: selectedStyle,
          description: description,
          elements: elements,
          view_types: viewTypes,
          n: viewTypes.length,
        }),
      });

      clearInterval(timer);

      if (!res.ok) throw new Error("API error");

      const data = await res.json();
      setProgress(100);
      setSketches(data.sketches || []);
      setMethod(data.method || "");

    } catch (error) {
      clearInterval(timer);
      console.error("Generation error:", error);
      alert("Erreur lors de la génération. Vérifiez que le backend est démarré et que HF_API_TOKEN est configuré.");
      setProgress(0);
    } finally {
      setGenerating(false);
    }
  };

  const toggleLike = (id: number) => {
    setLikedSketches(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  const handleShare = async () => {
    if (!user?.id) return;
    
    // Store sketches in localStorage to pass to messages page
    const likedSketchesArray = sketches.filter(s => likedSketches.has(s.id));
    const sketchesToShare = likedSketchesArray.length > 0 ? likedSketchesArray : sketches;
    
    localStorage.setItem('sketches_to_share', JSON.stringify({
      sketches: sketchesToShare.map(s => ({
        image_url: s.image_b64 || s.image_url,
        title: s.title,
        prompt: s.prompt,
      })),
      style: STYLES.find(s => s.id === selectedStyle)?.label || selectedStyle,
      timestamp: Date.now(),
    }));
    
    // Redirect to messages page
    window.location.href = '/client/messages';
  };

  return (
    <div style={{ maxWidth: 1100 }}>
      <div className="animate-fade-in" style={{ marginBottom: 32 }}>
        <h1 style={{ fontFamily: "'Playfair Display', serif", fontSize: 28, fontWeight: 700, color: "var(--text-primary)", marginBottom: 6 }}>
          Esquisses IA
        </h1>
        <p style={{ color: "var(--text-secondary)", fontSize: 15 }}>
          Générez des visualisations architecturales personnalisées avec l&apos;IA — Stable Diffusion XL.
        </p>
      </div>

      {/* Configuration Form */}
      <div className="animate-fade-in delay-100" style={{
        background: "var(--surface)", border: "1px solid var(--border)",
        borderRadius: "var(--radius-lg)", padding: 28, marginBottom: 24,
      }}>
        {/* Use Brief Toggle */}
        <div style={{ marginBottom: 24, padding: 16, background: "var(--accent-light)", borderRadius: "var(--radius)", border: "1px solid var(--accent)" }}>
          <label style={{ display: "flex", alignItems: "center", gap: 10, cursor: "pointer" }}>
            <input
              type="checkbox"
              checked={useBrief}
              onChange={(e) => setUseBrief(e.target.checked)}
              style={{ width: 18, height: 18, cursor: "pointer" }}
            />
            <span style={{ fontSize: 14, fontWeight: 600, color: "var(--accent-dark)" }}>
              📋 Utiliser mon brief existant (auto-remplissage)
            </span>
          </label>
        </div>

        {/* Style Selection */}
        <div style={{ marginBottom: 24 }}>
          <h3 style={{ fontSize: 15, fontWeight: 600, color: "var(--text-primary)", marginBottom: 12 }}>
            Style architectural
          </h3>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            {STYLES.map(style => (
              <button
                key={style.id}
                onClick={() => setSelectedStyle(style.id)}
                style={{
                  padding: "8px 16px", borderRadius: 999,
                  border: `1px solid ${selectedStyle === style.id ? "var(--accent)" : "var(--border)"}`,
                  background: selectedStyle === style.id ? "var(--accent-light)" : "var(--bg-secondary)",
                  color: selectedStyle === style.id ? "var(--accent-dark)" : "var(--text-secondary)",
                  fontSize: 13, fontWeight: selectedStyle === style.id ? 600 : 400,
                  cursor: "pointer", transition: "all 0.2s ease",
                  display: "flex", alignItems: "center", gap: 6,
                }}
              >
                {style.emoji} {style.label}
              </button>
            ))}
          </div>
        </div>

        {/* Description */}
        <div style={{ marginBottom: 24 }}>
          <label style={{ fontSize: 14, fontWeight: 600, color: "var(--text-primary)", display: "block", marginBottom: 8 }}>
            Description du projet
          </label>
          <textarea
            className="input"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Ex: Maison moderne pour famille de 4, cuisine ouverte sur salon, 3 chambres, terrasse bois..."
            style={{ minHeight: 100, resize: "vertical", fontFamily: "inherit", lineHeight: 1.6 }}
          />
          <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 4 }}>
            {useBrief ? "Auto-rempli depuis votre brief" : "Décrivez votre projet en détail"}
          </div>
        </div>

        {/* Architectural Elements */}
        <div style={{ marginBottom: 24 }}>
          <h3 style={{ fontSize: 14, fontWeight: 600, color: "var(--text-primary)", marginBottom: 12 }}>
            Éléments architecturaux
          </h3>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            {architecturalElements.map(elem => (
              <button
                key={elem.id}
                onClick={() => toggleElement(elem.id)}
                style={{
                  padding: "6px 14px", borderRadius: 999,
                  border: `1px solid ${elements.includes(elem.id) ? "var(--accent)" : "var(--border)"}`,
                  background: elements.includes(elem.id) ? "var(--accent-light)" : "var(--bg-secondary)",
                  color: elements.includes(elem.id) ? "var(--accent-dark)" : "var(--text-secondary)",
                  fontSize: 12, fontWeight: elements.includes(elem.id) ? 600 : 400,
                  cursor: "pointer", transition: "all 0.2s ease",
                  display: "flex", alignItems: "center", gap: 6,
                }}
              >
                {elements.includes(elem.id) ? "☑" : "☐"} {elem.emoji} {elem.label}
              </button>
            ))}
          </div>
        </div>

        {/* View Types */}
        <div style={{ marginBottom: 24 }}>
          <h3 style={{ fontSize: 14, fontWeight: 600, color: "var(--text-primary)", marginBottom: 12 }}>
            Types de vues à générer ({viewTypes.length} sélectionnées)
          </h3>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            {viewOptions.map(view => (
              <button
                key={view.id}
                onClick={() => toggleViewType(view.id)}
                style={{
                  padding: "6px 14px", borderRadius: 999,
                  border: `1px solid ${viewTypes.includes(view.id) ? "var(--accent)" : "var(--border)"}`,
                  background: viewTypes.includes(view.id) ? "var(--accent-light)" : "var(--bg-secondary)",
                  color: viewTypes.includes(view.id) ? "var(--accent-dark)" : "var(--text-secondary)",
                  fontSize: 12, fontWeight: viewTypes.includes(view.id) ? 600 : 400,
                  cursor: "pointer", transition: "all 0.2s ease",
                  display: "flex", alignItems: "center", gap: 6,
                }}
              >
                {viewTypes.includes(view.id) ? "☑" : "☐"} {view.emoji} {view.label}
              </button>
            ))}
          </div>
        </div>

        {/* Generate Button */}
        <button
          onClick={handleGenerate}
          disabled={generating || viewTypes.length === 0}
          className="btn btn-primary"
          style={{ opacity: generating || viewTypes.length === 0 ? 0.7 : 1, width: "100%" }}
        >
          {generating ? (
            <>
              <svg className="animate-spin-slow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
              </svg>
              Génération en cours... {progress}%
            </>
          ) : `🎨 Générer ${viewTypes.length} esquisse${viewTypes.length > 1 ? 's' : ''} avec IA`}
        </button>

        {generating && (
          <div className="progress-bar" style={{ marginTop: 12 }}>
            <div className="progress-fill" style={{ width: `${progress}%` }} />
          </div>
        )}
      </div>

      {/* Sketches Grid */}
      {sketches.length > 0 && (
        <div className="animate-scale-in">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
            <div>
              <h3 style={{ fontSize: 16, fontWeight: 600, color: "var(--text-primary)" }}>
                {sketches.length} esquisse{sketches.length > 1 ? 's' : ''} générée{sketches.length > 1 ? 's' : ''} — Style {STYLES.find(s => s.id === selectedStyle)?.label}
              </h3>
              {method && (
                <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>
                  🤖 Généré par {method === "pollinations_ai_flux" ? "Pollinations.ai (FLUX)" : method}
                </div>
              )}
            </div>
            <button
              onClick={handleShare}
              disabled={sharing}
              className="btn btn-secondary"
              style={{ fontSize: 13 }}
            >
              {sharing ? "Envoi..." : shared ? "✅ Partagé !" : "📤 Partager avec l'architecte"}
            </button>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: 16 }}>
            {sketches.map(sketch => (
              <div key={sketch.id} className="card-hover" style={{
                background: "var(--surface)", border: "1px solid var(--border)",
                borderRadius: "var(--radius-lg)", overflow: "hidden",
              }}>
                {/* Image */}
                <div style={{ height: 240, position: "relative", background: "#1a1714" }}>
                  {sketch.image_b64 ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={sketch.image_b64}
                      alt={sketch.title}
                      style={{ width: "100%", height: "100%", objectFit: "cover" }}
                    />
                  ) : (
                    <div style={{
                      height: "100%", display: "flex", alignItems: "center",
                      justifyContent: "center", color: "rgba(201,169,110,0.4)",
                      flexDirection: "column", gap: 8,
                    }}>
                      <div style={{ fontSize: 32 }}>🏛️</div>
                      <div style={{ fontSize: 11, textAlign: "center", padding: "0 20px" }}>{sketch.prompt.substring(0, 80)}...</div>
                    </div>
                  )}

                  {/* Like button */}
                  <button
                    onClick={() => toggleLike(sketch.id)}
                    style={{
                      position: "absolute", top: 10, right: 10,
                      width: 32, height: 32, borderRadius: "50%",
                      background: "rgba(0,0,0,0.5)", border: "none",
                      cursor: "pointer", display: "flex", alignItems: "center",
                      justifyContent: "center", fontSize: 14,
                    }}
                  >
                    {likedSketches.has(sketch.id) ? "❤️" : "🤍"}
                  </button>

                  {/* Badge */}
                  <div style={{
                    position: "absolute", bottom: 10, left: 10,
                    background: "rgba(0,0,0,0.6)", color: "white",
                    fontSize: 10, padding: "3px 8px", borderRadius: 999,
                    backdropFilter: "blur(4px)",
                  }}>
                    IA • Pollinations FLUX
                  </div>
                </div>

                <div style={{ padding: 16 }}>
                  <div style={{ fontSize: 14, fontWeight: 600, color: "var(--text-primary)", marginBottom: 4 }}>
                    {sketch.title}
                  </div>
                  <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 12, lineHeight: 1.4 }}>
                    {sketch.prompt.substring(0, 100)}...
                  </div>
                  <div style={{ display: "flex", gap: 8 }}>
                    <button
                      onClick={handleGenerate}
                      className="btn btn-secondary"
                      style={{ flex: 1, justifyContent: "center", fontSize: 12, padding: "6px 12px" }}
                    >
                      🔄 Regénérer
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty state */}
      {!generating && sketches.length === 0 && (
        <div style={{
          textAlign: "center", padding: 60, color: "var(--text-muted)",
          background: "var(--surface)", border: "1px solid var(--border)",
          borderRadius: "var(--radius-lg)",
        }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>🎨</div>
          <h3 style={{ fontSize: 18, fontWeight: 600, color: "var(--text-primary)", marginBottom: 8 }}>
            Prêt à générer vos esquisses
          </h3>
          <p style={{ fontSize: 14, marginBottom: 20 }}>
            Configurez votre projet ci-dessus et cliquez sur &quot;Générer&quot;
          </p>
        </div>
      )}
    </div>
  );
}
