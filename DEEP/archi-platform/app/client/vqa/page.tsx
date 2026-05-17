"use client";
import { useState, useRef, useEffect, useCallback } from "react";
import { useSearchParams } from "next/navigation";

interface Message {
  role: "user" | "ai";
  text: string;
  confidence?: number;
  time: string;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const SUGGESTED_QUESTIONS = [
  "Où est la salle de bain ?",
  "Quelle est la surface du salon ?",
  "Combien de fenêtres y a-t-il ?",
  "Quelle est la surface totale ?",
  "Y a-t-il un dressing ?",
  "Comment accède-t-on à la terrasse ?",
  "Quel est le style architectural ?",
  "Combien de chambres y a-t-il ?",
];

export default function VQAPage() {
  const searchParams = useSearchParams();
  const planId = searchParams.get("plan");
  
  const [question, setQuestion]   = useState("");
  const [loading, setLoading]     = useState(false);
  const [planFile, setPlanFile]   = useState<File | null>(null);
  const [planPreview, setPlanPreview] = useState<string>("");
  const [planTitle, setPlanTitle] = useState<string>("");
  const [messages, setMessages]   = useState<Message[]>([
    {
      role: "ai",
      text: "Bonjour ! Uploadez votre plan puis posez-moi n'importe quelle question — localisation des pièces, surfaces, ouvertures, style architectural...",
      time: "Maintenant",
    },
  ]);
  const fileRef = useRef<HTMLInputElement>(null);

  const handlePlanUpload = useCallback((f: File) => {
    setPlanFile(f);
    setPlanTitle("");
    const url = URL.createObjectURL(f);
    setPlanPreview(url);
    setMessages((prev) => [
      ...prev,
      {
        role: "ai",
        text: `Plan "${f.name}" chargé ✅ Vous pouvez maintenant poser vos questions.`,
        time: "Maintenant",
      },
    ]);
  }, []);

  // Load floor plan from Explorer if plan ID is provided
  useEffect(() => {
    if (planId) {
      loadFloorPlanFromLibrary(planId);
      return; // Don't check other sources if plan ID is provided
    }
    
    // Check for plan from messages (PRIORITY - check first)
    const planData = localStorage.getItem('plan_to_analyze');
    if (planData) {
      try {
        const data = JSON.parse(planData);
        console.log('📦 Found plan from messages:', data);
        
        // Only load if timestamp is recent (within 5 minutes)
        if (Date.now() - data.timestamp < 5 * 60 * 1000) {
          console.log('⏰ Timestamp valid, loading plan...');
          
          // Convert base64 to blob and create File
          if (data.image_url) {
            if (data.image_url.startsWith('data:image')) {
              // Base64 data URL
              console.log('📦 Loading base64 image...');
              try {
                // Extract base64 data
                const base64Data = data.image_url.split(',')[1];
                const byteCharacters = atob(base64Data);
                const byteNumbers = new Array(byteCharacters.length);
                for (let i = 0; i < byteCharacters.length; i++) {
                  byteNumbers[i] = byteCharacters.charCodeAt(i);
                }
                const byteArray = new Uint8Array(byteNumbers);
                const blob = new Blob([byteArray], { type: 'image/png' });
                
                const file = new File([blob], data.image_name || 'plan.png', { type: 'image/png' });
                console.log('✅ File created from messages:', file.name, file.size, 'bytes');
                
                handlePlanUpload(file);
                
                console.log('✅ Plan loaded from messages');
              } catch (err) {
                console.error('❌ Error converting base64:', err);
              }
            } else {
              // Regular URL - fetch and convert to File
              console.log('📦 Loading image from URL...');
              fetch(data.image_url)
                .then(response => response.blob())
                .then(blob => {
                  const file = new File([blob], data.image_name || 'plan.png', { type: blob.type || 'image/png' });
                  console.log('✅ File created from URL:', file.name, file.size, 'bytes');
                  
                  handlePlanUpload(file);
                  
                  console.log('✅ Plan loaded from messages');
                })
                .catch(err => {
                  console.error('❌ Error fetching image:', err);
                });
            }
          }
        } else {
          console.log('⏰ Plan data expired');
        }
        // Clear the data after loading
        localStorage.removeItem('plan_to_analyze');
      } catch (e) {
        console.error('❌ Error loading plan from messages:', e);
      }
      return; // Don't check sketches if we found a plan
    }
    
    // Check for shared sketches from localStorage (FALLBACK)
    const sharedData = localStorage.getItem('sketches_to_share');
    if (sharedData) {
      try {
        const data = JSON.parse(sharedData);
        // Only load if timestamp is recent (within 5 minutes)
        if (Date.now() - data.timestamp < 5 * 60 * 1000) {
          // Auto-attach the first sketch
          if (data.sketches && data.sketches.length > 0) {
            const firstSketch = data.sketches[0];
            
            // Convert base64 to blob and create File
            if (firstSketch.image_url) {
              fetch(firstSketch.image_url)
                .then(res => res.blob())
                .then(blob => {
                  const file = new File([blob], `${firstSketch.title}.png`, { type: 'image/png' });
                  handlePlanUpload(file);
                  
                  // Set pre-filled message
                  setQuestion(`J'ai généré des esquisses IA en style ${data.style}. Voici "${firstSketch.title}". Pouvez-vous me donner votre avis ? 🎨`);
                });
            }
          }
        }
        // Clear the data after loading
        localStorage.removeItem('sketches_to_share');
      } catch (e) {
        console.error('Error loading shared sketches:', e);
      }
    }
  }, [planId, handlePlanUpload]);

  const loadFloorPlanFromLibrary = async (id: string) => {
    console.log("🔍 Loading floor plan from library:", id);
    
    try {
      // Fetch plan metadata
      console.log("📡 Fetching plan metadata...");
      const res = await fetch(`${API_URL}/api/floor-plans/${id}`);
      console.log("📡 Response status:", res.status, res.statusText);
      
      if (!res.ok) {
        console.error("❌ Failed to fetch plan metadata");
        return;
      }
      
      const planData = await res.json();
      console.log("✅ Plan metadata:", planData);
      setPlanTitle(planData.title);
      
      // Set preview URL (use direct URL instead of downloading)
      const imageUrl = `${API_URL}/api/floor-plans/${id}/image`;
      console.log("🖼️  Image URL:", imageUrl);
      setPlanPreview(imageUrl);
      
      // Create a placeholder File object and store the plan ID
      const filename = planData.image_file?.split('/').pop() || "plan.png";
      const placeholderBlob = new Blob([], { type: 'image/png' });
      const file = new File([placeholderBlob], filename, { type: 'image/png' });
      
      // Store the plan ID instead of URL
      (file as any).planId = id;
      
      setPlanFile(file);
      
      console.log("✅ Plan loaded successfully:", filename, "with ID:", id);
      
      setMessages((prev) => [
        ...prev,
        {
          role: "ai",
          text: `Plan "${planData.title}" chargé depuis la bibliothèque ✅ Vous pouvez maintenant poser vos questions.`,
          time: "Maintenant",
        },
      ]);
    } catch (error) {
      console.error("❌ Error loading floor plan:", error);
      setMessages((prev) => [
        ...prev,
        {
          role: "ai",
          text: `Erreur lors du chargement du plan. Veuillez réessayer.`,
          time: "Maintenant",
        },
      ]);
    }
  };

  const handleAsk = async (q?: string) => {
    const query = (q || question).trim();
    if (!query) return;

    // Add user message
    const userMsg: Message = { role: "user", text: query, time: "Maintenant" };
    setMessages((prev) => [...prev, userMsg]);
    setQuestion("");
    setLoading(true);

    try {
      let answer: string;
      let confidence: number | undefined;

      if (planFile) {
        // Check if this is a library plan (has planId property)
        const planId = (planFile as any).planId;
        
        if (planId) {
          // Library plan - use plan ID endpoint
          console.log("📡 Using plan ID endpoint for library plan:", planId);
          console.log("📝 Question:", query);
          
          const formData = new FormData();
          formData.append("plan_id", planId);
          formData.append("question", query);

          console.log("📤 FormData contents:");
          for (const [key, value] of formData.entries()) {
            console.log(`  ${key}: ${value}`);
          }

          console.log("📤 Sending request to /api/ask-plan-url");
          const res = await fetch(`${API_URL}/api/ask-plan-url`, {
            method: "POST",
            body: formData,
          });

          console.log("📥 Response status:", res.status, res.statusText);
          
          if (!res.ok) {
            const errorText = await res.text();
            console.error("❌ Server error response:", errorText);
            throw new Error(`Erreur serveur: ${res.status} - ${errorText}`);
          }

          const data = await res.json();
          console.log("✅ Response data:", data);
          answer = data.answer;
          confidence = data.confidence_pct;
        } else {
          // Uploaded plan - use file endpoint
          console.log("📡 Using file endpoint for uploaded plan");
          const formData = new FormData();
          formData.append("file", planFile);
          formData.append("question", query);

          const res = await fetch(`${API_URL}/api/ask-plan`, {
            method: "POST",
            body: formData,
          });

          if (!res.ok) throw new Error(`Erreur serveur: ${res.status}`);

          const data = await res.json();
          answer = data.answer;
          confidence = data.confidence_pct;
        }
      } else {
        // No plan uploaded — ask user to upload
        answer = "Veuillez d'abord uploader un plan architectural pour que je puisse répondre à vos questions.";
      }

      const aiMsg: Message = {
        role: "ai",
        text: answer,
        confidence,
        time: "Maintenant",
      };
      setMessages((prev) => [...prev, aiMsg]);

    } catch (error) {
      console.error("❌ Error asking question:", error);
      setMessages((prev) => [
        ...prev,
        {
          role: "ai",
          text: "Impossible de contacter le serveur IA. Vérifiez que le backend tourne sur le port 8000.",
          time: "Maintenant",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 900 }}>
      <div className="animate-fade-in" style={{ marginBottom: 32 }}>
        <h1 style={{ fontFamily: "'Playfair Display', serif", fontSize: 28, fontWeight: 700, color: "var(--text-primary)", marginBottom: 6 }}>
          Questions sur le Plan
        </h1>
        <p style={{ color: "var(--text-secondary)", fontSize: 15 }}>
          Uploadez votre plan et posez vos questions — l&apos;IA répond en temps réel.
        </p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 280px", gap: 20 }}>
        {/* Chat */}
        <div style={{
          background: "var(--surface)", border: "1px solid var(--border)",
          borderRadius: "var(--radius-lg)", display: "flex",
          flexDirection: "column", height: 600,
        }}>
          {/* Messages */}
          <div style={{ flex: 1, overflowY: "auto", padding: 20, display: "flex", flexDirection: "column", gap: 16 }}>
            {messages.map((msg, i) => (
              <div key={i} style={{
                display: "flex", gap: 12,
                flexDirection: msg.role === "user" ? "row-reverse" : "row",
                alignItems: "flex-start",
              }}>
                <div style={{
                  width: 32, height: 32, borderRadius: "50%",
                  background: msg.role === "ai" ? "var(--accent)" : "var(--bg-secondary)",
                  border: "1px solid var(--border)",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: 14, flexShrink: 0,
                }}>
                  {msg.role === "ai" ? "🤖" : "👤"}
                </div>
                <div style={{ maxWidth: "75%" }}>
                  <div style={{
                    padding: "12px 16px",
                    borderRadius: msg.role === "user" ? "16px 4px 16px 16px" : "4px 16px 16px 16px",
                    background: msg.role === "user" ? "var(--accent)" : "var(--bg-secondary)",
                    color: msg.role === "user" ? "white" : "var(--text-primary)",
                    fontSize: 14, lineHeight: 1.6,
                    border: msg.role === "ai" ? "1px solid var(--border)" : "none",
                  }}>
                    {msg.text}
                  </div>
                  {msg.confidence !== undefined && (
                    <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 4 }}>
                      Confiance : {msg.confidence}%
                    </div>
                  )}
                </div>
              </div>
            ))}

            {loading && (
              <div style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
                <div style={{
                  width: 32, height: 32, borderRadius: "50%",
                  background: "var(--accent)", display: "flex",
                  alignItems: "center", justifyContent: "center", fontSize: 14,
                }}>🤖</div>
                <div style={{
                  padding: "12px 16px", background: "var(--bg-secondary)",
                  borderRadius: "4px 16px 16px 16px", border: "1px solid var(--border)",
                  display: "flex", gap: 4, alignItems: "center",
                }}>
                  {[0, 1, 2].map((i) => (
                    <div key={i} style={{
                      width: 6, height: 6, borderRadius: "50%",
                      background: "var(--accent)",
                      animation: `pulse-ring 1s ease ${i * 0.2}s infinite`,
                    }} />
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Input */}
          <div style={{ padding: 16, borderTop: "1px solid var(--border)", display: "flex", gap: 10 }}>
            <input
              className="input"
              placeholder={planFile ? "Posez votre question..." : "Uploadez d'abord un plan →"}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !loading && handleAsk()}
              style={{ flex: 1 }}
            />
            <button
              onClick={() => handleAsk()}
              disabled={loading || !question.trim()}
              className="btn btn-primary"
              style={{ padding: "10px 16px", opacity: loading || !question.trim() ? 0.5 : 1 }}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="22" y1="2" x2="11" y2="13"/>
                <polygon points="22 2 15 22 11 13 2 9 22 2"/>
              </svg>
            </button>
          </div>
        </div>

        {/* Right panel */}
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {/* Plan upload */}
          <div style={{
            background: "var(--surface)", border: "1px solid var(--border)",
            borderRadius: "var(--radius-lg)", padding: 16,
          }}>
            <h3 style={{ fontSize: 14, fontWeight: 600, color: "var(--text-primary)", marginBottom: 12 }}>
              Plan actif
            </h3>

            {planPreview ? (
              <div>
                <div style={{
                  height: 160, borderRadius: "var(--radius)", overflow: "hidden",
                  border: "1px solid var(--border)", marginBottom: 10,
                }}>
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={planPreview} alt="Plan" style={{ width: "100%", height: "100%", objectFit: "cover" }} />
                </div>
                <div style={{ fontSize: 12, color: "var(--accent)", marginBottom: 8, fontWeight: 500 }}>
                  ✅ {planTitle || planFile?.name}
                </div>
                <button
                  onClick={() => { setPlanFile(null); setPlanPreview(""); setPlanTitle(""); }}
                  className="btn btn-ghost"
                  style={{ width: "100%", justifyContent: "center", fontSize: 12 }}
                >
                  Changer de plan
                </button>
              </div>
            ) : (
              <div
                onClick={() => fileRef.current?.click()}
                style={{
                  height: 120, border: "2px dashed var(--border)",
                  borderRadius: "var(--radius)", display: "flex",
                  flexDirection: "column", alignItems: "center",
                  justifyContent: "center", cursor: "pointer",
                  gap: 8, transition: "all 0.2s ease",
                }}
              >
                <span style={{ fontSize: 28 }}>📐</span>
                <span style={{ fontSize: 12, color: "var(--text-muted)", textAlign: "center" }}>
                  Cliquez pour uploader votre plan
                </span>
              </div>
            )}

            <input
              ref={fileRef}
              type="file"
              accept=".png,.jpg,.jpeg,.webp"
              style={{ display: "none" }}
              onChange={(e) => e.target.files?.[0] && handlePlanUpload(e.target.files[0])}
            />
          </div>

          {/* Suggested questions */}
          <div style={{
            background: "var(--surface)", border: "1px solid var(--border)",
            borderRadius: "var(--radius-lg)", padding: 16,
          }}>
            <h3 style={{ fontSize: 14, fontWeight: 600, color: "var(--text-primary)", marginBottom: 12 }}>
              Questions suggérées
            </h3>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {SUGGESTED_QUESTIONS.map((q) => (
                <button
                  key={q}
                  onClick={() => handleAsk(q)}
                  disabled={loading}
                  style={{
                    padding: "8px 12px", background: "var(--bg-secondary)",
                    border: "1px solid var(--border)", borderRadius: "var(--radius)",
                    fontSize: 12, color: "var(--text-secondary)", cursor: "pointer",
                    textAlign: "left", transition: "all 0.2s ease",
                    opacity: loading ? 0.5 : 1,
                  }}
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
