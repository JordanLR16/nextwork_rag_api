import { useState } from "react";
import MainLayout from "./components/layout/MainLayout";
import AskPage from "./pages/AskPage";
import HomePage from "./pages/HomePage";
import PantryPage from "./pages/PantryPage";
import RecipeBookPage from "./pages/RecipeBookPage";
import GlobePage from "./pages/GlobePage";
import { SignInPanel, useAuth } from "./auth/AuthContext";

function renderPage(activePage) {
  switch (activePage) {
    case "recipes":
      return <RecipeBookPage />;
    case "pantry":
      return <PantryPage />;
    case "ask":
      return <AskPage />;
    case "globe":
      return <GlobePage />;
    case "home":
    default:
      return <HomePage />;
  }
}

export default function App() {
  const [activePage, setActivePage] = useState("home");
  const { user, loading } = useAuth();

  return (
    <MainLayout activePage={activePage} onNavigate={setActivePage}>
      <div key={user?.profile.sub || "signed-out"}>
        {activePage === "globe" || (user && !loading) ? renderPage(activePage) : <SignInPanel />}
      </div>
    </MainLayout>
  );
}
