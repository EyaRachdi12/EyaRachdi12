"use client";
import { useState, useEffect } from "react";
import Link from "next/link";

interface Notification {
  id: string;
  title: string;
  message: string;
  time: string;
  date: string;
  read: boolean;
  type: "message" | "project" | "document" | "system";
  link?: string;
}

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [filter, setFilter] = useState<"all" | "unread">("all");

  useEffect(() => {
    loadNotifications();
  }, []);

  const loadNotifications = () => {
    // Mock data - in production, fetch from API
    const mockNotifications: Notification[] = [
      {
        id: "1",
        title: "Nouveau message",
        message: "L'architecte a envoyé un nouveau plan révisé avec vos modifications",
        time: "Il y a 5 min",
        date: "10 Mai 2026",
        read: false,
        type: "message",
        link: "/client/messages",
      },
      {
        id: "2",
        title: "Document ajouté",
        message: "Plan V2 — Révisé est maintenant disponible au téléchargement",
        time: "Il y a 1h",
        date: "10 Mai 2026",
        read: false,
        type: "document",
        link: "/client/projects",
      },
      {
        id: "3",
        title: "Projet mis à jour",
        message: "La progression de votre projet est passée de 65% à 70%",
        time: "Il y a 2h",
        date: "10 Mai 2026",
        read: true,
        type: "project",
        link: "/client/projects",
      },
      {
        id: "4",
        title: "Esquisses IA générées",
        message: "Vos esquisses en style Contemporain sont prêtes",
        time: "Il y a 5h",
        date: "10 Mai 2026",
        read: true,
        type: "document",
        link: "/client/sketches",
      },
      {
        id: "5",
        title: "Nouveau message",
        message: "L'architecte a répondu à votre question sur la terrasse",
        time: "Hier",
        date: "9 Mai 2026",
        read: true,
        type: "message",
        link: "/client/messages",
      },
      {
        id: "6",
        title: "Brief validé",
        message: "Votre brief client a été validé par l'architecte",
        time: "Il y a 2 jours",
        date: "8 Mai 2026",
        read: true,
        type: "system",
        link: "/client/brief",
      },
    ];

    setNotifications(mockNotifications);
  };

  const markAsRead = (id: string) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read: true } : n))
    );
  };

  const markAllAsRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  };

  const deleteNotification = (id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  };

  const getIcon = (type: string) => {
    switch (type) {
      case "message":
        return "💬";
      case "project":
        return "📐";
      case "document":
        return "📄";
      case "system":
        return "⚙️";
      default:
        return "🔔";
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case "message":
        return "#56b4d3";
      case "project":
        return "var(--accent)";
      case "document":
        return "#6fcf97";
      case "system":
        return "#9c9590";
      default:
        return "var(--text-muted)";
    }
  };

  const filteredNotifications =
    filter === "unread"
      ? notifications.filter((n) => !n.read)
      : notifications;

  const unreadCount = notifications.filter((n) => !n.read).length;

  return (
    <div style={{ maxWidth: 800 }}>
      <div className="animate-fade-in" style={{ marginBottom: 32 }}>
        <h1
          style={{
            fontFamily: "'Playfair Display', serif",
            fontSize: 28,
            fontWeight: 700,
            color: "var(--text-primary)",
            marginBottom: 6,
          }}
        >
          Notifications
        </h1>
        <p style={{ color: "var(--text-secondary)", fontSize: 15 }}>
          {unreadCount > 0
            ? `${unreadCount} notification${unreadCount > 1 ? "s" : ""} non lue${unreadCount > 1 ? "s" : ""}`
            : "Toutes les notifications sont lues"}
        </p>
      </div>

      {/* Filters and actions */}
      <div
        className="animate-fade-in delay-100"
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 20,
          flexWrap: "wrap",
          gap: 12,
        }}
      >
        <div style={{ display: "flex", gap: 8 }}>
          <button
            onClick={() => setFilter("all")}
            className={filter === "all" ? "btn btn-primary" : "btn btn-secondary"}
            style={{ fontSize: 13, padding: "8px 16px" }}
          >
            Toutes ({notifications.length})
          </button>
          <button
            onClick={() => setFilter("unread")}
            className={filter === "unread" ? "btn btn-primary" : "btn btn-secondary"}
            style={{ fontSize: 13, padding: "8px 16px" }}
          >
            Non lues ({unreadCount})
          </button>
        </div>

        {unreadCount > 0 && (
          <button
            onClick={markAllAsRead}
            className="btn btn-ghost"
            style={{ fontSize: 13 }}
          >
            ✓ Tout marquer comme lu
          </button>
        )}
      </div>

      {/* Notifications list */}
      <div className="animate-fade-in delay-200">
        {filteredNotifications.length === 0 ? (
          <div
            style={{
              background: "var(--surface)",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius-lg)",
              padding: 60,
              textAlign: "center",
            }}
          >
            <div style={{ fontSize: 48, marginBottom: 16 }}>🔔</div>
            <div
              style={{
                fontSize: 16,
                fontWeight: 600,
                color: "var(--text-primary)",
                marginBottom: 8,
              }}
            >
              {filter === "unread"
                ? "Aucune notification non lue"
                : "Aucune notification"}
            </div>
            <div style={{ fontSize: 14, color: "var(--text-muted)" }}>
              {filter === "unread"
                ? "Toutes vos notifications sont à jour"
                : "Vous n'avez pas encore de notifications"}
            </div>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {filteredNotifications.map((notif) => (
              <div
                key={notif.id}
                className="card-hover"
                style={{
                  background: notif.read
                    ? "var(--surface)"
                    : "var(--accent-light)",
                  border: "1px solid var(--border)",
                  borderRadius: "var(--radius-lg)",
                  padding: 20,
                  display: "flex",
                  gap: 16,
                  alignItems: "flex-start",
                }}
              >
                {/* Icon */}
                <div
                  style={{
                    width: 48,
                    height: 48,
                    borderRadius: "50%",
                    background: `${getTypeColor(notif.type)}18`,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: 24,
                    flexShrink: 0,
                  }}
                >
                  {getIcon(notif.type)}
                </div>

                {/* Content */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "flex-start",
                      marginBottom: 6,
                      gap: 12,
                    }}
                  >
                    <h3
                      style={{
                        fontSize: 15,
                        fontWeight: notif.read ? 500 : 600,
                        color: "var(--text-primary)",
                      }}
                    >
                      {notif.title}
                    </h3>
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

                  <p
                    style={{
                      fontSize: 14,
                      color: "var(--text-secondary)",
                      marginBottom: 8,
                      lineHeight: 1.5,
                    }}
                  >
                    {notif.message}
                  </p>

                  <div
                    style={{
                      fontSize: 12,
                      color: "var(--text-muted)",
                      marginBottom: 12,
                    }}
                  >
                    {notif.time} · {notif.date}
                  </div>

                  {/* Actions */}
                  <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                    {notif.link && (
                      <Link
                        href={notif.link}
                        onClick={() => markAsRead(notif.id)}
                        className="btn btn-primary"
                        style={{ fontSize: 12, padding: "6px 12px" }}
                      >
                        Voir →
                      </Link>
                    )}
                    {!notif.read && (
                      <button
                        onClick={() => markAsRead(notif.id)}
                        className="btn btn-ghost"
                        style={{ fontSize: 12, padding: "6px 12px" }}
                      >
                        ✓ Marquer comme lu
                      </button>
                    )}
                    <button
                      onClick={() => deleteNotification(notif.id)}
                      className="btn btn-ghost"
                      style={{
                        fontSize: 12,
                        padding: "6px 12px",
                        color: "#eb5757",
                      }}
                    >
                      🗑 Supprimer
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
