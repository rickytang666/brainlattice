import { defineConfig } from 'tsup';
import dotenv from 'dotenv';
dotenv.config();

export default defineConfig({
  entry: ['src/index.ts'],
  format: ['esm'],
  clean: true,
  dts: false,
  minify: true,
  sourcemap: true,
  env: {
    // not BRAINLATTICE_API_URL: tsup would inline it and kill the runtime override
    BRAINLATTICE_DEFAULT_API_URL: process.env.BRAINLATTICE_DEFAULT_API_URL || 'https://api.brainlattice.rickytang.dev/api',
    BRAINLATTICE_FRONTEND_URL: process.env.BRAINLATTICE_FRONTEND_URL || 'https://brainlattice.rickytang.dev',
  }
});
