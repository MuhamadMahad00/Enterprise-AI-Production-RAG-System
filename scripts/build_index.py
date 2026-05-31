from app.ingestion import DocumentLoader, ChunkingService, VectorStore

loader = DocumentLoader("data/documents")
documents = loader.load_documents()
print(f"Loaded Documents: {len(documents)}")

chunker = ChunkingService()
chunks = chunker.create_chunks(documents)
print(f"Generated Chunks: {len(chunks)}")

vector_store = VectorStore()
vector_store.add_documents(chunks)
vector_store.save()
print("Vector index created successfully.")
