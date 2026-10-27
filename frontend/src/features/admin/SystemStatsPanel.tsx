import { useEffect, useState } from 'react';
import { systemApi, StatsResponse, GpuInfo } from '../../api/system';
import { Cpu, HardDrive, Server, Thermometer, Zap, Activity, MessageSquare, AlertCircle } from 'lucide-react';

// ==============================================================================
// БЛОК 1: ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ И КОМПОНЕНТЫ
// ==============================================================================

function formatBytes(bytes: number, decimals = 2) {
  if (!bytes || bytes === 0) return '0 Б';
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Б', 'КБ', 'МБ', 'ГБ', 'ТБ'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

// Выносим ProgressBar наверх, чтобы React не пересоздавал функцию при каждом рендере
function ProgressBar({ percent, color }: { percent: number, color: string }) {
  return (
    <div className="w-full bg-gray-200 rounded-full h-2.5 mt-2 overflow-hidden">
      <div 
        className={`h-2.5 rounded-full transition-all duration-500 ease-out ${color}`} 
        style={{ width: `${Math.min(Math.max(percent, 0), 100)}%` }} 
      />
    </div>
  );
}

// ==============================================================================
// БЛОК 2: ОСНОВНОЙ КОМПОНЕНТ
// ==============================================================================

export function SystemStatsPanel() {
  // ИСПРАВЛЕНО: используем типизированный стейт и сохраняем ВЕСЬ ответ с сервера
  const [data, setData] = useState<StatsResponse | null>(null);
  const [error, setError] = useState('');

  const loadStats = async () => {
    try {
      const response = await systemApi.getStats();
      setData(response);
      setError('');
    } catch (e: any) {
      setError(e.message);
    }
  };

  // Поллинг каждые 5 секунд
  useEffect(() => {
    loadStats();
    const interval = setInterval(loadStats, 5000);
    return () => clearInterval(interval);
  }, []);

  // ==========================================================================
  // СОСТОЯНИЯ ЗАГРУЗКИ И ОШИБОК
  // ==========================================================================

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-600 p-4 rounded-lg flex items-center gap-2">
        <AlertCircle size={20} /> {error}
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-gray-400 animate-pulse">
        <Activity size={32} className="mb-2" />
        Загрузка метрик системы...
      </div>
    );
  }

  // Распаковываем данные для удобства
  const stats = data.stats;
  const llm = data.llm_stats;

  // ==========================================================================
  // РЕНДЕР ИНТЕРФЕЙСА
  // ==========================================================================

  return (
    <div className="space-y-8 pb-10">
      
      {/* ЗАГОЛОВОК */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold flex items-center gap-2">
          <Activity className="text-blue-600" /> Мониторинг системы
        </h2>
        <span className="text-xs font-medium text-gray-500 bg-gray-100 px-2.5 py-1 rounded-full">
          Автообновление: 5 сек
        </span>
      </div>

      {/* БЛОК 1: ЖЕЛЕЗО (CPU, RAM, ДИСКИ) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* CPU */}
        <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-100">
          <div className="flex items-center gap-2 mb-2 text-gray-700 font-semibold">
            <Cpu size={18} className="text-blue-500" /> Процессор ({stats.cpu.cores} ядер)
          </div>
          <div className="text-3xl font-bold text-gray-900">{stats.cpu.percent}%</div>
          <ProgressBar percent={stats.cpu.percent} color="bg-blue-500" />
        </div>

        {/* RAM */}
        <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-100">
          <div className="flex items-center gap-2 mb-2 text-gray-700 font-semibold">
            <Server size={18} className="text-purple-500" /> Оперативная память
          </div>
          <div className="text-3xl font-bold text-gray-900">{stats.ram.percent}%</div>
          <div className="text-xs text-gray-500 mb-2 font-medium">
            {formatBytes(stats.ram.used)} / {formatBytes(stats.ram.total)}
          </div>
          <ProgressBar percent={stats.ram.percent} color={stats.ram.percent > 90 ? 'bg-red-500' : 'bg-purple-500'} />
        </div>

        {/* Диски */}
        <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-100">
          <div className="flex items-center gap-2 mb-2 text-gray-700 font-semibold">
            <HardDrive size={18} className="text-orange-500" /> Дисковое пространство
          </div>
          <div className="space-y-4 mt-2">
            <div>
              <div className="flex justify-between text-xs font-medium mb-1">
                <span>Данные (uploads, logs)</span>
                <span className="text-gray-500">{formatBytes(stats.disk_data.free)} свободно</span>
              </div>
              <ProgressBar percent={(stats.disk_data.used / stats.disk_data.total) * 100} color="bg-orange-500" />
            </div>
            <div>
              <div className="flex justify-between text-xs font-medium mb-1">
                <span>Модели (vLLM, Embeddings)</span>
                <span className="text-gray-500">{formatBytes(stats.disk_models.free)} свободно</span>
              </div>
              <ProgressBar percent={(stats.disk_models.used / stats.disk_models.total) * 100} color="bg-teal-500" />
            </div>
          </div>
        </div>
      </div>

      {/* БЛОК 2: СТАТИСТИКА НЕЙРОСЕТИ */}
      <div>
        <h3 className="text-xl font-bold mb-4 flex items-center gap-2 text-gray-800">
          <Zap className="text-yellow-500" /> Статистика нейросети
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-100 border-l-4 border-l-blue-500">
            <div className="flex items-center gap-2 mb-2 text-gray-600 font-medium text-sm">
              <MessageSquare size={16} /> Всего запросов
            </div>
            <div className="text-3xl font-bold text-gray-900">{llm.requests.toLocaleString()}</div>
            <div className="text-xs text-gray-400 mt-1">Успешных ответов ассистента</div>
          </div>

          <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-100 border-l-4 border-l-green-500">
            <div className="flex items-center gap-2 mb-2 text-gray-600 font-medium text-sm">
              <Activity size={16} /> Обработано токенов
            </div>
            <div className="text-3xl font-bold text-gray-900">{llm.total_tokens.toLocaleString()}</div>
            <div className="text-xs text-gray-400 mt-1 flex gap-2">
              <span className="text-blue-600 bg-blue-50 px-1 rounded">In: {llm.total_prompt_tokens.toLocaleString()}</span>
              <span className="text-green-600 bg-green-50 px-1 rounded">Out: {llm.total_completion_tokens.toLocaleString()}</span>
            </div>
          </div>

          <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-100 border-l-4 border-l-yellow-500">
            <div className="flex items-center gap-2 mb-2 text-gray-600 font-medium text-sm">
              <Zap size={16} /> Средняя скорость
            </div>
            <div className="text-3xl font-bold text-gray-900">
              {llm.avg_speed} <span className="text-sm font-normal text-gray-500">ток/сек</span>
            </div>
            <div className="text-xs text-gray-400 mt-1">Скорость генерации текста</div>
          </div>
        </div>
      </div>

      {/* БЛОК 3: ГРАФИЧЕСКИЕ УСКОРИТЕЛИ (GPU) */}
      <div>
        <h3 className="text-xl font-bold mb-4 text-gray-800">Графические ускорители</h3>
        
        {stats.gpus.length === 0 ? (
          <div className="bg-white border border-gray-200 p-8 rounded-xl text-center flex flex-col items-center">
            <Server size={32} className="text-gray-300 mb-2" />
            <div className="text-gray-500 font-medium">Видеокарты не обнаружены</div>
            <div className="text-sm text-gray-400 mt-1">Система использует CPU для вычислений</div>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {stats.gpus.map((gpu: GpuInfo, idx: number) => {
              const isNvidia = gpu.vendor === 'NVIDIA';
              const isAmd = gpu.vendor === 'AMD';
              const isIntel = gpu.vendor === 'INTEL';
              
              const badgeColor = isNvidia ? 'bg-green-100 text-green-700' : isAmd ? 'bg-red-100 text-red-700' : 'bg-blue-100 text-blue-700';
              const borderColor = isNvidia ? 'border-green-500' : isAmd ? 'border-red-500' : 'border-blue-500';
              const noVram = gpu.mem_total === 0;

              // Цвет температуры
              const tempColor = gpu.temperature > 80 ? 'text-red-600 bg-red-50' : 
                                gpu.temperature > 65 ? 'text-yellow-600 bg-yellow-50' : 
                                'text-blue-600 bg-blue-50';

              return (
                <div key={idx} className={`bg-white p-5 rounded-xl shadow-sm border border-gray-100 border-l-4 ${borderColor} flex flex-col lg:flex-row gap-6 items-center`}>
                  
                  {/* Инфо о карте */}
                  <div className="flex-1 min-w-[200px] w-full">
                    <div className="text-lg font-bold flex items-center gap-2 text-gray-800">
                      <Zap className={isNvidia ? 'text-green-500' : isAmd ? 'text-red-500' : 'text-blue-500'} size={20}/> 
                      {gpu.name}
                    </div>
                    <div className="text-sm text-gray-500 mt-2 flex items-center gap-2">
                      <span className={`px-2 py-0.5 rounded text-xs font-bold ${badgeColor}`}>
                        {gpu.vendor}
                      </span>
                      <span className="font-mono bg-gray-100 px-1.5 py-0.5 rounded text-xs">GPU #{idx}</span>
                    </div>
                  </div>
                  
                  {/* Прогресс-бары */}
                  <div className="flex-1 w-full">
                    {!noVram ? (
                      <>
                        <div className="flex justify-between text-sm font-medium mt-1">
                          <span>Видеопамять (VRAM)</span>
                          <span>{gpu.mem_percent}% <span className="text-gray-400 font-normal">({formatBytes(gpu.mem_used)} / {formatBytes(gpu.mem_total)})</span></span>
                        </div>
                        <ProgressBar percent={gpu.mem_percent} color={gpu.mem_percent > 90 ? 'bg-red-500' : 'bg-blue-500'} />
                      </>
                    ) : (
                      <div className="text-xs text-gray-400 italic mb-2 bg-gray-50 p-2 rounded">Выделенная VRAM не обнаружена (APU/iGPU)</div>
                    )}
                    
                    <div className="flex justify-between text-sm font-medium mt-4">
                      <span>Загрузка ядер</span>
                      <span>{gpu.utilization}%</span>
                    </div>
                    <ProgressBar percent={gpu.utilization} color={isNvidia ? 'bg-green-500' : isAmd ? 'bg-red-500' : 'bg-blue-500'} />
                  </div>

                  {/* Температура */}
                  <div className={`flex items-center gap-2 px-4 py-3 rounded-xl min-w-[120px] justify-center ${tempColor}`}>
                    <Thermometer size={22} className={gpu.temperature === 0 ? 'text-gray-400' : ''} />
                    <span className="text-2xl font-bold">
                      {gpu.temperature > 0 ? `${gpu.temperature}°C` : 'N/A'}
                    </span>
                  </div>
                  
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}