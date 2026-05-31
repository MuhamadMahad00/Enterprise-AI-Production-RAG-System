from pprint import pprint
from app.evaluation import RAGEvaluator

evaluator = RAGEvaluator()
report = evaluator.evaluate()
print("\nEVALUATION REPORT:\n")
pprint({k: v for k, v in report.items() if k != "results"})