import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { PromptsPanel } from '../src/features/admin/PromptsPanel';

vi.mock('../src/api/prompts', () => ({
  promptsApi: {
    getPrompts: vi.fn(),
    updatePrompt: vi.fn(),
  },
}));

import { promptsApi } from '../src/api/prompts';
const mocked = vi.mocked(promptsApi);

const PROMPTS = [
  { key: 'ai_name', value: 'Контур', description: 'Имя' },
  { key: 'system_prompt', value: 'Ты ...', description: 'Системный' },
];

describe('PromptsPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocked.getPrompts.mockResolvedValue({ prompts: PROMPTS } as any);
  });

  it('рендерит ai_name как input, а system_prompt как textarea', async () => {
    render(<PromptsPanel />);
    
    // Ждем загрузки
    await screen.findByDisplayValue('Контур');

    // Проверяем, что для ai_name использован <input> (у него нет атрибута rows)
    const input = screen.getByDisplayValue('Контур');
    expect(input.tagName).toBe('INPUT');

    // Проверяем, что для system_prompt использован <textarea>
    const textarea = screen.getByDisplayValue('Ты ...');
    expect(textarea.tagName).toBe('TEXTAREA');
  });
});