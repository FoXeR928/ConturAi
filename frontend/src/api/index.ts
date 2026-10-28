// ==============================================================================
// БЛОК 1: ИМПОРТ ВСЕХ API-МОДУЛЕЙ
// ==============================================================================

import { login, logout } from './auth';
import { aiApi, chatsApi } from './chats';
import { docsApi } from './docs';
import { llmConfigsApi } from './llmConfigs';
import { promptsApi } from './prompts';
import { usersApi } from './users';
import { auditApi } from './audit';
import { downloadsApi } from './downloads';
import { systemApi } from './system';

// Новые модули (Теги и Обучение)
import { tagsApi } from './tags';
import { fewShotsApi } from './fewShots';


// ==============================================================================
// БЛОК 2: СБОРКА ЕДИНОГО ОБЪЕКТА API
// ==============================================================================

/**
 * Глобальный объект `api`.
 * 
 * Зачем это нужно?
 * 1. Обратная совместимость: старый код, где использовался `api.getChats()`, 
 *    продолжит работать без переписывания.
 * 2. Удобство: вместо `import { chatsApi } from './chats'` и 
 *    `import { usersApi } from './users'` в компоненте можно просто 
 *    написать `import { api } from '../api'`.
 * 
 * Благодаря спред-оператору (...), все методы из модулей сливаются 
 * в один большой объект.
 */
export const api = {
  // --- Auth ---
  login,
  logout,

  // --- Chats + AI Generation ---
  ...chatsApi,
  ...aiApi,

  // --- Users ---
  ...usersApi,

  // --- Prompts & LLM Settings ---
  ...promptsApi,
  ...llmConfigsApi,

  // --- Documents ---
  ...docsApi,

  // --- Security & Access ---
  ...auditApi,
  ...downloadsApi,

  // --- System Monitoring ---
  ...systemApi,

  // --- Tags & Few-Shot Training ---
  ...tagsApi,
  ...fewShotsApi,
};


// ==============================================================================
// БЛОК 3: РЕЭКСПОРТ ТИПОВ И КЛАССА ОШИБОК
// ==============================================================================

// Позволяет импортировать ApiError прямо из папки api (import { ApiError } from '../api')
export { ApiError } from './http';

// Реэкспорт TypeScript-типов для удобства
export type { ApiErrorPayload, RequestOptions } from './http';