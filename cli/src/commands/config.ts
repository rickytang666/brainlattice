import { Command } from 'commander';
import { input } from '@inquirer/prompts';
import chalk from 'chalk';
import { getConfig, saveConfig } from '../utils/config.js';

export const configCommand = new Command('config')
  .description('configure your api keys and default vaults')
  .action(async () => {
    // default action if 'config init' is not used, redirect to init for now
    await runInit();
  });

configCommand
  .command('init')
  .description('interactive setup for api keys and default directories')
  .action(runInit);

async function runInit() {
  const current = getConfig();
  
  console.log(chalk.bold.blue('\nbrainlattice cli setup\n'));
  
  const geminiKey = await input({
    message: 'enter your gemini api key (required for core extraction):',
    default: current.gemini_key || '',
  });

  const openaiKey = await input({
    message: 'enter your openai api key (optional):',
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
