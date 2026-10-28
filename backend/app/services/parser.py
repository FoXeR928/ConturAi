from io import BytesIO

import pdfplumber
import pytesseract
from docx import Document as DocxDocument
from docx.table import Table
from docx.text.paragraph import Paragraph
from loguru import logger
from openpyxl import load_workbook
from pdf2image import convert_from_bytes

# ==============================================================================
# БЛОК 1: КОНСТАНТЫ MIME-ТИПОВ
# ==============================================================================

# Браузеры при загрузке файлов присылают разные MIME-типы. 
# Здесь мы собираем все возможные варианты для каждого формата, 
# чтобы точно определить, каким парсером обрабатывать файл.

PDF_MIMES = {"application/pdf", "application/x-pdf"}

WORD_MIMES = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "application/octet-stream",  # Некоторые браузеры шлют это для .docx
}

EXCEL_MIMES = {
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
}

TEXT_MIMES = {
    "text/plain",
    "text/markdown",
    "text/x-markdown",
    "application/octet-stream",  # Fallback для .md и .txt
}


# ==============================================================================
# БЛОК 2: ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (ТАБЛИЦЫ И WORD)
# ==============================================================================

def _table_to_markdown(rows: list[list[str | None]]) -> str:
    """
    Преобразует двумерный массив (список строк) в Markdown-таблицу.
    Нейросети (LLM) отлично понимают таблицы в формате Markdown, поэтому
    мы конвертируем все таблицы из PDF/DOCX/XLSX в этот формат.
    """
    if not rows:
        return ""
        
    # Убираем пустые строки (где все ячейки пустые)
    rows = [r for r in rows if any(c and str(c).strip() for c in r)]
    if not rows:
        return ""
        
    # Выравниваем таблицу: находим самую широкую строку и добиваем остальные пустыми ячейками
    width = max(len(r) for r in rows)
    norm = []
    for r in rows:
        r = [(str(c).strip() if c is not None else "") for c in r]
        r += [""] * (width - len(r))
        norm.append(r)
        
    # Формируем Markdown: Заголовок, Разделитель, Тело
    header = "| " + " | ".join(norm[0]) + " |"
    sep = "| " + " | ".join(["---"] * width) + " |"
    body = ["| " + " | ".join(r) + " |" for r in norm[1:]]
    
    return "\n".join([header, sep] + body)


def _iter_block_items(doc):
    """
    Итератор для Word-документа.
    Позволяет обходить параграфы и таблицы СТРОГО в том порядке, 
    в котором они находятся в документе (сверху вниз).
    Стандартный doc.paragraphs не видит таблицы, а doc.tables не видит параграфы.
    """
    from docx.oxml.text.paragraph import CT_P
    from docx.oxml.table import CT_Tbl

    parent = doc.element.body
    for child in parent.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, doc)
        elif isinstance(child, CT_Tbl):
            yield Table(child, doc)


# ==============================================================================
# БЛОК 3: ПАРСИНГ PDF (ТЕКСТ И OCR)
# ==============================================================================

def _pdf_text_pdfplumber(data: bytes) -> str:
    """Пытается извлечь текстовый слой из PDF с помощью библиотеки pdfplumber."""
    parts: list[str] = []
    with pdfplumber.open(BytesIO(data)) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            # Извлекаем текст
            text = page.extract_text() or ""
            if text.strip():
                parts.append(f"--- Страница {page_num} ---\n{text.strip()}")
            # Извлекаем таблицы (если они есть на странице)
            for t_idx, table in enumerate(page.extract_tables(), 1):
                if not table:
                    continue
                md = _table_to_markdown(table)
                if md:
                    parts.append(f"--- Таблица {page_num}.{t_idx} ---\n{md}")
    return "\n\n".join(parts)


def _pdf_ocr(data: bytes) -> str:
    """Резервный метод: рендерит страницы PDF в картинки и распознает текст через Tesseract OCR."""
    pages = convert_from_bytes(data, 300) # 300 DPI — оптимально для OCR
    parts = []
    for i, page in enumerate(pages, 1):
        # Поддерживаем русский и английский языки
        text = pytesseract.image_to_string(page, lang="rus+eng")
        if text.strip():
            parts.append(f"--- Страница {i} (OCR) ---\n{text.strip()}")
    return "\n\n".join(parts)


def read_pdf(data: bytes) -> str:
    """
    Главный метод чтения PDF.
    Сначала пытается извлечь "цифровой" текст. Если текста нет (или он слишком короткий,
    что значит, что это скан), запускает тяжелый OCR.
    """
    try:
        text = _pdf_text_pdfplumber(data)
        # Если текста больше 50 символов, считаем, что pdfplumber справился
        if text.strip() and len(text.strip()) > 50:
            logger.debug("PDF прочитан через pdfplumber")
            return text
            
        logger.info("PDF без текста (скан) — запускаю OCR")
        return _pdf_ocr(data)
    except Exception as err:
        logger.error(f"PDF: pdfplumber упал ({err}), пробую OCR")
        try:
            return _pdf_ocr(data)
        except Exception as ocr_err:
            logger.error(f"PDF: OCR тоже упал: {ocr_err}")
            return "Ошибка чтения файла"


