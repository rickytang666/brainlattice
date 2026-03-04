import axios from 'axios';
import chalk from 'chalk';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';

const CONFIG_DIR = path.join(os.homedir(), '.brainlattice');
const CACHE_FILE = path.join(CONFIG_DIR, 'update-check.json');
const CHECK_INTERVAL = 24 * 60 * 60 * 1000; // 24 hours

export async function checkForUpdates(currentVersion: string) {
  try {
    // check cache
    if (fs.existsSync(CACHE_FILE)) {
      const cache = JSON.parse(fs.readFileSync(CACHE_FILE, 'utf-8'));
      if (Date.now() - cache.lastCheck < CHECK_INTERVAL) {
        return;
      }
    }

    // check npm registry (short timeout)
    const response = await axios.get('https://registry.npmjs.org/brainlattice/latest', {
      timeout: 1000 
    });
    
    const latestVersion = response.data.version;

    // update cache
    if (!fs.existsSync(CONFIG_DIR)) {
      fs.mkdirSync(CONFIG_DIR, { recursive: true });
    }
    fs.writeFileSync(CACHE_FILE, JSON.stringify({
      lastCheck: Date.now(),
      latestVersion
    }));

    // compare versions
    if (latestVersion !== currentVersion) {
      console.log(
        boxen(
          `Update available ${chalk.dim(currentVersion)} → ${chalk.green(latestVersion)}\nRun ${chalk.cyan('npm install -g brainlattice')} to update`,
          { padding: 1, margin: 1, borderStyle: 'round', borderColor: 'yellow' }
        )
      );
    }
  } catch (error) {
    // silently fail on network error
  }
}

// boxen helper to avoid deps
function boxen(text: string, options: any) {
  const lines = text.split('\n');
  const width = Math.max(...lines.map(l => l.replace(/\u001b\[\d+m/g, '').length)) + 4;
  
  const top = chalk.yellow('╭' + '─'.repeat(width - 2) + '╮');
  const bottom = chalk.yellow('╰' + '─'.repeat(width - 2) + '╯');
  
  const content = lines.map(line => {
      const plainLine = line.replace(/\u001b\[\d+m/g, '');
      const padding = ' '.repeat(width - 4 - plainLine.length);
      return chalk.yellow('│ ') + line + padding + chalk.yellow(' │');
  }).join('\n');
  
  return `\n${top}\n${content}\n${bottom}\n`;
}
