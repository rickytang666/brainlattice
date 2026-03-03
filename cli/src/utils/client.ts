import axios, { AxiosInstance } from 'axios';
import { getConfig } from './config.js';
import chalk from 'chalk';

const BACKEND_URL = process.env.BRAINLATTICE_API_URL;

export function createApiClient(): AxiosInstance {
  const config = getConfig();

  const client = axios.create({
    baseURL: BACKEND_URL,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // automatically inject headers before every request
  client.interceptors.request.use(
    (req) => {
      // always attach the user's ID
      if (config.user_id) {
        req.headers['X-User-Id'] = config.user_id;
      }
      
      // attach clerk session token (if logged in)
      if (config.session_token) {
        req.headers['Authorization'] = `Bearer ${config.session_token}`;
      }

      // attach standard api keys (BYOK logic)
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

  // intercept responses to print clean error messages if the backend complains
  client.interceptors.response.use(
    (res) => res,
    (error) => {
      if (error.response) {
        const detail = error.response.data?.detail || error.message;
        console.error(chalk.red(`\n✖ api error: ${detail}`));
        if (error.response.status === 401 || error.response.status === 403) {
          console.error(chalk.gray('hint: your session may have expired. try running `brainlattice login` again.'));
        }
      } else {
        console.error(chalk.red(`\n✖ network error: could not connect to ${BACKEND_URL}`));
      }
      // re-throw to allow specific commands to handle it if they want
      return Promise.reject(error);
    }
  );

  return client;
}
