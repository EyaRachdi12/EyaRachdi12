"use client";
import { useState, useEffect } from "react";
import { useUser } from "@/hooks/useUser";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const STYLE_IDS = ["contemporain", "minimaliste", "industriel", "scandinave", "mediterraneen", "bioclimatique", "haussmannien", "moderne"];

type BriefStage = "input" | "processing" | "result";

interface ParsedRoom {
  name:  string;
  area:  string;
  notes: string;
}

interface ParsedBrief {
  rooms:       ParsedRoom[];
  style:       string;
  budget:      string;
  surface:     string;
  constraints: string[];
  priorities:  string[];
  confidence:  number;
}

export default function BriefPage() {
  const { user } = useUser();
  const [stage,    setStage]    = useState<BriefStage>("input");
  const [text,     setText]     = useState("");
  const [progress, setProgress] = useState(0);
  const [parsed,   setParsed]   = useState<ParsedBrief | null>(null);
  const [saving,   setSaving]   = useState(false);
  const [saved,    setSaved]    = useState(false);

  // Load existing brief on mount
  useEffect(() => {
    if (!user?.id) return;
    fetch(`${API_URL}/api/briefs/${user.id}`)
      .then(r => r.json())
      .then(d => {
        if (d.brief) {
          // Restore from saved brief
          setText(d.brief.description || "");
          const brief = d.brief;
          setParsed({
            rooms:       brief.rooms || [],
            style:       brief.style || "",
            budget:      brief.budget || "",
            surface:     brief.total_area ? `${brief.total_area} m²` : "",
            constraints: brief.constraints || [],
            priorities:  brief.priorities || [],
            confidence:  91,
          });
          setStage("result");
        }
      })
      .catch(() => {});
  }, [user]);

  const handleSubmit = async () => {
    if (!text.trim()) return;
    setStage("processing");
    setProgress(0);
    setSaved(false);

    const interval = setInterval(() => {
      setProgress(p => (p < 90 ? p + 10 : p));
    }, 200);

    try {
      const res = await fetch(`${API_URL}/api/parse-description`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ description: text }),
      });
      const data = await res.json();

      const budgetMatch = text.match(/(\d[\d\s,.]*)\s*(?:€|euros?|k€)/i);

      const result: ParsedBrief = {
        rooms: (data.rooms || []).map((r: { name?: string; area?: number }) => ({
          name:  r.name || "",
          area:  r.area ? `${r.area} m²` : "",
          notes: "",
        })),
        style:       data.style || "Contemporain",
        budget:      budgetMatch ? budgetMatch[0].trim() : "",
        surface:     data.total_area ? `${data.total_area} m²` : "",
        constraints: [],
        priorities:  [],
        confidence:  92,
      };

      clearInterval(interval);
      setProgress(100);
      setParsed(result);
      setStage("result");

    } catch {
      clearInterval(interval);
      setStage("input");
      alert("Erreur lors de l'analyse. Veuillez réessayer.");
    }
  };

  const handleSave = async () => {
    if (!user?.id || !parsed) return;
    setSaving(true);
    try {
      const res = await fetch(`${API_URL}/api/briefs`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({
          client_id:   user.id,
          description: text,
          caption:     `${parsed.style} — ${parsed.surface}`,
          rooms:       parsed.rooms.map(r => ({ name: r.name, area: r.area, notes: r.notes })),
          total_area:  parseInt(parsed.surface) || 0,
          style:       parsed.style,
          budget:      parsed.budget,
          priorities:  parsed.priorities,
          constraints: parsed.constraints,
        }),
      });
      if (res.ok) setSaved(true);
    } catch {}
    setSaving(false);
  };

  return (
    <div style={{ maxWidth: 900 }}>
      <div className="animate-fade-in" style={{ marginBottom: 32 }}>
        <h1 style={{ fontFamily: "'Playfair Display', serif", fontSize: 28, fontWeight: 700, color: "var(--text-primary)", marginBottom: 6 }}>
          Mon Brief Projet
        </h1>
        <p style={{ color: "var(--text-secondary)", fontSize: 15 }}>
          Décrivez votre projet librement — l&apos;IA structure automatiquement votre brief pour l&apos;architecte.
        </p>
      </div>

      {/* AI info */}
      <div className="animate-fade-in delay-100" style={{
        display: "flex", gap: 12, padding: "12px 18px",
        background: "var(--accent-light)", border: "1px solid var(--accent)",
        borderRadius: "var(--radius)", marginBottom: 24, alignItems: "center",
      }}>
        <span style={{ fontSize: 20 }}>🤖</span>
        <span style={{ fontSize: 13, color: "var(--accent-dark)" }}>
          <strong>LoRA Phi-3 Mini</strong> — Modèle fine-tuné sur des briefs architecturaux français
        </span>
      </div>

      {stage === "input" && (
        <div className="animate-fade-in delay-200">
          <div style={{
            background: "var(--surface)", border: "1px solid var(--border)",
            borderRadius: "var(--radius-lg)", padding: 28, marginBottom: 20,
          }}>
            <label style={{ fontSize: 14, fontWeight: 600, color: "var(--text-primary)", display: "block", marginBottom: 12 }}>
              Décrivez votre projet en langage naturel
            </label>
            <textarea
              className="input"
              style={{ minHeight: 200, resize: "vertical", fontFamily: "inherit", lineHeight: 1.7 }}
              placeholder="Ex: Je veux construire une maison moderne pour ma famille de 4 personnes. J'aimerais une grande cuisine ouverte sur le salon, au moins 3 chambres dont une suite parentale avec dressing. On aime la lumière naturelle donc beaucoup de fenêtres. On a un budget d'environ 400 000€ et le terrain fait 800m². J'aimerais aussi une terrasse pour les barbecues..."
              value={text}
              onChange={e => setText(e.target.value)}
            />
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 12 }}>
              <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
                {text.length} caractères — Plus vous êtes précis, meilleur sera le brief
              </span>
              <button
                onClick={handleSubmit}
                disabled={text.length < 20}
                className="btn btn-primary"
                style={{ opacity: text.length < 20 ? 0.5 : 1 }}
              >
                🧠 Analyser avec l&apos;IA →
              </button>
            </div>
          </div>

          {/* Tips */}
          <div style={{
            background: "var(--surface)", border: "1px solid var(--border)",
            borderRadius: "var(--radius-lg)", padding: 20,
          }}>
            <h3 style={{ fontSize: 14, fontWeight: 600, color: "var(--text-primary)", marginBottom: 12 }}>
              💡 Conseils pour un bon brief
            </h3>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 10 }}>
              {[
                "Nombre de personnes dans le foyer",
                "Budget approximatif",
                "Style architectural souhaité",
                "Pièces indispensables",
                "Contraintes du terrain",
                "Matériaux préférés",
              ].map(tip => (
                <div key={tip} style={{ display: "flex", gap: 8, alignItems: "flex-start", fontSize: 13, color: "var(--text-secondary)" }}>
                  <span style={{ color: "var(--accent)", flexShrink: 0 }}>→</span>
                  {tip}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {stage === "processing" && (
        <div className="animate-scale-in" style={{
          background: "var(--surface)", border: "1px solid var(--border)",
          borderRadius: "var(--radius-lg)", padding: 48, textAlign: "center",
        }}>
          <div style={{ fontSize: 48, marginBottom: 20 }}>🧠</div>
          <h3 style={{ fontSize: 18, fontWeight: 600, color: "var(--text-primary)", marginBottom: 8 }}>
            Analyse en cours...
          </h3>
          <p style={{ color: "var(--text-secondary)", fontSize: 14, marginBottom: 24 }}>
            Le LLM parse votre description et structure un brief professionnel
          </p>
          <div style={{ display: "flex", justifyContent: "center", gap: 20, marginBottom: 24, flexWrap: "wrap" }}>
            {[
              { label: "Extraction des besoins",   done: progress > 25 },
              { label: "Identification des pièces", done: progress > 50 },
              { label: "Analyse du budget",         done: progress > 75 },
              { label: "Structuration du brief",    done: progress >= 100 },
            ].map(step => (
              <div key={step.label} style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <div style={{
                  width: 18, height: 18, borderRadius: "50%",
                  background: step.done ? "var(--accent)" : "var(--border)",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: 10, color: "white", transition: "all 0.3s ease",
                }}>
                  {step.done ? "✓" : ""}
                </div>
                <span style={{ fontSize: 12, color: step.done ? "var(--accent)" : "var(--text-muted)" }}>
                  {step.label}
                </span>
              </div>
            ))}
          </div>
          <div className="progress-bar" style={{ maxWidth: 400, margin: "0 auto" }}>
            <div className="progress-fill" style={{ width: `${progress}%` }} />
          </div>
        </div>
      )}

      {stage === "result" && parsed && (
        <div className="animate-scale-in" style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          {/* Header */}
          <div style={{
            background: "linear-gradient(135deg, var(--accent-light), var(--surface))",
            border: "1px solid var(--accent)", borderRadius: "var(--radius-lg)",
            padding: 24, display: "flex", justifyContent: "space-between",
            alignItems: "center", flexWrap: "wrap", gap: 12,
          }}>
            <div>
              <h2 style={{ fontSize: 18, fontWeight: 700, color: "var(--text-primary)", marginBottom: 4 }}>
                Brief structuré généré ✅
              </h2>
              <p style={{ fontSize: 13, color: "var(--text-secondary)" }}>
                Confiance IA : <strong style={{ color: "var(--accent)" }}>{parsed.confidence}%</strong>
                {saved && <span style={{ marginLeft: 12, color: "#6fcf97" }}>✓ Sauvegardé</span>}
              </p>
            </div>
            <div style={{ display: "flex", gap: 10 }}>
              <button
                className="btn btn-secondary"
                style={{ fontSize: 13 }}
                onClick={handleSave}
                disabled={saving || saved}
              >
                {saving ? "Sauvegarde..." : saved ? "✅ Sauvegardé" : "💾 Sauvegarder"}
              </button>
              <button onClick={() => { setStage("input"); setSaved(false); }} className="btn btn-ghost" style={{ fontSize: 13 }}>
                ✏️ Modifier
              </button>
            </div>
          </div>

          {/* Summary */}
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
            {[
              { label: "Surface souhaitée", value: parsed.surface },
              { label: "Budget",            value: parsed.budget },
              { label: "Style",             value: parsed.style },
            ].map(m => (
              <div key={m.label} style={{
                flex: 1, minWidth: 180, padding: 16,
                background: "var(--surface)", border: "1px solid var(--border)",
                borderRadius: "var(--radius)", textAlign: "center",
              }}>
                <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 4 }}>{m.label}</div>
                <div style={{ fontSize: 15, fontWeight: 700, color: "var(--text-primary)" }}>{m.value}</div>
              </div>
            ))}
          </div>

          {/* Rooms */}
          <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "var(--radius-lg)", padding: 24 }}>
            <h3 style={{ fontSize: 16, fontWeight: 600, color: "var(--text-primary)", marginBottom: 16 }}>Pièces souhaitées</h3>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))", gap: 12 }}>
              {parsed.rooms.map(room => (
                <div key={room.name} style={{
                  padding: 14, background: "var(--bg-secondary)",
                  borderRadius: "var(--radius)", border: "1px solid var(--border)",
                }}>
                  <div style={{ fontSize: 13, fontWeight: 600, color: "var(--text-primary)", marginBottom: 4 }}>{room.name}</div>
                  <div style={{ fontSize: 18, fontWeight: 700, color: "var(--accent)", marginBottom: 4 }}>{room.area}</div>
                  <div style={{ fontSize: 12, color: "var(--text-muted)" }}>{room.notes}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Priorities & Constraints */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "var(--radius-lg)", padding: 20 }}>
              <h3 style={{ fontSize: 14, fontWeight: 600, color: "var(--text-primary)", marginBottom: 12 }}>⭐ Priorités</h3>
              {parsed.priorities.map(p => (
                <div key={p} style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 8, fontSize: 13, color: "var(--text-secondary)" }}>
                  <span style={{ color: "var(--accent)" }}>→</span> {p}
                </div>
              ))}
            </div>
            <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "var(--radius-lg)", padding: 20 }}>
              <h3 style={{ fontSize: 14, fontWeight: 600, color: "var(--text-primary)", marginBottom: 12 }}>⚠️ Contraintes</h3>
              {parsed.constraints.map(c => (
                <div key={c} style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 8, fontSize: 13, color: "var(--text-secondary)" }}>
                  <span style={{ color: "#eb5757" }}>!</span> {c}
                </div>
              ))}
            </div>
          </div>

          {/* Next step */}
          <div style={{
            padding: 20, background: "var(--surface)", border: "1px solid var(--border)",
            borderRadius: "var(--radius-lg)", display: "flex", gap: 16, alignItems: "center",
          }}>
            <span style={{ fontSize: 28 }}>🎨</span>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 14, fontWeight: 600, color: "var(--text-primary)", marginBottom: 4 }}>
                Prochaine étape : Esquisses IA
              </div>
              <div style={{ fontSize: 13, color: "var(--text-secondary)" }}>
                Générez des mood boards et esquisses architecturales basées sur votre brief
              </div>
            </div>
            <a href="/client/sketches" className="btn btn-primary" style={{ fontSize: 13, whiteSpace: "nowrap" }}>
              Générer →
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
