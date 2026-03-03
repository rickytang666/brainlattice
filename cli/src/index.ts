#!/usr/bin/env node
import { Command } from 'commander';
import chalk from 'chalk';

import { configCommand } from './commands/config.js';
import { authCommand } from './commands/auth.js';
import { genCommand } from './commands/gen.js';
import { statusCommand } from './commands/status.js';

import { exportCommand } from './commands/export.js';
import { checkForUpdates } from './utils/notifier.js';

const VERSION = '1.0.0';

const program = new Command();

// run update check in the background
checkForUpdates(VERSION).catch(() => {});

program
  .name('brainlattice')
  .description('CLI to extract PDFs into Obsidian vaults')
  .version(VERSION);

program.addCommand(configCommand);
program.addCommand(authCommand);
program.addCommand(genCommand);
program.addCommand(statusCommand);
program.addCommand(exportCommand);

program.parse();
