import axios, { AxiosInstance } from 'axios';
import { getConfig } from './config.js';
import chalk from 'chalk';

// normalize backend url
const rawUrl = process.env.BRAINLATTICE_API_URL || 'https://api.brainlattice.com/api';
export const BACKEND_URL = rawUrl.endsWith('/') ? rawUrl : `${rawUrl}/`;

export function createApiClient(): AxiosInstance {
  const config = getConfig();

  const client = axios.create({
    baseURL: BACKEND_URL,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // inject headers before every request
  client.interceptors.request.use(
    (req) => {
      // attach user id
      if (config.user_id) {
        req.headers['X-User-Id'] = config.user_id;
      }
      
      // attach session token
      if (config.session_token) {
        req.headers['Authorization'] = `Bearer ${config.session_token}`;
      }

      // attach byok keys
      if (config.gemini_key) {
        req.headers['X-Gemini-API-Key'] = config.gemini_key;
      }
      if (config.openai_key) {
        req.headers['X-OpenAI-API-Key'] = config.openai_key;
      }

      return req;
    },
    (error) => Promise.reject(error)
  );

  // intercept errors for clean reporting
  client.interceptors.response.use(
    (res) => res,
    (error) => {
      if (error.response) {
        const detail = error.response.data?.detail || error.message;
        const fullUrl = error.config?.url ? `${error.config.baseURL}${error.config.url}` : 'unknown url';
        
        console.error(chalk.red(`\n✖ api error: ${detail}`));
        console.error(chalk.gray(`  url: ${fullUrl}`));
        console.error(chalk.gray(`  status: ${error.response.status}`));
        
        if (error.response.status === 401 || error.response.status === 403) {
          console.error(chalk.gray('hint: your session may have expired. try running `brainlattice login` again.'));
        }
      } else {
        const fullUrl = error.config?.url ? `${error.config.baseURL}${error.config.url}` : 'unknown url';
        console.error(chalk.red(`\n✖ network error: could not connect to backend`));
        console.error(chalk.gray(`  attempted: ${fullUrl}`));
      }
      return Promise.reject(error);
    }
  );

  return client;
}
