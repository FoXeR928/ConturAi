import { ReactNode } from 'react';

export function Layout({ sidebar, header, children }: { sidebar: ReactNode; header?: ReactNode; children: ReactNode }) {
  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      <aside className="w-64 bg-gray-900 text-white flex flex-col border-r border-gray-800 shrink-0">
        {sidebar}
      </aside>
      <main className="flex-1 flex flex-col min-w-0">
        {header}
        <div className="flex-1 overflow-hidden relative">{children}</div>
      </main>
    </div>
  );
}