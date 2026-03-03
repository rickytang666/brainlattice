import { Command } from 'commander';
import http from 'node:http';
import open from 'open';
import chalk from 'chalk';
import ora from 'ora';
import { saveConfig, getConfig } from '../utils/config.js';
import { createApiClient } from '../utils/client.js';

const FRONTEND_URL = process.env.BRAINLATTICE_FRONTEND_URL;
const AUTH_URL = `${FRONTEND_URL}/cli-auth`;

export const authCommand = new Command('login')
  .description('authenticate with your brainlattice account')
  .action(async () => {
    console.log(chalk.bold.blue('\nbrainlattice cli login\n'));
    
    // find an open port
    const server = http.createServer();
    const port = 4135;
    
    server.listen(port, '127.0.0.1', () => {
      const callbackUrl = `http://127.0.0.1:${port}/callback`;
      const fullAuthUrl = `${AUTH_URL}?redirect_uri=${encodeURIComponent(callbackUrl)}`;
      
      console.log(chalk.gray(`opening browser to ${fullAuthUrl}...`));
      
      const spinner = ora('waiting for authentication...').start();
      
      // handle ctrl+c
      const cleanup = () => {
        spinner.stop();
        console.log(chalk.yellow('\n\n⚠ login cancelled.'));
        server.close();
        process.exit(0);
      };

      process.on('SIGINT', cleanup);

      // auto timeout
      const timeout = setTimeout(() => {
        spinner.warn('login timed out after 5 minutes.');
        server.close();
        process.off('SIGINT', cleanup);
      }, 5 * 60 * 1000);
      
      open(fullAuthUrl).catch(() => {
        spinner.warn('could not open browser automatically.');
        console.log(`please open this url manually: ${chalk.cyan(fullAuthUrl)}`);
        spinner.start('waiting for authentication...');
      });
    });

    // handle the incoming redirect request from the browser
    server.on('request', (req, res) => {
      // console.log(chalk.gray(`\n[debug] received request: ${req.method} ${req.url}`));
      
      if (!req.url?.startsWith('/callback')) {
        // console.log(chalk.yellow(`[debug] ignoring non-callback request: ${req.url}`));
        res.writeHead(404, { 'Access-Control-Allow-Origin': '*' });
        res.end();
        return;
      }

      // parse the query params
      const url = new URL(req.url, `http://127.0.0.1:${port}`);
      const userId = url.searchParams.get('user_id');
      const token = url.searchParams.get('token');

      if (!userId) {
        res.writeHead(400, { 'Access-Control-Allow-Origin': '*' });
        res.end('Missing user_id');
        console.log(chalk.red('\n✖ authentication failed.'));
        server.close();
        process.exit(1);
        return;
      }

      // save to local config
      saveConfig({
        user_id: userId,
        session_token: token || undefined
      });

      // send success (no body needed as web UI handles the visual)
      res.writeHead(200, { 'Access-Control-Allow-Origin': '*' });
      res.end('OK');

      // shutdown server and exit cleanly
      console.log(chalk.green('\n✔ successfully authenticated!'));
      console.log(chalk.gray(`logged in as user: ${userId}\n`));
      
      server.close(() => {
        process.exit(0);
      });
    });

    // handle port conflicts
    server.on('error', (e: any) => {
      if (e.code === 'EADDRINUSE') {
        console.error(chalk.red(`\n✖ error: port ${port} is already in use. is another login currently running?`));
        process.exit(1);
      }
    });
  });

export const whoamiCommand = new Command('whoami')
  .description('display the current authenticated user and usage')
  .action(async () => {
    const config = getConfig();
    if (!config.user_id) {
      console.log(chalk.yellow('\n⚠ not logged in. run `brainlattice login` to get started.\n'));
      return;
    }

    const spinner = ora('fetching user info...').start();
    try {
      const api = createApiClient();
      const res = await api.get('whoami');
      spinner.stop();

      console.log(chalk.bold.blue('\nbrainlattice user info\n'));
      console.log(`${chalk.cyan('user id:')}    ${res.data.user_id}`);
      console.log(`${chalk.cyan('projects:')}   ${res.data.project_count}`);
      console.log();
    } catch (err: any) {
      spinner.fail('failed to fetch user info.');
      console.error(chalk.red(`\n✖ error: ${err.message}\n`));
    }
  });

export const logoutCommand = new Command('logout')
  .description('log out of your brainlattice account')
  .action(async () => {
    const config = getConfig();
    if (!config.user_id) {
      console.log(chalk.yellow('\n⚠ already logged out.\n'));
      return;
    }

    saveConfig({
      user_id: undefined,
      session_token: undefined
    });

    console.log(chalk.green('\n✔ successfully logged out. all local session data cleared.\n'));
  });
