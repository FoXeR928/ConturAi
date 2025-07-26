from uuid import uuid4
from qdrant_client.http.models import PointStruct
from loguru import logger

from ai_chat.init_rag_db import model, client
from db.db_query_config import get_config


def add_docs(
    chunks, doc_name, norm_text, batch_size=256
):
    rag_collection=get_config('rag_collection')
    points = list()
    try:
        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i : i + batch_size]
            embedding = model.encode(batch_chunks, convert_to_tensor=True)
            for j, (chunk, embedding) in enumerate(zip(batch_chunks, embedding)):
                points.append(
                    PointStruct(
                        id=str(uuid4()),
                        vector=embedding.tolist(),
                        payload={
                            "text": chunk,
                            "text_norm": norm_text,
                            "source": doc_name,
                            "page": i + j + 1,
                            "language": "ru",
                        },
                    )
                )
        logger.trace(
            f"Сформированы данные по документу {doc_name} для выгрузки в RAG базу"
        )
    except Exception as err:
        logger.error(
            f"Не удалось сгенерировать данные для загрузки в RAG базу Ошибка: {err}"
        )
    try:
        client.upsert(collection_name=rag_collection, points=points, wait=False)
        logger.success(f"В RAG базу добавлен документ {doc_name}")
    except Exception as err:
        logger.error(
            f"Не удалось добавить документ {doc_name} в RAG базу Ошибка: {err}"
        )


def search_docs(query, limit=5):
    try:
        rag_collection=get_config('rag_collection')
        query_embedding = model.encode(query).tolist()
        result_search = client.search(
            collection_name=rag_collection, query_vector=query_embedding, limit=limit
        )
        result = str()
        for hit in result_search:
            result += hit.payload["text"][:200]
        logger.trace(f"Выполнен поиск по RAG базе")
    except Exception as err:
        logger.error(f"Не удалось выполнить поиск RAG базе Ошибка: {err}")
        result = None
    return result
