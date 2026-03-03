import os from 'node:os';
import path from 'node:path';
import fs from 'node:fs';

export interface CliConfig {
  gemini_key?: string;
  openai_key?: string;
  default_vault?: string;
  user_id?: string;
  session_token?: string;
}

const CONFIG_DIR = path.join(os.homedir(), '.brainlattice');
const CONFIG_FILE = path.join(CONFIG_DIR, 'config.json');

export function getConfig(): CliConfig {
  if (!fs.existsSync(CONFIG_FILE)) {
    // generate a permanent anonymous UUID for this device until they login
    const anonymousId = 'anon_' + Math.random().toString(36).substring(2, 15);
    return { user_id: anonymousId };
  }
  try {
    const data = fs.readFileSync(CONFIG_FILE, 'utf-8');
    const parsed = JSON.parse(data) as CliConfig;
    if (!parsed.user_id) {
      parsed.user_id = 'anon_' + Math.random().toString(36).substring(2, 15);
      saveConfig(parsed);
    }
    return parsed;
  } catch (error) {
    return { user_id: 'anon_' + Math.random().toString(36).substring(2, 15) };
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
