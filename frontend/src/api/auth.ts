import { api, getToken, setToken, clearToken } from './http';

export interface LoginPayload {
  login: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface MeResponse {
  id: string;
  login: string;
  display_name: string | null;
  role: 'user' | 'editor' | 'admin';
  is_active: boolean;
}

export const authApi = {
  async login(payload: LoginPayload): Promise<MeResponse> {
    const tokens = await api<TokenResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    setToken(tokens.access_token);
    return authApi.me();
  },

  me(): Promise<MeResponse> {
    return api<MeResponse>('/auth/me');
  },

  changeMyPassword(
    old_password: string,
    new_password: string,
  ): Promise<void> {
    return api('/auth/me/password', {
      method: 'PATCH',
      body: JSON.stringify({ old_password, new_password }),
    });
  },

  logout(): void {
    clearToken();
  },

  isAuthenticated(): boolean {
    return getToken() !== null;
  },
};