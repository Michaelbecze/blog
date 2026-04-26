import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://michaelbecze.github.io',
  base: '/blog/',
  markdown: {
    shikiConfig: {
      theme: 'github-dark',
      wrap: true,
    },
  },
});
