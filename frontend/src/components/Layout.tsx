import { ReactNode } from 'react';

export function Layout({ sidebar, children }: { sidebar: ReactNode, children: ReactNode }) {
  return (
    <div className="flex h-screen bg-gray-50">
      <aside className="w-64 bg-gray-900 text-white flex flex-col border-r border-gray-800">
        {sidebar}
      </aside>
      <main className="flex-1 flex flex-col overflow-hidden">
        {children}
      </main>
    </div>
  );
}