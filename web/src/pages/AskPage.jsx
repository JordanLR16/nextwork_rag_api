import { useState } from "react";
import { askKnowledgeBase } from "../api/recipes";

export default function AskPage() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const onAsk = async (event) => {
    event.preventDefault();
    setError("");
    setAnswer("");

    if (!question.trim()) {
      setError("Please enter a question.");
      return;
    }

    try {
      setLoading(true);
      const data = await askKnowledgeBase(question);
      setAnswer(data.answer || "No answer returned.");
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="panel">
      <h1>Ask</h1>
      <p className="subtitle">Ask questions from your recipe knowledge base.</p>

      <form onSubmit={onAsk} className="stack">
        <label htmlFor="question">Question</label>
        <textarea
          id="question"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          rows={4}
          placeholder="What can I make with spinach and rice?"
        />
        <button type="submit" disabled={loading}>
          {loading ? "Asking..." : "Ask"}
        </button>
      </form>

      {error && <p className="error">{error}</p>}
      {answer && (
        <article className="answer-box">
          <h2>Answer</h2>
          <p>{answer}</p>
        </article>
      )}
    </section>
  );
}
