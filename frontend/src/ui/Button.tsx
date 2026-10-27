import { ButtonHTMLAttributes, forwardRef } from 'react';
import { twMerge } from 'tailwind-merge';
import { Loader2 } from 'lucide-react';

// ==============================================================================
// БЛОК 1: ОПИСАНИЕ ТИПОВ
// ==============================================================================

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /** 
   * Визуальный стиль кнопки:
   * primary (синяя), secondary (серая), danger (красная), ghost (прозрачная)
   */
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  
  /** 
   * Если true, кнопка блокируется и показывает спиннер загрузки. 
   * Текст кнопки сохраняется, но становится полупрозрачным.
   */
  isLoading?: boolean;
}

// ==============================================================================
// БЛОК 2: КОМПОНЕНТ (С FORWARDREF)
// ==============================================================================

// forwardRef нужен для того, чтобы родительский компонент мог получить доступ 
// к реальному DOM-элементу <button> (например, для управления фокусом).
export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', isLoading, children, disabled, ...props }, ref) => {
    
    // ==========================================================================
    // БЛОК 3: БАЗОВЫЕ И ВАРИАТИВНЫЕ СТИЛИ
    // ==========================================================================
    
    // Базовые стили применяются ко всем кнопкам
    const baseStyles = 
      "inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg font-medium text-sm transition-all " +
      "focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 " +
      "active:scale-[0.98] disabled:opacity-60 disabled:pointer-events-none disabled:active:scale-100";

    // Цветовые схемы (варианты)
    const variants = {
      primary: "bg-blue-600 text-white hover:bg-blue-700 shadow-sm focus-visible:ring-blue-500",
      secondary: "bg-gray-100 text-gray-700 hover:bg-gray-200 border border-gray-300 focus-visible:ring-gray-400",
      danger: "bg-red-600 text-white hover:bg-red-700 shadow-sm focus-visible:ring-red-500",
      ghost: "bg-transparent text-gray-600 hover:bg-gray-100 hover:text-gray-900 focus-visible:ring-gray-400",
    };

    // ==========================================================================
    // БЛОК 4: РЕНДЕР
    // ==========================================================================
    
    return (
      <button
        ref={ref}
        // twMerge умно объединяет классы. Если пользователь передаст свой className,
        // он переопределит базовые стили (например, изменит padding).
        className={twMerge(baseStyles, variants[variant], className)}
        // Кнопка блокируется, если передан disabled ИЛИ если идет загрузка
        disabled={disabled || isLoading}
        // Атрибут для скринридеров
        aria-busy={isLoading}
        {...props}
      >
        {/* Если идет загрузка — показываем крутящуюся иконку */}
        {isLoading && <Loader2 size={16} className="animate-spin" />}
        
        {/* Текст кнопки (или другие элементы) */}
        {children}
      </button>
    );
  }
);

// Указываем имя компонента для React DevTools
Button.displayName = 'Button';