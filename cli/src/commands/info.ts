import { Command } from 'commander';
import chalk from 'chalk';

export const infoCommand = new Command('info')
  .description('show information about brainlattice and the project repo')
  .action(() => {
    console.log(chalk.bold.blue('\n  brainlattice\n'));
    console.log(chalk.white('  ai extraction engine for knowledge synthesis.'));
    
    console.log('\n  ' + chalk.bold.cyan('features:'));
    console.log(chalk.gray('  • ') + chalk.white('complex pdf -> structured obsidian vaults'));
    console.log(chalk.gray('  • ') + chalk.white('semantic linkage of concepts'));
    console.log(chalk.gray('  • ') + chalk.white('recursive llm synthesis for deep study'));

    console.log('\n  ' + chalk.bold.yellow('repo:'));
    console.log(chalk.cyan('  https://github.com/rickytang666/brainlattice\n'));
  });