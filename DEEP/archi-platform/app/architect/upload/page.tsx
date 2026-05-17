"use client";
import { useState, useRef } from "react";

type Stage = "idle" | "uploading" | "analyzing" | "done" | "error";

interface Room { name: string; area: number; windows: number; notes?: string; }

interface AnalysisResult {
  caption: string; summary: string; rooms: Room[];
  total_area: number; room_count: number; style: string;
  orientation: string; plan_type: string; n_windows: number;
  n_doors: number; confidence: number; confidence_pct: number;
  inference_time_s: number; method: string;
  image_metrics: { brightness: number; edge_density: number; is_floor_plan: boolean; } | null;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function UploadPage() {
  const [stage, setStage]     = useState<Stage>("idle");
  const [dragOver, setDragOver] = useState(false);
  const [progress, setProgress] = useState(0);
  const [file, setFile]       = useState<File | null>(null);
  const [result, setResult]   = useState<AnalysisResult | null>(null);
  const [error, setError]     = useState<string>("");
  const [previewUrl, setPreviewUrl] = useState<string>("");
  const [sharing, setSharing] = useState(false);
  const [shared, setShared] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleShare = async () => {
    if (!result || !previewUrl) return;
    
    setSharing(true);
    try {
      // Get the first conversation (assuming architect has one active conversation)
      const convRes = await fetch(`${API_URL}/api/conversations`);
      const convData = await convRes.json();
      const conversations = convData.conversations || [];
      
      if (conversations.length === 0) {
        alert("Aucune conversation active. Créez d'abord une conversation avec un client.");
        setSharing(false);
        return;
      }
      
      const conv = conversations[0]; // Use first conversation
      
      // Convert preview URL to base64 if needed
      let imageData = previewUrl;
      if (!previewUrl.startsWith('data:')) {
        // Fetch the image and convert to base64
        const response = await fetch(previewUrl);
        const blob = await response.blob();
        imageData = await new Promise<string>((resolve) => {
          const reader = new FileReader();
          reader.onloadend = () => resolve(reader.result as string);
          reader.readAsDataURL(blob);
        });
      }
      
      // Send message with image
      await fetch(`${API_URL}/api/messages/${conv.id}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: `Voici l'analyse du plan : ${result.plan_type} - ${result.style}. ${result.caption}`,
          sender: "Architecte",
          sender_role: "architect",
          image_url: imageData,
          image_name: file?.name || "plan.png",
        }),
      });
      
