#!/usr/bin/env node
import { Command } from 'commander';
import chalk from 'chalk';

import { configCommand } from './commands/config.js';
import { authCommand } from './commands/auth.js';
import { genCommand } from './commands/gen.js';
import { statusCommand } from './commands/status.js';

const program = new Command();

program
  .name('brainlattice')
  .description('CLI to extract PDFs into Obsidian vaults')
  .version('1.0.0');

program.addCommand(configCommand);
program.addCommand(authCommand);
program.addCommand(genCommand);
program.addCommand(statusCommand);

program
  .command('export')
  .description('download your previously generated graphs from the remote server')
  .action(() => {
    console.log(chalk.gray('export command coming soon'));
  });

program.parse();
