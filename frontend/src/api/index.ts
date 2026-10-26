import { login, logout } from './auth';
import { aiApi, chatsApi } from './chats';
import { docsApi } from './docs';
import { llmConfigsApi } from './llmConfigs';
import { promptsApi } from './prompts';
import { usersApi } from './users';
import { auditApi } from './audit';
import { downloadsApi } from './downloads';
import { systemApi } from './system';

export const api = {
  // auth
  login,
  logout,

  // chats + ai
  ...chatsApi,
  ...aiApi,

  // users
  ...usersApi,

  // prompts
  ...promptsApi,

  // llm configs
  ...llmConfigsApi,

  // docs
  ...docsApi,

  // audit
  ...auditApi,

  // downloads
  ...downloadsApi,

  // system
  ...systemApi,
};

export { ApiError } from './http';
export type { ApiErrorPayload, RequestOptions } from './http';