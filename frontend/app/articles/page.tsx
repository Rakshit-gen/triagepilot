"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { fetchArticles, type KnowledgeArticle } from "@/lib/api";

export default function Articles() {
  const [articles, setArticles] = useState<KnowledgeArticle[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchArticles().then(setArticles).catch((err) => setError(err.message));
  }, []);

  return (
    <main className="mx-auto max-w-3xl px-5 py-10">
      <Link href="/" className="text-sm underline">
        ← Back to queue
      </Link>
      <h1 className="mt-4 mb-1 text-2xl font-semibold">Knowledge base</h1>
      <p className="mb-8 text-zinc-500">
        Articles the agent searches before drafting a reply.
      </p>

      {error && <p className="text-red-600 dark:text-red-400">{error}</p>}

      <div className="space-y-4">
        {articles.map((a) => (
          <article key={a.id} className="rounded border border-zinc-200 p-4 dark:border-zinc-800">
            <h2 className="font-medium">{a.title}</h2>
            <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">{a.body}</p>
            {a.tags && <p className="mt-2 text-xs text-zinc-500">tags: {a.tags}</p>}
          </article>
        ))}
        {articles.length === 0 && <p className="text-zinc-500">No articles yet.</p>}
      </div>
    </main>
  );
}
