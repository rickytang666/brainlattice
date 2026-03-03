import { Command } from 'commander';
import { input } from '@inquirer/prompts';
import chalk from 'chalk';
import { getConfig, saveConfig } from '../utils/config.js';

export const configCommand = new Command('config')
  .description('configure your api keys and default vaults')
  .action(runInit);

async function runInit() {
  const current = getConfig();
  
  console.log(chalk.bold.blue('\nbrainlattice cli setup\n'));
  
  const geminiKey = await input({
    message: 'enter your gemini api key (required for core extraction):',
    default: current.gemini_key || '',
  });

  const openaiKey = await input({
    message: 'enter your openai api key (optional, but better for embeddings):',
    default: current.openai_key || '',
  });

  const defaultVault = await input({
    message: 'enter your default obsidian vault path (e.g., ~/obsidian/university):',
    default: current.default_vault || '',
  });

  saveConfig({
    gemini_key: geminiKey,
    openai_key: openaiKey,
    default_vault: defaultVault,
  });

  console.log(chalk.green('\n✔ configuration saved successfully to ~/.brainlattice/config.json\n'));
}
