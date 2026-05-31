"""
Data ingestion module.
Combines: document loader, chunking service, embeddings, vector store.
"""

import os
import pickle
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.config import settings, logger


# ═══════════════════════════════════════════════════════════════
# EMBEDDING MODEL (singleton)
# ═══════════════════════════════════════════════════════════════

embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)


# ═══════════════════════════════════════════════════════════════
# DOCUMENT LOADER
# ═══════════════════════════════════════════════════════════════

class DocumentLoader:
    def __init__(self, data_path):
        self.data_path = data_path

    def load_documents(self):
        import pypdf
        documents = []
        if not os.path.exists(self.data_path):
            return documents

        for file_name in os.listdir(self.data_path):
            file_path = os.path.join(self.data_path, file_name)
            if not os.path.isfile(file_path):
                continue
                
            if file_name.endswith(".txt"):
                with open(file_path, "r", encoding="utf-8") as file:
                    text = file.read()
                    documents.append({
                        "content": text,
                        "source": file_name
                    })
            elif file_name.endswith(".pdf"):
                try:
                    with open(file_path, "rb") as file:
                        reader = pypdf.PdfReader(file)
                        text = "\n".join(page.extract_text() for page in reader.pages if page.extract_text())
                        documents.append({
                            "content": text,
                            "source": file_name
                        })
                except Exception as e:
                    logger.error(f"Error reading PDF {file_name}: {e}")
        return documents


# ═══════════════════════════════════════════════════════════════
# CHUNKING SERVICE
# ═══════════════════════════════════════════════════════════════

class ChunkingService:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP
        )

    def create_chunks(self, documents):
        chunks = []
        chunk_id = 0
        for doc in documents:
            split_chunks = self.text_splitter.split_text(doc["content"])
            for chunk in split_chunks:
                chunks.append({
                    "content": chunk,
                    "source": doc["source"],
                    "chunk_id": chunk_id
                })
                chunk_id += 1
        return chunks


# ═══════════════════════════════════════════════════════════════
# VECTOR STORE (FAISS)
# ═══════════════════════════════════════════════════════════════

class VectorStore:
    def __init__(self):
        self.dimension = 384
        self.index = faiss.IndexFlatL2(self.dimension)
        self.documents = []

    def add_documents(self, chunks):
        texts = [chunk["content"] for chunk in chunks]
        embeddings = embedding_model.encode(texts)
        self.index.add(np.array(embeddings).astype("float32"))
        self.documents.extend(chunks)

    def save(self):
        os.makedirs(settings.VECTOR_DB_PATH, exist_ok=True)
        faiss.write_index(self.index, f"{settings.VECTOR_DB_PATH}/faiss.index")
        with open(f"{settings.VECTOR_DB_PATH}/documents.pkl", "wb") as f:
            pickle.dump(self.documents, f)

    def load(self):
        self.index = faiss.read_index(f"{settings.VECTOR_DB_PATH}/faiss.index")
        with open(f"{settings.VECTOR_DB_PATH}/documents.pkl", "rb") as f:
            self.documents = pickle.load(f)

    def search(self, query, top_k=5):
        query_embedding = embedding_model.encode([query])
        distances, indices = self.index.search(
            np.array(query_embedding).astype("float32"), top_k
        )
        results = []
        for idx in indices[0]:
            if 0 <= idx < len(self.documents):
                results.append({
                    "content": self.documents[idx]["content"],
                    "source": self.documents[idx]["source"],
                    "chunk_id": self.documents[idx]["chunk_id"]
                })
        return results
