import { useEffect, useState } from 'react';
import { systemApi } from '../../api/system';
import { Cpu, HardDrive, Server, Thermometer, Zap } from 'lucide-react';

function formatBytes(bytes: number, decimals = 2) {
  if (bytes === 0) return '0 Б';
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Б', 'КБ', 'МБ', 'ГБ', 'ТБ'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

export function SystemStatsPanel() {
  const [stats, setStats] = useState<any>(null);
  const [error, setError] = useState('');

  const loadStats = async () => {
    try {
      const data = await systemApi.getStats();
      setStats(data.stats);
      setError('');
    } catch (e: any) {
      setError(e.message);
    }
  };

  useEffect(() => {
    loadStats();
    const interval = setInterval(loadStats, 5000); // Обновление раз в 5 сек
    return () => clearInterval(interval);
  }, []);

  if (error) return <div className="bg-red-50 text-red-600 p-3 rounded">{error}</div>;
  if (!stats) return <div className="text-gray-500 animate-pulse">Загрузка метрик...</div>;

  const ProgressBar = ({ percent, color }: { percent: number, color: string }) => (
    <div className="w-full bg-gray-200 rounded-full h-2.5 mt-2">
      <div className={`h-2.5 rounded-full ${color}`} style={{ width: `${Math.min(percent, 100)}%` }} />
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Мониторинг системы</h2>
        <span className="text-xs text-gray-400">Обновление каждые 5 сек</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* CPU */}
        <div className="bg-white p-4 rounded-lg shadow border border-gray-100">
          <div className="flex items-center gap-2 mb-2 text-gray-700 font-semibold">
            <Cpu size={18} /> Процессор ({stats.cpu.cores} ядер)
          </div>
          <div className="text-3xl font-bold">{stats.cpu.percent}%</div>
          <ProgressBar percent={stats.cpu.percent} color="bg-blue-500" />
        </div>

        {/* RAM */}
        <div className="bg-white p-4 rounded-lg shadow border border-gray-100">
          <div className="flex items-center gap-2 mb-2 text-gray-700 font-semibold">
            <Server size={18} /> Оперативная память
          </div>
          <div className="text-3xl font-bold">{stats.ram.percent}%</div>
          <div className="text-sm text-gray-500 mb-2">
            {formatBytes(stats.ram.used)} / {formatBytes(stats.ram.total)}
          </div>
          <ProgressBar percent={stats.ram.percent} color={stats.ram.percent > 90 ? 'bg-red-500' : 'bg-green-500'} />
        </div>

        {/* Диски */}
        <div className="bg-white p-4 rounded-lg shadow border border-gray-100">
          <div className="flex items-center gap-2 mb-2 text-gray-700 font-semibold">
            <HardDrive size={18} /> Место на диске
          </div>
          <div className="space-y-3 mt-3">
            <div>
              <div className="flex justify-between text-sm">
                <span>Данные (uploads, logs)</span>
                <span className="text-gray-500">{formatBytes(stats.disk_data.free)} свободно</span>
              </div>
              <ProgressBar percent={(stats.disk_data.used / stats.disk_data.total) * 100} color="bg-purple-500" />
            </div>
            <div>
              <div className="flex justify-between text-sm">
                <span>Модели (vLLM, Embeddings)</span>
                <span className="text-gray-500">{formatBytes(stats.disk_models.free)} свободно</span>
              </div>
              <ProgressBar percent={(stats.disk_models.used / stats.disk_models.total) * 100} color="bg-orange-500" />
            </div>
          </div>
        </div>
      </div>

      {/* GPU */}
      <h3 className="text-xl font-bold mt-8 mb-4">Графические ускорители</h3>
      {stats.gpus.length === 0 ? (
        <div className="bg-gray-50 border border-gray-200 p-6 rounded-lg text-center text-gray-500">
          Видеокарты не обнаружены (используется CPU).
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {stats.gpus.map((gpu: any, idx: number) => {
            const isNvidia = gpu.vendor === 'NVIDIA';
            const badgeColor = isNvidia ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700';
            const borderColor = isNvidia ? 'border-green-500' : 'border-red-500';
            const noVram = gpu.mem_total === 0;

            return (
              <div key={idx} className={`bg-white p-5 rounded-lg shadow border-l-4 ${borderColor} flex flex-col md:flex-row gap-6 items-center`}>
                <div className="flex-1 min-w-[200px]">
                  <div className="text-lg font-bold flex items-center gap-2 text-gray-800">
                    <Zap className={isNvidia ? 'text-green-500' : 'text-red-500'} size={20}/> 
                    {gpu.name}
                  </div>
                  <div className="text-sm text-gray-500 mt-2 flex items-center gap-2">
                    <span className={`px-2 py-0.5 rounded text-xs font-bold ${badgeColor}`}>
                      {gpu.vendor}
                    </span>
                    <span>GPU #{idx}</span>
                  </div>
                </div>
                
                <div className="flex-1 w-full">
                  {!noVram ? (
                    <>
                      <div className="flex justify-between text-sm font-medium mt-1">
                        <span>Видеопамять (VRAM)</span>
                        <span>{gpu.mem_percent}% ({formatBytes(gpu.mem_used)} / {formatBytes(gpu.mem_total)})</span>
                      </div>
                      <ProgressBar percent={gpu.mem_percent} color={gpu.mem_percent > 90 ? 'bg-red-500' : 'bg-blue-500'} />
                    </>
                  ) : (
                    <div className="text-sm text-gray-400 italic mb-2">Выделенная VRAM не обнаружена (APU/iGPU)</div>
                  )}
                  
                  <div className="flex justify-between text-sm font-medium mt-3">
                    <span>Загрузка ядер</span>
                    <span>{gpu.utilization}%</span>
                  </div>
                  <ProgressBar percent={gpu.utilization} color={isNvidia ? 'bg-green-500' : 'bg-orange-500'} />
                </div>

                <div className="flex items-center gap-2 bg-gray-50 px-4 py-2 rounded-lg min-w-[100px] justify-center">
                  <Thermometer className={gpu.temperature > 80 ? 'text-red-500' : 'text-blue-500'} size={20} />
                  <span className="text-xl font-bold">
                    {gpu.temperature > 0 ? `${gpu.temperature}°C` : 'N/A'}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}