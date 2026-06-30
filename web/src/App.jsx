import { useState } from "react";
import Header from './components/Header';


const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const ADD_API_KEY = import.meta.env.VITE_ADD_API_KEY || "";

async function postJson(path, body, extraHeaders = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...extraHeaders },
    body: JSON.stringify(body),
  });

  let data = {};
  try {
    data = await response.json();
  } catch {
    data = {};
  }

  if (!response.ok) {
    const message = data?.detail || "Request failed";
    throw new Error(message);
  }

  return data;
}

export default function App() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [queryLoading, setQueryLoading] = useState(false);
  const [queryError, setQueryError] = useState("");

  const [knowledgeText, setKnowledgeText] = useState("");
  const [addLoading, setAddLoading] = useState(false);
  const [addStatus, setAddStatus] = useState("");

  const onAsk = async (event) => {
    event.preventDefault();
    setQueryError("");
    setAnswer("");

    if (!question.trim()) {
      setQueryError("Please enter a question.");
      return;
    }

    try {
      setQueryLoading(true);
      const data = await postJson("/query", { q: question, n_results: 3 });
      setAnswer(data.answer || "No answer returned.");
    } catch (error) {
      setQueryError(error.message);
    } finally {
      setQueryLoading(false);
    }
  };

  const onAddKnowledge = async (event) => {
    event.preventDefault();
    setAddStatus("");

    if (!knowledgeText.trim()) {
      setAddStatus("Please enter text to add.");
      return;
    }

    try {
      setAddLoading(true);
      const extraHeaders = ADD_API_KEY ? { "X-API-Key": ADD_API_KEY } : {};
      const data = await postJson("/add", { text: knowledgeText }, extraHeaders);
      setAddStatus(`Added successfully. id: ${data.id}`);
      setKnowledgeText("");
    } catch (error) {
      setAddStatus(`Failed to add content: ${error.message}`);
    } finally {
      setAddLoading(false);
    }
  };

  return (
    <main className="app-shell">
      <Header />
      <section className="panel">
        <h1>RAG Assistant</h1>
        <p className="subtitle">Ask questions from your Chroma knowledge base.</p>

        <form onSubmit={onAsk} className="stack">
          <label htmlFor="question">Question</label>
          <textarea
            id="question"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            rows={4}
            placeholder="What do the docs say about..."
          />
          <button type="submit" disabled={queryLoading}>
            {queryLoading ? "Asking..." : "Ask"}
          </button>
        </form>

        {queryError && <p className="error">{queryError}</p>}
        {answer && (
          <article className="answer-box">
            <h2>Answer</h2>
            <p>{answer}</p>
          </article>
        )}
      </section>

      <section className="panel">
        <h2>Add Knowledge</h2>
        <form onSubmit={onAddKnowledge} className="stack">
          <label htmlFor="knowledge">Text</label>
          <textarea
            id="knowledge"
            value={knowledgeText}
            onChange={(event) => setKnowledgeText(event.target.value)}
            rows={8}
            placeholder="Paste text to add to the vector store"
          />
          <button type="submit" disabled={addLoading}>
            {addLoading ? "Adding..." : "Add"}
          </button>
        </form>
        {addStatus && <p className="status">{addStatus}</p>}
      </section>
    </main>
  );
}
