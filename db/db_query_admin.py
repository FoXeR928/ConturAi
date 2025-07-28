from sqlalchemy import select, update
from loguru import logger
from flask import flash

from db.db_create import Files, db


# Files
def add_file(file, filetype, file_name):
    session = db.session
    try:
        check_file = session.execute(
            select(Files.file_name).where(file_name=file_name)
        ).one_or_none
        logger.trace(f"Проверино на личие файл {file_name}")
    except Exception as err:
        logger.warning(f"Не проверить существование файла {file_name} Ошибка {err}")
    if check_file == None:
        try:
            create_file = Files(
                file_name=file_name, file_type=filetype, file=file.read()
            )
            session.add(create_file)
            session.commit()
            logger.success(f"Файл {file_name} добавлен в базу")
        except Exception as err:
            logger.error(f"Не удалось добавить файл {file_name} Ошибка {err}")
    else:
        try:
            session.execute(
                update(Files)
                .where(Files.file_name == file_name)
                .values(file_type=filetype, file=file.read())
            )
            session.commit
            logger.success(f"Файл {file_name} обнавлен в базе")
        except Exception as err:
            logger.error(f"Не удалось обновить файл {file_name} в базе Ошибка {err}")
