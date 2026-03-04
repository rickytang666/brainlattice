import { Command } from 'commander';
import chalk from 'chalk';
import { showBanner } from '../utils/banner.js';
import { input } from '@inquirer/prompts';

// parse string to args with quote support
function parseArgs(input: string): string[] {
  const regex = /[^\s"']+|"([^"]*)"|'([^']*)'/g;
  const args: string[] = [];
  let match;
  while ((match = regex.exec(input)) !== null) {
    args.push(match[1] || match[2] || match[0]);
  }
  return args;
}

export async function runShell(program: Command) {
  // apply exit override and custom output to all commands
  const applyConfig = (cmd: Command) => {
    cmd.exitOverride();
    cmd.configureOutput({
      writeErr: (str) => process.stdout.write(chalk.red(str)),
      writeOut: (str) => process.stdout.write(str),
    });
    cmd.commands.forEach(applyConfig);
  };
  applyConfig(program);

  console.clear();
  showBanner();
  console.log(chalk.gray('  type "exit" to quit, or "help" for commands\n'));

  // keep track of whether we are running as a shell
  process.env.BRAINLATTICE_SHELL = 'true';

  while (true) {
    try {
      const line = await input({
        message: '',
        theme: {
          prefix: chalk.hex('#07b7d6').bold('brainlattice ❯'),
        }
      });

      const trimmed = line.trim();
      if (!trimmed) continue;

      if (trimmed === 'exit' || trimmed === 'quit') {
        process.stdout.write(chalk.gray('goodbye!\n'));
        process.exit(0);
      }

      if (trimmed === 'clear') {
        console.clear();
        showBanner();
        continue;
      }

      const args = parseArgs(trimmed);

      // reset state for next parse
      (program as any).args = [];
      (program as any).rawArgs = [];

      // commander expects node and script as prefix
      await program.parseAsync(['node', 'brainlattice', ...args]);
      
    } catch (err: any) {
      // handle specific inquirer exit (ctrl+c)
      if (err.name === 'ExitPromptError') {
        process.stdout.write(chalk.gray('\ngoodbye!\n'));
        process.exit(0);
      }

      // ignore commander-handled signals (help, version, and usage errors)
      // usage errors are printed via writeErr in configureOutput
      const isCommanderSignal = [
        'commander.helpDisplayed',
        'commander.help',
        'commander.version',
        'commander.unknownCommand',
        'commander.missingArgument',
        'commander.unknownOption',
        'commander.missingMandatoryOptionValue'
      ].includes(err.code);

      if (!isCommanderSignal) {
        process.stdout.write(chalk.red(`\n✖ error: ${err.message}\n`));
      }
    }
    console.log(); // spacer
  }
}
