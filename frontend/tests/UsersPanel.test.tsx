import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { UsersPanel } from '../src/features/admin/UsersPanel';

vi.mock('../src/api/users', () => ({
  usersApi: {
    getUsers: vi.fn(),
    createUser: vi.fn(),
    updateUserStatus: vi.fn(),
    updateUserRole: vi.fn(),
    deleteUser: vi.fn(),
    purgeUser: vi.fn(),
  },
}));

import { usersApi } from '../src/api/users';
const mocked = vi.mocked(usersApi);

const USERS = [
  { login: 'admin', user_name: 'Админ', is_admin: true,  disabled: false },
  { login: 'bob',   user_name: 'Bob',   is_admin: false, disabled: false },
];

/** Ждём, пока список отрисуется. 'Bob' уникален — встречается только в колонке «Имя». */
async function waitForList() {
  await screen.findByText('Bob');
}

describe('UsersPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocked.getUsers.mockResolvedValue({ users: USERS } as any);
  });

  it('рендерит пользователей после загрузки', async () => {
    render(<UsersPanel />);
    await waitForList();

    expect(screen.getByText('Админ')).toBeInTheDocument();
    expect(screen.getByText('Bob')).toBeInTheDocument();

    // 'admin' встречается дважды: логин и бейдж роли
    expect(screen.getAllByText('admin')).toHaveLength(2);
  });

  it('переключает include_deleted при нажатии «Показать удаленных»', async () => {
    render(<UsersPanel />);
    await waitForList();

    await userEvent.click(screen.getByLabelText(/показать удаленных/i));

    await waitFor(() => {
      expect(mocked.getUsers).toHaveBeenLastCalledWith(true);
    });
  });

  it('вызывает updateUserStatus при «Заблокировать»', async () => {
    render(<UsersPanel />);
    await waitForList();

    mocked.updateUserStatus.mockResolvedValue({} as any);

    // У двух пользователей есть кнопка «Заблокировать» — берём первую (admin)
    const buttons = screen.getAllByRole('button', { name: /заблокировать/i });
    await userEvent.click(buttons[0]);

    await waitFor(() => {
      expect(mocked.updateUserStatus).toHaveBeenCalledWith('admin', true);
    });
  });
});