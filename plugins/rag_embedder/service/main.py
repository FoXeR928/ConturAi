from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer, CrossEncoder
import os

app = FastAPI()

# Загружаем модели в память один раз при старте
EMBEDDING_PATH = os.environ.get("EMBEDDING_MODEL_PATH", "/models/multilingual-e5-large")
RERANKER_PATH = os.environ.get("RERANKER_MODEL_PATH", "/models/bge-reranker-v2-m3")

print(f"Загрузка модели эмбеддингов: {EMBEDDING_PATH}")
model = SentenceTransformer(EMBEDDING_PATH, device="cpu")

print(f"Загрузка реранкера: {RERANKER_PATH}")
reranker = CrossEncoder(RERANKER_PATH, device="cpu")

class EmbedRequest(BaseModel):
    texts: list[str]

class RerankRequest(BaseModel):
    query: str
    documents: list[str]

@app.post("/embed")
def embed_texts(req: EmbedRequest):
    vectors = model.encode(req.texts, normalize_embeddings=True)
    return {"vectors": [v.tolist() for v in vectors]}

@app.post("/rerank")
def rerank(req: RerankRequest):
    pairs = [[req.query, doc] for doc in req.documents]
    scores = reranker.predict(pairs)
    return {"scores": scores.tolist()}

@app.get("/health")
def health():
    return {"status": "ok"}