      setShared(true);
      setTimeout(() => setShared(false), 3000);
    } catch (error) {
      console.error("Error sharing:", error);
      alert("Erreur lors du partage. Vérifiez que le backend est démarré.");
    }
    setSharing(false);
  };

  const handleFile = async (f: File) => {
    setFile(f); setError(""); setResult(null);
    setPreviewUrl(URL.createObjectURL(f));
    setStage("uploading"); setProgress(0);

    const uploadTimer = setInterval(() => {
      setProgress(p => { if (p >= 90) { clearInterval(uploadTimer); return 90; } return p + 15; });
    }, 60);

    try {
      const formData = new FormData();
      formData.append("file", f);
      clearInterval(uploadTimer);
      setStage("analyzing"); setProgress(0);

      const analysisTimer = setInterval(() => {
        setProgress(p => { if (p >= 85) { clearInterval(analysisTimer); return 85; } return p + 5; });
      }, 120);

      const response = await fetch(`${API_URL}/api/analyze-plan`, { method: "POST", body: formData });
      clearInterval(analysisTimer);

      if (!response.ok) {
        const err = await response.json().catch(() => ({ detail: `Erreur ${response.status}` }));
        throw new Error(err.detail || `Erreur serveur: ${response.status}`);
      }

      const data: AnalysisResult = await response.json();
      setProgress(100);
      setTimeout(() => { setResult(data); setStage("done"); }, 300);

    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Erreur inconnue";
      setError(msg.includes("fetch") || msg.includes("Failed") || msg.includes("NetworkError")
        ? "Impossible de contacter le serveur IA. Vérifiez que le backend tourne sur le port 8000."
        : msg);
      setStage("error");
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault(); setDragOver(false);
    const f = e.dataTransfer.files[0]; if (f) handleFile(f);
  };

  const reset = () => {
    setStage("idle"); setFile(null); setResult(null);
    setError(""); setProgress(0);
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl("");
  };

  return (
    <div style={{ maxWidth: 900 }}>
      <div className="animate-fade-in" style={{ marginBottom: 32 }}>
        <h1 style={{ fontFamily: "'Playfair Display', serif", fontSize: 28, fontWeight: 700, color: "var(--text-primary)", marginBottom: 6 }}>
          Analyser un Plan
        </h1>
        <p style={{ color: "var(--text-secondary)", fontSize: 15 }}>
          Uploadez votre plan 2D — l&apos;IA génère automatiquement une description complète.
        </p>
      </div>

      <div className="animate-fade-in delay-100" style={{
        display: "flex", gap: 16, padding: "14px 20px",
        background: "var(--accent-light)", border: "1px solid var(--accent)",
        borderRadius: "var(--radius)", marginBottom: 28, flexWrap: "wrap",
      }}>
        {[
          { label: "Moteur", value: "Vision IA + Analyse structurelle" },
          { label: "Précision", value: "85-95%" },
          { label: "Formats", value: "PNG, JPG, WEBP" },
          { label: "Temps", value: "< 2 secondes" },
        ].map(item => (
          <div key={item.label} style={{ display: "flex", gap: 6, alignItems: "center" }}>
            <span style={{ fontSize: 12, color: "var(--text-muted)" }}>{item.label}:</span>
            <span style={{ fontSize: 12, fontWeight: 600, color: "var(--accent-dark)" }}>{item.value}</span>
          </div>
        ))}
      </div>

      {stage === "idle" && (
        <div className={`upload-zone animate-fade-in delay-200 ${dragOver ? "drag-over" : ""}`}
          onDragOver={e => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => fileRef.current?.click()}>
          <input ref={fileRef} type="file" accept=".png,.jpg,.jpeg,.webp"
            style={{ display: "none" }}
            onChange={e => e.target.files?.[0] && handleFile(e.target.files[0])} />
          <div style={{ fontSize: 48, marginBottom: 16 }}>📐</div>
          <h3 style={{ fontSize: 18, fontWeight: 600, color: "var(--text-primary)", marginBottom: 8 }}>
            Déposez votre plan ici
          </h3>
          <p style={{ color: "var(--text-secondary)", fontSize: 14, marginBottom: 20 }}>
            ou cliquez pour sélectionner un fichier
          </p>
          <span className="badge badge-gold">PNG · JPG · WEBP — Max 50 MB</span>
        </div>
      )}

      {(stage === "uploading" || stage === "analyzing") && (
        <div className="animate-scale-in" style={{
          background: "var(--surface)", border: "1px solid var(--border)",
          borderRadius: "var(--radius-lg)", padding: 40, textAlign: "center",
        }}>
          <div style={{ fontSize: 48, marginBottom: 20 }}>{stage === "uploading" ? "📤" : "🧠"}</div>
          <h3 style={{ fontSize: 18, fontWeight: 600, color: "var(--text-primary)", marginBottom: 8 }}>
            {stage === "uploading" ? "Envoi en cours..." : "Analyse IA en cours..."}
          </h3>
          <p style={{ color: "var(--text-secondary)", fontSize: 14, marginBottom: 24 }}>
            {stage === "uploading" ? `Envoi de ${file?.name}` : "Analyse visuelle → Détection des pièces → Génération de la description"}
          </p>
          {stage === "analyzing" && (
            <div style={{ display: "flex", justifyContent: "center", gap: 24, marginBottom: 24, flexWrap: "wrap" }}>
              {[
                { label: "Analyse visuelle", done: progress > 25 },
                { label: "Détection pièces", done: progress > 50 },
                { label: "Calcul surfaces",  done: progress > 70 },
                { label: "Génération caption", done: progress >= 85 },
              ].map(step => (
                <div key={step.label} style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <div style={{
                    width: 20, height: 20, borderRadius: "50%",
                    background: step.done ? "var(--accent)" : "var(--border)",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    fontSize: 10, color: "white", transition: "all 0.3s ease",
                  }}>{step.done ? "✓" : ""}</div>
                  <span style={{ fontSize: 12, color: step.done ? "var(--accent)" : "var(--text-muted)" }}>{step.label}</span>
                </div>
              ))}
            </div>
          )}
          <div className="progress-bar" style={{ maxWidth: 400, margin: "0 auto" }}>
            <div className="progress-fill" style={{ width: `${progress}%` }} />
          </div>
          <div style={{ fontSize: 13, color: "var(--text-muted)", marginTop: 8 }}>{progress}%</div>
        </div>
      )}

      {stage === "error" && (
        <div className="animate-scale-in" style={{
          background: "var(--surface)", border: "1px solid #eb5757",
          borderRadius: "var(--radius-lg)", padding: 32, textAlign: "center",
        }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>❌</div>
          <h3 style={{ fontSize: 18, fontWeight: 600, color: "var(--text-primary)", marginBottom: 8 }}>Erreur d&apos;analyse</h3>
          <p style={{ color: "#eb5757", fontSize: 14, maxWidth: 500, margin: "0 auto 16px" }}>{error}</p>
          {(error.includes("backend") || error.includes("serveur")) && (
            <div style={{ background: "var(--bg-secondary)", borderRadius: "var(--radius)", padding: "12px 16px", marginBottom: 20, textAlign: "left", fontSize: 13, color: "var(--text-secondary)", maxWidth: 500, margin: "0 auto 20px" }}>
              <strong>Pour démarrer le backend :</strong><br />
              <code style={{ color: "var(--accent)" }}>python archi-platform/backend/main.py</code>
            </div>
          )}
          <button onClick={reset} className="btn btn-primary">↩ Réessayer</button>
        </div>
      )}

      {stage === "done" && result && (
        <div className="animate-scale-in" style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          <div style={{
            background: "linear-gradient(135deg, var(--accent-light), var(--surface))",
            border: "1px solid var(--accent)", borderRadius: "var(--radius-lg)",
            padding: 24, display: "flex", gap: 20, alignItems: "flex-start", flexWrap: "wrap",
          }}>
            {previewUrl && (
              <div style={{ width: 120, height: 120, borderRadius: 12, overflow: "hidden", border: "2px solid var(--accent)", flexShrink: 0 }}>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={previewUrl} alt="Plan" style={{ width: "100%", height: "100%", objectFit: "cover" }} />
              </div>
            )}
            <div style={{ flex: 1 }}>
              <div style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 8, flexWrap: "wrap" }}>
                <span style={{ fontSize: 20 }}>✅</span>
                <h2 style={{ fontSize: 17, fontWeight: 700, color: "var(--text-primary)" }}>
                  {result.plan_type.charAt(0).toUpperCase() + result.plan_type.slice(1)} — {result.style}
                </h2>
                <span className="badge badge-gold">Confiance : {result.confidence_pct}%</span>
                <span style={{ fontSize: 11, color: "var(--text-muted)", background: "var(--bg-secondary)", padding: "2px 8px", borderRadius: 999 }}>
                  {result.inference_time_s}s
                </span>
              </div>
              <p style={{ fontSize: 14, color: "var(--text-secondary)", lineHeight: 1.7 }}>{result.caption}</p>
            </div>
          </div>

          <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "var(--radius-lg)", padding: 24 }}>
            <h3 style={{ fontSize: 16, fontWeight: 600, color: "var(--text-primary)", marginBottom: 16 }}>
              Pièces détectées — {result.room_count} pièce{result.room_count > 1 ? "s" : ""}
            </h3>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))", gap: 12 }}>
              {result.rooms.map((room, i) => (
                <div key={i} style={{ padding: 16, background: "var(--bg-secondary)", borderRadius: "var(--radius)", border: "1px solid var(--border)" }}>
                  <div style={{ fontSize: 13, fontWeight: 600, color: "var(--text-primary)", marginBottom: 6 }}>{room.name}</div>
                  <div style={{ fontSize: 22, fontWeight: 700, color: "var(--accent)", marginBottom: 4 }}>{room.area} m²</div>
                  <div style={{ fontSize: 11, color: "var(--text-muted)" }}>{room.windows} fenêtre{room.windows !== 1 ? "s" : ""}</div>
                  {room.notes && <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 4, fontStyle: "italic" }}>{room.notes}</div>}
                </div>
              ))}
            </div>
          </div>

          <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
            {[
              { label: "Surface totale", value: `${result.total_area} m²` },
              { label: "Style",          value: result.style },
              { label: "Orientation",    value: result.orientation },
              { label: "Fenêtres",       value: `${result.n_windows}` },
              { label: "Portes",         value: `${result.n_doors}` },
            ].map(m => (
              <div key={m.label} style={{ flex: 1, minWidth: 120, padding: "14px 16px", background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "var(--radius)", textAlign: "center" }}>
                <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 4 }}>{m.label}</div>
                <div style={{ fontSize: 16, fontWeight: 700, color: "var(--text-primary)" }}>{m.value}</div>
              </div>
            ))}
          </div>

          <div style={{ padding: "12px 16px", background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "var(--radius)", display: "flex", gap: 20, flexWrap: "wrap", alignItems: "center" }}>
            <span style={{ fontSize: 13, color: "var(--text-muted)" }}>Qualité image :</span>
            <span style={{ fontSize: 13, color: result.image_metrics?.is_floor_plan ? "#6fcf97" : "var(--text-muted)" }}>
              {result.image_metrics?.is_floor_plan ? "✅ Plan architectural détecté" : "⚠️ Image générique"}
            </span>
            {result.image_metrics?.brightness != null && (
              <span style={{ fontSize: 12, color: "var(--text-muted)" }}>Luminosité : {result.image_metrics.brightness.toFixed(0)}</span>
            )}
          </div>

          <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
            <a href="/architect/visualize" className="btn btn-primary" style={{ flex: 1, justifyContent: "center", minWidth: 200 }}>🎬 Générer Vidéo 3D</a>
            <button 
              onClick={handleShare}
              disabled={sharing}
              className="btn btn-secondary" 
              style={{ flex: 1, justifyContent: "center", minWidth: 200 }}
            >
              {sharing ? "Envoi..." : shared ? "✅ Partagé !" : "📤 Partager avec le client"}
            </button>
            <button onClick={reset} className="btn btn-ghost" style={{ flex: 1, justifyContent: "center", minWidth: 160 }}>↩ Nouveau plan</button>
          </div>
        </div>
      )}
    </div>
  );
}
