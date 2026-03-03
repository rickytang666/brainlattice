import { Command } from 'commander';
import chalk from 'chalk';
import ora from 'ora';
import fs from 'node:fs';
import path from 'node:path';
import extract from 'extract-zip';
import axios from 'axios';
import cliProgress from 'cli-progress';
import { createApiClient, BACKEND_URL } from '../utils/client.js';
import { getConfig } from '../utils/config.js';
import os from 'node:os';
import { select } from '@inquirer/prompts';

const sleep = (ms: number) => new Promise(r => setTimeout(r, ms));

const sanitizeName = (name: string) => name.replace(/[^a-z0-9]/gi, '_').toLowerCase();

const formatDate = (dateStr: string) => {
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  } catch {
    return 'unknown date';
  }
};

export const exportCommand = new Command('export')
  .description('download previously generated graphs from the remote server')
  .argument('[project_id]', 'optional project ID to export directly')
  .option('-v, --vault <vault_path>', 'destination obsidian vault')
  .option('--mock', 'simulate the process without making api calls (for testing purposes)')
  .action(async (projectIdArg, options) => {
    try {

      const config = getConfig();
      const vaultPathRaw = options.vault || config.default_vault;
      if (!vaultPathRaw) {
        throw new Error('no vault path specified. provide --vault or set a default via `brainlattice config init`.');
      }
      const vaultPath = path.resolve(vaultPathRaw.replace('~', os.homedir()));

      const api = createApiClient();
      let projectId = projectIdArg;
      let projectName = '';

      if (options.mock) {
        console.log(chalk.yellow('running in mock mode - no tokens will be used\n'));
        
        if (!projectId) {
          const selection = await select<{ id: string, name: string }>({
            message: 'Select a project to export:',
            loop: false,
            pageSize: 10,
            choices: [
              { name: `Quantum Computing Paper ${chalk.gray('(created Mar 2)')}`, value: { id: 'mock-1', name: 'quantum_paper' } },
              { name: `History of AI ${chalk.gray('(created Feb 28)')}`, value: { id: 'mock-2', name: 'ai_history' } },
              { name: `Biology Notes ${chalk.gray('(created Feb 15)')}`, value: { id: 'mock-3', name: 'biology_notes' } },
            ],
          });
          projectId = selection.id;
          projectName = selection.name;
        } else {
          projectName = `mock_${projectId}`;
        }

        const targetZipPath = path.join(vaultPath, `${projectName}.zip`);
        const extractDir = path.join(vaultPath, projectName);

        // simulate progress
        const exportBar = new cliProgress.SingleBar({
          format: `${chalk.magenta('vault exploration')} |${chalk.magenta('{bar}')}| {percentage}% | {step}`,
          barCompleteChar: '\u2588',
          barIncompleteChar: '\u2591',
          hideCursor: true
        });
        exportBar.start(100, 0, { step: 'preparing...' });
        for (let i = 0; i <= 100; i += 20) {
          await sleep(500);
          exportBar.update(i, { step: i < 50 ? 'generating notes...' : 'packing canvas...' });
        }
        exportBar.stop();

        const spinner = ora(`[mock] creating ${chalk.cyan(projectName + '.zip')}...`).start();
        await sleep(1000);
        if (!fs.existsSync(extractDir)) fs.mkdirSync(extractDir, { recursive: true });
        
        fs.writeFileSync(targetZipPath, 'mock zip content');
        fs.writeFileSync(path.join(extractDir, 'Exported Note.md'), `# Exported Note\nMock export for project ${projectId}`);
        spinner.succeed(`[mock] export complete! check ${chalk.cyan(extractDir)} for the notes.\n`);
        return;
      }

      // 1. resolve project ID and Name
      if (!projectId) {
        const spinner = ora('fetching projects...').start();
        try {
          const res = await api.get('projects/list');
          spinner.stop();
          
          if (!res.data || res.data.length === 0) {
            throw new Error('no projects found on remote server.');
          }

          const selection = await select<{ id: string, name: string }>({
            message: 'Select a project to export:',
            loop: false,
            pageSize: 10,
            choices: res.data.map((p: any) => ({
              name: `${p.title || p.name || p.filename || p.id} ${chalk.gray(`(created ${formatDate(p.created_at)})`)}`,
              value: { 
                id: p.id, 
                name: sanitizeName(p.title || p.name || p.filename || p.id) 
              },
              description: `Status: ${p.status}`
            })),
          });
          
          projectId = selection.id;
          projectName = selection.name;
        } catch (err: any) {
          spinner.fail('failed to fetch projects.');
          throw err;
        }
      } else {
        projectName = `project_${projectId.slice(0, 8)}`;
      }
      
      // 2. trigger export
      const spinner = ora('triggering obsidian vault export...').start();
      await api.post(`project/${projectId}/export/obsidian`);
      spinner.succeed('obsidian export triggered.');

      // 3. poll status
      const exportBar = new cliProgress.SingleBar({
        format: `${chalk.magenta('vault exploration')} |${chalk.magenta('{bar}')}| {percentage}% | {step}`,
        barCompleteChar: '\u2588',
        barIncompleteChar: '\u2591',
        hideCursor: true
      });
      exportBar.start(100, 0, { step: 'preparing...' });

      let downloadUrl = null;
      while (true) {
        await sleep(2000);
        const statusRes = await api.get(`project/${projectId}/export/status`);
        const status = statusRes.data.status;
        const progress = statusRes.data.progress || 0;
        const message = statusRes.data.message || 'processing...';
        
        exportBar.update(progress, { step: message.toLowerCase() });

        if (status === 'complete' || status === 'completed') {
          exportBar.update(100, { step: 'done' });
          exportBar.stop();
          console.log(chalk.green('✔ obsidian export ready.'));
          downloadUrl = statusRes.data.download_url;
          break;
        } else if (status === 'failed') {
          exportBar.stop();
          throw new Error('export generation failed.');
        }
      }

      // 4. download & extract
      spinner.start('downloading vault zip...');
      const dlRes = await api.get(`project/${projectId}/export/download`);
      const signedUrl = dlRes.data.download_url;

      if (!signedUrl) {
        throw new Error('failed to retrieve a valid download URL from the server.');
      }

      const zipData = await axios.get(signedUrl, { responseType: 'arraybuffer' });
      
      const targetZipPath = path.join(vaultPath, `${projectName}.zip`);
      const extractDir = path.join(vaultPath, projectName);

      if (!fs.existsSync(vaultPath)) {
        fs.mkdirSync(vaultPath, { recursive: true });
      }
      
      fs.writeFileSync(targetZipPath, Buffer.from(zipData.data));
      spinner.succeed(`downloaded ${chalk.cyan(projectName + '.zip')}.`);

      spinner.start(`extracting into ${chalk.cyan(projectName + '/')}...`);
      if (!fs.existsSync(extractDir)) {
        fs.mkdirSync(extractDir, { recursive: true });
      }

      await extract(targetZipPath, { dir: extractDir });
      spinner.succeed(`extraction complete! knowledge graph ready at: ${chalk.cyan(extractDir)}\n`);

    } catch (error: any) {
      console.error(chalk.red(`\n✖ error: ${error.message}`));
      process.exit(1);
    }
  });
