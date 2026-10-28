from app.services.parser import _table_to_markdown
from app.rag import split_text

def test_table_to_markdown():
    rows = [
        ["Имя", "Возраст", "Город"],
        ["Иван", "25", "Москва"],
        ["Анна", "30", "Санкт-Петербург"]
    ]
    md = _table_to_markdown(rows)
    
    assert "| Имя | Возраст | Город |" in md
    assert "| --- | --- | --- |" in md
    assert "| Иван | 25 | Москва |" in md
    assert "\n" in md

def test_split_text():
    text = "А" * 500 + "\n\n" + "Б" * 500
    chunks = split_text(text, chunk_size=600, chunk_overlap=50)
    
    assert len(chunks) == 2
    assert chunks[0].startswith("А")
    assert chunks[1].startswith("Б")