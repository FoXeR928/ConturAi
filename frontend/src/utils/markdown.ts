export function cleanMarkdown(text: string): string {
  if (!text) return '';
  
  let cleaned = text;
  
  // 1. Убираем ```markdown в начале и ``` в конце
  cleaned = cleaned.replace(/```(?:markdown|md)?\s*\n?/gi, '');
  cleaned = cleaned.replace(/```/g, '');
  
  // 2. Добавляем пустую строку перед таблицей, ТОЛЬКО если перед ней нет символа "|"
  // Регулярка ищет символ (не перенос строки и не |), затем перенос строки, затем начало таблицы
  cleaned = cleaned.replace(/([^\n|])\n(\|.*\|)/g, '$1\n\n$2');
  
  return cleaned.trim();
}