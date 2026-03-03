import chalk from 'chalk';

export function showBanner() {
  const banner = `
   ${chalk.cyan('____                 _       _              _   _                ')}
  ${chalk.cyan('| __ ) _ __ __ _(_)_ __ | |    __ _  | |_| |_(_) ___ ___ ')}
  ${chalk.cyan('|  _ \\| \'__/ _` | | \'_ \\| |   / _` | | __| __| |/ __/ _ \\')}
  ${chalk.cyan('| |_) | | | (_| | | | | | |__| (_| | | |_| |_| | (_|  __/')}
  ${chalk.cyan('|____/|_|  \\__,_|_|_| |_|_____\\__,_|  \\__|\\__|_|\\___\\___|')}
  `;

  const tagline = chalk.dim('  turn pdfs into living knowledge networks');

  console.log(banner);
  console.log(tagline + '\n');
}
