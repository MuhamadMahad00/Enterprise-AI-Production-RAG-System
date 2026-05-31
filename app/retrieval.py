"""
Retrieval module.
Combines: BM25 retriever, dense retriever, RRF fusion, hybrid retriever, query processor.
"""

from rank_bm25 import BM25Okapi
from app.ingestion import VectorStore


# ═══════════════════════════════════════════════════════════════
# QUERY PROCESSOR (rewriting, expansion, decomposition)
# ═══════════════════════════════════════════════════════════════

class QueryProcessor:
    def rewrite_query(self, query):
        return query.strip()

    def expand_query(self, query):
        expansions = {
            "office timings": "working hours office schedule",
            "leave policy": "annual leave paid leave vacation policy",
            "remote work": "work from home hybrid work",
            "authentication": "login security access control",
            "onboarding": "new hire orientation training setup",
            "deployment": "CI/CD pipeline release production",
            "database": "PostgreSQL data storage schema",
            "monitoring": "observability metrics logging alerts",
        }
        expanded = query
        for key, value in expansions.items():
            if key in query.lower():
                expanded += " " + value
        return expanded

    def decompose_query(self, query):
        if " and " in query.lower():
            return [part.strip() for part in query.split(" and ")]
        return [query]

    def process_query(self, query):
        rewritten = self.rewrite_query(query)
        expanded = self.expand_query(rewritten)
        return self.decompose_query(expanded)


# ═══════════════════════════════════════════════════════════════
# BM25 SPARSE RETRIEVER
# ═══════════════════════════════════════════════════════════════

class BM25Retriever:
    def __init__(self, documents):
        self.documents = documents
        self.texts = [doc["content"] for doc in documents]
        self.tokenized_docs = [text.lower().split() for text in self.texts]
        self.bm25 = BM25Okapi(self.tokenized_docs)

    def retrieve(self, query, top_k=5):
        tokenized_query = query.lower().split()
        scores = self.bm25.get_scores(tokenized_query)
        ranked_indices = sorted(
            range(len(scores)), key=lambda i: scores[i], reverse=True
        )[:top_k]
        return [self.documents[i] for i in ranked_indices]


# ═══════════════════════════════════════════════════════════════
# DENSE RETRIEVER (FAISS)
# ═══════════════════════════════════════════════════════════════

class DenseRetriever:
    def __init__(self):
        self.vector_store = VectorStore()
        self.vector_store.load()

    def retrieve(self, query, top_k=5):
        return self.vector_store.search(query, top_k)


# ═══════════════════════════════════════════════════════════════
# RECIPROCAL RANK FUSION (RRF)
# ═══════════════════════════════════════════════════════════════

class RRFFusion:
    def __init__(self, k=60):
        self.k = k

    def fuse(self, dense_results, sparse_results):
        scores = {}
        documents = {}
        for rank, doc in enumerate(dense_results):
            key = doc["content"]
            documents[key] = doc
            scores[key] = scores.get(key, 0) + 1 / (self.k + rank + 1)
        for rank, doc in enumerate(sparse_results):
            key = doc["content"]
            documents[key] = doc
            scores[key] = scores.get(key, 0) + 1 / (self.k + rank + 1)
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [documents[key] for key, _ in ranked]


# ═══════════════════════════════════════════════════════════════
# HYBRID RETRIEVER (Dense + Sparse + RRF)
# ═══════════════════════════════════════════════════════════════

class HybridRetriever:
    def __init__(self):
        self.vector_store = VectorStore()
        self.vector_store.load()
        self.documents = self.vector_store.documents
        self.dense_retriever = DenseRetriever()
        self.sparse_retriever = BM25Retriever(self.documents)
        self.rrf = RRFFusion()

    def retrieve(self, query, top_k=5):
        dense_results = self.dense_retriever.retrieve(query, top_k)
        sparse_results = self.sparse_retriever.retrieve(query, top_k)
        fused_results = self.rrf.fuse(dense_results, sparse_results)
        return fused_results[:top_k]
