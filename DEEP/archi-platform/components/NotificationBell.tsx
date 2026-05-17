"use client";
import { useState, useEffect, useRef } from "react";
import Link from "next/link";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const MOCK_NOTIFICATIONS: Notification[] = [
  {
    id: "1",
    title: "Nouveau message",
    message: "L'architecte a envoyé un nouveau plan",
    time: "Il y a 5 min",
    read: false,
    type: "message",
    link: "/client/messages",
  },
  {
    id: "2",
    title: "Document ajouté",
    message: "Plan V2 — Révisé est disponible",
    time: "Il y a 1h",
    read: false,
    type: "document",
    link: "/client/projects",
  },
  {
    id: "3",
    title: "Projet mis à jour",
    message: "Progression : 65% → 70%",
    time: "Il y a 2h",
    read: true,
    type: "project",
    link: "/client/projects",
  },
];

interface Notification {
  id: string;
  title: string;
  message: string;
  time: string;
  read: boolean;
  type: "message" | "project" | "document" | "system";
  link?: string;
}

export default function NotificationBell() {
  const [showDropdown, setShowDropdown] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Load notifications
  useEffect(() => {
    loadNotifications();
    
    // Poll for new notifications every 30 seconds
    const interval = setInterval(loadNotifications, 30000);
    return () => clearInterval(interval);
  }, []);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowDropdown(false);
      }
    };

    if (showDropdown) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [showDropdown]);

  const loadNotifications = () => {
    // Static mock data — defined outside to avoid re-render on each poll
    setNotifications(MOCK_NOTIFICATIONS);
  };

  const markAsRead = (id: string) => {
    setNotifications(prev =>
      prev.map(n => n.id === id ? { ...n, read: true } : n)
    );
  };

  const markAllAsRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
  };

  const unreadCount = notifications.filter(n => !n.read).length;

  const getIcon = (type: string) => {
    switch (type) {
      case "message": return "💬";
      case "project": return "📐";
      case "document": return "📄";
      case "system": return "⚙️";
      default: return "🔔";
    }
  };

  return (
    <div ref={dropdownRef} style={{ position: "relative" }}>
      <button
        onClick={() => setShowDropdown(!showDropdown)}
        className="btn btn-ghost"
        style={{
          padding: 8,
          borderRadius: "50%",
          width: 40,
          height: 40,
          justifyContent: "center",
          position: "relative",
        }}
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
          <path d="M13.73 21a2 2 0 0 1-3.46 0" />
        </svg>
        {unreadCount > 0 && (
          <span
            style={{
              position: "absolute",
              top: 6,
              right: 6,
              width: 8,
              height: 8,
              background: "var(--accent)",
              borderRadius: "50%",
              border: "2px solid var(--bg)",
            }}
          />
        )}
      </button>

      {/* Dropdown */}
      {showDropdown && (
        <div
          className="animate-scale-in"
          style={{
            position: "absolute",
            top: "calc(100% + 8px)",
            right: 0,
            width: 360,
            maxHeight: 480,
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: "var(--radius-lg)",
            boxShadow: "0 8px 24px rgba(0,0,0,0.15)",
            zIndex: 1000,
            display: "flex",
            flexDirection: "column",
          }}
        >
          {/* Header */}
          <div
            style={{
              padding: "16px 20px",
              borderBottom: "1px solid var(--border)",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <h3 style={{ fontSize: 15, fontWeight: 600, color: "var(--text-primary)" }}>
              Notifications {unreadCount > 0 && `(${unreadCount})`}
            </h3>
            {unreadCount > 0 && (
              <button
                onClick={markAllAsRead}
                style={{
                  fontSize: 12,
                  color: "var(--accent)",
                  background: "none",
                  border: "none",
                  cursor: "pointer",
                  padding: "4px 8px",
                }}
              >
                Tout marquer lu
              </button>
            )}
          </div>

          {/* Notifications list */}
          <div style={{ flex: 1, overflowY: "auto", maxHeight: 400 }}>
            {notifications.length === 0 ? (
              <div
                style={{
                  padding: 40,
                  textAlign: "center",
                  color: "var(--text-muted)",
                }}
              >
                <div style={{ fontSize: 32, marginBottom: 8 }}>🔔</div>
                <div style={{ fontSize: 14 }}>Aucune notification</div>
              </div>
            ) : (
              notifications.map((notif) => (
                <Link
                  key={notif.id}
                  href={notif.link || "#"}
                  onClick={() => {
                    markAsRead(notif.id);
                    setShowDropdown(false);
                  }}
                  style={{
                    display: "block",
                    padding: "12px 20px",
                    borderBottom: "1px solid var(--border)",
                    background: notif.read ? "transparent" : "var(--accent-light)",
                    textDecoration: "none",
                    transition: "background 0.2s",
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = "var(--bg-secondary)";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = notif.read
                      ? "transparent"
                      : "var(--accent-light)";
                  }}
                >
                  <div style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
                    <div style={{ fontSize: 20, flexShrink: 0 }}>
                      {getIcon(notif.type)}
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div
                        style={{
                          fontSize: 13,
                          fontWeight: notif.read ? 400 : 600,
                          color: "var(--text-primary)",
                          marginBottom: 2,
                        }}
                      >
                        {notif.title}
                      </div>
                      <div
                        style={{
                          fontSize: 12,
                          color: "var(--text-secondary)",
                          marginBottom: 4,
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
                        }}
                      >
                        {notif.message}
                      </div>
                      <div style={{ fontSize: 11, color: "var(--text-muted)" }}>
                        {notif.time}
                      </div>
                    </div>
                    {!notif.read && (
                      <div
                        style={{
                          width: 8,
                          height: 8,
                          borderRadius: "50%",
                          background: "var(--accent)",
                          flexShrink: 0,
                          marginTop: 4,
                        }}
                      />
                    )}
                  </div>
                </Link>
              ))
            )}
          </div>

          {/* Footer */}
          {notifications.length > 0 && (
            <div
              style={{
                padding: "12px 20px",
                borderTop: "1px solid var(--border)",
                textAlign: "center",
              }}
            >
              <Link
                href="/client/notifications"
                onClick={() => setShowDropdown(false)}
                style={{
                  fontSize: 13,
                  color: "var(--accent)",
                  textDecoration: "none",
                  fontWeight: 500,
                }}
              >
                Voir toutes les notifications →
              </Link>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
