// @ts-check
const { defineConfig } = require('@playwright/test');

const matrixEnabled = /^(1|true|yes)$/i.test(process.env.PW_MATRIX || '');
const projects = matrixEnabled
  ? [
    { name: 'chromium', use: { browserName: 'chromium', headless: true } },
    { name: 'firefox', use: { browserName: 'firefox', headless: true } },
  ]
  : [
    { name: 'chromium', use: { browserName: 'chromium', headless: true } },
  ];

module.exports = defineConfig({
  testDir: './tests',
  testIgnore: ['**/unit/**'],
  timeout: 30_000,
  retries: 0,
  workers: 1, // sequential; each test starts its own server
  use: {
    headless: true,
  },
  projects,
});
