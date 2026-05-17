"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import ThemeToggle from "./ThemeToggle";
import NotificationBell from "./NotificationBell";
import { useUser } from "@/hooks/useUser";

interface NavbarProps {
  role?: "architect" | "client" | "public";
}

export default function Navbar({ role = "public" }: NavbarProps) {
  const pathname = usePathname();
  const { user, logout } = useUser();

  const architectLinks = [
    { href: "/architect/dashboard", label: "Dashboard" },
    { href: "/architect/projects", label: "Projets" },
    { href: "/architect/upload", label: "Analyser Plan" },
    { href: "/architect/clients", label: "Clients" },
  ];

  const clientLinks = [
    { href: "/client/dashboard", label: "Accueil" },
    { href: "/client/brief", label: "Mon Brief" },
    { href: "/client/projects", label: "Mes Projets" },
    { href: "/explorer", label: "Explorer" },
  ];

  const links = role === "architect" ? architectLinks : role === "client" ? clientLinks : [];

  return (
    <nav style={{
      position: "fixed",
      top: 0,
      left: 0,
      right: 0,
      zIndex: 100,
      height: 64,
      display: "flex",
      alignItems: "center",
      padding: "0 24px",
      background: "var(--bg)",
      borderBottom: "1px solid var(--border)",
      backdropFilter: "blur(12px)",
      gap: 24,
    }}>
      {/* Logo */}
      <Link href="/" style={{ textDecoration: "none", display: "flex", alignItems: "center", gap: 10 }}>
        <div style={{
          width: 32,
          height: 32,
          background: "var(--accent)",
          borderRadius: 8,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5">
            <polygon points="3 9 12 2 21 9 21 20 3 20 3 9"/>
            <rect x="9" y="14" width="6" height="6"/>
          </svg>
        </div>
        <span style={{
          fontFamily: "'Playfair Display', serif",
          fontWeight: 700,
          fontSize: 18,
          color: "var(--text-primary)",
          letterSpacing: "-0.3px",
        }}>
          Archi<span style={{ color: "var(--accent)" }}>Guide</span>
        </span>
      </Link>

      {/* Nav links */}
      <div style={{ display: "flex", gap: 4, flex: 1 }}>
        {links.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            style={{
              padding: "6px 14px",
              borderRadius: 8,
              fontSize: 14,
              fontWeight: 500,
              textDecoration: "none",
              color: pathname === link.href ? "var(--accent)" : "var(--text-secondary)",
              background: pathname === link.href ? "var(--accent-light)" : "transparent",
              transition: "all 0.2s ease",
            }}
          >
            {link.label}
          </Link>
        ))}
      </div>

      {/* Right side */}
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <ThemeToggle />

        {role !== "public" && (
          <>
            {/* Notifications */}
            <NotificationBell />

            {/* Avatar */}
            <div style={{
              width: 36,
              height: 36,
              borderRadius: "50%",
              background: "linear-gradient(135deg, var(--accent), #e8c98e)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              cursor: "pointer",
              fontSize: 14,
              fontWeight: 600,
              color: "white",
              position: "relative",
            }}
            title={user?.name || (role === "architect" ? "Architecte" : "Client")}
            onClick={logout}
            >
              {user?.name ? user.name[0].toUpperCase() : (role === "architect" ? "A" : "C")}
            </div>
          </>
        )}

        {role === "public" && (
          <div style={{ display: "flex", gap: 8 }}>
            <Link href="/auth/login" className="btn btn-secondary" style={{ fontSize: 13, padding: "8px 16px" }}>
              Connexion
            </Link>
            <Link href="/auth/register" className="btn btn-primary" style={{ fontSize: 13, padding: "8px 16px" }}>
              Commencer
            </Link>
          </div>
        )}
      </div>
    </nav>
  );
}
