from io import BytesIO

import pdfplumber
import pytesseract
from docx import Document as DocxDocument
from docx.table import Table
from docx.text.paragraph import Paragraph
from loguru import logger
from openpyxl import load_workbook
from pdf2image import convert_from_bytes

PDF_MIME = "application/pdf"
WORD_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
EXCEL_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


# ---------- helpers ----------

def _table_to_markdown(rows: list[list[str | None]]) -> str:
    """Преобразует 2D-список в markdown-таблицу."""
    if not rows:
        return ""
    # убираем полностью пустые строки
    rows = [r for r in rows if any(c and str(c).strip() for c in r)]
    if not rows:
        return ""
    # нормализуем ширину
    width = max(len(r) for r in rows)
    norm = []
    for r in rows:
        r = [(str(c).strip() if c is not None else "") for c in r]
        r += [""] * (width - len(r))
        norm.append(r)
    header = "| " + " | ".join(norm[0]) + " |"
    sep = "| " + " | ".join(["---"] * width) + " |"
    body = ["| " + " | ".join(r) + " |" for r in norm[1:]]
    return "\n".join([header, sep] + body)


def _iter_block_items(doc):
    """Итерирует параграфы и таблицы Word в исходном порядке."""
    from docx.oxml.text.paragraph import CT_P
    from docx.oxml.table import CT_Tbl

    parent = doc.element.body
    for child in parent.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, doc)
        elif isinstance(child, CT_Tbl):
            yield Table(child, doc)


# ---------- PDF ----------

def _pdf_text_pdfplumber(data: bytes) -> str:
    """Извлекает текст и таблицы через pdfplumber."""
    parts: list[str] = []
    with pdfplumber.open(BytesIO(data)) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            # сначала текст
            text = page.extract_text() or ""
            if text.strip():
                parts.append(f"--- Страница {page_num} ---\n{text.strip()}")
            # потом таблицы
            tables = page.extract_tables()
            for t_idx, table in enumerate(tables, 1):
                if not table:
                    continue
                md = _table_to_markdown(table)
                if md:
                    parts.append(f"--- Таблица {page_num}.{t_idx} ---\n{md}")
    return "\n\n".join(parts)


def _pdf_ocr(data: bytes) -> str:
    """OCR-фолбэк для сканированных PDF."""
    pages = convert_from_bytes(data, 300)
    parts = []
    for i, page in enumerate(pages, 1):
        text = pytesseract.image_to_string(page, lang="rus+eng")
        if text.strip():
            parts.append(f"--- Страница {i} (OCR) ---\n{text.strip()}")
    return "\n\n".join(parts)


def read_pdf(data: bytes) -> str:
    try:
        text = _pdf_text_pdfplumber(data)
        if text.strip() and len(text.strip()) > 50:
            logger.debug("PDF прочитан через pdfplumber (текст+таблицы)")
            return text
        logger.info("PDF без текстового слоя — переключаюсь на OCR")
        return _pdf_ocr(data)
    except Exception as err:
        logger.error(f"PDF: pdfplumber упал ({err}), пробую OCR")
        try:
            return _pdf_ocr(data)
        except Exception as ocr_err:
            logger.error(f"PDF: OCR тоже упал: {ocr_err}")
            return "Ошибка чтения файла"


# ---------- Word ----------

def read_word(data: bytes) -> str:
    try:
        doc = DocxDocument(BytesIO(data))
        parts: list[str] = []
        table_counter = 0

        for block in _iter_block_items(doc):
            if isinstance(block, Paragraph):
                t = block.text.strip()
                if t:
                    parts.append(t)
            elif isinstance(block, Table):
                table_counter += 1
                rows: list[list[str]] = []
                for row in block.rows:
                    rows.append([cell.text.strip() for cell in row.cells])
                md = _table_to_markdown(rows)
                if md:
                    parts.append(f"--- Таблица {table_counter} ---\n{md}")

        result = "\n\n".join(parts)
        logger.debug(f"Word прочитан: параграфы + {table_counter} таблиц")
        return result or "Документ не содержит текста"
    except Exception as err:
        logger.error(f"Word: ошибка чтения: {err}")
        return "Ошибка чтения файла"


# ---------- Excel ----------

def read_excel(data: bytes) -> str:
    try:
        wb = load_workbook(BytesIO(data), read_only=True, data_only=True)
        parts: list[str] = []
        for ws in wb.worksheets:
            parts.append(f"--- Лист: {ws.title} ---")
            rows: list[list[str]] = []
            for row in ws.iter_rows(values_only=True):
                vals = [str(c).strip() if c is not None else "" for c in row]
                if any(vals):
                    rows.append(vals)
            md = _table_to_markdown(rows)
            if md:
                parts.append(md)
        result = "\n\n".join(parts)
        logger.debug(f"Excel прочитан: {len(wb.worksheets)} листов")
        return result or "Документ не содержит данных"
    except Exception as err:
        logger.error(f"Excel: ошибка чтения: {err}")
        return "Ошибка чтения файла"


# ---------- dispatcher ----------

def parse_file(content_type: str, data: bytes) -> str | None:
    try:
        if content_type == PDF_MIME:
            return read_pdf(data)
        if content_type == WORD_MIME:
            return read_word(data)
        if content_type == EXCEL_MIME:
            return read_excel(data)
        return None
    except Exception as err:
        logger.error(f"Не удалось прочитать документ: {err}")
        return None