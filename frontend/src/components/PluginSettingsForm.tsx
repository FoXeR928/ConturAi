import { useEffect, useMemo, useState } from 'react';
import { pluginsApi } from '../api/plugins';
import type {
  PluginSettings,
  PluginView,
  SelectOption,
  SettingValue,
  SettingsFieldSchema,
} from '../types/plugin';

interface PluginSettingsFormProps {
  plugin: PluginView;
  onChange?: (updated: PluginView) => void;
}

export function PluginSettingsForm({
  plugin,
  onChange,
}: PluginSettingsFormProps) {
  const [settings, setSettings] = useState<PluginSettings>(plugin.settings);
  const [isActive, setIsActive] = useState<boolean>(
    plugin.manifest.is_active,
  );
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [flash, setFlash] = useState<'idle' | 'saved' | 'toggled'>('idle');

  useEffect(() => {
    setSettings(plugin.settings);
    setIsActive(plugin.manifest.is_active);
  }, [plugin]);

  const entries = useMemo(
    () => Object.entries(plugin.manifest.settings_schema),
    [plugin.manifest.settings_schema],
  );

  const setField = (key: string, value: SettingValue): void => {
    setSettings((prev) => ({ ...prev, [key]: value }));
  };

  const handleToggle = async (): Promise<void> => {
    const next = !isActive;
    setIsActive(next);
    setError(null);
    try {
      const updated = await pluginsApi.toggle(
        plugin.manifest.id, next,
      );
      onChange?.(updated);
      setFlash('toggled');
      setTimeout(() => setFlash('idle'), 1200);
    } catch (err: unknown) {
      setIsActive(!next);
      setError(
        err instanceof Error ? err.message : 'Ошибка переключения',
      );
    }
  };

  const handleSave = async (): Promise<void> => {
    setIsSaving(true);
    setError(null);
    try {
      const updated = await pluginsApi.updateSettings(
        plugin.manifest.id, settings,
      );
      onChange?.(updated);
      setFlash('saved');
      setTimeout(() => setFlash('idle'), 1200);
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : 'Ошибка сохранения',
      );
    } finally {
      setIsSaving(false);
    }
  };

  const formDisabled = !isActive;

  return (
    <section className="bg-white rounded-lg border border-slate-200 shadow-sm p-6 space-y-6">
      <header className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex items-center gap-3">
            <h2 className="text-lg font-semibold text-slate-900 truncate">
              {plugin.manifest.name}
            </h2>
            <span
              className={
                'px-2 py-0.5 rounded-full text-xs font-medium ' +
                (isActive
                  ? 'bg-indigo-50 text-indigo-700'
                  : 'bg-slate-100 text-slate-500')
              }
            >
              {isActive ? 'Активен' : 'Отключен'}
            </span>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            {plugin.manifest.description || 'Без описания'}
          </p>
          <p className="text-xs text-slate-400 mt-1">
            v{plugin.manifest.version} · {plugin.manifest.kind} · id:{' '}
            {plugin.manifest.id}
          </p>
        </div>
        <ToggleSwitch checked={isActive} onChange={handleToggle} />
      </header>

      <div
        className={
          formDisabled
            ? 'space-y-5 opacity-50 pointer-events-none select-none'
            : 'space-y-5'
        }
        aria-disabled={formDisabled}
      >
        {entries.length === 0 && (
          <p className="text-sm text-slate-500">
            У плагина нет настраиваемых параметров.
          </p>
        )}

        {entries.map(([key, schema]) => (
          <FieldRenderer
            key={key}
            fieldKey={key}
            schema={schema}
            value={settings[key] ?? schema.default ?? null}
            onChange={(value) => setField(key, value)}
          />
        ))}

        <div className="flex items-center justify-end gap-3 pt-2">
          {error && (
            <span className="text-sm text-rose-600 mr-auto">{error}</span>
          )}
          {!error && flash === 'saved' && (
            <span className="text-sm text-emerald-600 mr-auto">
              Сохранено
            </span>
          )}
          {!error && flash === 'toggled' && (
            <span className="text-sm text-emerald-600 mr-auto">
              {isActive ? 'Плагин включён' : 'Плагин отключён'}
            </span>
          )}
          <button
            type="button"
            onClick={handleSave}
            disabled={isSaving || formDisabled}
            className="px-4 py-2 rounded-lg bg-indigo-600 text-white text-sm font-medium
                       hover:bg-indigo-700 disabled:opacity-60
                       disabled:cursor-not-allowed transition-colors"
          >
            {isSaving ? 'Сохранение...' : 'Сохранить'}
          </button>
        </div>
      </div>
    </section>
  );
}

interface ToggleSwitchProps {
  checked: boolean;
  onChange: () => void;
}

