export type FieldType = 'select' | 'slider' | 'number' | 'text' | 'boolean';
export type HealthStatus = 'ok' | 'down' | 'unknown';

export interface SelectOption {
  label: string;
  value: string;
}

export interface SettingsFieldSchema {
  type: FieldType;
  label: string;
  default?: string | number | boolean | null;
  description?: string;
  required?: boolean;
  options?: SelectOption[];
  min?: number;
  max?: number;
  step?: number;
}

export type PluginKind = 'internal' | 'external';

export interface PluginManifest {
  id: string;
  name: string;
  description: string;
  version: string;
  api_version: string;
  kind: PluginKind;
  is_active: boolean;
  streaming: boolean;
  max_history_chars: number;
  execution_timeout: number;
  max_concurrent: number;
  settings_schema: Record<string, SettingsFieldSchema>;
}

export type SettingValue = string | number | boolean | null;
export type PluginSettings = Record<string, SettingValue>;

export interface PluginView {
  manifest: PluginManifest;
  settings: PluginSettings;
  health_status: HealthStatus;
}