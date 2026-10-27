import { API_BASE, request, getToken, redirectToLogin, ApiError } from './http';

// ==============================================================================
// БЛОК 1: ОПИСАНИЕ ТИПОВ (TYPESCRIPT INTERFACES)
// ==============================================================================

export interface GpuInfo {
  vendor: 'NVIDIA' | 'AMD' | 'INTEL';
  name: string;
  mem_total: number;
  mem_used: number;
  mem_percent: number;
  utilization: number;
  temperature: number;
}

export interface SystemStats {
  cpu: { percent: number; cores: number };
  ram: { total: number; used: number; percent: number };
  disk_data: { total: number; used: number; free: number };
  disk_models: { total: number; used: number; free: number };
  gpus: GpuInfo[];
}

export interface LlmStats {
  requests: number;
  total_prompt_tokens: number;
  total_completion_tokens: number;
  total_tokens: number;
  avg_speed: number;
}

export interface StatsResponse {
  result: boolean;
  stats: SystemStats;
  llm_stats: LlmStats;
}

export interface BackupFile {
  name: string;
  size: number;
  created_at: string;
}

export interface BackupsResponse {
  result: boolean;
  backups: BackupFile[];
  db_size: number;
}

// ==============================================================================
// БЛОК 2: API ДЛЯ МОНИТОРИНГА И СТАТУСА
// ==============================================================================

export const systemApi = {
  /**
   * Получить метрики "железа" (CPU, RAM, Диски, GPU) и статистику нейросети.
   * 
   * Вызывается на вкладке «Мониторинг» каждые 5 секунд (через setInterval).
   * Возвращает типизированный объект, чтобы фронтенд мог безопасно обращаться 
   * к свойствам (например, `stats.ram.percent`).
   */
  getStats: () => request<StatsResponse>('/system/stats'),

  /**
   * Проверка статуса vLLM (жив ли сервер).
   * Возвращает { status: 'ok' } или { status: 'offline' }.
   * Используется в Header для отображения индикатора "Онлайн/Оффлайн".
   */
  getVllmStatus: () => request<{ status: string }>('/system/vllm-status'),


// ==============================================================================
// БЛОК 3: УПРАВЛЕНИЕ РЕЗЕРВНЫМИ КОПИЯМИ (БЭКАПАМИ)
// ==============================================================================

  /**
   * Получить список всех существующих бэкапов и размер текущей БД.
   */
  getBackups: () => request<BackupsResponse>('/system/db/backups'),

  /**
   * Создать новый бэкап.
   * 
   * Бэкенд сделает дамп базы данных (pg_dump) и упакует папку с загруженными файлами в ZIP.
   * Это синхронная операция, поэтому на больших базах данных запрос может занять несколько секунд.
   */
  createBackup: () => request('/system/db/backup', { method: 'POST' }),

  /**
   * Удалить файл бэкапа с сервера.
   * 
   * @param filename - Имя файла (например, 'db_20231027_120000.sql').
   */
  deleteBackup: (filename: string) => 
    request(`/system/db/backups/${filename}`, { method: 'DELETE' }),

  /**
   * Скачать файл бэкапа на компьютер.
   * 
   * Реализовано через fetch + Blob, так как это скачивание файла, а не JSON-ответ.
   * Аналогично методу downloadDoc в docs.ts.
   */
  downloadBackup: async (filename: string) => {
    const token = getToken();
    const res = await fetch(`${API_BASE}/system/db/backups/${filename}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });

    if (res.status === 401) {
      redirectToLogin();
      return;
    }

    if (!res.ok) {
      throw new ApiError(`Не удалось скачать бэкап (HTTP ${res.status})`, res.status);
    }

    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.style.display = 'none';
    document.body.appendChild(a);
    a.click();

    setTimeout(() => {
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }, 1000);
  }
};