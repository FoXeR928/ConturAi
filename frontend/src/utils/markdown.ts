/**
 * Очищает Markdown-текст, пришедший от LLM, перед отправкой в ReactMarkdown.
 * Решает две частые проблемы:
 * 1. Модель оборачивает весь ответ в ```markdown ... ```.
 * 2. Модель не ставит пустую строку перед таблицей, из-за чего таблица не рендерится.
 */
export function cleanMarkdown(text: string): string {
  if (!text) return '';

  let cleaned = text;

  // ==========================================================================
  // ШАГ 1: УДАЛЕНИЕ ОБЕРТКИ ```markdown
  // ==========================================================================
  // Убираем ```markdown или ```md ТОЛЬКО в самом начале текста
  cleaned = cleaned.replace(/^```(?:markdown|md)?\s*\n?/i, '');
  
  // Убираем закрывающие ``` ТОЛЬКО в самом конце текста
  cleaned = cleaned.replace(/\n?```\s*$/, '');


  // ==========================================================================
  // ШАГ 2: ФОРМАТИРОВАНИЕ ТАБЛИЦ
  // ==========================================================================
  // Markdown-таблицы требуют пустой строки перед началом.
  // Проходим по строкам и добавляем пустую строку, если таблица слиплась с текстом.
  const lines = cleaned.split('\n');
  const resultLines: string[] = [];

  for (let i = 0; i < lines.length; i++) {
    const currentLine = lines[i];
    const prevLine = resultLines[resultLines.length - 1];

    // Проверяем, является ли текущая строка началом таблицы.
    // Начало таблицы — это строка, содержащая '|'.
    const isTableRow = currentLine.includes('|');
    
    // Если это таблица, и предыдущая строка не пустая, добавляем пустую строку
    if (isTableRow && prevLine !== undefined && prevLine.trim() !== '') {
      // Проверяем, что это именно начало таблицы, а не продолжение
      const isPrevTableRow = prevLine.includes('|');
      if (!isPrevTableRow) {
        resultLines.push(''); // Добавляем пустую строку
      }
    }

    resultLines.push(currentLine);
  }

  cleaned = resultLines.join('\n');

  // Убираем лишние пустые строки в начале и конце
  return cleaned.trim();
}