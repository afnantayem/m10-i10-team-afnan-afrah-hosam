import Link from "next/link";

export default function Home() {
  return (
    <main>
      <h1>M10 Recipe Service — Demo</h1>
      <ul>
        <li><Link href="/extract">Extract entities</Link></li>
        <li><Link href="/kg">Query the recipe knowledge graph</Link></li>
        <li><Link href="/rag">Ask a recipe question (RAG)</Link></li>
      </ul>
    </main>
  );
}
