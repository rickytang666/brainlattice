import { Command } from 'commander';
import chalk from 'chalk';
import ora from 'ora';
import { confirm } from '@inquirer/prompts';
import { createApiClient } from '../utils/client.js';
import { getConfig } from '../utils/config.js';

export const deleteCommand = new Command('delete')
  .description('delete a project')
  .argument('<identifier>', 'project ID or title')
  .action(async (identifier) => {
    const config = getConfig();
    if (!config.user_id) {
       console.log(chalk.yellow('\n⚠ not logged in. run `brainlattice login` to get started.\n'));
       return;
    }

    const spinner = ora('searching for project...').start();
    try {
      const api = createApiClient();
      const res = await api.get('projects/list');
      const projects = res.data || [];
      
      // match by title (case insensitive)
      const project = projects.find((p: any) => 
        p.title.toLowerCase() === identifier.toLowerCase()
      );

      if (!project) {
        spinner.fail(chalk.red(`could not find project matching "${identifier}"`));
        return;
      }

      spinner.stop();

      const shouldDelete = await confirm({
        message: `are you sure you want to delete "${chalk.bold(project.title)}"? this cannot be undone.`,
        default: false,
      });

      if (!shouldDelete) {
        console.log(chalk.gray('deletion cancelled.'));
        return;
      }

      spinner.start(`deleting "${project.title}"...`);
      await api.delete(`project/${project.id}`);
      spinner.succeed(chalk.green(`successfully deleted "${project.title}".`));

    } catch (err: any) {
      if (spinner.isSpinning) {
        spinner.fail('failed to delete project.');
      }
      // error is already logged by api client interceptor
    }
  });
