from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams,
    Distance,
    OptimizersConfigDiff,
)
from sentence_transformers import SentenceTransformer
import torch
from loguru import logger

from db_modules.db_query_config import get_config_ai


def init_ai_chunk():
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
        return model
    except Exception as err:
        logger.critical(
            f"Не удалось инициализированть AI модель для генерации чанков Ошибка {err}"
        )
        return False


def init_rag():
    try:
        rag_host = get_config_ai("rag_host")
        rag_port_http = get_config_ai("rag_port_http")
        rag_port_grpc = get_config_ai("rag_port_grpc")
        rag_grpc = bool(get_config_ai("rag_grpc"))
        rag_collection = get_config_ai("collection")
        client = QdrantClient(
            host=rag_host,
            port=rag_port_http,
            grpc_port=rag_port_grpc,
            prefer_grpc=rag_grpc,
        )
        try:
            check_rag_base = client.collection_exists(rag_collection)
            logger.trace("Проверка коллекции в векторной базы прошла успешно")
        except Exception as err:
            logger.critical(
                f"Не удалось проверить наличие коллекции в векторной базе Ошибка {err}"
            )
            return False
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
                return client
            except Exception as err:
                logger.critical(
                    f"Не удалось создать коллекцию в векторной базе Ошибка {err}"
                )
                return False
        else:
            logger.debug(f"Коллекция {rag_collection} уже есть в векторной базе")
            logger.debug("Инициализирован клиент векторной базы")
            return client
    except Exception as err:
        logger.critical(
            f"Не удалось инициализированть клиент векторной базы Ошибка {err}"
        )
        return False


model = init_ai_chunk()
client = init_rag()
