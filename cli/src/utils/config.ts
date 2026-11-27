import os from 'node:os';
import path from 'node:path';
import fs from 'node:fs';
import { randomUUID } from 'node:crypto';

export interface CliConfig {
  gemini_key?: string;
  openai_key?: string;
  openrouter_key?: string;
  default_vault?: string;
  user_id?: string;
  session_token?: string;
}

const CONFIG_DIR = path.join(os.homedir(), '.brainlattice');
const CONFIG_FILE = path.join(CONFIG_DIR, 'config.json');

// getConfig must write through this, not saveConfig: saveConfig reads via getConfig, so they'd recurse
function writeConfig(config: CliConfig): void {
  fs.mkdirSync(CONFIG_DIR, { recursive: true });
  fs.writeFileSync(CONFIG_FILE, JSON.stringify(config, null, 2), 'utf-8');
}

export function getConfig(): CliConfig {
  // the backend only accepts a uuid from a signed-out caller
  const generateAnonId = () => randomUUID();

  if (!fs.existsSync(CONFIG_FILE)) {
    const config = { user_id: generateAnonId() };
    writeConfig(config);
    return config;
  }
  try {
    const data = fs.readFileSync(CONFIG_FILE, 'utf-8');
    const parsed = JSON.parse(data) as CliConfig;
    // ids from older cli versions looked like anon_x7k2; the backend now rejects them
    if (!parsed.user_id || parsed.user_id.startsWith('anon_')) {
      parsed.user_id = generateAnonId();
      writeConfig(parsed);
    }
    return parsed;
  } catch (error) {
    const config = { user_id: generateAnonId() };
    writeConfig(config);
    return config;
  }
}

export function saveConfig(newConfig: Partial<CliConfig>): CliConfig {
  const merged = { ...getConfig(), ...newConfig };
  writeConfig(merged);
  return merged;
}
