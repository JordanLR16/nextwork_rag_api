import { useState } from "react";
import MainLayout from "./components/layout/MainLayout";
import AskPage from "./pages/AskPage";
import HomePage from "./pages/HomePage";
import PantryPage from "./pages/PantryPage";
import RecipeBookPage from "./pages/RecipeBookPage";

function renderPage(activePage) {
  switch (activePage) {
    case "recipes":
      return <RecipeBookPage />;
    case "pantry":
      return <PantryPage />;
    case "ask":
      return <AskPage />;
    case "home":
    default:
      return <HomePage />;
  }
}

export default function App() {
  const [activePage, setActivePage] = useState("home");

  return (
    <MainLayout activePage={activePage} onNavigate={setActivePage}>
      {renderPage(activePage)}
    </MainLayout>
  );
}
