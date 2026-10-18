"use client";

import { useEffect, useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import Chat from "./Chat";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function get(path) {
  const r = await fetch(`${API}${path}`);
  if (!r.ok) throw new Error(String(r.status));
  return r.json();
}

const fmtTime = (t) =>
  new Date(t).toLocaleString("en-IN", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

export default function Dashboard() {
  const [summary, setSummary] = useState([]);
  const [ticker, setTicker] = useState("NVDA");
  const [series, setSeries] = useState([]);
  const [news, setNews] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    get("/api/summary")
      .then(setSummary)
      .catch(() => setError("Could not load data. Is the backend running on port 8000?"));
  }, []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    Promise.all([
      get(`/api/prices/${ticker}?limit=130`),
      get(`/api/features/${ticker}?limit=130`),
      get(`/api/news?ticker=${ticker}&limit=8`),
    ])
      .then(([p, f, n]) => {
        if (cancelled) return;
        const sma = new Map(f.map((x) => [x.timestamp, x.sma_20]));
        setSeries(
          p.candles.map((c, i) => ({
            t: c.timestamp,
            close: c.close,
            sma: i >= 19 ? sma.get(c.timestamp) ?? null : null,
          }))
        );
        setNews(n);
        setError("");
      })
      .catch(() => {
        if (!cancelled) setError("Could not load data. Is the backend running on port 8000?");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [ticker]);

  const asOf = summary[0]?.as_of;

  return (
    <main className="mx-auto max-w-7xl space-y-6 p-4 md:p-8">
      <header className="flex flex-wrap items-end justify-between gap-2">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">QuantPulse</h1>
          <p className="text-sm text-slate-400">Market monitor and AI assistant</p>
        </div>
        {asOf && (
          <p className="text-xs text-slate-500">
            Latest data: {fmtTime(asOf)} (15-minute bars, not live)
          </p>
        )}
      </header>

      {error && (
        <div className="rounded-lg border border-rose-800 bg-rose-950/60 p-3 text-sm text-rose-200">
          {error}
        </div>
      )}

      <section className="grid grid-cols-2 gap-3 md:grid-cols-5">
        {summary.map((s) => {
          const up = (s.change_pct ?? 0) >= 0;
          return (
            <button
              key={s.ticker}
              onClick={() => setTicker(s.ticker)}
              className={`rounded-xl border p-4 text-left transition ${
                ticker === s.ticker
                  ? "border-emerald-400 bg-slate-800"
                  : "border-slate-800 bg-slate-900 hover:border-slate-600"
              }`}
            >
              <div className="text-sm text-slate-400">{s.ticker}</div>
              <div className="text-xl font-semibold">${Number(s.last_price).toFixed(2)}</div>
              <div className={`text-sm ${up ? "text-emerald-400" : "text-rose-400"}`}>
                {s.change_pct == null ? "-" : `${up ? "+" : ""}${Number(s.change_pct).toFixed(2)}%`}
              </div>
            </button>
          );
        })}
      </section>

      <section className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
            <div className="mb-2 flex items-center justify-between">
              <h2 className="font-semibold">{ticker} price</h2>
              <div className="flex gap-4 text-xs text-slate-400">
                <span className="text-emerald-400">close</span>
                <span className="text-amber-400">20-bar average</span>
              </div>
            </div>
            <div className="h-80">
              {loading ? (
                <div className="flex h-full items-center justify-center text-slate-500">Loading...</div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={series} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
                    <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" />
                    <XAxis
                      dataKey="t"
                      tickFormatter={fmtTime}
                      minTickGap={60}
                      stroke="#64748b"
                      fontSize={11}
                    />
                    <YAxis domain={["auto", "auto"]} stroke="#64748b" fontSize={11} width={55} />
                    <Tooltip
                      labelFormatter={fmtTime}
                      contentStyle={{ background: "#0f172a", border: "1px solid #334155" }}
                      formatter={(v) => (v == null ? "-" : Number(v).toFixed(2))}
                    />
                    <Line type="monotone" dataKey="close" stroke="#34d399" dot={false} strokeWidth={2} />
                    <Line
                      type="monotone"
                      dataKey="sma"
                      stroke="#fbbf24"
                      dot={false}
                      strokeWidth={1.5}
                      connectNulls={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
            <h2 className="mb-3 font-semibold">{ticker} news</h2>
            {news.length === 0 && !loading && (
              <p className="text-sm text-slate-500">No news found for this ticker.</p>
            )}
            <ul className="divide-y divide-slate-800">
              {news.map((n) => (
                <li key={n.url} className="py-2">
                  <a
                    href={n.url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-sm font-medium text-slate-100 hover:text-emerald-400"
                  >
                    {n.headline}
                  </a>
                  <div className="text-xs text-slate-500">
                    {n.source} {n.published_at ? `- ${fmtTime(n.published_at)}` : ""}
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <Chat />
      </section>
    </main>
  );
}