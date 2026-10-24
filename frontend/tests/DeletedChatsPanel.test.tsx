import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { DeletedChatsPanel } from '../src/features/admin/DeletedChatsPanel';

vi.mock('../src/api/chats', () => ({
  chatsApi: {
    getDeletedChats: vi.fn(),
    recoverChats: vi.fn(),
    purgeDeletedChats: vi.fn(),
    purgeAllDeletedChats: vi.fn(),
  },
  aiApi: {},
}));

import { chatsApi } from '../src/api/chats';
const mocked = vi.mocked(chatsApi);

const DELETED = [
  { id: 'c1', name: 'Чат 1', user_login: 'bob' },
  { id: 'c2', name: 'Чат 2', user_login: 'admin' },
];

async function waitForList() {
  // 'Чат 1' — уникален, встречается только в колонке «Название»
  await screen.findByText('Чат 1');
}

describe('DeletedChatsPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    mocked.getDeletedChats.mockResolvedValue({ chats: DELETED } as any);
  });

  it('рендерит список удалённых чатов', async () => {
    render(<DeletedChatsPanel />);
    await waitForList();

    expect(screen.getByText('Чат 2')).toBeInTheDocument();
    expect(screen.getByText('bob')).toBeInTheDocument();
    expect(screen.getByText('admin')).toBeInTheDocument();
  });

  it('показывает «Корзина пуста», если чатов нет', async () => {
    mocked.getDeletedChats.mockResolvedValue({ chats: [] } as any);
    render(<DeletedChatsPanel />);
    expect(await screen.findByText(/корзина пуста/i)).toBeInTheDocument();
  });

  it('восстанавливает выбранные чаты через chatsApi.recoverChats', async () => {
    mocked.recoverChats.mockResolvedValue({} as any);
    render(<DeletedChatsPanel />);
    await waitForList();

    // [0] — «выбрать все» в шапке; [1] — Чат 1; [2] — Чат 2
    const checkboxes = screen.getAllByRole('checkbox');
    await userEvent.click(checkboxes[1]);

    await userEvent.click(screen.getByRole('button', { name: /восстановить/i }));

    await waitFor(() => {
      expect(mocked.recoverChats).toHaveBeenCalledWith(['c1']);
    });
  });

  it('удаляет выбранные через chatsApi.purgeDeletedChats', async () => {
    mocked.purgeDeletedChats.mockResolvedValue({} as any);
    render(<DeletedChatsPanel />);
    await waitForList();

    const checkboxes = screen.getAllByRole('checkbox');
    await userEvent.click(checkboxes[1]);
    await userEvent.click(checkboxes[2]);

    await userEvent.click(screen.getByRole('button', { name: /удалить выбранные/i }));

    await waitFor(() => {
      expect(mocked.purgeDeletedChats).toHaveBeenCalledWith(['c1', 'c2']);
    });
  });

  it('очищает всё через chatsApi.purgeAllDeletedChats', async () => {
    mocked.purgeAllDeletedChats.mockResolvedValue({} as any);
    render(<DeletedChatsPanel />);
    await waitForList();

    await userEvent.click(screen.getByRole('button', { name: /очистить всё/i }));

    await waitFor(() => {
      expect(mocked.purgeAllDeletedChats).toHaveBeenCalled();
    });
  });

  it('показывает ошибку, если getDeletedChats отклонён', async () => {
    mocked.getDeletedChats.mockRejectedValue(new Error('Доступ запрещён'));
    render(<DeletedChatsPanel />);
    expect(await screen.findByText('Доступ запрещён')).toBeInTheDocument();
  });
});