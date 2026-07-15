"use client";

import { useEffect, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import * as api from "@/lib/api";

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-yellow-200 text-yellow-800",
  ready: "bg-blue-200 text-blue-800",
  indexed: "bg-green-200 text-green-800",
  embedding: "bg-yellow-200 text-yellow-800",
  embedded: "bg-emerald-200 text-emerald-800",
  embedding_failed: "bg-red-200 text-red-800",
  failed: "bg-red-200 text-red-800",
};

export default function ReposPage() {
  const router = useRouter();
  const [repos, setRepos] = useState<api.Repository[]>([]);
  const [githubUrl, setGithubUrl] = useState("");
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);
  const [busyRepoId, setBusyRepoId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function loadRepos() {
    try {
      const data = await api.getRepositories();
      setRepos(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load repos");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!api.getToken()) {
      router.push("/login");
      return;
    }

    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadRepos();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleAdd(e: FormEvent) {
    e.preventDefault();
    if (!githubUrl.trim()) return;

    setAdding(true);
    setError(null);

    try {
      await api.addRepository(githubUrl.trim());
      setGithubUrl("");
      await loadRepos();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add repo");
    } finally {
      setAdding(false);
    }
  }

  async function handleIndex(repoId: string) {
    setBusyRepoId(repoId);
    setError(null);

    try {
      await api.indexRepository(repoId);
      await loadRepos();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start indexing");
    } finally {
      setBusyRepoId(null);
    }
  }

  async function handleEmbed(repoId: string) {
    setBusyRepoId(repoId);
    setError(null);

    try {
      await api.embedRepository(repoId);
      await loadRepos();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to embed repo");
    } finally {
      setBusyRepoId(null);
    }
  }
  

  if (loading) {
    return <main className="p-6">Loading...</main>;
  }

  return (
    <main className="mx-auto max-w-2xl space-y-6 p-6">
      <h1 className="text-xl font-bold">Your Repositories</h1>

      <form onSubmit={handleAdd} className="flex gap-2">
        <input
          type="text"
          placeholder="https://github.com/owner/repo"
          value={githubUrl}
          onChange={(e) => setGithubUrl(e.target.value)}
          className="flex-1 border p-2 rounded"
        />
        <button
          type="submit"
          disabled={adding}
          className="rounded bg-black px-4 py-2 text-white disabled:opacity-50"
        >
          {adding ? "Adding..." : "Add"}
        </button>
      </form>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <ul className="space-y-2">
        {repos.map((repo) => (
          <li key={repo.id} className="flex items-center gap-2 border p-3 rounded">
            <Link href={`/repos/${repo.id}/chat`} className="flex-1 hover:underline">
              {repo.name}
            </Link>

            <span
              className={`rounded px-2 py-1 text-xs ${
                STATUS_COLORS[repo.status] ?? "bg-gray-200 text-gray-800"
              }`}
            >
              {repo.status}
            </span>

            <button
              type="button"
              onClick={() => handleIndex(repo.id)}
              disabled={busyRepoId === repo.id}
              className="rounded border px-2 py-1 text-xs disabled:opacity-50"
            >
              Index
            </button>

            <button
              type="button"
              onClick={() => handleEmbed(repo.id)}
              disabled={busyRepoId === repo.id}
              className="rounded border px-2 py-1 text-xs disabled:opacity-50"
            >
              Embed
            </button>
          </li>
        ))}

        {repos.length === 0 && (
          <p className="text-sm text-gray-500">No repositories yet.</p>
        )}
      </ul>
    </main>
  );
}
