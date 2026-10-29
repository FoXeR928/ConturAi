export type FieldType = 'select' | 'slider' | 'number' | 'text' | 'boolean';

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
  kind: PluginKind;
  is_active: boolean;
  settings_schema: Record<string, SettingsFieldSchema>;
}

export type SettingValue = string | number | boolean | null;
export type PluginSettings = Record<string, SettingValue>;

export interface PluginView {
  manifest: PluginManifest;
  settings: PluginSettings;
}