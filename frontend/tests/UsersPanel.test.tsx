import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { UsersPanel } from '../src/features/admin/UsersPanel';

// Мокаем useToast, так как он используется в компоненте
vi.mock('../src/components/ToastContext', () => ({
  useToast: () => ({ toast: vi.fn() }),
}));

vi.mock('../src/api/users', () => ({
  usersApi: {
    getUsers: vi.fn(),
    createUser: vi.fn(),
    updateUserStatus: vi.fn(),
    updateUserRole: vi.fn(),
    updateUserName: vi.fn(),
    updatePassword: vi.fn(),
    deleteUser: vi.fn(),
    purgeUser: vi.fn(),
  },
}));

import { usersApi } from '../src/api/users';
const mocked = vi.mocked(usersApi);

const USERS = [
  { login: 'admin', user_name: 'Админ', role: 'admin', disabled: false },
  { login: 'bob',   user_name: 'Bob',   role: 'user',  disabled: false },
];

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

    const buttons = screen.getAllByRole('button', { name: /заблокировать/i });
    await userEvent.click(buttons[0]);

    await waitFor(() => {
      expect(mocked.updateUserStatus).toHaveBeenCalledWith('admin', true);
    });
  });

  it('открывает модалку редактирования и меняет пароль', async () => {
    render(<UsersPanel />);
    await waitForList();

    // Нажимаем "Изменить" у первого пользователя
    const editButtons = screen.getAllByRole('button', { name: /изменить/i });
    await userEvent.click(editButtons[0]);

    // Вводим новый пароль
    const passInput = screen.getByPlaceholderText(/оставьте пустым/i);
    await userEvent.type(passInput, 'new-secret');

    // Нажимаем сохранить
    await userEvent.click(screen.getByRole('button', { name: /сохранить/i }));

    await waitFor(() => {
      expect(mocked.updatePassword).toHaveBeenCalledWith('admin', 'new-secret');
    });
  });
});