function ToggleSwitch({ checked, onChange }: ToggleSwitchProps) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={onChange}
      className={
        'relative inline-flex h-6 w-11 shrink-0 items-center rounded-full ' +
        'transition-colors ' +
        (checked ? 'bg-indigo-600' : 'bg-slate-300')
      }
    >
      <span
        className={
          'inline-block h-5 w-5 transform rounded-full bg-white shadow ' +
          'transition-transform ' +
          (checked ? 'translate-x-5' : 'translate-x-0.5')
        }
      />
      <span className="sr-only">
        {checked ? 'Отключить плагин' : 'Включить плагин'}
      </span>
    </button>
  );
}

interface FieldRendererProps {
  fieldKey: string;
  schema: SettingsFieldSchema;
  value: SettingValue;
  onChange: (value: SettingValue) => void;
}

function FieldRenderer({
  fieldKey,
  schema,
  value,
  onChange,
}: FieldRendererProps) {
  const fieldId = `field-${fieldKey}`;
  return (
    <div className="space-y-1.5">
      <div className="flex items-baseline justify-between gap-3">
        <label
          htmlFor={fieldId}
          className="text-sm font-medium text-slate-700"
        >
          {schema.label}
        </label>
        {schema.description && (
          <span className="text-xs text-slate-400 text-right">
            {schema.description}
          </span>
        )}
      </div>
      {renderControl(fieldId, schema, value, onChange)}
    </div>
  );
}

function renderControl(
  id: string,
  schema: SettingsFieldSchema,
  value: SettingValue,
  onChange: (value: SettingValue) => void,
): JSX.Element {
  switch (schema.type) {
    case 'select':
      return renderSelect(id, schema, value, onChange);
    case 'slider':
      return renderSlider(id, schema, value, onChange);
    case 'number':
      return renderNumber(id, schema, value, onChange);
    case 'text':
      return renderText(id, value, onChange);
    case 'boolean':
      return renderBoolean(id, value, onChange);
  }
}

function renderSelect(
  id: string,
  schema: SettingsFieldSchema,
  value: SettingValue,
  onChange: (value: SettingValue) => void,
): JSX.Element {
  const options: SelectOption[] = schema.options ?? [];
  return (
    <select
      id={id}
      value={value === null || value === undefined ? '' : String(value)}
      onChange={(event) => onChange(event.target.value)}
      className="w-full px-3 py-2 rounded-lg border border-slate-300 bg-white
                 text-sm text-slate-900 focus:outline-none focus:ring-2
                 focus:ring-indigo-500 focus:border-indigo-500"
    >
      {options.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  );
}

function renderSlider(
  id: string,
  schema: SettingsFieldSchema,
  value: SettingValue,
  onChange: (value: SettingValue) => void,
): JSX.Element {
  const min = schema.min ?? 0;
  const max = schema.max ?? 100;
  const step = schema.step ?? 1;
  const raw = typeof value === 'number' ? value : Number(value);
  const numeric = Number.isFinite(raw) ? raw : min;
  return (
    <div className="flex items-center gap-4">
      <input
        id={id}
        type="range"
        min={min}
        max={max}
        step={step}
        value={numeric}
        onChange={(event) => onChange(Number(event.target.value))}
        className="flex-1 h-2 rounded-full bg-slate-200
                   accent-indigo-600 cursor-pointer"
      />
      <span className="min-w-[3.5rem] text-right text-sm font-medium
                       text-slate-700 tabular-nums">
        {numeric}
      </span>
    </div>
  );
}

function renderNumber(
  id: string,
  schema: SettingsFieldSchema,
  value: SettingValue,
  onChange: (value: SettingValue) => void,
): JSX.Element {
  const raw = typeof value === 'number' ? value : Number(value);
  return (
    <input
      id={id}
      type="number"
      min={schema.min}
      max={schema.max}
      step={schema.step}
      value={Number.isFinite(raw) ? raw : ''}
      onChange={(event) => onChange(Number(event.target.value))}
      className="w-full px-3 py-2 rounded-lg border border-slate-300
                 bg-white text-sm text-slate-900 focus:outline-none
                 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
    />
  );
}

function renderText(
  id: string,
  value: SettingValue,
  onChange: (value: SettingValue) => void,
): JSX.Element {
  return (
    <input
      id={id}
      type="text"
      value={value === null || value === undefined ? '' : String(value)}
      onChange={(event) => onChange(event.target.value)}
      className="w-full px-3 py-2 rounded-lg border border-slate-300
                 bg-white text-sm text-slate-900 focus:outline-none
                 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
    />
  );
}

function renderBoolean(
  id: string,
  value: SettingValue,
  onChange: (value: SettingValue) => void,
): JSX.Element {
  return (
    <label
      htmlFor={id}
      className="inline-flex items-center gap-2 cursor-pointer"
    >
      <input
        id={id}
        type="checkbox"
        checked={Boolean(value)}
        onChange={(event) => onChange(event.target.checked)}
        className="h-4 w-4 rounded border-slate-300 text-indigo-600
                   focus:ring-indigo-500"
      />
      <span className="text-sm text-slate-700">Включено</span>
    </label>
  );
}