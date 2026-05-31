from app.retrieval import HybridRetriever

retriever = HybridRetriever()
results = retriever.retrieve("What are office timings?")
for r in results:
    print(f"[{r['source']}] {r['content'][:100]}...")