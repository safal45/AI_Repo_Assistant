"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import * as api from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (mode === "register") {
        await api.register(name, email, password);
      }

      await api.login(email, password);
      router.push("/repos");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center p-4">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-sm space-y-4 border p-6 rounded"
      >
        <h1 className="text-xl font-bold">
          {mode === "login" ? "Log in" : "Register"}
        </h1>

        {mode === "register" && (
          <input
            type="text"
            placeholder="Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            className="w-full border p-2 rounded"
          />
        )}

        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          className="w-full border p-2 rounded"
        />

        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          className="w-full border p-2 rounded"
        />

        {error && <p className="text-sm text-red-600">{error}</p>}

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded bg-black p-2 text-white disabled:opacity-50"
        >
          {loading ? "..." : mode === "login" ? "Log in" : "Register"}
        </button>

        <button
          type="button"
          onClick={() => {
            setError(null);
            setMode(mode === "login" ? "register" : "login");
          }}
          className="w-full text-sm underline"
        >
          {mode === "login"
            ? "Need an account? Register"
            : "Already have an account? Log in"}
        </button>
      </form>
    </main>
  );
}
