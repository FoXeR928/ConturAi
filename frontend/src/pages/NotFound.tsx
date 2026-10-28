import { Link } from 'react-router-dom';
import { Ghost } from 'lucide-react';

// ==============================================================================
// БЛОК 1: КОМПОНЕНТ СТРАНИЦЫ 404
// ==============================================================================

export function NotFound() {
  return (
    // min-h-screen — растягиваем на всю высоту экрана.
    // flex-col — элементы идут друг под другом (сверху вниз).
    // items-center justify-center — центрируем по горизонтали и вертикали.
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 p-4">
      
      {/* Иконка-призрак для визуального акцента */}
      <div className="text-gray-200 mb-4">
        <Ghost size={96} strokeWidth={1.5} />
      </div>

      {/* Большой заголовок 404 */}
      <h1 className="text-7xl font-black text-gray-300 tracking-tighter select-none">
        404
      </h1>

      {/* Описание */}
      <p className="text-lg text-gray-600 mt-4 mb-8 text-center">
        Упс! Такой страницы не существует.
        <br />
        <span className="text-sm text-gray-400">Возможно, она была удалена или вы ошиблись адресом.</span>
      </p>

      {/* Кнопка возврата на главную */}
      <Link
        to="/chat"
        className="px-6 py-2.5 bg-blue-600 text-white font-medium rounded-lg shadow-sm hover:bg-blue-700 hover:shadow-md transition-all focus:outline-none focus:ring-4 focus:ring-blue-500/30"
      >
        Вернуться в чат
      </Link>
    </div>
  );
}