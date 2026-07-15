"use client";

import { useEffect, useState, type FormEvent } from "react";
import { useParams, useRouter } from "next/navigation";
import * as api from "@/lib/api";
import { askStream, type AgentStreamEvent } from "@/lib/api";

type ChatEvent = Exclude<AgentStreamEvent, { type: "answer" }>;

export default function ChatPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const repoId = params.id;

  const [question, setQuestion] = useState("");
  const [events, setEvents] = useState<ChatEvent[]>([]);
  const [answer, setAnswer] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [sending, setSending] = useState(false);

  useEffect(() => {
    if (!api.getToken()) {
      router.push("/login");
    }
  }, [router]);

  async function handleSend(e: FormEvent) {
    e.preventDefault();
    if (!question.trim() || sending) return;

    setEvents([]);
    setAnswer("");
    setError(null);
    setSending(true);
    try {
      await askStream(repoId, question, (event) => {
        if (event.type === "answer") {
          setAnswer(event.content);
        } else {
          setEvents((prev) => [...prev, event]);
        }
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to get a response");
    } finally {
      setSending(false);
    }
  }

  return (
    <main className="mx-auto max-w-2xl space-y-4 p-6">
      <h1 className="text-xl font-bold">Chat — {repoId}</h1>

      <div className="min-h-[300px] space-y-1 rounded border p-4">
        {events.length === 0 && !answer && (
          <p className="text-sm text-gray-500">Events will appear here.</p>
        )}
        {events.map((e, i) => (
          <div key={i}>
            {e.type === "thinking" && `Thinking...`}
            {e.type === "tool_call" && `${e.tool}(${JSON.stringify(e.arguments)})`}
            {e.type === "tool_result" && `${e.success ? "" : ""} ${e.tool}`}
            {e.type === "error" && ` ${e.message}`}
          </div>
        ))}
        {answer && <div className="answer">{answer}</div>}
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <form onSubmit={handleSend} className="flex gap-2">
        <input
          type="text"
          placeholder="Ask a question about this repo..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          className="flex-1 rounded border p-2"
        />
        <button
          type="submit"
          disabled={sending}
          className="rounded bg-black px-4 py-2 text-white disabled:opacity-50"
        >
          {sending ? "Asking..." : "Send"}
        </button>
      </form>
    </main>
  );
}
