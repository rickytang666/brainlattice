import os from 'node:os';
import path from 'node:path';
import fs from 'node:fs';

export interface CliConfig {
  gemini_key?: string;
  openai_key?: string;
  default_vault?: string;
}

const CONFIG_DIR = path.join(os.homedir(), '.brainlattice');
const CONFIG_FILE = path.join(CONFIG_DIR, 'config.json');

export function getConfig(): CliConfig {
  if (!fs.existsSync(CONFIG_FILE)) {
    return {};
  }
  try {
    const data = fs.readFileSync(CONFIG_FILE, 'utf-8');
    return JSON.parse(data) as CliConfig;
  } catch (error) {
    return {};
  }
}

export function saveConfig(newConfig: Partial<CliConfig>): CliConfig {
  if (!fs.existsSync(CONFIG_DIR)) {
    fs.mkdirSync(CONFIG_DIR, { recursive: true });
  }
  const current = getConfig();
  const merged = { ...current, ...newConfig };
  fs.writeFileSync(CONFIG_FILE, JSON.stringify(merged, null, 2), 'utf-8');
  return merged;
}
