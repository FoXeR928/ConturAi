import { Suspense, lazy } from 'react';

const componentCache = new Map();

export function PluginRenderer({ url, props = {} }: { url: string; props?: any }) {
  if (!url) return null;

  if (!componentCache.has(url)) {
    const Component = lazy(() => 
      import(/* @vite-ignore */ url).catch(err => {
        console.error(`Ошибка загрузки плагина: ${url}`, err);
        return { default: () => <span className="text-red-500 text-xs">Ошибка UI плагина</span> };
      })
    );
    componentCache.set(url, Component);
  }

  const CachedComponent = componentCache.get(url);

  return (
    <Suspense fallback={<span className="text-xs text-gray-400 animate-pulse">Загрузка...</span>}>
      <CachedComponent {...props} />
    </Suspense>
  );
}