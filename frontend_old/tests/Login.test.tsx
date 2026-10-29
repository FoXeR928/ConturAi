import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Login } from '../src/pages/Login';

describe('Login', () => {
  it('отправляет onLogin с введёнными значениями (без галочки)', async () => {
    const onLogin = vi.fn().mockResolvedValue(undefined);
    render(<Login onLogin={onLogin} />);

    await userEvent.type(screen.getByLabelText(/логин/i), 'admin');
    await userEvent.type(screen.getByLabelText(/пароль/i), 'secret');
    await userEvent.click(screen.getByRole('button', { name: /войти/i }));

    expect(onLogin).toHaveBeenCalledWith('admin', 'secret', false);
  });

  it('отправляет rememberMe=true, если стоит галочка', async () => {
    const onLogin = vi.fn().mockResolvedValue(undefined);
    render(<Login onLogin={onLogin} />);

    await userEvent.type(screen.getByLabelText(/логин/i), 'admin');
    await userEvent.type(screen.getByLabelText(/пароль/i), 'secret');
    // Ставим галочку
    await userEvent.click(screen.getByLabelText(/запомнить меня/i));
    await userEvent.click(screen.getByRole('button', { name: /войти/i }));

    expect(onLogin).toHaveBeenCalledWith('admin', 'secret', true);
  });
});