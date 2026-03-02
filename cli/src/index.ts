#!/usr/bin/env node
import { Command } from 'commander';
import chalk from 'chalk';

import { configCommand } from './commands/config.js';

const program = new Command();

program
  .name('brainlattice')
  .description('CLI to extract PDFs into Obsidian vaults')
  .version('1.0.0');

program.addCommand(configCommand);

program
  .command('gen <pdf_path>')
  .description('generate a knowledge graph from a local PDF')
  .option('-v, --vault <vault_path>', 'destination obsidian vault')
  .action((pdfPath, options) => {
    console.log(chalk.gray(`gen command coming soon, will process ${pdfPath}`));
  });

program
  .command('export')
  .description('download your previously generated graphs from the remote server')
  .action(() => {
    console.log(chalk.gray('export command coming soon'));
  });

program.parse();
