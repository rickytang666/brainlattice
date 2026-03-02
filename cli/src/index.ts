#!/usr/bin/env node
import { Command } from 'commander';
import chalk from 'chalk';

const program = new Command();

program
  .name('brainlattice')
  .description('CLI to extract PDFs into Obsidian vaults')
  .version('1.0.0');

program
  .command('config')
  .description('configure your api keys and default vaults')
  .action(() => {
    console.log(chalk.gray('config command coming soon'));
  });

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
