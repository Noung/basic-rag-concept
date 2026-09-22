"""Offline evaluation utilities for the Basic RAG Learning Lab.

The evaluator focuses on retrieval evidence first. Generation quality can be
added later without changing the golden-question format.
"""

import json
import time
from dataclasses import asdict, dataclass
from typing import List

import rag_app


@dataclass(frozen=True)
class GoldenQuestion:
    question: str
    expected_terms: List[str]
    expected_source: str
    category: str


GOLDEN_QUESTIONS = [
    GoldenQuestion(
        question="วันสงกรานต์ปี 2568 มีวันไหนบ้าง",
        expected_terms=["14 เมษายน 2568", "15 เมษายน 2568"],
        expected_source="thai_holiday.txt",
        category="รายการ",
    ),
    GoldenQuestion(
        question="วันมาฆบูชาปี 2568 ตรงกับวันที่เท่าไร",
        expected_terms=["12 กุมภาพันธ์ 2568"],
        expected_source="thai_holiday.txt",
        category="วันที่",
    ),
    GoldenQuestion(
        question="วันแรงงานแห่งชาติปี 2568 ตรงกับวันใด",
        expected_terms=["1 พฤษภาคม 2568"],
        expected_source="thai_holiday.txt",
        category="วันที่",
    ),
    GoldenQuestion(
        question="วันรัฐธรรมนูญปี 2568 ตรงกับวันที่เท่าไร",
        expected_terms=["10 ธันวาคม 2568"],
        expected_source="thai_holiday.txt",
        category="วันที่",
    ),
    GoldenQuestion(
        question="วันหยุดพิเศษในเดือนมิถุนายน 2568 คือวันใด",
        expected_terms=["2 มิถุนายน 2568"],
        expected_source="thai_holiday.txt",
        category="ค้นตามเงื่อนไข",
    ),
    GoldenQuestion(
        question="วันที่ 31 ธันวาคม 2568 เป็นวันอะไร",
        expected_terms=["วันสิ้นปี"],
        expected_source="thai_holiday.txt",
        category="คำอธิบาย",
    ),
]


def evaluate_question(item: GoldenQuestion, n_results=5):
    """Evaluate whether retrieval returned the expected evidence."""
    started = time.perf_counter()
    selected, stats = rag_app.retrieve_relevant_chunks(
        item.question,
        n_results=n_results,
    )
    latency_ms = (time.perf_counter() - started) * 1000

    context = "\n".join(chunk.get("document", "") for chunk in selected)
    source_names = {
        (chunk.get("metadata") or {}).get("source", "unknown")
        for chunk in selected
    }
    terms_found = [
        term for term in item.expected_terms if term in context
    ]
    source_match = item.expected_source in source_names
    evidence_match = len(terms_found) == len(item.expected_terms)

    if evidence_match and source_match:
        status = "Correct"
    elif not selected:
        status = "No Answer"
    else:
        status = "Incorrect"

    return {
        "question": item.question,
        "category": item.category,
        "expected_source": item.expected_source,
        "sources": sorted(source_names),
        "terms_found": terms_found,
        "status": status,
        "source_match": source_match,
        "evidence_match": evidence_match,
        "retrieval_hit": bool(selected),
        "top_score": round(stats.get("top_score", 0.0), 4),
        "latency_ms": round(latency_ms, 2),
    }


def evaluate_golden_set(n_results=5):
    """Evaluate all golden questions and return detailed metrics."""
    results = [
        evaluate_question(item, n_results=n_results)
        for item in GOLDEN_QUESTIONS
    ]
    total = len(results)
    retrieval_hits = sum(result["retrieval_hit"] for result in results)
    source_matches = sum(result["source_match"] for result in results)
    correct = sum(result["status"] == "Correct" for result in results)
    no_answer = sum(result["status"] == "No Answer" for result in results)
    latencies = [result["latency_ms"] for result in results]

    summary = {
        "total_questions": total,
        "retrieval_hit_rate_at_k": round(retrieval_hits / total, 4) if total else 0,
        "source_match_rate": round(source_matches / total, 4) if total else 0,
        "correct_evidence_rate": round(correct / total, 4) if total else 0,
        "no_answer_rate": round(no_answer / total, 4) if total else 0,
        "average_latency_ms": round(sum(latencies) / total, 2) if total else 0,
        "max_latency_ms": round(max(latencies), 2) if latencies else 0,
        "k": n_results,
    }
    return {"summary": summary, "results": results}


def format_report(report):
    """Format evaluation output for terminal or an Admin textbox."""
    summary = report["summary"]
    lines = [
        "RAG Evaluation Lab",
        f"Questions: {summary['total_questions']}",
        f"Hit Rate@{summary['k']}: {summary['retrieval_hit_rate_at_k']:.1%}",
        f"Source Match: {summary['source_match_rate']:.1%}",
        f"Correct Evidence: {summary['correct_evidence_rate']:.1%}",
        f"No Answer: {summary['no_answer_rate']:.1%}",
        f"Average latency: {summary['average_latency_ms']:.2f} ms",
        f"Max latency: {summary['max_latency_ms']:.2f} ms",
        "",
        "Question Results:",
    ]
    for index, result in enumerate(report["results"], start=1):
        lines.append(
            f"{index}. [{result['status']}] {result['question']} | "
            f"hit={result['retrieval_hit']} | "
            f"source={result['source_match']} | "
            f"latency={result['latency_ms']:.2f} ms"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    evaluation = evaluate_golden_set()
    print(format_report(evaluation))
    print("\nJSON:")
    print(json.dumps(evaluation, ensure_ascii=False, indent=2))
