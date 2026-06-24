import { useState } from "react";
import type { RAGResponse } from "../lib/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function RagPage() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<RAGResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const r = await fetch(`${API_URL}/rag/answer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, k: 4 }),
      });
      if (r.status === 422) {
        setError("Question shape rejected by validation.");
        return;
      }
      if (r.status === 503) {
        setError("Backend not ready. Try again in a moment.");
        return;
      }
      if (!r.ok) {
        setError(`Unexpected status: ${r.status}`);
        return;
      }
      setResult((await r.json()) as RAGResponse);
    } catch (e) {
      setError("Network error reaching the backend.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main>
      <h1>RAG — Cited Answer</h1>
      <input
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="Ask a recipe question..."
        size={60}
      />
      <button onClick={submit} disabled={loading || !question}>
        {loading ? "Asking..." : "Ask"}
      </button>
      {error && (
        <p role="alert" data-testid="error">
          {error}
        </p>
      )}
      {result && (
        <article>
          <p data-testid="rag-answer">{result.answer}</p>
          <ul>
            {result.citations.map((c) => (
              <li key={c.chunk_id}>
                [
                <span data-testid="citation-marker">{c.chunk_id}</span>
                ] score: {c.score.toFixed(3)}
              </li>
            ))}
          </ul>
          <p>Confidence: {result.confidence.toFixed(2)}</p>
        </article>
      )}
    </main>
  );
}
