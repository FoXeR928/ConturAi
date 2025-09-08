import pytesseract
from pdf2image import convert_from_bytes
from docx import Document
from openpyxl import load_workbook
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
        result = "Ошибка чтения файла"
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
        result = "Ошибка чтения файла"
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
        result = "Ошибка чтения файла"
        logger.error(f"Не удалось прочитать документ Ошибка {err}")
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
    else:
        file_text=None
    return file_text
