import React, { Suspense, lazy } from 'react';

// Кэш компонентов, чтобы не грузить один и тот же файл дважды
const componentCache = new Map();

interface PluginRendererProps {
  url: string;
  props?: Record<string, any>;
}

export function PluginRenderer({ url, props = {} }: PluginRendererProps) {
  if (!url) return null;

  // Если плагин уже загружался — берем из кэша
  if (!componentCache.has(url)) {
    // Динамический импорт. @vite-ignore нужен, чтобы Vite не пытался собрать этот файл при билде.
    const Component = lazy(() => import(/* @vite-ignore */ url).catch(err => {
      console.error("Ошибка загрузки UI плагина:", url, err);
      return { default: () => <div className="text-red-500 text-sm">Ошибка UI плагина</div> };
    }));
    componentCache.set(url, Component);
  }

  const CachedComponent = componentCache.get(url);

  return (
    <Suspense fallback={<div className="text-xs text-gray-400">Загрузка модуля...</div>}>
      <CachedComponent {...props} />
    </Suspense>
  );
}