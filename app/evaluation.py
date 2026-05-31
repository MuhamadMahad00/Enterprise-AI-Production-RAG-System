"""
Evaluation module.
Combines: metrics logger, RAGAS-style evaluator.
"""

import csv
import os
import re
import json
import time
from datetime import datetime

from app.config import settings, logger


# ═══════════════════════════════════════════════════════════════
# METRICS LOGGER
# ═══════════════════════════════════════════════════════════════

class MetricsLogger:
    def __init__(self):
        self.file_path = "reports/metrics.csv"
        self.breakdown_path = "reports/latency_breakdown.json"

    def log(self, query, model, latency, breakdown=None):
        file_exists = os.path.exists(self.file_path)
        with open(self.file_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["timestamp","query","model","total_latency","retrieval_ms","reranking_ms","generation_ms"])
            r = breakdown.get("retrieval", 0) if breakdown else 0
            rr = breakdown.get("reranking", 0) if breakdown else 0
            g = breakdown.get("generation", 0) if breakdown else 0
            writer.writerow([datetime.now().isoformat(), query, model, latency,
                             round(r*1000,2), round(rr*1000,2), round(g*1000,2)])
        if breakdown:
            self._log_breakdown(query, latency, breakdown)

    def _log_breakdown(self, query, total, breakdown):
        entries = []
        if os.path.exists(self.breakdown_path):
            try:
                with open(self.breakdown_path, "r") as f:
                    entries = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                entries = []
        entries.append({"timestamp": datetime.now().isoformat(), "query": query[:100],
                        "total_latency": total, "breakdown": breakdown})
        entries = entries[-500:]
        with open(self.breakdown_path, "w") as f:
            json.dump(entries, f, indent=2)

    def get_metrics_summary(self):
        if not os.path.exists(self.file_path):
            return {"total_queries": 0}
        latencies, models_used = [], {}
        with open(self.file_path, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                try:
                    lat = float(row.get("total_latency", row.get("latency", 0)))
                    latencies.append(lat)
                    m = row.get("model", "unknown")
                    models_used[m] = models_used.get(m, 0) + 1
                except (ValueError, TypeError):
                    continue
        if not latencies:
            return {"total_queries": 0}
        latencies.sort()
        p95 = int(len(latencies) * 0.95)
        return {
            "total_queries": len(latencies),
            "avg_latency": round(sum(latencies)/len(latencies), 4),
            "min_latency": round(min(latencies), 4),
            "max_latency": round(max(latencies), 4),
            "p95_latency": round(latencies[min(p95, len(latencies)-1)], 4),
            "models_used": models_used,
        }


# ═══════════════════════════════════════════════════════════════
# RAGAS-STYLE EVALUATOR
# ═══════════════════════════════════════════════════════════════

_STOP = {
    "the","a","an","is","are","was","were","be","been","being","have","has",
    "had","do","does","did","will","would","could","should","may","might",
    "can","shall","to","of","in","for","on","with","at","by","from","as",
    "and","but","or","not","no","this","that","it","its","they","them",
    "their","we","our","you","your","i","me","my","he","she","him","her",
    "his","so","if","then","than","too","very","just","about","also",
    "what","how","when","where","why","who","which",
}


class RAGEvaluator:
    def __init__(self):
        # Lazy import to avoid circular dependency
        from app.generation import RAGPipeline
        self.pipeline = RAGPipeline()

    def load_questions(self, path="benchmark/questions.json"):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def evaluate(self, max_questions=None):
        questions = self.load_questions()
        if max_questions:
            questions = questions[:max_questions]

        results = []
        total_lat = total_f = total_r = total_cr = successful = 0

        for i, item in enumerate(questions):
            q = item["question"]
            expected = item.get("expected_answer", "")
            keywords = item.get("expected_keywords", [])

            start = time.time()
            result = self.pipeline.run(q)
            lat = time.time() - start

            answer = result["answer"]
            sources = result.get("sources", [])
            context = " ".join(s.get("content","") for s in sources)

            faith = self._faithfulness(answer, context)
            relev = self._relevancy(answer, q)
            recall = self._context_recall(expected, keywords, context)
            grounded = expected.lower() in answer.lower() if expected else False
            if grounded:
                successful += 1

            total_lat += lat; total_f += faith; total_r += relev; total_cr += recall
            results.append({
                "question": q, "category": item.get("category","general"),
                "expected": expected, "answer": answer, "grounded": grounded,
                "latency": round(lat,2), "model": result.get("model"),
                "faithfulness": round(faith,3), "relevancy": round(relev,3),
                "context_recall": round(recall,3),
                "latency_breakdown": result.get("latency_breakdown",{}),
                "num_sources": len(sources),
            })

        n = len(questions)
        lats = sorted(r["latency"] for r in results)
        p95 = lats[min(int(len(lats)*0.95), len(lats)-1)] if lats else 0

        report = {
            "evaluation_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "timestamp": datetime.now().isoformat(),
            "total_questions": n,
            "accuracy": round(successful/n, 3) if n else 0,
            "average_latency": round(total_lat/n, 2) if n else 0,
            "p95_latency": round(p95, 2),
            "latency_sla_met": p95 < 3.0,
            "ragas_scores": {
                "faithfulness": round(total_f/n, 3) if n else 0,
                "answer_relevancy": round(total_r/n, 3) if n else 0,
                "context_recall": round(total_cr/n, 3) if n else 0,
            },
            "results": results,
        }
        self._save_report(report)
        return report

    def _faithfulness(self, answer, context):
        if not context or not answer:
            return 0.0
        ctx = context.lower()
        tokens = [w for w in re.findall(r'\w+', answer.lower()) if w not in _STOP and len(w) > 2]
        if not tokens:
            return 1.0
        return sum(1 for t in tokens if t in ctx) / len(tokens)

    def _relevancy(self, answer, question):
        if not answer or not question:
            return 0.0
        qt = {w for w in re.findall(r'\w+', question.lower()) if w not in _STOP and len(w) > 2}
        at = {w for w in re.findall(r'\w+', answer.lower()) if w not in _STOP and len(w) > 2}
        if not qt:
            return 1.0
        return len(qt & at) / len(qt)

    def _context_recall(self, expected, keywords, context):
        if not context:
            return 0.0
        ctx = context.lower()
        if keywords:
            return sum(1 for k in keywords if k.lower() in ctx) / len(keywords)
        if expected:
            tokens = [w for w in re.findall(r'\w+', expected.lower()) if len(w) > 2]
            if not tokens:
                return 1.0
            return sum(1 for t in tokens if t in ctx) / len(tokens)
        return 0.0

    def _save_report(self, report):
        os.makedirs("reports", exist_ok=True)
        path = f"reports/evaluation_report_{report['evaluation_id']}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        with open("reports/latest_evaluation.json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        logger.info(f"Report saved: {path}")
