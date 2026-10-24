import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ChatWindow } from '../src/features/chat/ChatWindow';

vi.mock('../src/api/chats', () => ({
  chatsApi: {
    deleteMessage: vi.fn(),
  },
  aiApi: {},
}));

import { chatsApi } from '../src/api/chats';
const mocked = vi.mocked(chatsApi);

const messages = [
  { id: 'm1', chat_role: 'user',      text: 'Привет' },
  { id: 'm2', chat_role: 'assistant', text: '| a | b |\n| --- | --- |\n| 1 | 2 |' },
];

describe('ChatWindow', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('рендерит сообщения пользователя и ассистента', () => {
    render(
      <ChatWindow
        messages={messages}
        onSendMessage={vi.fn()}
        loading={false}
        chatId="c1"
        onRefresh={vi.fn()}
      />
    );
    expect(screen.getByText('Привет')).toBeInTheDocument();
    expect(screen.getByRole('table')).toBeInTheDocument();
  });

  it('применяет cleanMarkdown к ответу ассистента', () => {
    const wrapped = [
      { id: 'm3', chat_role: 'assistant', text: '```markdown\n# Заголовок\n```' },
    ];
    render(
      <ChatWindow
        messages={wrapped}
        onSendMessage={vi.fn()}
        loading={false}
        chatId="c1"
        onRefresh={vi.fn()}
      />
    );
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Заголовок');
  });

  it('отправляет текст через onSendMessage по Enter', async () => {
    const onSend = vi.fn().mockResolvedValue(undefined);
    render(
      <ChatWindow
        messages={[]}
        onSendMessage={onSend}
        loading={false}
        chatId="c1"
        onRefresh={vi.fn()}
      />
    );
    const input = screen.getByPlaceholderText(/введите сообщение/i);
    await userEvent.type(input, 'привет{enter}');
    expect(onSend).toHaveBeenCalledWith('привет');
  });

  it('удаляет сообщение через chatsApi.deleteMessage', async () => {
    const onRefresh = vi.fn();
    mocked.deleteMessage.mockResolvedValue({} as any);
    vi.spyOn(window, 'confirm').mockReturnValue(true);

    render(
      <ChatWindow
        messages={messages}
        onSendMessage={vi.fn()}
        loading={false}
        chatId="c1"
        onRefresh={onRefresh}
      />
    );

    const deleteButtons = screen.getAllByTitle(/удалить сообщение/i);
    await userEvent.click(deleteButtons[0]);

    await waitFor(() => {
      expect(mocked.deleteMessage).toHaveBeenCalledWith('c1', 'm1');
      expect(onRefresh).toHaveBeenCalled();
    });
  });

  it('показывает индикатор «печатает» при loading', () => {
    render(
      <ChatWindow
        messages={[]}
        onSendMessage={vi.fn()}
        loading={true}
        chatId="c1"
        onRefresh={vi.fn()}
      />
    );
    expect(screen.getByText(/печатает/i)).toBeInTheDocument();
  });
});