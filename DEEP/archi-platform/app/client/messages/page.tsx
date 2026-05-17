"use client";
import { useState, useEffect, useRef } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Message {
  id: string;
  sender_role: "architect" | "client";
  sender: string;
  text: string;
  time: string;
  image_url?: string;  // URL de l'image attachée
  image_name?: string; // Nom du fichier
}

interface Conversation {
  id: string;
  project: string;
  architect: string;
  client: string;
  last_message: string;
  last_time: string;
  unread_client: number;
}

export default function ClientMessagesPage() {
  const [conv,     setConv]     = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMsg,   setNewMsg]   = useState("");
  const [loading,  setLoading]  = useState(true);
  const [sending,  setSending]  = useState(false);
  const [attachedImage, setAttachedImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string>("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Get conv_id from logged-in user — computed once on mount (localStorage is client-only)
  const [CONV_ID] = useState<string>(() => {
    if (typeof window === "undefined") return "conv_1";
    try {
      const user = JSON.parse(localStorage.getItem("archi_user") || "{}");
      if (user.id) return `conv_${user.id.substring(0, 8)}`;
    } catch {}
    return "conv_1";
  });

  useEffect(() => {
    fetch(`${API_URL}/api/messages/${CONV_ID}`)
      .then(r => r.json())
      .then(d => {
        setMessages(d.messages || []);
        setConv(d.conversation || null);
        setLoading(false);
        fetch(`${API_URL}/api/messages/${CONV_ID}/read?role=client`, { method: "PUT" });
      })
      .catch(() => {
        setMessages([
          { id: "m1", sender_role: "architect", sender: "Jean-Marc Leblanc", text: "Bonjour ! J'ai bien reçu votre brief. Je commence les premières esquisses.", time: "28 Avr, 09:15" },
          { id: "m2", sender_role: "client",    sender: "Moi",               text: "Merci ! On est très enthousiastes.", time: "28 Avr, 10:30" },
          { id: "m3", sender_role: "architect", sender: "Jean-Marc Leblanc", text: "J'ai révisé le plan selon vos retours. Pouvez-vous valider ?", time: "1 Mai, 09:00" },
        ]);
        setConv({ id: CONV_ID, project: "Villa Moderne — Dupont", architect: "Jean-Marc Leblanc", client: "M. & Mme Dupont", last_message: "", last_time: "", unread_client: 0 });
        setLoading(false);
      });
    
    // Check for shared sketches from localStorage
    const sharedData = localStorage.getItem('sketches_to_share');
    if (sharedData) {
      try {
        const data = JSON.parse(sharedData);
        console.log('📦 Found shared sketches:', data);
        
        // Only load if timestamp is recent (within 5 minutes)
        if (Date.now() - data.timestamp < 5 * 60 * 1000) {
          // Auto-attach the first sketch
          if (data.sketches && data.sketches.length > 0) {
            const firstSketch = data.sketches[0];
            console.log('🖼️  Loading sketch:', firstSketch.title);
            
            // Convert base64 to blob and create File
            if (firstSketch.image_url) {
              // Check if it's a base64 data URL
              if (firstSketch.image_url.startsWith('data:image')) {
                // Extract base64 data
                const base64Data = firstSketch.image_url.split(',')[1];
                const byteCharacters = atob(base64Data);
                const byteNumbers = new Array(byteCharacters.length);
                for (let i = 0; i < byteCharacters.length; i++) {
                  byteNumbers[i] = byteCharacters.charCodeAt(i);
                }
                const byteArray = new Uint8Array(byteNumbers);
                const blob = new Blob([byteArray], { type: 'image/png' });
                
                const file = new File([blob], `${firstSketch.title}.png`, { type: 'image/png' });
                console.log('✅ File created:', file.name, file.size, 'bytes');
                
                handleImageAttach(file);
                
                // Set pre-filled message
                setNewMsg(`J'ai généré des esquisses IA en style ${data.style}. Voici "${firstSketch.title}". Pouvez-vous me donner votre avis ? 🎨`);
                
                console.log('✅ Image attached and message pre-filled');
              } else {
                console.error('❌ Image URL is not a base64 data URL');
              }
            }
          }
        } else {
          console.log('⏰ Shared data expired');
        }
        // Clear the data after loading
        localStorage.removeItem('sketches_to_share');
      } catch (e) {
        console.error('❌ Error loading shared sketches:', e);
      }
    } else {
      console.log('📭 No shared sketches found');
    }
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Poll every 3s — only update if server has more real messages
  useEffect(() => {
    const interval = setInterval(() => {
      fetch(`${API_URL}/api/messages/${CONV_ID}`)
        .then(r => r.json())
        .then(d => {
          const serverMsgs = d.messages || [];
          const realCount = serverMsgs.filter((m: Message) => !m.id.startsWith("temp_")).length;
          setMessages(prev => {
            const localReal = prev.filter(m => !m.id.startsWith("temp_")).length;
            return realCount > localReal ? serverMsgs : prev;
          });
        })
        .catch(() => {});
    }, 3000);
    return () => clearInterval(interval);
  }, [CONV_ID]);

  const handleSend = async () => {
    if (!newMsg.trim() && !attachedImage) return;
    setSending(true);
    const text = newMsg;
    setNewMsg("");

    // Create image URL if there's an attached image
    let imageUrl = "";
    let imageName = "";
    if (attachedImage) {
      imageUrl = imagePreview;
      imageName = attachedImage.name;
    }

    const optimistic: Message = {
      id: `temp_${Date.now()}`,
      sender_role: "client",
      sender: "Moi",
      text,
      time: "Maintenant",
      image_url: imageUrl,
      image_name: imageName,
    };
    setMessages(prev => [...prev, optimistic]);

    // Clear attachment
    setAttachedImage(null);
    setImagePreview("");

    try {
      const user = JSON.parse(localStorage.getItem("archi_user") || "{}");
      const senderName = user.name || "Client";
      
      // For now, we'll send the message with image info
      // In a real app, you'd upload the image to a server first
      const res = await fetch(`${API_URL}/api/messages/${CONV_ID}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          text, 
          sender: senderName, 
          sender_role: "client",
          image_url: imageUrl,
          image_name: imageName,
        }),
      });
      if (res.ok) {
        const msg = await res.json();
        setMessages(prev => [...prev.filter(m => m.id !== optimistic.id), msg]);
      }
    } catch {
      // Keep optimistic
    } finally {
      setSending(false);
    }
  };

  const handleImageAttach = (file: File) => {
    setAttachedImage(file);
    const url = URL.createObjectURL(file);
    setImagePreview(url);
  };

  const removeAttachment = () => {
    setAttachedImage(null);
    setImagePreview("");
  };

  return (
    <div style={{ maxWidth: 800, height: "calc(100vh - 130px)", display: "flex", flexDirection: "column" }}>
      <div className="animate-fade-in" style={{ marginBottom: 20 }}>
        <h1 style={{ fontFamily: "'Playfair Display', serif", fontSize: 28, fontWeight: 700, color: "var(--text-primary)", marginBottom: 6 }}>
          Messages
        </h1>
      </div>

      <div style={{
        flex: 1, background: "var(--surface)", border: "1px solid var(--border)",
        borderRadius: "var(--radius-lg)", display: "flex", flexDirection: "column", overflow: "hidden",
      }}>
        {/* Header */}
        <div style={{ padding: "16px 20px", borderBottom: "1px solid var(--border)", display: "flex", gap: 12, alignItems: "center" }}>
          <div style={{ width: 40, height: 40, borderRadius: "50%", background: "linear-gradient(135deg, var(--accent), #e8c98e)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 16, fontWeight: 700, color: "white" }}>
            JL
          </div>
          <div>
            <div style={{ fontSize: 15, fontWeight: 600, color: "var(--text-primary)" }}>
              {conv?.architect || "Jean-Marc Leblanc"}
            </div>
            <div style={{ fontSize: 12, color: "var(--accent)" }}>
              Architecte · {conv?.project || "Villa Moderne"}
            </div>
          </div>
          <div style={{ marginLeft: "auto" }}>
            <button className="btn btn-secondary" style={{ fontSize: 12, padding: "6px 12px" }}>📐 Voir le plan</button>
          </div>
        </div>

        {/* Messages */}
        <div style={{ flex: 1, overflowY: "auto", padding: 20, display: "flex", flexDirection: "column", gap: 16 }}>
          {loading ? (
            <div style={{ textAlign: "center", color: "var(--text-muted)", padding: 40 }}>Chargement...</div>
          ) : messages.map(msg => (
            <div key={msg.id} style={{
              display: "flex", gap: 10,
              flexDirection: msg.sender_role === "client" ? "row-reverse" : "row",
              alignItems: "flex-end",
            }}>
              {msg.sender_role === "architect" && (
                <div style={{ width: 30, height: 30, borderRadius: "50%", background: "linear-gradient(135deg, var(--accent), #e8c98e)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 11, fontWeight: 700, color: "white", flexShrink: 0 }}>
                  JL
                </div>
              )}
              <div style={{ maxWidth: "72%" }}>
                <div style={{
                  padding: "10px 14px",
                  borderRadius: msg.sender_role === "client" ? "16px 4px 16px 16px" : "4px 16px 16px 16px",
                  background: msg.sender_role === "client" ? "var(--accent)" : "var(--bg-secondary)",
                  color: msg.sender_role === "client" ? "white" : "var(--text-primary)",
                  fontSize: 14, lineHeight: 1.5,
                  border: msg.sender_role === "architect" ? "1px solid var(--border)" : "none",
                }}>
                  {msg.image_url && (
                    <div style={{ marginBottom: 8 }}>
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img 
                        src={msg.image_url} 
                        alt={msg.image_name || "Image attachée"} 
                        style={{ 
                          maxWidth: "100%", 
                          borderRadius: 8, 
                          border: "1px solid rgba(255,255,255,0.2)",
                          cursor: "pointer",
                        }}
                        onClick={() => {
                          // Store image data in localStorage and redirect to VQA page
                          localStorage.setItem('plan_to_analyze', JSON.stringify({
                            image_url: msg.image_url,
                            image_name: msg.image_name || 'plan.png',
                            timestamp: Date.now(),
                          }));
                          window.location.href = '/client/vqa';
                        }}
                      />
                      <div style={{ fontSize: 11, marginTop: 4, opacity: 0.8 }}>
                        📎 {msg.image_name} · Cliquez pour analyser
                      </div>
                    </div>
                  )}
                  {msg.text}
                </div>
                <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 4, textAlign: msg.sender_role === "client" ? "right" : "left" }}>
                  {msg.time}
                </div>
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div style={{ padding: 16, borderTop: "1px solid var(--border)" }}>
          {/* Image preview */}
          {imagePreview && (
            <div style={{ 
              marginBottom: 12, 
              padding: 12, 
              background: "var(--bg-secondary)", 
              borderRadius: "var(--radius)",
              border: "1px solid var(--border)",
              display: "flex",
              gap: 12,
              alignItems: "center",
            }}>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img 
                src={imagePreview} 
                alt="Preview" 
                style={{ 
                  width: 60, 
                  height: 60, 
                  objectFit: "cover", 
                  borderRadius: 6,
                  border: "1px solid var(--border)",
                }} 
              />
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 13, fontWeight: 500, color: "var(--text-primary)" }}>
                  {attachedImage?.name}
                </div>
                <div style={{ fontSize: 11, color: "var(--text-muted)" }}>
                  {attachedImage && (attachedImage.size / 1024).toFixed(1)} KB
                </div>
              </div>
              <button 
                onClick={removeAttachment}
                className="btn btn-ghost"
                style={{ padding: "6px 10px", fontSize: 12 }}
              >
                ✕
              </button>
            </div>
          )}
          
          {/* Input row */}
          <div style={{ display: "flex", gap: 10 }}>
            <button
              onClick={() => fileInputRef.current?.click()}
              className="btn btn-ghost"
              style={{ padding: "10px 12px" }}
              title="Attacher une image"
            >
              📎
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              style={{ display: "none" }}
              onChange={(e) => e.target.files?.[0] && handleImageAttach(e.target.files[0])}
            />
            <input
              className="input"
              placeholder="Écrire un message à votre architecte..."
              value={newMsg}
              onChange={e => setNewMsg(e.target.value)}
              onKeyDown={e => e.key === "Enter" && !e.shiftKey && handleSend()}
              style={{ flex: 1 }}
            />
            <button 
              onClick={handleSend} 
              disabled={(!newMsg.trim() && !attachedImage) || sending} 
              className="btn btn-primary" 
              style={{ padding: "10px 16px" }}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
