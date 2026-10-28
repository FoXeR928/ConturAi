import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { LlmConfigsPanel } from '../src/features/admin/LlmConfigsPanel';

vi.mock('../src/api/llmConfigs', () => ({
  llmConfigsApi: {
    getLlmConfigs: vi.fn(),
    updateLlmConfig: vi.fn(),
  },
}));

import { llmConfigsApi } from '../src/api/llmConfigs';
const mocked = vi.mocked(llmConfigsApi);

const CONFIGS = [
  { key: 'vllm_temperature', value: '0.7', description: 'Температура', input_type: 'float' },
  { key: 'vllm_stream', value: 'false', description: 'Стриминг', input_type: 'boolean' },
];

describe('LlmConfigsPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocked.getLlmConfigs.mockResolvedValue({ configs: CONFIGS } as any);
  });

  it('рендерит числовое поле и чекбокс', async () => {
    render(<LlmConfigsPanel />);
    
    // Ждем загрузки (температура)
    await screen.findByDisplayValue('0.7');

    // Проверяем числовое поле
    const numInput = screen.getByDisplayValue('0.7');
    expect(numInput).toHaveAttribute('type', 'number');

    // Проверяем чекбокс
    const checkbox = screen.getByRole('checkbox');
    expect(checkbox).not.toBeChecked();
  });
});