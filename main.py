"""
main.py — FastAPI entry point with all API routes.
Single file for app setup, schemas, and endpoints.
"""

import os
import json
from typing import Optional

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.config import settings, logger
from app.generation import RAGPipeline
from app.evaluation import RAGEvaluator, MetricsLogger
from app.ingestion import DocumentLoader, ChunkingService, VectorStore


# ═══════════════════════════════════════════════════════════════
# SCHEMAS
# ═══════════════════════════════════════════════════════════════

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1)

class QueryResponse(BaseModel):
    query: str
    answer: str
    model: Optional[str] = None
    latency: float
    sources: list
    latency_breakdown: dict = {}
    guardrail_status: str = "passed"
    grounding_score: Optional[float] = None

class IngestRequest(BaseModel):
    file_path: Optional[str] = None
    text: Optional[str] = None
    source_name: str = "manual_upload"

class EvaluationRequest(BaseModel):
    max_questions: Optional[int] = None

class HealthResponse(BaseModel):
    status: str
    version: str
    components: dict
    metrics_summary: dict


# ═══════════════════════════════════════════════════════════════
# APP SETUP
# ═══════════════════════════════════════════════════════════════

app = FastAPI(
    title="AI Production RAG System",
    description="Production-Grade RAG System with Evaluation & Guardrails",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pipeline = RAGPipeline()
metrics_logger = MetricsLogger()


# ═══════════════════════════════════════════════════════════════
# QUERY ENDPOINT
# ═══════════════════════════════════════════════════════════════

@app.post("/query", response_model=QueryResponse, tags=["Query"])
def query_rag(request: QueryRequest):
    try:
        result = pipeline.run(request.query)
        return QueryResponse(
            query=result["query"], answer=result["answer"],
            model=result.get("model"), latency=result["latency"],
            sources=[{"content": s.get("content","")[:200], "source": s.get("source","unknown"),
                       "chunk_id": s.get("chunk_id",-1)} for s in result.get("sources",[])],
            latency_breakdown=result.get("latency_breakdown",{}),
            guardrail_status=result.get("guardrail_status","passed"),
            grounding_score=result.get("grounding_score"),
        )
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(500, str(e))


# ═══════════════════════════════════════════════════════════════
# DOCUMENT INGESTION
# ═══════════════════════════════════════════════════════════════

@app.post("/ingest", tags=["Admin"])
def ingest_documents(request: IngestRequest):
    try:
        vs = VectorStore(); chunker = ChunkingService(); docs = []
        if request.text:
            docs.append({"content": request.text, "source": request.source_name})
        elif request.file_path and os.path.exists(request.file_path):
            docs = DocumentLoader(request.file_path).load_documents()
        else:
            docs = DocumentLoader(settings.DOCUMENTS_PATH).load_documents()
        if not docs:
            return {"status":"warning","documents_loaded":0,"chunks_created":0,"message":"No documents found."}
        chunks = chunker.create_chunks(docs); vs.add_documents(chunks); vs.save()
        return {"status":"success","documents_loaded":len(docs),"chunks_created":len(chunks),
                "message":f"Ingested {len(docs)} docs into {len(chunks)} chunks."}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/upload", tags=["Admin"])
async def upload_document(file: UploadFile = File(...)):
    os.makedirs(settings.DOCUMENTS_PATH, exist_ok=True)
    content = await file.read()
    with open(os.path.join(settings.DOCUMENTS_PATH, file.filename), "wb") as f:
        f.write(content)
    return {"status":"success","filename":file.filename,"size":len(content)}


@app.post("/reindex", tags=["Admin"])
def reindex_documents():
    try:
        docs = DocumentLoader(settings.DOCUMENTS_PATH).load_documents()
        if not docs:
            return {"status":"warning","documents_processed":0,"chunks_created":0,"index_size":0,"message":"No documents."}
        chunks = ChunkingService().create_chunks(docs)
        vs = VectorStore(); vs.add_documents(chunks); vs.save()
        return {"status":"success","documents_processed":len(docs),"chunks_created":len(chunks),
                "index_size":vs.index.ntotal,"message":f"Re-indexed {len(docs)} documents."}
    except Exception as e:
        raise HTTPException(500, str(e))


# ═══════════════════════════════════════════════════════════════
# EVALUATION
# ═══════════════════════════════════════════════════════════════

@app.post("/evaluate", tags=["Evaluation"])
def run_evaluation(request: EvaluationRequest = EvaluationRequest()):
    try:
        report = RAGEvaluator().evaluate(max_questions=request.max_questions)
        return {k: v for k, v in report.items() if k != "results"}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/evaluation/report", tags=["Evaluation"])
def get_evaluation_report():
    path = "reports/latest_evaluation.json"
    if not os.path.exists(path):
        raise HTTPException(404, "No evaluation report found. Run /evaluate first.")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@app.get("/evaluation/reports", tags=["Evaluation"])
def list_evaluation_reports():
    reports = [f for f in os.listdir("reports") if f.startswith("evaluation_report_") and f.endswith(".json")] if os.path.exists("reports") else []
    return {"reports": sorted(reports, reverse=True)}


# ═══════════════════════════════════════════════════════════════
# METRICS & HEALTH
# ═══════════════════════════════════════════════════════════════

@app.get("/metrics", tags=["Monitoring"])
def get_metrics():
    return metrics_logger.get_metrics_summary()


@app.get("/metrics/latency-breakdown", tags=["Monitoring"])
def get_latency_breakdown():
    path = "reports/latency_breakdown.json"
    if not os.path.exists(path):
        return {"entries": []}
    with open(path, "r") as f:
        return {"entries": json.load(f)[-50:]}


@app.get("/health", response_model=HealthResponse, tags=["Monitoring"])
def health_check():
    components = {
        "vector_store": os.path.exists(f"{settings.VECTOR_DB_PATH}/faiss.index"),
        "documents": os.path.exists(settings.DOCUMENTS_PATH),
        "benchmark": os.path.exists(settings.BENCHMARK_PATH),
        "reports_dir": os.path.exists(settings.REPORTS_PATH),
    }
    doc_count = len([f for f in os.listdir(settings.DOCUMENTS_PATH) if f.endswith(".txt")]) if os.path.exists(settings.DOCUMENTS_PATH) else 0
    return HealthResponse(
        status="healthy" if all(components.values()) else "degraded",
        version="1.0.0",
        components={**components, "document_count": doc_count},
        metrics_summary=metrics_logger.get_metrics_summary(),
    )


@app.get("/documents", tags=["Admin"])
def list_documents():
    if not os.path.exists(settings.DOCUMENTS_PATH):
        return {"documents":[],"total":0}
    docs = [{"filename":f,"size_bytes":os.path.getsize(os.path.join(settings.DOCUMENTS_PATH,f)),
             "type":f.rsplit(".",1)[-1] if "." in f else "unknown"}
            for f in os.listdir(settings.DOCUMENTS_PATH) if os.path.isfile(os.path.join(settings.DOCUMENTS_PATH,f))]
    return {"documents":docs,"total":len(docs)}