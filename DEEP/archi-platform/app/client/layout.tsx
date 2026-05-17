import Navbar from "@/components/Navbar";
import Sidebar from "@/components/Sidebar";

export default function ClientLayout({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ minHeight: "100vh", background: "var(--bg)" }}>
      <Navbar role="client" />
      <Sidebar role="client" />
      <main style={{
        marginLeft: 220,
        marginTop: 64,
        padding: "32px",
        minHeight: "calc(100vh - 64px)",
      }}>
        {children}
      </main>
    </div>
  );
}
