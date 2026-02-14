$ source /opt/venv/bin/activate && python tests/test_sentence_transformer.py 
tensor([[0.7646, 0.1414],
        [0.1355, 0.6000]])

# alternative method
$ uv run python tests/test_sentence_transformer.py 
tensor([[0.7646, 0.1414],
        [0.1355, 0.6000]])

# use "Qwen/Qwen3-Embedding-0.6B" as the default embedding model
pete@pop-os:/home/project/Step-3.5-Flash
$ grep -v ^# tests/test_sentence_transformer.py

from sentence_transformers import SentenceTransformer

model = SentenceTransformer("Qwen/Qwen3-Embedding-0.6B")


queries = [
    "What is the capital of China?",
    "Explain gravity",
]
documents = [
    "The capital of China is Beijing.",
    "Gravity is a force that attracts two bodies towards each other. It gives weight to physical objects and is responsible for the movement of planets around the sun.",
]

query_embeddings = model.encode(queries, prompt_name="query")
document_embeddings = model.encode(documents)

similarity = model.similarity(query_embeddings, document_embeddings)
print(similarity)

