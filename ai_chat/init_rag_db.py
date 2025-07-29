from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams,
    Distance,
    OptimizersConfigDiff,
    PayloadSchemaType,
    HnswConfigDiff,
)
from sentence_transformers import SentenceTransformer
import torch
from loguru import logger

from db.db_query_config import get_config_ai


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


try:
    model_chunk = get_config_ai("model_chunk")
    model = SentenceTransformer(
        model_name_or_path=model_chunk,
        device=(
            "cuda"
            if torch.cuda.is_available()
            else "mps" if torch.backends.mps.is_available() else "cpu"
        ),
    )
    logger.debug("Инициализирована AI модель для генерации чанков")
except Exception as err:
    logger.critical(
        f"Не удалось инициализированть AI модель для генерации чанков Ошибка {err}"
    )
    exit()

try:
    rag_host = get_config_ai("rag_host")
    rag_port_http = get_config_ai("rag_port_http")
    rag_port_grpc = get_config_ai("rag_port_grpc")
    rag_grpc = get_config_ai("rag_grpc")
    rag_collection = get_config_ai("collection")
    client = QdrantClient(
        host=rag_host, port=rag_port_http, grpc_port=rag_port_grpc, prefer_grpc=rag_grpc
    )
    logger.debug("Инициализирован клиент векторной базы")
except Exception as err:
    logger.critical(f"Не удалось инициализированть клиент векторной базы Ошибка {err}")
    exit()

try:
    check_rag_base = client.collection_exists(rag_collection)
    logger.trace("Проверка коллекции в векторной базы прошла успешно")
except Exception as err:
    logger.critical(
        f"Не удалось проверить наличие коллекции в векторной базе Ошибка {err}"
    )
    exit()

if not check_rag_base:
    try:
        client.recreate_collection(
            collection_name=rag_collection,
            vectors_config=VectorParams(
                size=1024, distance=Distance.COSINE, on_disk=True
            ),
            optimizers_config=OptimizersConfigDiff(
                indexing_threshold=20000, memmap_threshold=20000
            ),
        )
        logger.info(f"Создана коллекция {rag_collection} в векторной базе")
    except Exception as err:
        logger.critical(f"Не удалось создать коллекцию в векторной базе Ошибка {err}")
        exit()
else:
    logger.debug(f"Коллекция {rag_collection} уже есть в векторной базе")
