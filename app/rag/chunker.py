import re

from langchain_text_splitters import RecursiveCharacterTextSplitter
from pymorphy3 import MorphAnalyzer

from app.core.config import settings

_morph = MorphAnalyzer()


def normalize_text(text: str) -> str:
    cleaned = re.sub(r"[^\w\s]", "", text.lower())
    return " ".join(_morph.normal_forms(w)[0] for w in cleaned.split())


def split_text(text: str) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.rag_chunk_size,
        chunk_overlap=settings.rag_chunk_overlap,
        separators=["\n\n", "\n", "(?<=\\.)!", " "],
        length_function=len,
    )
    return splitter.split_text(text)