# ==============================================================================
# БЛОК 4: ПАРСИНГ WORD (DOCX)
# ==============================================================================

def read_word(data: bytes) -> str:
    """Извлекает текст и таблицы из документа Word, сохраняя их порядок."""
    try:
        doc = DocxDocument(BytesIO(data))
        parts: list[str] = []
        table_counter = 0

        # Используем кастомный итератор для правильного порядка
        for block in _iter_block_items(doc):
            if isinstance(block, Paragraph):
                t = block.text.strip()
                if t:
                    parts.append(t)
            elif isinstance(block, Table):
                table_counter += 1
                # Извлекаем данные из таблицы Word
                rows = [[cell.text.strip() for cell in row.cells] for row in block.rows]
                md = _table_to_markdown(rows)
                if md:
                    parts.append(f"--- Таблица {table_counter} ---\n{md}")

        result = "\n\n".join(parts)
        logger.debug(f"Word прочитан: {table_counter} таблиц")
        return result or "Документ не содержит текста"
    except Exception as err:
        logger.error(f"Word: {err}")
        return "Ошибка чтения файла"


# ==============================================================================
# БЛОК 5: ПАРСИНГ EXCEL (XLSX)
# ==============================================================================

def read_excel(data: bytes) -> str:
    """Извлекает данные из всех листов Excel и конвертирует их в Markdown."""
    try:
        # read_only=True экономит память для больших файлов.
        # data_only=True заставляет возвращать значения ячеек, а не формулы (например, 2, а не =A1+B1).
        wb = load_workbook(BytesIO(data), read_only=True, data_only=True)
        parts: list[str] = []
        
        for ws in wb.worksheets:
            parts.append(f"--- Лист: {ws.title} ---")
            rows: list[list[str]] = []
            for row in ws.iter_rows(values_only=True):
                vals = [str(c).strip() if c is not None else "" for c in row]
                if any(vals): # Пропускаем полностью пустые строки
                    rows.append(vals)
            md = _table_to_markdown(rows)
            if md:
                parts.append(md)
                
        result = "\n\n".join(parts)
        logger.debug(f"Excel прочитан: {len(wb.worksheets)} листов")
        return result or "Документ не содержит данных"
    except Exception as err:
        logger.error(f"Excel: {err}")
        return "Ошибка чтения файла"


# ==============================================================================
# БЛОК 6: ПАРСИНГ ТЕКСТА (TXT, MD, CSV)
# ==============================================================================

def read_text(data: bytes) -> str:
    """Простое чтение текстовых файлов с поддержкой популярных кодировок."""
    # Пробуем UTF-8 (стандарт), затем UTF-8 с BOM (часто бывает на Windows), затем Windows-1251
    for encoding in ("utf-8", "utf-8-sig", "cp1251"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    logger.error("Не удалось декодировать текстовый файл")
    return "Ошибка чтения файла"


# ==============================================================================
# БЛОК 7: ГЛАВНЫЙ ДИСПЕТЧЕР (ВЫБОР ПАРСЕРА)
# ==============================================================================

def parse_file(content_type: str, data: bytes, filename: str = "") -> str | None:
    """
    Точка входа для парсинга. 
    Определяет тип файла по MIME-типу (предпочтительно) или по расширению (как fallback),
    и вызывает соответствующую функцию (read_pdf, read_word и т.д.).
    Возвращает извлеченный текст или None, если формат не поддерживается.
    """
    logger.debug(
        f"parse_file: content_type={content_type!r}, filename={filename!r}, "
        f"size={len(data)}"
    )

    # Очищаем MIME-тип от возможных параметров (например, "text/plain; charset=utf-8")
    ct = (content_type or "").lower().split(";")[0].strip()
    name = (filename or "").lower()

    try:
        # 1. Сначала пытаемся определить по MIME-типу
        if ct in PDF_MIMES:
            return read_pdf(data)
        if ct in WORD_MIMES:
            return read_word(data)
        if ct in EXCEL_MIMES:
            return read_excel(data)
        if ct in TEXT_MIMES:
            return read_text(data)

        # 2. Если MIME-тип не сработал (например, application/octet-stream), смотрим на расширение
        if name.endswith(".pdf"):
            return read_pdf(data)
        if name.endswith((".docx", ".doc")):
            return read_word(data)
        if name.endswith((".xlsx", ".xls")):
            return read_excel(data)
        if name.endswith((".txt", ".md", ".markdown", ".csv")):
            return read_text(data)

        logger.warning(f"Формат не поддерживается: {ct} / {name}")
        return None
    except Exception as err:
        logger.error(f"Не удалось прочитать документ: {err}")
        return None