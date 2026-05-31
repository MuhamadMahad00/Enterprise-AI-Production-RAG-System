"""
Generation module.
Combines: LLM client, prompt builder, input/output guardrails, RAG pipeline.
"""

import re
import time
from openai import OpenAI
from sentence_transformers import CrossEncoder

from app.config import settings, logger, LatencyTracker
from app.retrieval import QueryProcessor, HybridRetriever
from app.evaluation import MetricsLogger


# ═══════════════════════════════════════════════════════════════
# INPUT GUARDRAILS
# ═══════════════════════════════════════════════════════════════

class InputGuardrails:
    def __init__(self):
        self.injection_patterns = [
            r"ignore\s+(all\s+)?previous\s+instructions",
            r"system\s+prompt", r"bypass\s+security",
            r"reveal\s+confidential", r"delete\s+database",
            r"shutdown\s+server", r"disregard\s+(all\s+)?prior",
            r"forget\s+your\s+(instructions|rules|guidelines)",
            r"you\s+are\s+now\s+(a|an)", r"pretend\s+you\s+are",
            r"override\s+(your\s+)?instructions", r"jailbreak", r"DAN\s+mode",
            r"execute\s+(shell|command|code|script)", r"rm\s+-rf",
            r"DROP\s+TABLE", r"<script[\s>]", r"javascript:",
            r"\{\{.*\}\}", r"__import__", r"eval\s*\(", r"exec\s*\(",
            r"os\.system",
        ]
        self.off_topic_indicators = [
            r"(write|compose|create)\s+(me\s+)?(a\s+)?(poem|song|story|essay|joke)",
            r"(cook|recipe|ingredients)\s+for",
            r"(weather|temperature)\s+in\s+",
            r"translate\s+.+\s+to\s+",
        ]

    def validate_query(self, query):
        lower = query.lower().strip()
        if len(query) < settings.MIN_QUERY_LENGTH:
            return {"allowed": False, "reason": "Query is too short.", "category": "length_validation"}
        if len(query) > settings.MAX_QUERY_LENGTH:
            return {"allowed": False, "reason": "Query exceeds maximum length.", "category": "length_validation"}
        for p in self.injection_patterns:
            if re.search(p, lower, re.IGNORECASE):
                logger.warning(f"Prompt injection detected: '{query[:80]}'")
                return {"allowed": False, "reason": "Potential prompt injection detected.", "category": "prompt_injection"}
        for p in self.off_topic_indicators:
            if re.search(p, lower, re.IGNORECASE):
                return {"allowed": False, "reason": "Off-topic query rejected.", "category": "off_topic"}
        sanitized = re.sub(r'<[^>]+>', '', query)
        sanitized = re.sub(r'\s+', ' ', sanitized).strip().replace('\x00', '')
        return {"allowed": True, "reason": None, "category": "passed", "sanitized_query": sanitized}


# ═══════════════════════════════════════════════════════════════
# OUTPUT GUARDRAILS
# ═══════════════════════════════════════════════════════════════

class OutputGuardrails:
    STOP_WORDS = {
        "the","a","an","is","are","was","were","be","been","being","have","has",
        "had","do","does","did","will","would","could","should","may","might",
        "can","shall","to","of","in","for","on","with","at","by","from","as",
        "into","through","and","but","or","not","no","this","that","these",
        "those","it","its","they","them","their","we","our","you","your","i",
        "me","my","he","she","him","her","his","so","if","then","than","too",
    }
    HALLUCINATION_INDICATORS = [
        "as an ai", "i think", "i believe", "in my opinion",
        "as a language model", "i cannot access",
    ]

    def validate_response(self, answer, retrieved_docs):
        if not retrieved_docs:
            return {"valid": False, "reason": "No context.", "grounding_score": 0.0}
        context = " ".join(doc["content"] for doc in retrieved_docs).lower()
        words = [w for w in answer.lower().split() if w not in self.STOP_WORDS and len(w) > 2]
        if not words:
            return {"valid": True, "reason": None, "grounding_score": 1.0}
        matched = sum(1 for w in words if w in context)
        score = matched / len(words)
        if score < settings.GROUNDING_THRESHOLD:
            return {"valid": False, "reason": f"Low grounding ({score:.2f}).", "grounding_score": score}
        lower_answer = answer.lower()
        for ind in self.HALLUCINATION_INDICATORS:
            if ind in lower_answer:
                return {"valid": False, "reason": f"Hallucination indicator: '{ind}'.", "grounding_score": score}
        return {"valid": True, "reason": None, "grounding_score": score}


# ═══════════════════════════════════════════════════════════════
# PROMPT BUILDER
# ═══════════════════════════════════════════════════════════════

