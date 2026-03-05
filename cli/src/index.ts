#!/usr/bin/env node
import { Command } from 'commander';
import chalk from 'chalk';

import { configCommand } from './commands/config.js';
import { authCommand, whoamiCommand, logoutCommand } from './commands/auth.js';
import { genCommand } from './commands/gen.js';
import { statusCommand } from './commands/status.js';

import { exportCommand } from './commands/export.js';
import { listCommand } from './commands/list.js';
import { deleteCommand } from './commands/delete.js';
import { infoCommand } from './commands/info.js';
import { checkForUpdates } from './utils/notifier.js';
import { runShell } from './commands/shell.js';

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
program.addCommand(whoamiCommand);
program.addCommand(logoutCommand);
program.addCommand(listCommand);
program.addCommand(genCommand);
program.addCommand(statusCommand);
program.addCommand(exportCommand);
program.addCommand(deleteCommand);
program.addCommand(infoCommand);

// enter interactive shell if no args
if (process.argv.length <= 2) {
  runShell(program);
} else {
  program.parse();
}
