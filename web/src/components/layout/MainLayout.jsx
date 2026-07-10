import Header from "./Header";
import Sidebar from "./Sidebar";

export default function MainLayout({ activePage, onNavigate, children }) {
  return (
    <main className="app-layout">
      <Sidebar activePage={activePage} onNavigate={onNavigate} />
      <section className="content-shell">
        <Header />
        {children}
      </section>
    </main>
  );
}
