import Link from "next/link";
import Image from "next/image";
import Navbar from "@/components/Navbar";

export default function HomePage() {
  const galleryImages = [
    {
      src: "https://images.unsplash.com/photo-1487958449943-2429e8be8625?w=800&q=80",
      alt: "Architecture moderne — façade blanche",
      label: "Résidentiel moderne",
    },
    {
      src: "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=800&q=80",
      alt: "Villa contemporaine avec piscine",
      label: "Villa contemporaine",
    },
    {
      src: "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=800&q=80",
      alt: "Maison architecturale lumineuse",
      label: "Design lumineux",
    },
    {
      src: "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=800&q=80",
      alt: "Intérieur minimaliste salon",
      label: "Intérieur minimaliste",
    },
    {
      src: "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800&q=80",
      alt: "Plan architectural sur table",
      label: "Plans & conception",
    },
    {
      src: "https://images.unsplash.com/photo-1503387762-592deb58ef4e?w=800&q=80",
      alt: "Architecte travaillant sur des plans",
      label: "Collaboration",
    },
  ];

  const projectShowcase = [
    {
      src: "https://images.unsplash.com/photo-1600566753086-00f18fb6b3ea?w=900&q=80",
      alt: "Villa moderne avec grandes baies vitrées",
      title: "Villa Les Pins",
      desc: "Résidentiel · 180 m² · Analyse IA complète",
      tag: "NeRF 3D",
    },
    {
      src: "https://images.unsplash.com/photo-1600585154526-990dced4db0d?w=900&q=80",
      alt: "Maison contemporaine extérieur",
      title: "Maison Horizon",
      desc: "Contemporain · 140 m² · Brief structuré",
      tag: "CNN + LSTM",
    },
    {
      src: "https://images.unsplash.com/photo-1600047509807-ba8f99d2cdde?w=900&q=80",
      alt: "Architecture intérieure ouverte",
      title: "Loft Lumière",
      desc: "Intérieur · 95 m² · Esquisses générées",
      tag: "Stable Diffusion",
    },
  ];

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg)" }}>
      <Navbar role="public" />

      {/* ── HERO ── */}
      <section style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        padding: "80px 24px 40px",
        position: "relative",
        overflow: "hidden",
        maxWidth: 1400,
        margin: "0 auto",
        gap: 60,
      }}>
        {/* Background grid */}
        <div style={{
          position: "fixed",
          inset: 0,
          backgroundImage: `
            linear-gradient(var(--border) 1px, transparent 1px),
            linear-gradient(90deg, var(--border) 1px, transparent 1px)
          `,
          backgroundSize: "60px 60px",
          opacity: 0.2,
          pointerEvents: "none",
          zIndex: 0,
        }} />

        {/* Left — text */}
        <div className="animate-fade-in-left" style={{ flex: 1, position: "relative", zIndex: 1, minWidth: 300 }}>
          <div style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 8,
            padding: "6px 16px",
            borderRadius: 999,
            border: "1px solid var(--accent)",
            background: "var(--accent-light)",
            marginBottom: 28,
          }}>
            <span style={{ width: 6, height: 6, borderRadius: "50%", background: "var(--accent)", display: "inline-block" }} />
            <span style={{ fontSize: 13, color: "var(--accent-dark)", fontWeight: 500 }}>
              Plateforme IA pour Architectes
            </span>
          </div>

          <h1 style={{
            fontFamily: "'Playfair Display', serif",
            fontSize: "clamp(36px, 5vw, 68px)",
            fontWeight: 700,
            lineHeight: 1.1,
            marginBottom: 24,
            color: "var(--text-primary)",
          }}>
            Donnez vie à vos{" "}
            <span className="gradient-text">plans</span>
            <br />avec l&apos;IA
          </h1>

          <p style={{
            fontSize: 17,
            color: "var(--text-secondary)",
            maxWidth: 480,
            marginBottom: 36,
            lineHeight: 1.7,
          }}>
            Analysez vos plans 2D, générez des visualisations 3D immersives,
            et collaborez avec vos clients en temps réel — tout en un.
          </p>

          <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 48 }}>
            <Link href="/auth/register?role=architect" className="btn btn-primary" style={{ fontSize: 15, padding: "14px 28px" }}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polygon points="3 9 12 2 21 9 21 20 3 20 3 9"/>
              </svg>
              Je suis Architecte
            </Link>
            <Link href="/auth/register?role=client" className="btn btn-secondary" style={{ fontSize: 15, padding: "14px 28px" }}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                <circle cx="12" cy="7" r="4"/>
              </svg>
              Je suis Client
            </Link>
          </div>

          {/* Stats */}
          <div style={{ display: "flex", gap: 32, flexWrap: "wrap" }}>
            {[
              { value: "5K+", label: "Plans analysés" },
              { value: "98%", label: "Précision IA" },
              { value: "200+", label: "Architectes" },
            ].map((stat) => (
              <div key={stat.label}>
                <div style={{
                  fontFamily: "'Playfair Display', serif",
                  fontSize: 28,
                  fontWeight: 700,
                  color: "var(--accent)",
                }}>
                  {stat.value}
                </div>
                <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 2 }}>
                  {stat.label}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right — hero image collage */}
        <div className="animate-fade-in-right" style={{
          flex: 1,
          position: "relative",
          zIndex: 1,
          minWidth: 300,
          maxWidth: 560,
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gridTemplateRows: "240px 180px",
          gap: 12,
        }}>
          {/* Large image */}
          <div style={{
            gridColumn: "1 / 2",
            gridRow: "1 / 2",
            borderRadius: 16,
            overflow: "hidden",
            position: "relative",
            boxShadow: "var(--shadow-lg)",
          }}>
            <Image
              src="https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=600&q=80"
              alt="Villa contemporaine"
              fill
              style={{ objectFit: "cover" }}
              unoptimized
            />
            <div style={{
              position: "absolute", bottom: 10, left: 10,
              background: "rgba(0,0,0,0.65)", backdropFilter: "blur(6px)",
              borderRadius: 8, padding: "4px 10px",
              fontSize: 11, color: "white", fontWeight: 500,
            }}>
              Villa contemporaine
            </div>
          </div>

          {/* Top right */}
          <div style={{
            gridColumn: "2 / 3",
            gridRow: "1 / 2",
            borderRadius: 16,
            overflow: "hidden",
            position: "relative",
            boxShadow: "var(--shadow-lg)",
          }}>
            <Image
              src="https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=400&q=80"
              alt="Maison architecturale"
              fill
              style={{ objectFit: "cover" }}
              unoptimized
            />
            {/* AI badge */}
            <div style={{
              position: "absolute", top: 10, right: 10,
              background: "var(--accent)", borderRadius: 999,
              padding: "3px 10px", fontSize: 10, fontWeight: 700, color: "white",
            }}>
              IA Analysé ✓
            </div>
          </div>

          {/* Bottom left */}
          <div style={{
            gridColumn: "1 / 2",
            gridRow: "2 / 3",
            borderRadius: 16,
            overflow: "hidden",
            position: "relative",
            boxShadow: "var(--shadow-lg)",
          }}>
            <Image
              src="https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&q=80"
              alt="Plans architecturaux"
              fill
              style={{ objectFit: "cover" }}
              unoptimized
            />
          </div>

          {/* Bottom right — stat card */}
          <div style={{
            gridColumn: "2 / 3",
            gridRow: "2 / 3",
            borderRadius: 16,
            background: "linear-gradient(135deg, var(--accent), #e8c98e)",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            padding: 20,
            boxShadow: "var(--shadow-lg)",
          }}>
            <div style={{ fontSize: 36, fontWeight: 700, color: "white", fontFamily: "'Playfair Display', serif" }}>3x</div>
            <div style={{ fontSize: 13, color: "rgba(255,255,255,0.85)", textAlign: "center", marginTop: 4 }}>
              Plus rapide avec ArchiGuide
            </div>
          </div>
        </div>
      </section>

      {/* ── GALLERY ── */}
      <section style={{ padding: "80px 24px", background: "var(--bg-secondary)", borderTop: "1px solid var(--border)" }}>
        <div style={{ maxWidth: 1200, margin: "0 auto" }}>
          <div style={{ textAlign: "center", marginBottom: 48 }}>
            <span className="badge badge-gold" style={{ marginBottom: 12, display: "inline-block" }}>Galerie</span>
            <h2 style={{
              fontFamily: "'Playfair Display', serif",
              fontSize: 36,
              fontWeight: 700,
              color: "var(--text-primary)",
              marginBottom: 12,
            }}>
              Des projets qui inspirent
            </h2>
            <p style={{ color: "var(--text-secondary)", fontSize: 15, maxWidth: 480, margin: "0 auto" }}>
              Découvrez des réalisations analysées et visualisées avec ArchiGuide.
            </p>
          </div>

          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(3, 1fr)",
            gridTemplateRows: "220px 220px",
            gap: 14,
          }}>
            {galleryImages.map((img, i) => (
              <div
                key={img.src}
                className="card-hover"
                style={{
                  borderRadius: 16,
                  overflow: "hidden",
                  position: "relative",
                  gridColumn: i === 0 ? "1 / 2" : i === 3 ? "3 / 4" : undefined,
                  boxShadow: "var(--shadow-md)",
                }}
              >
                <Image
                  src={img.src}
                  alt={img.alt}
                  fill
                  style={{ objectFit: "cover", transition: "transform 0.4s ease" }}
                  unoptimized
                />
                {/* Overlay */}
                <div style={{
                  position: "absolute",
                  inset: 0,
                  background: "linear-gradient(to top, rgba(0,0,0,0.6) 0%, transparent 50%)",
                }} />
                <div style={{
                  position: "absolute",
                  bottom: 12,
                  left: 14,
                  fontSize: 13,
                  fontWeight: 600,
                  color: "white",
                }}>
                  {img.label}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── PROJECT SHOWCASE ── */}
      <section style={{ padding: "80px 24px", maxWidth: 1200, margin: "0 auto" }}>
        <div style={{ textAlign: "center", marginBottom: 48 }}>
          <span className="badge badge-gold" style={{ marginBottom: 12, display: "inline-block" }}>Projets réalisés</span>
          <h2 style={{
            fontFamily: "'Playfair Display', serif",
            fontSize: 36,
            fontWeight: 700,
            color: "var(--text-primary)",
            marginBottom: 12,
          }}>
            Analysés par ArchiGuide IA
          </h2>
          <p style={{ color: "var(--text-secondary)", fontSize: 15, maxWidth: 480, margin: "0 auto" }}>
            Chaque projet bénéficie de l&apos;analyse CNN+LSTM, de la visualisation 3D et du brief structuré.
          </p>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: 24 }}>
          {projectShowcase.map((project) => (
            <div key={project.title} className="card-hover" style={{
              background: "var(--surface)",
              border: "1px solid var(--border)",
              borderRadius: 20,
              overflow: "hidden",
            }}>
              <div style={{ height: 220, position: "relative" }}>
                <Image
                  src={project.src}
                  alt={project.alt}
                  fill
                  style={{ objectFit: "cover" }}
                  unoptimized
                />
                <div style={{
                  position: "absolute",
                  inset: 0,
                  background: "linear-gradient(to top, rgba(0,0,0,0.5) 0%, transparent 60%)",
                }} />
                <div style={{
                  position: "absolute",
                  top: 12,
                  right: 12,
                  background: "var(--accent)",
                  borderRadius: 999,
                  padding: "3px 10px",
                  fontSize: 11,
                  fontWeight: 700,
                  color: "white",
                }}>
                  {project.tag}
                </div>
              </div>
              <div style={{ padding: "18px 20px" }}>
                <h3 style={{ fontSize: 17, fontWeight: 700, color: "var(--text-primary)", marginBottom: 6 }}>
                  {project.title}
                </h3>
                <p style={{ fontSize: 13, color: "var(--text-secondary)" }}>{project.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ── FEATURES ── */}
      <section style={{ padding: "80px 24px", background: "var(--bg-secondary)", borderTop: "1px solid var(--border)" }}>
        <div style={{ maxWidth: 1200, margin: "0 auto" }}>
          <div style={{ textAlign: "center", marginBottom: 56 }}>
            <h2 style={{
              fontFamily: "'Playfair Display', serif",
              fontSize: 36,
              fontWeight: 700,
              color: "var(--text-primary)",
              marginBottom: 16,
            }}>
              Tout ce dont vous avez besoin
            </h2>
            <p style={{ color: "var(--text-secondary)", fontSize: 15, maxWidth: 500, margin: "0 auto" }}>
              Des outils IA puissants intégrés dans un workflow fluide pour architectes et clients.
            </p>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 20 }}>
            {[
              { icon: "🧠", title: "Analyse IA de Plans", desc: "CNN + LSTM + Attention génère automatiquement une description détaillée : pièces, surfaces, ouvertures, style.", tag: "ResNet-101 + LSTM" },
              { icon: "🎬", title: "Visualisation 3D", desc: "Transformez vos plans en vidéos de visite virtuelle immersives grâce aux modèles NeRF et Stable Video Diffusion.", tag: "NeRF + Diffusion" },
              { icon: "✍️", title: "Brief Client IA", desc: "Le client décrit son projet librement. Le LLM structure automatiquement un brief formel pour l'architecte.", tag: "GPT-4 / Claude" },
              { icon: "🎨", title: "Esquisses Générées", desc: "Générez des mood boards et esquisses architecturales à partir du brief client avec Stable Diffusion.", tag: "Stable Diffusion" },
              { icon: "❓", title: "Questions sur Plan", desc: "Le client pose des questions directement sur le plan : surfaces, localisation des pièces, ouvertures.", tag: "VQA Model" },
              { icon: "💬", title: "Collaboration Temps Réel", desc: "Espace partagé architecte-client avec annotations sur plan, messagerie intégrée et suivi de projet.", tag: "WebSocket" },
            ].map((feature) => (
              <div key={feature.title} className="card-hover" style={{
                background: "var(--surface)",
                border: "1px solid var(--border)",
                borderRadius: 16,
                padding: 24,
              }}>
                <div style={{ fontSize: 32, marginBottom: 14 }}>{feature.icon}</div>
                <span className="badge badge-gold" style={{ fontSize: 10, marginBottom: 10, display: "inline-block" }}>{feature.tag}</span>
                <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 8, color: "var(--text-primary)" }}>
                  {feature.title}
                </h3>
                <p style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.6 }}>
                  {feature.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── TESTIMONIALS ── */}
      <section style={{ padding: "80px 24px", maxWidth: 1100, margin: "0 auto" }}>
        <div style={{ textAlign: "center", marginBottom: 48 }}>
          <h2 style={{
            fontFamily: "'Playfair Display', serif",
            fontSize: 36,
            fontWeight: 700,
            color: "var(--text-primary)",
            marginBottom: 12,
          }}>
            Ce qu&apos;ils en disent
          </h2>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 20 }}>
          {[
            { name: "Sophie Marchand", role: "Architecte DPLG", avatar: "SM", text: "ArchiGuide a transformé ma façon de présenter les projets. Mes clients comprennent immédiatement le plan grâce aux descriptions IA et aux vidéos 3D." },
            { name: "Thomas Leroy", role: "Client — Villa Horizon", avatar: "TL", text: "J'ai pu poser toutes mes questions sur le plan directement dans l'app. L'architecte et moi sommes toujours alignés. Gain de temps énorme !" },
            { name: "Marc Dubois", role: "Architecte d'intérieur", avatar: "MD", text: "Les esquisses générées par IA sont un excellent point de départ pour les discussions avec les clients. Ça accélère vraiment la phase de conception." },
          ].map((t) => (
            <div key={t.name} className="card-hover" style={{
              background: "var(--surface)",
              border: "1px solid var(--border)",
              borderRadius: 16,
              padding: 24,
            }}>
              <div style={{ fontSize: 24, color: "var(--accent)", marginBottom: 14, fontFamily: "serif" }}>&ldquo;</div>
              <p style={{ fontSize: 14, color: "var(--text-secondary)", lineHeight: 1.7, marginBottom: 20 }}>
                {t.text}
              </p>
              <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
                <div style={{
                  width: 40, height: 40, borderRadius: "50%",
                  background: "linear-gradient(135deg, var(--accent), #e8c98e)",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: 13, fontWeight: 700, color: "white",
                }}>
                  {t.avatar}
                </div>
                <div>
                  <div style={{ fontSize: 14, fontWeight: 600, color: "var(--text-primary)" }}>{t.name}</div>
                  <div style={{ fontSize: 12, color: "var(--text-muted)" }}>{t.role}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ── CTA ── */}
      <section style={{
        padding: "80px 24px",
        textAlign: "center",
        background: "var(--bg-secondary)",
        borderTop: "1px solid var(--border)",
        position: "relative",
        overflow: "hidden",
      }}>
        {/* Background image */}
        <div style={{ position: "absolute", inset: 0, zIndex: 0 }}>
          <Image
            src="https://images.unsplash.com/photo-1487958449943-2429e8be8625?w=1400&q=60"
            alt="Architecture background"
            fill
            style={{ objectFit: "cover", opacity: 0.08 }}
            unoptimized
          />
        </div>
        <div style={{ position: "relative", zIndex: 1 }}>
          <h2 style={{
            fontFamily: "'Playfair Display', serif",
            fontSize: 40,
            fontWeight: 700,
            marginBottom: 16,
            color: "var(--text-primary)",
          }}>
            Prêt à transformer votre pratique ?
          </h2>
          <p style={{ color: "var(--text-secondary)", marginBottom: 36, fontSize: 16, maxWidth: 480, margin: "0 auto 36px" }}>
            Rejoignez les architectes qui utilisent déjà ArchiGuide pour gagner du temps et impressionner leurs clients.
          </p>
          <div style={{ display: "flex", gap: 12, justifyContent: "center", flexWrap: "wrap" }}>
            <Link href="/auth/register?role=architect" className="btn btn-primary" style={{ fontSize: 15, padding: "16px 32px" }}>
              Commencer gratuitement →
            </Link>
            <Link href="/auth/login" className="btn btn-secondary" style={{ fontSize: 15, padding: "16px 32px" }}>
              Se connecter
            </Link>
          </div>
        </div>
      </section>

      {/* ── FOOTER ── */}
      <footer style={{
        padding: "40px 24px",
        borderTop: "1px solid var(--border)",
        maxWidth: 1200,
        margin: "0 auto",
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 32, marginBottom: 32 }}>
          {/* Brand */}
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 12 }}>
              <div style={{ width: 32, height: 32, background: "var(--accent)", borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center" }}>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5">
                  <polygon points="3 9 12 2 21 9 21 20 3 20 3 9"/>
                  <rect x="9" y="14" width="6" height="6"/>
                </svg>
              </div>
              <span style={{ fontFamily: "'Playfair Display', serif", fontWeight: 700, fontSize: 18, color: "var(--text-primary)" }}>
                Archi<span style={{ color: "var(--accent)" }}>Guide</span>
              </span>
            </div>
            <p style={{ fontSize: 13, color: "var(--text-muted)", maxWidth: 240, lineHeight: 1.6 }}>
              La plateforme IA qui transforme vos plans en expériences immersives.
            </p>
          </div>

          {/* Links */}
          <div style={{ display: "flex", gap: 48, flexWrap: "wrap" }}>
            {[
              { title: "Produit", links: ["Fonctionnalités", "Tarifs", "Démo"] },
              { title: "Ressources", links: ["Documentation", "Blog", "Support"] },
              { title: "Légal", links: ["Confidentialité", "Conditions", "Contact"] },
            ].map((col) => (
              <div key={col.title}>
                <div style={{ fontSize: 12, fontWeight: 700, color: "var(--text-primary)", textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: 12 }}>
                  {col.title}
                </div>
                {col.links.map((l) => (
                  <div key={l} style={{ marginBottom: 8 }}>
                    <Link href="#" style={{ fontSize: 13, color: "var(--text-muted)", textDecoration: "none" }}>{l}</Link>
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>

        <div style={{ borderTop: "1px solid var(--border)", paddingTop: 20, display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 12 }}>
          <span style={{ fontSize: 12, color: "var(--text-muted)" }}>© 2026 ArchiGuide. Tous droits réservés.</span>
          <span style={{ fontSize: 12, color: "var(--text-muted)" }}>Photos : Unsplash · IA : ResNet-101, NeRF, Stable Diffusion</span>
        </div>
      </footer>
    </div>
  );
}
