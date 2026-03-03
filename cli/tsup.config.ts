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
    BRAINLATTICE_API_URL: process.env.BRAINLATTICE_API_URL || 'https://api.brainlattice.com',
  }
});
