import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { TagSelect } from '../src/ui/TagSelect';

vi.mock('../src/api/tags', () => ({
  tagsApi: {
    getTags: vi.fn(),
  },
}));

import { tagsApi } from '../src/api/tags';
const mocked = vi.mocked(tagsApi);

const TAGS = [
  { id: 't1', name: 'IT', color: '#ff0000' },
  { id: 't2', name: 'HR', color: '#00ff00' },
];

describe('TagSelect', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocked.getTags.mockResolvedValue({ tags: TAGS } as any);
  });

  it('рендерит кнопку и открывает выпадающий список', async () => {
    render(<TagSelect selected={[]} onChange={vi.fn()} />);
    
    // Ждем, пока загрузятся теги и нажимаем на кнопку
    const button = await screen.findByRole('button', { name: /выбрать теги/i });
    await userEvent.click(button);

    expect(screen.getByText('IT')).toBeInTheDocument();
    expect(screen.getByText('HR')).toBeInTheDocument();
  });

  it('вызывает onChange при выборе тега', async () => {
    const onChange = vi.fn();
    render(<TagSelect selected={[]} onChange={onChange} />);
    
    await userEvent.click(await screen.findByRole('button', { name: /выбрать теги/i }));
    await userEvent.click(screen.getByText('IT'));

    expect(onChange).toHaveBeenCalledWith(['IT']);
  });

  it('отрисовывает выбранные теги в виде чипсов', () => {
    render(<TagSelect selected={['HR']} onChange={vi.fn()} />);
    
    // Ожидаем, что HR отобразится как чипс (и в кнопке, и в списке выбранных)
    expect(screen.getAllByText('HR').length).toBeGreaterThan(0);
  });
});