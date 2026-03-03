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
        res.writeHead(400, { 
          'Content-Type': 'text/html',
          'Access-Control-Allow-Origin': '*'
        });
        res.end(`
          <!DOCTYPE html>
          <html>
            <head>
              <meta charset="utf-8">
              <title>Authentication Failed | BrainLattice</title>
              <style>
                :root { --bg: #09090b; --fg: #fafafa; --muted: #71717a; --error: #ef4444; }
                body { 
                  background-color: var(--bg); color: var(--fg); 
                  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                  display: flex; flex-direction: column; align-items: center; justify-content: center;
                  height: 100vh; margin: 0; text-align: center;
                }
                .container { 
                  max-width: 400px; padding: 2rem; 
                  animation: fade-in 0.8s ease-out;
                }
                h1 { font-family: "Big Caslon", "Book Antiqua", "Palatino Linotype", Georgia, serif; font-weight: 500; font-size: 1.5rem; margin-bottom: 0.5rem; color: var(--error); }
                p { color: var(--muted); font-size: 0.9rem; line-height: 1.5; }
                @keyframes fade-in { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
              </style>
            </head>
            <body>
              <div class="container">
                <h1>authentication failed</h1>
                <p>Missing user credentials in callback. <br/> Please close this window and try running <code>brainlattice login</code> again.</p>
              </div>
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
      res.writeHead(200, { 
        'Content-Type': 'text/html',
        'Access-Control-Allow-Origin': '*'
      });
      res.end(`
        <!DOCTYPE html>
        <html>
          <head>
            <meta charset="utf-8">
            <title>Authenticated | BrainLattice</title>
            <style>
              :root { --bg: #09090b; --fg: #fafafa; --muted: #a1a1aa; --accent: #7c3aed; --success: #10b981; }
              body { 
                background-color: var(--bg); color: var(--fg); 
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                display: flex; flex-direction: column; align-items: center; justify-content: center;
                height: 100vh; margin: 0; text-align: center;
              }
              .container { 
                max-width: 440px; padding: 2rem; 
                animation: fade-in 1s cubic-bezier(0.16, 1, 0.3, 1);
              }
              .logo { font-family: Georgia, serif; font-style: italic; font-size: 1.25rem; color: var(--muted); margin-bottom: 2rem; }
              h1 { font-family: "Big Caslon", "Book Antiqua", "Palatino Linotype", Georgia, serif; font-weight: 500; font-size: 1.75rem; margin-bottom: 1rem; color: var(--fg); }
              p { color: var(--muted); font-size: 0.95rem; line-height: 1.6; letter-spacing: -0.01em; }
              .badge { display: inline-flex; align-items: center; gap: 0.5rem; color: var(--success); font-weight: 600; font-size: 0.85rem; text-transform: lowercase; margin-bottom: 1rem; }
              .dot { width: 6px; height: 6px; background-color: var(--success); border-radius: 50%; box-shadow: 0 0 10px var(--success); }
              code { background: #18181b; padding: 0.2rem 0.4rem; border-radius: 4px; color: var(--accent); }
              @keyframes fade-in { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
            </style>
          </head>
          <body>
            <div class="container">
              <div class="logo">brainlattice</div>
              <div class="badge"><span class="dot"></span> linked</div>
              <h1>successfully authenticated</h1>
              <p>
                Your CLI has been authorized. <br/>
                You can now return to your terminal and close this tab.
              </p>
            </div>
            <script>
              // auto-close the tab after 4 seconds
              setTimeout(() => { window.close(); }, 4000);
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
