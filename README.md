# 🤖 Enterprise AI Production RAG System

A production-grade Retrieval-Augmented Generation (RAG) system developed as part of the AI Engineering Internship Program.

This project demonstrates how modern enterprise AI assistants retrieve, rerank, validate, and generate responses from organizational knowledge sources using a scalable and modular architecture.

The system combines semantic search, keyword retrieval, reciprocal rank fusion (RRF), cross-encoder reranking, guardrails, evaluation frameworks, monitoring, FastAPI backend services, and a modern React interface to deliver accurate and grounded responses.

---

## 🚀 Project Overview

Enterprise organizations generate large volumes of internal knowledge across HR policies, onboarding guides, technical documentation, compliance manuals, and operational workflows.

Traditional keyword search often fails to retrieve the most relevant information, resulting in poor user experience and reduced productivity.

This project addresses that challenge by building a production-ready RAG pipeline capable of:

- Understanding natural language queries
- Retrieving relevant information using hybrid search (BM25 + FAISS)
- Improving relevance through Cross-Encoder reranking
- Generating context-aware responses using LLMs (OpenRouter)
- Providing source attribution for transparency
- Monitoring system performance and latency profiling stage-by-stage
- Enforcing safety through strict input/output guardrails
- Automated RAGAS-style evaluation metrics (Faithfulness, Relevancy, Context Recall)

The result is an enterprise-grade AI knowledge assistant capable of delivering accurate, explainable, and trustworthy answers.

---

## 🎯 Key Objectives

- Build a modular production-style RAG architecture (consolidated into 6 clean python files)
- Implement document ingestion and preprocessing pipelines (Supports `.txt` and `.pdf`)
- Generate semantic embeddings using transformer models
- Store and retrieve vectors using FAISS
- Combine semantic retrieval with BM25 keyword search via Reciprocal Rank Fusion (RRF)
- Improve ranking using Cross-Encoder reranking
- Generate grounded responses using Large Language Models
- Implement query safety and multi-layer guardrails
- Expose services through FastAPI APIs
- Create an interactive React frontend with Vite
- Evaluate system accuracy and latency (< 3s p95 SLAs)
- Implement monitoring and performance logging

---

## ✨ Core Features

✅ **Document Ingestion Pipeline**: Reads text and PDF files and splits them into recursive chunks.
✅ **Semantic Embeddings**: `sentence-transformers/all-MiniLM-L6-v2`
✅ **FAISS Vector Database**: Fast similarity search.
✅ **BM25 Keyword Retrieval**: Sparse vector lexical matching.
✅ **Hybrid Retrieval System**: Fusing Dense and Sparse via RRF.
✅ **Cross-Encoder Reranking**: `cross-encoder/ms-marco-MiniLM-L-6-v2` for high accuracy context selection.
✅ **Query Processing Pipeline**: Automatic query expansion and decomposition.
✅ **OpenRouter LLM Integration**: Flexible access to GPT, Claude, and other models.
✅ **Source Attribution**: Strict `[Source N]` formatting.
✅ **Security Guardrails**: Regex prompt injection detection, off-topic rejection, and grounding checks.
✅ **FastAPI Backend**: Consolidated, highly-modular routing.
✅ **React Frontend**: Beautiful, modern UI with Framer Motion animations.
✅ **Evaluation Framework**: Custom RAGAS metrics and p95 latency tracking.

---

## 🏗️ System Architecture

The system follows a modular production-style architecture.

```text
User Query
     │
     ▼
Query Processing (Expansion & Decomposition)
     │
     ▼
Hybrid Retrieval
 ├── BM25 Retrieval
 └── Dense Retrieval (FAISS)
     │
     ▼
RRF Fusion
     │
     ▼
Cross Encoder Reranking
     │
     ▼
Top Context Selection
     │
     ▼
LLM Generation (OpenRouter)
     │
     ▼
Guardrails Validation (Hallucination/Grounding check)
     │
     ▼
Response + Sources
```

---

## 📂 Project Structure

```text
AI-Production-RAG-System/
│
├── app/                  # Consolidated Backend Modules
│   ├── __init__.py
│   ├── config.py         # Settings, Logging, Latency tracking
│   ├── ingestion.py      # Loaders, Chunking, Vector Store (FAISS)
│   ├── retrieval.py      # BM25, Dense, RRF, Hybrid Retriever
│   ├── generation.py     # Prompting, LLM, Guardrails, RAG Pipeline
│   └── evaluation.py     # Metrics Logger, RAGAS Evaluator
│
├── frontend/             # React + Vite UI
│   ├── src/
│   │   ├── pages/        # Query, Documents, Evaluation, Guardrails, Metrics
│   │   ├── App.jsx
│   │   ├── api.js        # API Client 
│   │   └── index.css     # Design System
│   └── package.json
│
├── data/                 # Data storage
│   ├── documents/        # PDF & TXT knowledge base
│   └── vector_store/     # FAISS indexes
│
├── benchmark/
│   └── questions.json    # 100-question eval dataset
│
├── reports/              # Auto-generated logs and metrics
│
├── scripts/              # CLI runners for indexing, testing, evaluation
│
├── main.py               # FastAPI entry point
├── requirements.txt      # Python dependencies
├── Dockerfile            # Container configuration
└── .env                  # Environment Variables
```

---

## 🛠️ Getting Started

### 1. Prerequisites
- Python 3.11+
- Node.js v24+

### 2. Backend Setup
Create a `.env` file in the root directory and add your API key:
```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

Install dependencies and index the documents:
```bash
pip install -r requirements.txt
python scripts/build_index.py
```

Start the FastAPI server:
```bash
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```
The backend API will be available at `http://127.0.0.1:8000` (Swagger docs at `/docs`).

### 3. Frontend Setup
Open a new terminal window:
```bash
cd frontend
npm install
npm run dev
```
Access the UI at `http://localhost:5173`.

---

## 🛡️ Security Guardrails

The system includes strong input/output protection mechanisms:
- **Input Validation:** Rejects prompt injections (e.g., "ignore previous instructions"), system prompt leaks, code execution requests, and off-topic queries (e.g., "write a poem").
- **Output Validation:** Measures the strict grounding overlap between the LLM's response and the retrieved context. If hallucination keywords are detected or the grounding score is too low, the output is flagged.

---

## 📊 Monitoring & Evaluation

### Metrics
Each query tracks stage-by-stage latency (retrieval, reranking, generation) and logs it to `reports/metrics.csv` to ensure p95 latency stays under the 3-second SLA. The React dashboard visualizes this data.

### Automated Evaluation
Using the `benchmark/questions.json` dataset, the automated evaluator mimics RAGAS metrics:
- **Faithfulness:** Does the answer hallucinate?
- **Answer Relevancy:** Does the answer directly address the question?
- **Context Recall:** Did the retriever pull the correct keywords/concepts?

You can trigger this evaluation from the React UI under the "Evaluation" tab.

---

## 🎉 Conclusion

This project demonstrates the design and implementation of a production-style Retrieval-Augmented Generation (RAG) system. By combining semantic retrieval, Reciprocal Rank Fusion, Cross-Encoder reranking, rigorous guardrails, evaluation frameworks, and a modern React interface, the system provides accurate, explainable, and reliable answers while maintaining high performance.
