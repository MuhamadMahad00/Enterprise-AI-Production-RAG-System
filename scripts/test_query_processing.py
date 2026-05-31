from app.retrieval import QueryProcessor

qp = QueryProcessor()
result = qp.process_query("What are office timings and leave policy?")
print("Processed queries:", result)