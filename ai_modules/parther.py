import pytesseract
from pdf2image import convert_from_bytes
from docx import Document
from openpyxl import load_workbook
from pymorphy3 import MorphAnalyzer
from re import sub
from langchain_text_splitters import RecursiveCharacterTextSplitter
from loguru import logger

from db_modules.db_query_config import get_config


def read_pdf(file: bytes):
    try:
        pages = convert_from_bytes(file.read(), 600)
        result = str()
        for page in pages:
            text = pytesseract.image_to_string(page, lang="rus")
            result += text + " "
        logger.debug("Файл прочитан")
    except Exception as err:
        result = None
        logger.error(f"Не удалось прочитать документ Ошибка {err}")
    return result


def read_word(file: bytes):
    try:
        read = Document(file)
        result = str()
        if read.paragraphs:
            for paragraph in read.paragraphs:
                result += paragraph.text
        logger.debug("Файл прочитан")
    except Exception as err:
        result = None
        logger.error(f"Не удалось прочитать документ Ошибка {err}")
    return result


def read_excel(file: bytes):
    try:
        dataTable = load_workbook(file)
        result = str()
        for sheet_name in dataTable.worksheets:
            sheet = dataTable[sheet_name.title]
            for row in sheet.iter_rows():
                for cell in row:
                    result += f"{cell.value}. "
        logger.debug("Файл прочитан")
    except Exception as err:
        result = None
        logger.error(f"Не удалось прочитать документ Ошибка {err}")
    return result


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


def check_file_type(file_type: str, file_dytes: bytes):
    if file_type == get_config("pdf"):
        file_type = "pdf"
        file_text = read_pdf(file_dytes)
    elif file_type == get_config("word"):
        file_type = "docx"
        file_text = read_word(file_dytes)
    elif file_type == get_config("excel"):
        file_type = "xlsx"
        file_text = read_excel(file_dytes)
    logger.debug("Файл прочитан")
    return file_text
