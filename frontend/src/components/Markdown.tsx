import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export function Markdown({ children }: { children: string }) {
  return (
    <div className="prose prose-sm prose-slate max-w-none break-words
                    prose-pre:bg-slate-900 prose-pre:text-slate-100
                    prose-pre:rounded-lg prose-pre:p-3
                    prose-code:text-indigo-700 prose-code:before:content-none
                    prose-code:after:content-none
                    prose-a:text-indigo-600 prose-a:underline">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>
        {children}
      </ReactMarkdown>
    </div>
  );
}