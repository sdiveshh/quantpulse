"use client";

import { useEffect, useRef, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const SUGGESTIONS = [
  "Which stock was most volatile last week?",
  "Why is Tesla in the news lately?",
  "What was the highest NVDA price in the latest data?",
];

export default function Chat() {
  const [messages, setMessages] = useState([
    { role: "assistant", text: "Ask me about prices, volatility, or the news behind a stock." },
  ]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy]);

  async function send(q) {
    const question = (q ?? input).trim();
    if (question.length < 3 || busy) return;
    setInput("");
    setBusy(true);
    setMessages((m) => [...m, { role: "user", text: question }]);
    try {
      const r = await fetch(`${API}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      if (!r.ok) throw new Error(String(r.status));
      const d = await r.json();
      setMessages((m) => [
        ...m,
        { role: "assistant", text: d.answer, route: d.route, sql: d.sql },
      ]);
    } catch {
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          text: "Sorry, I could not get an answer. The AI service may be busy, so try again in a minute.",
          error: true,
        },
      ]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex h-[38rem] flex-col rounded-xl border border-slate-800 bg-slate-900">
      <div className="border-b border-slate-800 px-4 py-3 font-semibold">AI assistant</div>

      <div className="flex-1 space-y-3 overflow-y-auto p-4">
        {messages.map((m, i) => (
          <div key={i} className={m.role === "user" ? "text-right" : "text-left"}>
            <div
              className={`inline-block max-w-[92%] whitespace-pre-wrap rounded-lg px-3 py-2 text-sm ${
                m.role === "user"
                  ? "bg-emerald-600 text-white"
                  : m.error
                  ? "bg-rose-900/60 text-rose-100"
                  : "bg-slate-800 text-slate-100"
              }`}
            >
              {m.text.replace(/\*\*/g, "")}
            </div>
            {m.route && (
              <div className="mt-1 text-xs text-slate-500">
                route: {m.route}
                {m.sql && (
                  <details className="mt-1">
                    <summary className="cursor-pointer">show SQL</summary>
                    <code className="mt-1 block whitespace-pre-wrap break-words rounded bg-slate-950 p-2 text-left text-slate-300">
                      {m.sql}
                    </code>
                  </details>
                )}
              </div>
            )}
          </div>
        ))}
        {busy && <div className="text-sm text-slate-400">Thinking... this can take up to 20 seconds</div>}
        <div ref={endRef} />
      </div>

      <div className="flex flex-wrap gap-2 px-4 pb-2">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            onClick={() => send(s)}
            disabled={busy}
            className="rounded-full border border-slate-700 px-3 py-1 text-xs text-slate-300 hover:border-emerald-400 disabled:opacity-50"
          >
            {s}
          </button>
        ))}
      </div>

      <div className="flex gap-2 border-t border-slate-800 p-3">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          maxLength={500}
          placeholder="Ask about a stock..."
          className="flex-1 rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-emerald-400"
        />
        <button
          onClick={() => send()}
          disabled={busy || input.trim().length < 3}
          className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-500 disabled:opacity-50"
        >
          Send
        </button>
      </div>
    </div>
  );
}