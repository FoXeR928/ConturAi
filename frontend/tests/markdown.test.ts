import { describe, it, expect } from 'vitest';
import { cleanMarkdown } from '../src/utils/markdown';

describe('cleanMarkdown', () => {
  it('убирает ```markdown обёртку', () => {
    expect(cleanMarkdown('```markdown\n# Hi\n```')).toBe('# Hi');
    expect(cleanMarkdown('```md\n**bold**\n```')).toBe('**bold**');
  });

  it('добавляет пустую строку перед слипшейся таблицей', () => {
    const input = 'Ответ:\n| a | b |\n| --- | --- |\n| 1 | 2 |';
    const out = cleanMarkdown(input);
    expect(out).toContain('Ответ:\n\n| a | b |');
  });

  it('не вставляет лишнюю пустую строку, если таблица уже отделена', () => {
    const input = 'Текст\n\n| a |\n| --- |\n| 1 |';
    const out = cleanMarkdown(input);
    expect(out).not.toMatch(/\n\n\n\|/);
  });

  it('возвращает пустую строку для пустого входа', () => {
    expect(cleanMarkdown('')).toBe('');
  });

  it('не меняет обычный текст', () => {
    expect(cleanMarkdown('Привет, мир!')).toBe('Привет, мир!');
  });
});