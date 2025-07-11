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

from config.config import (
    AI_MODEL_CHANK,
    RAG_COLLECTION,
    RAG_HOST,
    RAG_PORT_HTTP,
    RAG_PORT_GRPC,
    RAG_GRPC,
)


def optimizate_base(collection = RAG_COLLECTION):
    try:
        client.create_payload_index(
            collection_name=collection,
            field_name="source",
            field_schema=PayloadSchemaType.TEXT,
        )
        logger.debug('Произведена индексация по полю source')
    except Exception as err:
        logger.error(f'Не удалось индексировать по полям source Ошибка {err}')
    try:
        client.create_payload_index(
            collection_name=collection,
            field_name="text",
            field_schema=PayloadSchemaType.TEXT,
            tokenizer_type="word",
        )
        logger.debug('Произведена индексация по полю text')
    except Exception as err:
        logger.error(f'Не удалось индексировать по полям text Ошибка {err}')
    
        client.update_collection(
            collection_name=collection,
            hnsw_config=HnswConfigDiff(
                ef_consruct=256,
                m=16,
            ),
        )
        logger.debug('Произведена структуризация графов')
    except Exception as err:
        logger.error(f'Не удалось структуризировать графы Ошибка {err}')

try:
    model = SentenceTransformer(
        model_name_or_path=AI_MODEL_CHANK,
        device=(
            "cuda"
            if torch.cuda.is_available()
            else "mps" if torch.backends.mps.is_available() else "cpu"
        ),
    )
    logger.info('Инициализирована AI модель для генерации чанков')
except Exception as err:
    logger.critical(f'Не удалось инициализированть AI модель для генерации чанков Ошибка {err}')
    exit()

try:
    client = QdrantClient(
        host=RAG_HOST, port=RAG_PORT_HTTP, grpc_port=RAG_PORT_GRPC, prefer_grpc=RAG_GRPC
    )
    logger.info('Инициализирован клиент векторной базы')
except Exception as err:
    logger.critical(f'Не удалось инициализированть клиент векторной базы Ошибка {err}')
    exit()

try:
    check_rag_base=client.collection_exists(RAG_COLLECTION)
    logger.trace('Проверка коллекции в векторной базы прошла успешно')
except Exception as err:
    logger.critical(f'Не удалось проверить наличие коллекции в векторной базе Ошибка {err}')
    exit()

if not check_rag_base:
    try:
        client.recreate_collection(
            collection_name=RAG_COLLECTION,
            vectors_config=VectorParams(size=1024, distance=Distance.COSINE, on_disk=True),
            optimizers_config=OptimizersConfigDiff(
                indexing_threshold=20000, memmap_threshold=20000
            ),
        )
        logger.info(f'Создана коллекция {RAG_COLLECTION} в векторной базе')
    except Exception as err:
        logger.critical(f'Не удалось создать коллекцию в векторной базе Ошибка {err}')
        exit()
else:
    logger.debug(f'Коллекция {RAG_COLLECTION} уже есть в векторной базе')