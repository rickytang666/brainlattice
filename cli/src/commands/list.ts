import { Command } from 'commander';
import chalk from 'chalk';
import ora from 'ora';
import { createApiClient } from '../utils/client.js';
import { getConfig } from '../utils/config.js';

export const listCommand = new Command('list')
  .description('list all your projects')
  .action(async () => {
    const config = getConfig();
    if (!config.user_id) {
       console.log(chalk.yellow('\n⚠ not logged in. run `brainlattice login` to get started.\n'));
       return;
    }

    const spinner = ora('fetching projects...').start();
    try {
      const api = createApiClient();
      const res = await api.get('projects/list');
      spinner.stop();

      const projects = res.data || [];

      if (projects.length === 0) {
        console.log(chalk.yellow('\nno projects found. use `brainlattice gen` to create one!\n'));
        return;
      }

      console.log(chalk.bold.blue('\nyour brainlattice projects\n'));

      // table display logic
      const header = {
          title: 'title',
          status: 'status',
          date: 'created'
      };

      // calculate column widths
      const colWidths = {
          title: Math.max(...projects.map((p: any) => (p.title || p.filename || p.id).slice(0, 30).length), header.title.length) + 2,
          status: 14,
          date: 20
      };

      // print header
      const headStr = 
          chalk.bold(header.title.padEnd(colWidths.title)) + 
          chalk.bold(header.status.padEnd(colWidths.status)) +
          chalk.bold(header.date);
      
      console.log(headStr);
      console.log(chalk.gray('─'.repeat(colWidths.title + colWidths.status + colWidths.date)));

      // print rows
      projects.forEach((p: any) => {
          const rawTitle = (p.title || p.filename || p.id);
          const title = (rawTitle.length > 30 ? rawTitle.slice(0, 27) + '...' : rawTitle).padEnd(colWidths.title);
          
          let statusText = p.status || 'unknown';
          let statusColor = chalk.white;
          
          if (statusText === 'complete') statusColor = chalk.green;
          else if (statusText === 'processing' || statusText === 'uploading') statusColor = chalk.yellow;
          else if (statusText === 'failed') statusColor = chalk.red;
          
          const status = statusColor(statusText.padEnd(colWidths.status));
          const date = formatDate(p.created_at);
          
          console.log(`${title}${status}${date}`);
      });

      console.log(chalk.gray(`\n(${projects.length} project${projects.length === 1 ? '' : 's'} total)\n`));

    } catch (err: any) {
      spinner.fail('failed to fetch projects.');
      console.error(chalk.red(`\n✖ error: ${err.message}\n`));
    }
  });

function formatDate(dateStr: string) {
    try {
        const d = new Date(dateStr);
        return d.toLocaleDateString(undefined, { 
            month: 'short', 
            day: 'numeric', 
            hour: '2-digit', 
            minute: '2-digit' 
        });
    } catch {
        return 'unknown';
    }
}
