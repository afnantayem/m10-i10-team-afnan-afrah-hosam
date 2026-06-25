import { test, expect } from '@playwright/test';

const BASE_URL = process.env.PLAYWRIGHT_BASE_URL ?? 'http://localhost:3000';

test('extract page renders and returns entities', async ({ page }) => {
  await page.goto(`${BASE_URL}/extract`);

  await expect(page.getByRole('heading', { name: /Extract/i })).toBeVisible();

  await page
    .getByPlaceholder('Paste text to extract named entities from...')
    .fill('Barack Obama visited Paris in 2020.');

  await page.getByRole('button', { name: 'Extract' }).click();

  await expect(page.getByTestId('entity-span').first()).toBeVisible({
    timeout: 15000,
  });
});
