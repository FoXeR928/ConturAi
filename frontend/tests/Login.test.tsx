import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Login } from '../src/pages/Login';

describe('Login', () => {
  it('отправляет onLogin с введёнными значениями', async () => {
    const onLogin = vi.fn().mockResolvedValue(undefined);
    render(<Login onLogin={onLogin} />);

    await userEvent.type(screen.getByLabelText(/логин/i), 'admin');
    await userEvent.type(screen.getByLabelText(/пароль/i), 'secret');
    await userEvent.click(screen.getByRole('button', { name: /войти/i }));

    expect(onLogin).toHaveBeenCalledWith('admin', 'secret');
  });

  it('показывает ошибку, если onLogin отклонён', async () => {
    const onLogin = vi.fn().mockRejectedValue(new Error('Неверный логин или пароль'));
    render(<Login onLogin={onLogin} />);

    await userEvent.type(screen.getByLabelText(/логин/i), 'x');
    await userEvent.type(screen.getByLabelText(/пароль/i), 'y');
    await userEvent.click(screen.getByRole('button', { name: /войти/i }));

    expect(await screen.findByText(/Неверный логин или пароль/)).toBeInTheDocument();
  });
});