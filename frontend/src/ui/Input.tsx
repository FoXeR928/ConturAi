import { InputHTMLAttributes, forwardRef, ReactNode } from 'react';
import { twMerge } from 'tailwind-merge';

// ==============================================================================
// БЛОК 1: ОПИСАНИЕ ТИПОВ
// ==============================================================================

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  /** 
   * Подсветить поле красным (например, при ошибке валидации). 
   */
  isInvalid?: boolean;
  
  /** 
   * Иконка слева от текста (например, иконка поиска или конверта). 
   */
  leftIcon?: ReactNode;
  
  /** 
   * Иконка справа от текста (например, кнопка "показать пароль" или галочка).
   */
  rightIcon?: ReactNode;
}

// ==============================================================================
// БЛОК 2: КОМПОНЕНТ
// ==============================================================================

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, isInvalid, leftIcon, rightIcon, disabled, ...props }, ref) => {
    
    // ==========================================================================
    // БЛОК 3: БАЗОВЫЕ И ДИНАМИЧЕСКИЕ СТИЛИ
    // ==========================================================================

    // Базовые стили для самого input
    const baseStyles = 
      "w-full rounded-lg border p-2 text-sm text-gray-900 outline-none transition-colors duration-200 " +
      "placeholder:text-gray-400 " +
      // Состояние disabled (серый фон, запрет клика)
      "disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed " +
      // Учитываем иконки (добавляем отступы, если они есть)
      (leftIcon ? "pl-10 " : "") + 
      (rightIcon ? "pr-10 " : "");

    // Стили в зависимости от валидности поля
    const stateStyles = isInvalid
      ? "border-red-400 focus:border-red-500 focus:ring-2 focus:ring-red-500/20 text-red-900"
      : "border-gray-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 hover:border-gray-400";

    // ==========================================================================
    // БЛОК 4: РЕНДЕР
    // ==========================================================================

    // Если иконок нет, возвращаем "чистый" input (без обертки, чтобы не ломать flex-верстку)
    const inputElement = (
      <input
        ref={ref}
        disabled={disabled}
        aria-invalid={isInvalid}
        className={twMerge(baseStyles, stateStyles, className)}
        {...props}
      />
    );

    // Если передана хотя бы одна иконка — оборачиваем input в relative-контейнер
    if (leftIcon || rightIcon) {
      return (
        <div className="relative w-full flex items-center">
          
          {/* Иконка слева */}
          {leftIcon && (
            <div className="absolute left-3 text-gray-400 pointer-events-none flex items-center justify-center">
              {leftIcon}
            </div>
          )}

          {/* Сам Input */}
          {inputElement}

          {/* Иконка справа (может быть интерактивной, например, кнопкой "показать пароль") */}
          {rightIcon && (
            <div className="absolute right-3 text-gray-400 flex items-center justify-center">
              {rightIcon}
            </div>
          )}
        </div>
      );
    }

    return inputElement;
  }
);

Input.displayName = 'Input';