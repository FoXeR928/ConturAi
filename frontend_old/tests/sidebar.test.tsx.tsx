import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { Sidebar } from '../src/features/chat/Sidebar';

vi.mock('../src/api/chats', () => ({
  chatsApi: {
    softDeleteChat: vi.fn(),
  },
  aiApi: {},
}));

import { chatsApi } from '../src/api/chats';
const mocked = vi.mocked(chatsApi);

const CHATS = [{ id: 'chat-1', name: 'Тестовый чат' }];

function setup(overrides: Record<string, unknown> = {}) {
  return render(
    <MemoryRouter>
      <Sidebar
        chats={CHATS}
        activeChatId="chat-1"
        onSelectChat={vi.fn()}
        onCreateChat={vi.fn()}
        onLogout={vi.fn()}
        onChatDeleted={vi.fn()}
        {...overrides}
      />
    </MemoryRouter>
  );
}

describe('Sidebar', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(window, 'confirm').mockReturnValue(true);
  });

  it('рендерит список чатов', () => {
    setup();
    expect(screen.getByText('Тестовый чат')).toBeInTheDocument();
  });

  it('удаляет чат в корзину через chatsApi.softDeleteChat', async () => {
    const onChatDeleted = vi.fn();
    mocked.softDeleteChat.mockResolvedValue({} as any);
    setup({ onChatDeleted });

    await userEvent.click(screen.getByTitle('Удалить в корзину'));

    await waitFor(() => {
      expect(mocked.softDeleteChat).toHaveBeenCalledWith('chat-1');
      expect(onChatDeleted).toHaveBeenCalled();
    });
  });

  it('не вызывает onSelectChat при клике на корзину', async () => {
    const onSelectChat = vi.fn();
    mocked.softDeleteChat.mockResolvedValue({} as any);
    setup({ onSelectChat });

    await userEvent.click(screen.getByTitle('Удалить в корзину'));

    await waitFor(() => {
      expect(mocked.softDeleteChat).toHaveBeenCalled();
    });
    expect(onSelectChat).not.toHaveBeenCalled();
  });
});