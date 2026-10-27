import { request } from './http';

// ==============================================================================
// БЛОК 1: ОПИСАНИЕ ТИПОВ (TYPESCRIPT INTERFACES)
// ==============================================================================

export interface TagItem {
  id: string;
  name: string;
  color: string; // HEX-цвет (например, "#3b82f6")
}

export interface TagsResponse {
  result: boolean;
  tags: TagItem[];
}

// ==============================================================================
// БЛОК 2: API ДЛЯ РАБОТЫ С ТЕГАМИ
// ==============================================================================

export const tagsApi = {
  /**
   * Получить список всех доступных тегов.
   * 
   * Доступно любому авторизованному пользователю.
   * Используется в ChatWindow для отрисовки выпадающего списка (multiselect) 
   * и в TagsPanel для отображения таблицы тегов.
   */
  getTags: () => request<TagsResponse>('/tags/get'),

  /**
   * Создать новый тег (доступно только администратору).
   * 
   * @param name - Название тега (например, "Бухгалтерия"). Бэкенд проверит на дубликаты.
   * @param color - HEX-цвет тега (например, "#ff0000").
   */
  createTag: (name: string, color: string) => 
    request('/tags/create', { 
      method: 'POST', 
      body: JSON.stringify({ name, color }) 
    }),

  /**
   * Удалить тег по его ID (доступно только администратору).
   * 
   * @param id - UUID тега, который нужно удалить из справочника.
   */
  deleteTag: (id: string) => 
    request(`/tags/${id}`, { method: 'DELETE' }),
};