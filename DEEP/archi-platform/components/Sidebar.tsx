"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

interface SidebarItem {
  href: string;
  label: string;
  icon: React.ReactNode;
  badge?: string | number;
}

interface SidebarProps {
  role: "architect" | "client";
}

const ArchitectItems: SidebarItem[] = [
  {
    href: "/architect/dashboard",
    label: "Dashboard",
    icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>,
  },
  {
    href: "/architect/upload",
    label: "Analyser Plan",
    icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>,
  },
  {
    href: "/architect/projects",
    label: "Projets",
    icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>,
    badge: 4,
  },
  {
    href: "/architect/clients",
    label: "Clients",
    icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>,
  },
  {
    href: "/architect/visualize",
    label: "Visualisation 3D",
    icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>,
  },
  {
    href: "/architect/messages",
    label: "Messages",
    icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>,
    badge: 2,
  },
  {
    href: "/architect/analytics",
    label: "Analytiques",
    icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>,
  },
];

const ClientItems: SidebarItem[] = [
  {
    href: "/client/dashboard",
    label: "Accueil",
    icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>,
  },
  {
    href: "/client/brief",
    label: "Mon Brief",
    icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>,
  },
  {
    href: "/client/projects",
    label: "Mes Projets",
    icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="3 9 12 2 21 9 21 20 3 20 3 9"/><rect x="9" y="14" width="6" height="6"/></svg>,
  },
  {
    href: "/client/sketches",
    label: "Esquisses IA",
    icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>,
    badge: "Nouveau",
  },
  {
    href: "/client/vqa",
    label: "Questions sur Plan",
    icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>,
  },
  {
    href: "/client/messages",
    label: "Messages",
    icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>,
    badge: 1,
  },
];

export default function Sidebar({ role }: SidebarProps) {
  const pathname = usePathname();
  const items = role === "architect" ? ArchitectItems : ClientItems;

  return (
    <aside style={{
      position: "fixed",
      top: 64,
      left: 0,
      bottom: 0,
      width: 220,
      background: "var(--surface)",
      borderRight: "1px solid var(--border)",
      padding: "16px 12px",
      display: "flex",
      flexDirection: "column",
      gap: 4,
      overflowY: "auto",
      zIndex: 50,
    }}>
      {/* Role badge */}
      <div style={{
        padding: "8px 12px",
        marginBottom: 8,
        borderRadius: 8,
        background: "var(--accent-light)",
        display: "flex",
        alignItems: "center",
        gap: 8,
      }}>
        <div style={{
          width: 8,
          height: 8,
          borderRadius: "50%",
          background: "var(--accent)",
        }} />
        <span style={{ fontSize: 12, fontWeight: 600, color: "var(--accent-dark)", textTransform: "uppercase", letterSpacing: "0.5px" }}>
          {role === "architect" ? "Architecte" : "Client"}
        </span>
      </div>

      {items.map((item) => {
        const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
        return (
          <Link
            key={item.href}
            href={item.href}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              padding: "10px 12px",
              borderRadius: 10,
              textDecoration: "none",
              color: isActive ? "var(--accent)" : "var(--text-secondary)",
              background: isActive ? "var(--accent-light)" : "transparent",
              fontWeight: isActive ? 600 : 400,
              fontSize: 14,
              transition: "all 0.15s ease",
              position: "relative",
            }}
          >
            <span style={{ opacity: isActive ? 1 : 0.7 }}>{item.icon}</span>
            <span style={{ flex: 1 }}>{item.label}</span>
            {item.badge && (
              <span style={{
                background: typeof item.badge === "string" ? "var(--accent)" : "var(--accent)",
                color: "white",
                fontSize: 10,
                fontWeight: 700,
                padding: "2px 6px",
                borderRadius: 999,
                minWidth: 18,
                textAlign: "center",
              }}>
                {item.badge}
              </span>
            )}
          </Link>
        );
      })}

      {/* Bottom: Settings & Logout */}
      <div style={{ marginTop: "auto", borderTop: "1px solid var(--border)", paddingTop: 12, display: "flex", flexDirection: "column", gap: 4 }}>
        <Link href="/settings" style={{
          display: "flex", alignItems: "center", gap: 10, padding: "10px 12px",
          borderRadius: 10, textDecoration: "none", color: "var(--text-secondary)", fontSize: 14,
          transition: "all 0.15s ease",
        }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="3"/>
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
          </svg>
          Paramètres
        </Link>
        <Link href="/auth/login" style={{
          display: "flex", alignItems: "center", gap: 10, padding: "10px 12px",
          borderRadius: 10, textDecoration: "none", color: "var(--danger)", fontSize: 14,
          transition: "all 0.15s ease",
        }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
            <polyline points="16 17 21 12 16 7"/>
            <line x1="21" y1="12" x2="9" y2="12"/>
          </svg>
          Déconnexion
        </Link>
      </div>
    </aside>
  );
}
