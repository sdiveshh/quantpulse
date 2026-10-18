import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))
from agents.graph import build_graph  # noqa: E402


def ask(graph, question: str):
    out = graph.invoke({"question": question})
    print(f"\n[route: {out.get('route')} | tickers: {out.get('tickers')}]")
    if out.get("sql"):
        print(f"[sql: {out['sql']}]")
    print(f"\n{out['answer']}\n")


def main():
    graph = build_graph()
    if len(sys.argv) > 1:
        ask(graph, " ".join(sys.argv[1:]))
        return
    print("QuantPulse assistant. Type a question, or 'exit' to quit.")
    while True:
        q = input("> ").strip()
        if q.lower() in ("exit", "quit", ""):
            break
        ask(graph, q)


if __name__ == "__main__":
    main()