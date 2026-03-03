import { Command } from 'commander';
import chalk from 'chalk';
import ora from 'ora';
import fs from 'node:fs';
import path from 'node:path';
import FormData from 'form-data';
import extract from 'extract-zip';
import axios from 'axios';
import cliProgress from 'cli-progress';
import { createApiClient } from '../utils/client.js';
import { getConfig } from '../utils/config.js';
import os from 'node:os';

const sleep = (ms: number) => new Promise(r => setTimeout(r, ms));

export const genCommand = new Command('gen')
  .description('generate an Obsidian vault from a local PDF')
  .argument('<pdf_path>', 'path to the local pdf file')
  .option('-v, --vault <vault_path>', 'destination obsidian vault')
  .option('--graph-only', 'only export the graph.json file (import the json to scratchpad on brainlattice web to visualize)')
  .option('--mock', 'simulate the process without making api calls (for testing purposes)')
  .action(async (pdfPath, options) => {
    try {
      console.log(chalk.bold.blue('\nbrainlattice generate\n'));

      const config = getConfig();
      if (!config.gemini_key) {
        throw new Error('missing gemini_key. please run `brainlattice config init` or `brainlattice login`.');
      }

      const absolutePdfPath = path.resolve(process.cwd(), pdfPath);
      if (!fs.existsSync(absolutePdfPath)) {
        throw new Error(`file not found: ${absolutePdfPath}`);
      }

      const vaultPathRaw = options.vault || config.default_vault;
      if (!options.graphOnly && !vaultPathRaw) {
        throw new Error('no vault path specified. provide --vault or set a default via `brainlattice config init`.');
      }

      const vaultPath = vaultPathRaw ? path.resolve(vaultPathRaw.replace('~', os.homedir())) : '';

      const api = createApiClient();
      const filename = path.basename(absolutePdfPath);

      if (options.mock) {
        console.log(chalk.yellow('running in mock mode - no tokens will be used\n'));
        
        // 1. mock upload
        const spinner = ora(`[mock] uploading ${chalk.cyan(filename)}...`).start();
        await sleep(1500);
        spinner.succeed(`[mock] uploaded successfully.`);

        // 2. mock extraction
        const extractionBar = new cliProgress.SingleBar({
          format: `${chalk.blue('graph extraction')} |${chalk.cyan('{bar}')}| {percentage}% | {step}`,
          barCompleteChar: '\u2588',
          barIncompleteChar: '\u2591',
          hideCursor: true
        });
        extractionBar.start(100, 0, { step: 'initializing...' });
        for (let i = 0; i <= 100; i += 10) {
          await sleep(500);
          extractionBar.update(i, { step: i < 50 ? 'extracting text...' : (i < 90 ? 'building graph...' : 'done') });
        }
        extractionBar.stop();
        console.log(chalk.green('✔ [mock] graph extraction complete!'));

        if (options.graphOnly) {
          const outPath = path.resolve(process.cwd(), `${filename.replace('.pdf', '')}_graph_mock.json`);
          fs.writeFileSync(outPath, JSON.stringify({ mock: true, nodes: [], edges: [] }, null, 2));
          console.log(chalk.green(`✔ [mock] saved mock graph to ${outPath}\n`));
          return;
        }

        // 3. mock export
        console.log(chalk.gray('triggering obsidian vault export...'));
        const exportBar = new cliProgress.SingleBar({
          format: `${chalk.magenta('vault exploration')} |${chalk.magenta('{bar}')}| {percentage}% | {step}`,
          barCompleteChar: '\u2588',
          barIncompleteChar: '\u2591',
          hideCursor: true
        });
        exportBar.start(100, 0, { step: 'preparing...' });
        for (let i = 0; i <= 100; i += 20) {
          await sleep(600);
          exportBar.update(i, { step: i < 50 ? 'generating notes...' : 'packing canvas...' });
        }
        exportBar.stop();
        console.log(chalk.green('✔ [mock] obsidian export ready.'));

        // 4. mock file operation
        const projectName = filename.replace('.pdf', '');
        const targetZipPath = path.join(vaultPath, `${projectName}.zip`);
        const extractDir = path.join(vaultPath, projectName);

        spinner.start(`[mock] creating ${chalk.cyan(projectName + '.zip')}...`);
        await sleep(1000);

        if (!fs.existsSync(extractDir)) {
          fs.mkdirSync(extractDir, { recursive: true });
        }
        
        // create a dummy zip file just to show it
        fs.writeFileSync(targetZipPath, 'mock zip content');
        fs.writeFileSync(path.join(extractDir, 'Mock Note.md'), `# Mock Note\nGenerated via brainlattice --mock mode.`);
        
        spinner.succeed(`[mock] extraction complete! check ${chalk.cyan(extractDir)} for the notes.\n`);
        return;
      }

      // 1. upload
      const spinner = ora(`uploading ${chalk.cyan(filename)}...`).start();
      const formData = new FormData();
      formData.append('file', fs.createReadStream(absolutePdfPath));
      
      const uploadRes = await api.post('ingest/upload', formData, {
        headers: {
          ...formData.getHeaders(),
        }
      });
      const jobId = uploadRes.data.job_id;
      spinner.succeed(`uploaded successfully.`);

      // 2. poll ingest status
      const extractionBar = new cliProgress.SingleBar({
        format: `${chalk.blue('graph extraction')} |${chalk.cyan('{bar}')}| {percentage}% | {step}`,
        barCompleteChar: '\u2588',
        barIncompleteChar: '\u2591',
        hideCursor: true
      });

      extractionBar.start(100, 0, { step: 'initializing...' });
      
      let projectId = null;
      while (true) {
        await sleep(2000);
        const statusRes = await api.get(`ingest/status/${jobId}`);
        const status = statusRes.data.status;
        const progress = statusRes.data.progress || 0;
        const details = statusRes.data.details || {};
        const step = status === 'completed' ? 'done' : (details.current_step || 'processing...');
        
        extractionBar.update(progress, { step: step.toLowerCase() });

        if (status === 'completed') {
          extractionBar.update(100, { step: 'done' });
          extractionBar.stop();
          console.log(chalk.green('✔ graph extraction complete!'));
          projectId = statusRes.data.metadata?.project_id || statusRes.data.details?.project_id || statusRes.data.result?.project_id;
          
          if (!projectId) {
            projectId = statusRes.data.details?.project_id || uploadRes.data.project_id;
          }
          break;
        } else if (status === 'failed') {
          extractionBar.stop();
          throw new Error('remote processing failed: ' + (statusRes.data.details?.error || 'unknown error'));
        }
      }

      if (!projectId) {
         // try to get it from the projects list as a fallback
         const projList = await api.get('projects/list');
         if (projList.data && projList.data.length > 0) {
            projectId = projList.data[0].id;
         } else {
             throw new Error('could not determine project_id from backend response.');
         }
      }

      // 3. graph only flow
      if (options.graphOnly) {
        spinner.start(`downloading graph.json...`);
        const graphRes = await api.get(`project/${projectId}/graph`);
        const outPath = path.resolve(process.cwd(), `${filename.replace('.pdf', '')}_graph.json`);
        fs.writeFileSync(outPath, JSON.stringify(graphRes.data, null, 2), 'utf-8');
        spinner.succeed(`saved graph to ${outPath}\n`);
        return;
      }

      // 4. obsidian export flow
      spinner.start('triggering obsidian vault export...');
      await api.post(`project/${projectId}/export/obsidian`);
      spinner.succeed('obsidian export triggered.');

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
        const exportStatusRes = await api.get(`project/${projectId}/export/status`);
        const estatus = exportStatusRes.data.status;
        const eprog = exportStatusRes.data.progress || 0;
        const emsg = exportStatusRes.data.message || 'processing...';
        
        exportBar.update(eprog, { step: emsg.toLowerCase() });

        if (estatus === 'complete' || estatus === 'completed') {
          exportBar.update(100, { step: 'done' });
          exportBar.stop();
          console.log(chalk.green('✔ obsidian export ready.'));
          downloadUrl = exportStatusRes.data.download_url;
          break;
        } else if (estatus === 'failed') {
          exportBar.stop();
          throw new Error('export generation failed.');
        }
      }

      spinner.start('downloading vault zip...');
      const dlRes = await api.get(`project/${projectId}/export/download`);
      const signedUrl = dlRes.data.download_url;

      const projectName = filename.replace('.pdf', '');
      const targetZipPath = path.join(vaultPath, `${projectName}.zip`);
      const extractDir = path.join(vaultPath, projectName);

      const zipData = await axios.get(signedUrl, { responseType: 'arraybuffer' });
      
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