class PromptBuilder:
    def build_prompt(self, query, retrieved_docs):
        parts = []
        for i, doc in enumerate(retrieved_docs, 1):
            source = doc.get("source", "Unknown")
            parts.append(f"[Source {i}: {source} | Chunk {doc.get('chunk_id','N/A')}]\n{doc['content']}")
        context = "\n\n---\n\n".join(parts)
        return f"""You are an enterprise AI assistant. Answer ONLY using the provided context.
If not found, say: "I could not find relevant information in the provided documents."
Be concise, accurate, professional. ALWAYS cite sources using [Source N].

Context:
{context}

Question: {query}

Answer (with source citations):"""


# ═══════════════════════════════════════════════════════════════
# LLM CLIENT
# ═══════════════════════════════════════════════════════════════

_client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=settings.OPENROUTER_API_KEY)


class LLMClient:
    def __init__(self):
        self.models = ["openai/gpt-3.5-turbo", "anthropic/claude-3-haiku"]

    def generate(self, prompt):
        for model in self.models:
            for attempt in range(3):
                try:
                    logger.info(f"Trying model: {model}")
                    response = _client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=settings.LLM_TEMPERATURE,
                        max_tokens=settings.LLM_MAX_TOKENS,
                    )
                    return {"answer": response.choices[0].message.content, "model": model}
                except Exception as e:
                    logger.warning(f"Attempt {attempt+1} failed for {model}: {e}")
                    time.sleep(2)
        return {"answer": "LLM generation failed after all fallback attempts.", "model": None}


# ═══════════════════════════════════════════════════════════════
# CROSS-ENCODER RERANKER
# ═══════════════════════════════════════════════════════════════

class CrossEncoderReranker:
    def __init__(self):
        self.model = CrossEncoder(settings.CROSS_ENCODER_MODEL)

    def rerank(self, query, documents, top_k=3):
        pairs = [[query, doc] for doc in documents]
        scores = self.model.predict(pairs)
        scored = sorted(zip(documents, scores), key=lambda x: x[1], reverse=True)
        return [doc for doc, _ in scored[:top_k]]


# ═══════════════════════════════════════════════════════════════
# RAG PIPELINE
# ═══════════════════════════════════════════════════════════════

class RAGPipeline:
    def __init__(self):
        self.query_processor = QueryProcessor()
        self.retriever = HybridRetriever()
        self.reranker = CrossEncoderReranker()
        self.prompt_builder = PromptBuilder()
        self.llm_client = LLMClient()
        self.input_guardrails = InputGuardrails()
        self.output_guardrails = OutputGuardrails()
        self.metrics_logger = MetricsLogger()

    def run(self, query):
        tracker = LatencyTracker()
        tracker.start()

        # Guardrails
        tracker.start_stage("guardrails")
        validation = self.input_guardrails.validate_query(query)
        tracker.end_stage("guardrails")
        if not validation["allowed"]:
            return {
                "query": query, "answer": f"⚠️ {validation['reason']}",
                "model": None, "sources": [], "latency": 0,
                "latency_breakdown": {}, "guardrail_status": validation.get("category", "blocked"),
            }

        clean_query = validation.get("sanitized_query", query)

        # Query processing
        tracker.start_stage("query_processing")
        processed_queries = self.query_processor.process_query(clean_query)
        tracker.end_stage("query_processing")

        # Retrieval
        tracker.start_stage("retrieval")
        retrieved_docs = []
        for q in processed_queries:
            retrieved_docs.extend(self.retriever.retrieve(q))
        seen, unique_docs = set(), []
        for doc in retrieved_docs:
            if doc["content"] not in seen:
                seen.add(doc["content"])
                unique_docs.append(doc)
        tracker.end_stage("retrieval")

        # Reranking
        tracker.start_stage("reranking")
        reranked = self.reranker.rerank(clean_query, [d["content"] for d in unique_docs])
        final_docs = []
        for content in reranked:
            for doc in unique_docs:
                if doc["content"] == content:
                    final_docs.append(doc)
                    break
        tracker.end_stage("reranking")

        # Generation
        tracker.start_stage("generation")
        prompt = self.prompt_builder.build_prompt(clean_query, final_docs)
        response = self.llm_client.generate(prompt)
        tracker.end_stage("generation")

        # Output validation
        tracker.start_stage("output_validation")
        out_val = self.output_guardrails.validate_response(response["answer"], final_docs)
        if not out_val["valid"]:
            response["answer"] = "⚠️ Response failed grounding validation."
        tracker.end_stage("output_validation")

        total = tracker.stop()
        breakdown = tracker.get_breakdown()
        logger.info(f"RAG completed in {total}s | {breakdown}")
        self.metrics_logger.log(query=clean_query, model=response["model"], latency=total, breakdown=breakdown)

        return {
            "query": clean_query, "answer": response["answer"],
            "model": response["model"], "sources": final_docs,
            "latency": total, "latency_breakdown": breakdown,
            "guardrail_status": "passed", "grounding_score": out_val.get("grounding_score"),
        }
