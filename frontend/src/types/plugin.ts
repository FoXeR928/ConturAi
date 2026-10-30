export type FieldType = 'select' | 'slider' | 'number' | 'text' | 'boolean';
export type HealthStatus = 'ok' | 'down' | 'unknown';
export type PluginKind = 'internal' | 'external';

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

export interface PluginAction {
  id: string;
  label: string;
  confirm: boolean;
  description?: string | null;
}

export interface PluginManifest {
  id: string;
  name: string;
  description: string;
  version: string;
  api_version: string;
  kind: PluginKind;
  is_active: boolean;
  priority: number;
  provides_stream: boolean;
  execution_timeout: number;
  max_concurrent: number;
  settings_schema: Record<string, SettingsFieldSchema>;
  actions: PluginAction[];
}

export type SettingValue = string | number | boolean | null;
export type PluginSettings = Record<string, SettingValue>;

export interface PluginView {
  manifest: PluginManifest;
  settings: PluginSettings;
  health_status: HealthStatus;
}

export interface PipelineTraceItem {
  plugin_id: string;
  plugin_name: string;
  duration_ms: number;
  ok: boolean;
  error?: string | null;
}