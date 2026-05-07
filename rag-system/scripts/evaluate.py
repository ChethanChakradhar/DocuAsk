from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional

from app.core.config import get_settings
from app.services.rag_service import RAGService


def load_dataset(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    if not isinstance(payload, list):
        raise ValueError("Dataset must be a JSON array.")

    return payload


def evaluate_item(item: dict, rag_service: RAGService, top_k: Optional[int]) -> dict:
    question = str(item.get("question", "")).strip()
    expected_keywords = [
        str(x).lower() for x in item.get("expected_answer_contains", []) if str(x).strip()
    ]
    expected_sources = [
        str(x).lower() for x in item.get("expected_sources", []) if str(x).strip()
    ]

    if not question:
        raise ValueError("Each row must include a non-empty 'question'.")

    result = rag_service.ask(question=question, top_k=top_k)
    answer_lower = result.answer.lower()

    keyword_hit = True
    if expected_keywords:
        keyword_hit = all(keyword in answer_lower for keyword in expected_keywords)

    source_hit = True
    if expected_sources:
        observed = {s.filename.lower() for s in result.sources}
        source_hit = any(expected in observed for expected in expected_sources)

    return {
        "question": question,
        "answer": result.answer,
        "grounded": result.grounded,
        "keyword_hit": keyword_hit,
        "source_hit": source_hit,
        "num_sources": len(result.sources),
    }


def print_summary(rows: list[dict]) -> None:
    total = len(rows)
    grounded = sum(1 for r in rows if r["grounded"])
    keyword = sum(1 for r in rows if r["keyword_hit"])
    source = sum(1 for r in rows if r["source_hit"])

    print("\n=== Evaluation Summary ===")
    print(f"Total questions      : {total}")
    print(f"Grounded rate        : {grounded / total:.2%}")
    print(f"Keyword match rate   : {keyword / total:.2%}")
    print(f"Expected source rate : {source / total:.2%}")

    print("\n=== Per-question ===")
    for idx, row in enumerate(rows, start=1):
        print(f"[{idx}] {row['question']}")
        print(f"  grounded={row['grounded']} keyword_hit={row['keyword_hit']} source_hit={row['source_hit']} sources={row['num_sources']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate RAG quality on a QA dataset")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("eval/eval_dataset.json"),
        help="Path to evaluation JSON dataset",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=None,
        help="Optional retrieval top-k override",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("eval/eval_results.json"),
        help="Where to write detailed evaluation output",
    )
    args = parser.parse_args()

    settings = get_settings()
    rag_service = RAGService(settings)
    dataset = load_dataset(args.dataset)

    rows = [evaluate_item(item, rag_service, args.top_k) for item in dataset]
    print_summary(rows)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)

    print(f"\nSaved detailed results to: {args.output}")


if __name__ == "__main__":
    main()
