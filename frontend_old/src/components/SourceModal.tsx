import { Modal } from './Modal';
import { Source } from '../api/chats';
import { FileText } from 'lucide-react';

export function SourceModal({ source, onClose }: { source: Source; onClose: () => void }) {
  return (
    <Modal title={`Источник: ${source.source}`} onClose={onClose}>
      <div className="space-y-4">
        <div className="flex items-center gap-2 text-sm text-gray-500 bg-gray-50 p-2 rounded border">
          <FileText size={16} />
          <span>Страница / Чанк: {source.page}</span>
        </div>
        <div className="bg-yellow-50/50 border border-yellow-200 rounded-lg p-4 text-sm text-gray-800 leading-relaxed whitespace-pre-wrap font-serif">
          {source.text}
        </div>
        <div className="flex justify-end">
          <button onClick={onClose} className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm font-medium transition-colors">
            Закрыть
          </button>
        </div>
      </div>
    </Modal>
  );
}