"use client";
import { useState, useEffect, useRef } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Message {
  id: string;
  sender_role: "architect" | "client";
  sender: string;
  text: string;
  time: string;
  image_url?: string;
  image_name?: string;
}

interface Conversation {
  id: string;
  project: string;
  architect: string;
  client: string;
  client_id: string;
  last_message: string;
  last_time: string;
  unread_client: number;
  unread_arch: number;
}

interface Client {
  id: string;
  name: string;
  email: string;
  project: string;
  avatar: string;
  status: string;
}

export default function ArchitectMessagesPage() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConvId, setActiveConvId]   = useState<string>("");
  const [messages, setMessages]           = useState<Message[]>([]);
  const [activeConv, setActiveConv]       = useState<Conversation | null>(null);
  const [newMsg, setNewMsg]               = useState("");
  const [loading, setLoading]             = useState(false);
  const [sending, setSending]             = useState(false);
  const [showNewConv, setShowNewConv]     = useState(false);
  const [clients, setClients]             = useState<Client[]>([]);
  const [selectedClient, setSelectedClient] = useState<Client | null>(null);
  const [loadingClients, setLoadingClients] = useState(false);
  const [attachedImage, setAttachedImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string>("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    fetch(`${API_URL}/api/conversations`)
      .then(r => r.json())
      .then(d => {
        const list = d.conversations || [];
        setConversations(list);
        if (list.length > 0) setActiveConvId(list[0].id);
      })
      .catch(() => {
        // Fallback: load from local data files
        setConversations([]);
      });
  }, []);

  useEffect(() => {
    if (!activeConvId) return;
    setLoading(true);
    fetch(`${API_URL}/api/messages/${activeConvId}`)
      .then(r => r.json())
      .then(d => {
        setMessages(d.messages || []);
        setActiveConv(d.conversation || null);
        setLoading(false);
        fetch(`${API_URL}/api/messages/${activeConvId}/read?role=architect`, { method: "PUT" });
      })
      .catch(() => setLoading(false));
  }, [activeConvId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    if (!activeConvId) return;
    const interval = setInterval(() => {
      fetch(`${API_URL}/api/messages/${activeConvId}`)
        .then(r => r.json())
        .then(d => {
          const srv = (d.messages || []).filter((m: Message) => !m.id.startsWith("temp_"));
          setMessages(prev => {
            const loc = prev.filter(m => !m.id.startsWith("temp_"));
            return srv.length > loc.length ? (d.messages || []) : prev;
          });
        })
        .catch(() => {});
    }, 3000);
    return () => clearInterval(interval);
  }, [activeConvId]);

  const openNewConvDialog = () => {
    setShowNewConv(true);
    setSelectedClient(null);
    setLoadingClients(true);
    fetch(`${API_URL}/api/clients`)
      .then(r => r.json())
      .then(d => {
        const list = Array.isArray(d) ? d : (d.clients || []);
        const existing = conversations.map(c => c.client_id);
        setClients(list.filter((c: Client) => !existing.includes(c.id)));
        setLoadingClients(false);
      })
      .catch(() => setLoadingClients(false));
  };

  const handleStartConversation = async () => {
    if (!selectedClient) return;
    try {
      const res = await fetch(`${API_URL}/api/conversations`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          project: selectedClient.project || "Nouveau projet",
          architect_id: "arch_1", architect: "Architecte",
          client_id: selectedClient.id, client: selectedClient.name,
        }),
      });
      if (res.ok) {
        const c = await res.json();
        setConversations(prev => [c, ...prev]);
        setActiveConvId(c.id);
        setShowNewConv(false);
      }
    } catch {}
  };

  const handleSend = async () => {
    if ((!newMsg.trim() && !attachedImage) || !activeConvId) return;
    setSending(true);
    const text = newMsg;
    setNewMsg("");
    
    let imageUrl = "";
    let imageName = "";
    if (attachedImage) {
      imageUrl = imagePreview;
      imageName = attachedImage.name;
    }
    
    const opt: Message = { 
      id: `temp_${Date.now()}`, 
      sender_role: "architect", 
      sender: "Architecte", 
      text, 
      time: "Maintenant",
      image_url: imageUrl,
      image_name: imageName,
    };
    setMessages(prev => [...prev, opt]);
    
    setAttachedImage(null);
    setImagePreview("");
    
    try {
      const res = await fetch(`${API_URL}/api/messages/${activeConvId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          text, 
          sender: "Architecte", 
          sender_role: "architect",
          image_url: imageUrl,
          image_name: imageName,
        }),
      });
      if (res.ok) {
        const msg = await res.json();
        setMessages(prev => [...prev.filter(m => m.id !== opt.id), msg]);
        setConversations(prev => prev.map(c =>
          c.id === activeConvId ? { ...c, last_message: text.substring(0, 60), last_time: "Maintenant" } : c
        ));
      }
    } catch {} finally { setSending(false); }
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

  const conv = activeConv || conversations.find(c => c.id === activeConvId);

  return (
    <div style={{ maxWidth: 1100, height: "calc(100vh - 130px)", display: "flex", flexDirection: "column" }}>
      <div className="animate-fade-in" style={{ marginBottom: 20, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h1 style={{ fontFamily: "'Playfair Display', serif", fontSize: 28, fontWeight: 700, color: "var(--text-primary)" }}>Messages</h1>
        <button onClick={openNewConvDialog} className="btn btn-primary" style={{ fontSize: 13 }}>+ Nouvelle conversation</button>
      </div>

      {showNewConv && (
        <div style={{ position: "fixed", inset: 0, zIndex: 200, background: "rgba(0,0,0,0.6)", backdropFilter: "blur(4px)", display: "flex", alignItems: "center", justifyContent: "center" }}
          onClick={() => setShowNewConv(false)}>
          <div style={{ background: "var(--surface)", borderRadius: "var(--radius-lg)", border: "1px solid var(--border)", padding: 28, width: "100%", maxWidth: 480 }}
            onClick={e => e.stopPropagation()}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
              <h2 style={{ fontSize: 18, fontWeight: 700, color: "var(--text-primary)" }}>Nouvelle conversation</h2>
              <button onClick={() => setShowNewConv(false)} style={{ background: "none", border: "none", cursor: "pointer", fontSize: 20, color: "var(--text-muted)" }}>x</button>
            </div>
            {loadingClients ? (
              <div style={{ textAlign: "center", padding: 32, color: "var(--text-muted)" }}>Chargement...</div>
            ) : clients.length === 0 ? (
              <div style={{ textAlign: "center", padding: 32, color: "var(--text-muted)" }}>
                <div style={{ fontSize: 32, marginBottom: 8 }}>👥</div>
                <div>Tous les clients ont déjà une conversation</div>
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 8, maxHeight: 320, overflowY: "auto", marginBottom: 20 }}>
                {clients.map(client => (
                  <div key={client.id} onClick={() => setSelectedClient(client)} style={{
                    display: "flex", gap: 12, alignItems: "center", padding: "12px 14px",
                    borderRadius: "var(--radius)",
                    border: `2px solid ${selectedClient?.id === client.id ? "var(--accent)" : "var(--border)"}`,
                    background: selectedClient?.id === client.id ? "var(--accent-light)" : "var(--bg-secondary)",
                    cursor: "pointer",
                  }}>
                    <div style={{ width: 40, height: 40, borderRadius: "50%", background: "linear-gradient(135deg, var(--accent), #e8c98e)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 16, fontWeight: 700, color: "white" }}>
                      {(client.avatar || client.name[0]).toUpperCase()}
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 14, fontWeight: 600, color: "var(--text-primary)" }}>{client.name}</div>
                      <div style={{ fontSize: 12, color: "var(--text-muted)" }}>{client.email}</div>
                    </div>
                    {selectedClient?.id === client.id && <span style={{ color: "var(--accent)", fontSize: 18 }}>✓</span>}
                  </div>
                ))}
              </div>
            )}
            <div style={{ display: "flex", gap: 10 }}>
              <button onClick={handleStartConversation} disabled={!selectedClient} className="btn btn-primary"
                style={{ flex: 1, justifyContent: "center", opacity: selectedClient ? 1 : 0.5 }}>
                💬 Démarrer la conversation
              </button>
              <button onClick={() => setShowNewConv(false)} className="btn btn-ghost" style={{ padding: "10px 16px" }}>Annuler</button>
            </div>
          </div>
        </div>
      )}

      <div style={{ flex: 1, display: "flex", background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "var(--radius-lg)", overflow: "hidden", minHeight: 0 }}>
        {/* LEFT — Conversations list */}
        <div style={{ width: 280, minWidth: 280, borderRight: "1px solid var(--border)", overflowY: "auto", display: "flex", flexDirection: "column", flexShrink: 0 }}>
          <div style={{ padding: "12px", borderBottom: "1px solid var(--border)" }}>
            <input className="input" placeholder="Rechercher..." style={{ fontSize: 13 }} />
          </div>
          {conversations.length === 0 ? (
            <div style={{ padding: 24, textAlign: "center", color: "var(--text-muted)", fontSize: 13 }}>
              <div style={{ fontSize: 28, marginBottom: 8 }}>💬</div>
              Aucune conversation
              <br />
              <button onClick={openNewConvDialog} style={{ marginTop: 12, fontSize: 12, color: "var(--accent)", background: "none", border: "none", cursor: "pointer", textDecoration: "underline" }}>
                + Démarrer une conversation
              </button>
            </div>
          ) : conversations.map(c => (
            <div key={c.id} onClick={() => setActiveConvId(c.id)} style={{
              padding: "14px 16px", cursor: "pointer",
              background: activeConvId === c.id ? "var(--accent-light)" : "transparent",
              borderLeft: `3px solid ${activeConvId === c.id ? "var(--accent)" : "transparent"}`,
              transition: "all 0.15s ease",
            }}>
              <div style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
                <div style={{ width: 40, height: 40, borderRadius: "50%", background: "linear-gradient(135deg, var(--accent), #e8c98e)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 15, fontWeight: 700, color: "white", flexShrink: 0 }}>
                  {c.client[0].toUpperCase()}
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span style={{ fontSize: 13, fontWeight: 600, color: "var(--text-primary)" }}>{c.client}</span>
                    <span style={{ fontSize: 10, color: "var(--text-muted)" }}>{c.last_time}</span>
                  </div>
                  <div style={{ fontSize: 11, color: "var(--accent)", marginBottom: 2 }}>{c.project}</div>
                  <div style={{ fontSize: 12, color: "var(--text-muted)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {c.last_message || "Aucun message"}
                  </div>
                </div>
                {c.unread_arch > 0 && (
                  <div style={{ width: 18, height: 18, borderRadius: "50%", background: "var(--accent)", color: "white", fontSize: 10, fontWeight: 700, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                    {c.unread_arch}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* RIGHT — Chat */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
          {conv ? (
            <>
              <div style={{ padding: "14px 20px", borderBottom: "1px solid var(--border)", display: "flex", gap: 12, alignItems: "center" }}>
                <div style={{ width: 38, height: 38, borderRadius: "50%", background: "linear-gradient(135deg, var(--accent), #e8c98e)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14, fontWeight: 700, color: "white" }}>
                  {conv.client[0].toUpperCase()}
                </div>
                <div>
                  <div style={{ fontSize: 14, fontWeight: 600, color: "var(--text-primary)" }}>{conv.client}</div>
                  <div style={{ fontSize: 12, color: "var(--accent)" }}>{conv.project}</div>
                </div>
                <div style={{ marginLeft: "auto" }}>
                  <button className="btn btn-secondary" style={{ fontSize: 12, padding: "6px 12px" }}>📐 Voir le plan</button>
                </div>
              </div>

              <div style={{ flex: 1, overflowY: "auto", padding: 20, display: "flex", flexDirection: "column", gap: 14 }}>
                {loading ? (
                  <div style={{ textAlign: "center", color: "var(--text-muted)", padding: 40 }}>Chargement...</div>
                ) : messages.length === 0 ? (
                  <div style={{ textAlign: "center", color: "var(--text-muted)", padding: 40 }}>
                    <div style={{ fontSize: 32, marginBottom: 8 }}>💬</div>
                    Démarrez la conversation
                  </div>
                ) : messages.map(msg => (
                  <div key={msg.id} style={{
                    display: "flex", gap: 10,
                    flexDirection: msg.sender_role === "architect" ? "row-reverse" : "row",
                    alignItems: "flex-end",
                  }}>
                    {msg.sender_role === "client" && (
                      <div style={{ width: 28, height: 28, borderRadius: "50%", background: "linear-gradient(135deg, var(--accent), #e8c98e)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 11, fontWeight: 700, color: "white", flexShrink: 0 }}>
                        {msg.sender[0].toUpperCase()}
                      </div>
                    )}
                    <div style={{ maxWidth: "70%" }}>
                      {msg.sender_role === "client" && (
                        <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 4 }}>{msg.sender}</div>
                      )}
                      <div style={{
                        padding: "10px 14px",
                        borderRadius: msg.sender_role === "architect" ? "16px 4px 16px 16px" : "4px 16px 16px 16px",
                        background: msg.sender_role === "architect" ? "var(--accent)" : "var(--bg-secondary)",
                        color: msg.sender_role === "architect" ? "white" : "var(--text-primary)",
                        fontSize: 14, lineHeight: 1.5,
                        border: msg.sender_role === "client" ? "1px solid var(--border)" : "none",
                        opacity: msg.id.startsWith("temp_") ? 0.7 : 1,
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
                              onClick={() => window.open(msg.image_url, '_blank')}
                            />
                            <div style={{ fontSize: 11, marginTop: 4, opacity: 0.8 }}>
                              📎 {msg.image_name}
                            </div>
                          </div>
                        )}
                        {msg.text}
                      </div>
                      <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 4, textAlign: msg.sender_role === "architect" ? "right" : "left" }}>
                        {msg.sender_role === "client" ? `${msg.sender} · ` : ""}{msg.time}
                      </div>
                    </div>
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>

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
                  <input className="input" placeholder={`Écrire à ${conv.client}...`} value={newMsg}
                    onChange={e => setNewMsg(e.target.value)}
                    onKeyDown={e => e.key === "Enter" && !e.shiftKey && handleSend()}
                    style={{ flex: 1 }} />
                  <button onClick={handleSend} disabled={(!newMsg.trim() && !attachedImage) || sending} className="btn btn-primary" style={{ padding: "10px 16px" }}>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
                    </svg>
                  </button>
                </div>
              </div>
            </>
          ) : (
            <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 12, color: "var(--text-muted)" }}>
              <div style={{ fontSize: 48 }}>💬</div>
              <div style={{ fontSize: 16 }}>Sélectionnez une conversation</div>
              <button onClick={openNewConvDialog} className="btn btn-primary" style={{ fontSize: 13, marginTop: 8 }}>+ Nouvelle conversation</button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
