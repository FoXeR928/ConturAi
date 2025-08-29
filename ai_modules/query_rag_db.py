from uuid import uuid4
from qdrant_client.http.models import PointStruct, PayloadSchemaType, HnswConfigDiff
from loguru import logger
from pymorphy3 import MorphAnalyzer
from re import sub
from langchain_text_splitters import RecursiveCharacterTextSplitter

from db_modules.db_query_config import get_config_ai
from ai_modules.init_rag_db import model, client

def normalize_text(text: str):
    try:
        morphanaliz = MorphAnalyzer()
        text = sub(pattern=r"[^\w\s]", repl="", string=text.lower())
        result = " ".join(morphanaliz.normal_forms(word)[0] for word in text.split())
        logger.debug("Текст нормализирован")
    except Exception as err:
        logger.error(f"Не удалось нормализировать текст Ошибка {err}")
        result = False
    return result


def chunk_create(text: str):
    try:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100,
            separators=["\n\n", "\n", "(?<=\.)!", " "],
            length_function=len,
        )
        result = splitter.split_text(text=text)
        logger.debug("Сгенерированы чанки")
    except Exception as err:
        logger.error(f"Не удалось сгенерировать чанки Ошибка {err}")
        result = False
    return result

def optimizate_base():
    collection = get_config_ai("collection")
    try:
        client.create_payload_index(
            collection_name=collection,
            field_name="source",
            field_schema=PayloadSchemaType.TEXT,
        )
        logger.debug("Произведена индексация по полю source")
    except Exception as err:
        logger.error(f"Не удалось индексировать по полям source Ошибка {err}")
    try:
        client.create_payload_index(
            collection_name=collection,
            field_name="text",
            field_schema=PayloadSchemaType.TEXT,
            tokenizer_type="word",
        )
        logger.debug("Произведена индексация по полю text")
    except Exception as err:
        logger.error(f"Не удалось индексировать по полям text Ошибка {err}")

        client.update_collection(
            collection_name=collection,
            hnsw_config=HnswConfigDiff(
                ef_consruct=256,
                m=16,
            ),
        )
        logger.debug("Произведена структуризация графов")
    except Exception as err:
        logger.error(f"Не удалось структуризировать графы Ошибка {err}")


def add_docs_rquery(doc_name:str, doc_text:str):
    chunks=chunk_create(text=doc_text)
    normal_text=normalize_text(text=doc_text)
    batch_size=get_config_ai(name="batch_size") or 256
    if chunks!=False and normal_text!=False:
        rag_collection = get_config_ai("collection")
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
                                "text_norm": normal_text,
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
            raise {
                "result": False,
                "message": "Ошибка сервера не удалось сгенерировать данные для загрузки RAG базу",
                "category": "error",
                "cod": 500,
            }
        try:
            client.upsert(collection_name=rag_collection, points=points, wait=False)
            result={
                "result": True,
                "message": "Документ загружен в RAG базу",
                "category": "success",
                "cod": 201,
            }
            logger.success(f"В RAG базу добавлен документ {doc_name}")
        except Exception as err:
            logger.error(
                f"Не удалось добавить документ {doc_name} в RAG базу Ошибка: {err}"
            )
            result={
                "result": False,
                "message": "Ошибка сервера не загружен документ в RAG базу",
                "category": "error",
                "cod": 500,
            }
    else:
        result={
                "result": False,
                "message": "Ошибка сервера не удалось подготовить текст для выгрузки",
                "category": "error",
                "cod": 500,
            }
    return result


def search_docs_rquery(query:str):
    try:
        rag_collection = get_config_ai("collection")
        query_embedding = model.encode(query).tolist()
        result_search = client.search(
            collection_name=rag_collection, query_vector=query_embedding, limit=get_config_ai(name="search_rag")
        )
        result = str()
        for hit in result_search:
            result += hit.payload["text"][:200]
        logger.trace(f"Выполнен поиск по RAG базе")
    except Exception as err:
        logger.error(f"Не удалось выполнить поиск RAG базе Ошибка: {err}")
        result = None
    return result
