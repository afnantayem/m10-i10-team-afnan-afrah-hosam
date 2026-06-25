import { test, expect } from '@playwright/test';

const BASE_URL = process.env.PLAYWRIGHT_BASE_URL ?? 'http://localhost:3000';

test('kg page renders and returns rows', async ({ page }) => {
  await page.goto(`${BASE_URL}/kg`);

  await expect(page.getByRole('heading', { name: /Knowledge Graph/i })).toBeVisible();

  await page
    .getByPlaceholder('e.g. Find Sichuan recipes')
    .fill('Find Sichuan recipes');

  await page.getByRole('button', { name: 'Ask' }).click();

  await expect(page.getByTestId('kg-row').first()).toBeVisible({
    timeout: 15000,
  });
});
