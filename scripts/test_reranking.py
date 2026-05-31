from app.generation import CrossEncoderReranker

reranker = CrossEncoderReranker()
docs = ["Office hours are 9 to 5", "Leave policy allows 20 days", "The sky is blue"]
ranked = reranker.rerank("What are office timings?", docs)
for r in ranked:
    print(r)