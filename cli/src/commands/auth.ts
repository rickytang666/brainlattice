import { Command } from 'commander';
import http from 'node:http';
import open from 'open';
import chalk from 'chalk';
import ora from 'ora';
import { saveConfig } from '../utils/config.js';

const AUTH_URL = 'https://brainlattice.rickytang.dev/cli-auth';

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
      
      open(fullAuthUrl).catch(() => {
        spinner.warn('could not open browser automatically.');
        console.log(`please open this url manually: ${chalk.cyan(fullAuthUrl)}`);
        spinner.start('waiting for authentication...');
      });
    });

    // handle the incoming redirect request from the browser
    server.on('request', (req, res) => {
      if (!req.url?.startsWith('/callback')) {
        res.writeHead(404);
        res.end();
        return;
      }

      // parse the query params
      const url = new URL(req.url, `http://127.0.0.1:${port}`);
      const userId = url.searchParams.get('user_id');
      const token = url.searchParams.get('token');

      if (!userId) {
        res.writeHead(400, { 'Content-Type': 'text/html' });
        res.end(`
          <html>
            <body style="font-family: sans-serif; text-align: center; padding-top: 50px;">
              <h2 style="color: red;">authentication failed.</h2>
              <p>missing user_id in callback. you can close this window and try again.</p>
            </body>
          </html>
        `);
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

      // send success html to browser
      res.writeHead(200, { 'Content-Type': 'text/html' });
      res.end(`
        <html>
          <body style="font-family: sans-serif; text-align: center; padding-top: 50px; background-color: #f8f9fa;">
            <h2 style="color: #10b981;">successfully authenticated!</h2>
            <p style="color: #6b7280; margin-top: 10px;">
              your credentials have been shared successfully with the brainlattice cli. <br/>
              <b>you can now close this tab.</b>
            </p>
            <script>
              // optionally attempt to auto-close the tab after 3 seconds
              setTimeout(() => { window.close(); }, 3000);
            </script>
          </body>
        </html>
      `);

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
