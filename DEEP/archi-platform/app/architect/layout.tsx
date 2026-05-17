import Navbar from "@/components/Navbar";
import Sidebar from "@/components/Sidebar";

export default function ArchitectLayout({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ minHeight: "100vh", background: "var(--bg)" }}>
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
    </div>
  );
}
