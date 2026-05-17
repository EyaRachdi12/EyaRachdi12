import Navbar from "@/components/Navbar";
import Sidebar from "@/components/Sidebar";

export default function SettingsLayout({ children }: { children: React.ReactNode }) {
  // Detect role from localStorage is not possible server-side
  // Use a client wrapper instead
  return (
    <div style={{ minHeight: "100vh", background: "var(--bg)" }}>
      <SettingsLayoutClient>{children}</SettingsLayoutClient>
    </div>
  );
}

function SettingsLayoutClient({ children }: { children: React.ReactNode }) {
  return (
    <>
      <Navbar role="architect" />
      <Sidebar role="architect" />
      <main style={{
        marginLeft: 220,
        marginTop: 64,
        padding: "32px",
        minHeight: "calc(100vh - 64px)",
      }}>
        {children}
      </main>
    </>
  );
}
