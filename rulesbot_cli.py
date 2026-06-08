"""A lightweight, fully functional RulesBot chat experience for the terminal.

This entrypoint avoids the Gradio runtime path entirely. It reuses the existing
document ingestion and semantic retrieval pipeline, then formats the top result
into a grounded answer that cites the matching game.
"""

from __future__ import annotations

import argparse
import re
import textwrap
from typing import Iterable

from ingest import chunk_document, load_documents
from retriever import embed_and_store, get_collection, retrieve


def ensure_index_ready() -> bool:
    """Populate the vector store if it is empty.

    Returns True when ingestion was performed, False when the index already
    contained chunks.
    """
    collection = get_collection()
    if collection.count() > 0:
        return False

    documents = load_documents()
    all_chunks = []
    for document in documents:
        all_chunks.extend(chunk_document(document["text"], document["game"]))

    if all_chunks:
        embed_and_store(all_chunks)
    return True


def _split_sentences(text: str) -> list[str]:
    """Split text into lightweight sentence-like pieces."""
    cleaned = " ".join(text.split())
    if not cleaned:
        return []

    parts = re.split(r"(?<=[.!?])\s+", cleaned)
    return [part.strip() for part in parts if part.strip()]


def _query_terms(query: str) -> set[str]:
    """Extract simple searchable terms from the user's question."""
    return {
        term
        for term in re.findall(r"[a-z0-9]+", query.lower())
        if len(term) > 2 or term.isdigit()
    }


def _best_excerpt(query: str, text: str, max_sentences: int = 2, max_chars: int = 500) -> str:
    """Return the most relevant sentence span for a query.

    The sentence span is chosen by overlap with query terms. If no sentence has
    overlap, the function falls back to the first sentences in the chunk.
    """
    sentences = _split_sentences(text)
    if not sentences:
        return ""

    terms = _query_terms(query)
    if not terms:
        summary = " ".join(sentences[:max_sentences])
        return summary[:max_chars].rstrip()

    scored_sentences = []
    for index, sentence in enumerate(sentences):
        sentence_terms = set(re.findall(r"[a-z0-9]+", sentence.lower()))
        score = len(terms & sentence_terms)
        if score:
            scored_sentences.append((score, index, sentence))

    if not scored_sentences:
        summary = " ".join(sentences[:max_sentences])
        return summary[:max_chars].rstrip()

    scored_sentences.sort(key=lambda item: (-item[0], item[1]))
    best_index = scored_sentences[0][1]
    chosen = sentences[best_index : best_index + max_sentences]
    summary = " ".join(chosen)
    if len(summary) > max_chars:
        summary = summary[:max_chars].rstrip()
    return summary


def format_answer(query: str, retrieved_chunks: list[dict]) -> str:
    """Turn retrieval results into a readable grounded answer."""
    if not retrieved_chunks:
        return (
            "I couldn't find anything relevant in the loaded rule books. "
            "Try rephrasing your question."
        )

    best_chunk = retrieved_chunks[0]
    game = best_chunk.get("game") or "Unknown game"
    distance = best_chunk.get("distance")
    chunk_text = best_chunk.get("text", "")

    lines = [
        f"Question: {query}",
        f"Best match: {game} (distance {distance:.3f})" if isinstance(distance, (int, float)) else f"Best match: {game}",
        "",
        f"Based on {game}, the relevant rule passage says:",
        textwrap.fill(_best_excerpt(query, chunk_text), width=88),
    ]

    if len(retrieved_chunks) > 1:
        lines.append("")
        lines.append("Other supporting matches:")
        for chunk in retrieved_chunks[1:]:
            support_game = chunk.get("game") or "Unknown game"
            support_distance = chunk.get("distance")
            support_excerpt = _best_excerpt(query, chunk.get("text", ""), max_sentences=1, max_chars=220)
            support_label = (
                f"- {support_game} (distance {support_distance:.3f}): {support_excerpt}"
                if isinstance(support_distance, (int, float))
                else f"- {support_game}: {support_excerpt}"
            )
            lines.append(textwrap.fill(support_label, width=88, subsequent_indent="  "))

    return "\n".join(lines)


def handle_query(query: str, n_results: int = 3) -> str:
    """Run retrieval and formatting for a single user question."""
    retrieved_chunks = retrieve(query, n_results=n_results)
    return format_answer(query, retrieved_chunks)


def chat_loop(n_results: int = 3) -> None:
    """Start an interactive terminal chat session."""
    print("RulesBot CLI")
    print("Type a question and press Enter. Type 'exit' or 'quit' to stop.\n")

    while True:
        query = input("You: ").strip()
        if query.lower() in {"exit", "quit"}:
            print("Goodbye.")
            break
        if not query:
            continue

        print()
        print(handle_query(query, n_results=n_results))
        print()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="RulesBot terminal chatbot")
    parser.add_argument("query", nargs="?", help="Ask one question and exit")
    parser.add_argument("--n-results", type=int, default=3, help="Number of retrieved chunks to use")
    parser.add_argument(
        "--skip-ingest",
        action="store_true",
        help="Do not auto-populate the vector store if it is empty",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not args.skip_ingest:
        ingested = ensure_index_ready()
        if ingested:
            print("Vector store was empty, so the documents were ingested automatically.\n")

    if args.query:
        print(handle_query(args.query, n_results=args.n_results))
        return

    chat_loop(n_results=args.n_results)


if __name__ == "__main__":
    main()