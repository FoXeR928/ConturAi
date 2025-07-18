# host
PORT = 7000
HOST = "0.0.0.0"
SKEY = "sekretkey"
DEBUG = True

# log
LOG_DAYS = 10
LOG_SIZE = "256 MB"

# db
SQL_PATH = "sqlite:///../db/db.db"
SQL_PATH_DEV = "sqlite:///../db/db_dev.db"
AI_LOGIN = "system"
AI_NAME = ""
if AI_NAME == None:
    AI_NAME = "Раги"

# AI
AI_MODEL_CHANK = "./ai_chat/models/sbert_large_nlu_ru"
AI_MODEL = "ilyagusev/saiga_llama3"
RAG_COLLECTION = "docs"
RAG_HOST = "localhost"
RAG_PORT_HTTP = 6333
RAG_PORT_GRPC = 6334
RAG_GRPC = True
