from app.generation import RAGPipeline

pipeline = RAGPipeline()
result = pipeline.run("What are office timings?")
print("Answer:", result["answer"])
print("Latency:", result["latency"])
print("Breakdown:", result["latency_breakdown"])