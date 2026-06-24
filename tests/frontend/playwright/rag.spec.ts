import { test, expect } from '@playwright/test';

const BASE_URL = process.env.PLAYWRIGHT_BASE_URL ?? 'http://localhost:3000';

test('rag page renders cited answer', async ({ page }) => {
  await page.goto(`${BASE_URL}/rag`);

  await expect(page.getByRole('heading', { name: /RAG/i })).toBeVisible();

  await page
    .getByPlaceholder('Ask a recipe question...')
    .fill('What ingredients does carbonara use?');

  await page.getByRole('button', { name: 'Ask' }).click();

  await expect(page.getByTestId('rag-answer')).toBeVisible({
    timeout: 30000,
  });

  await expect(page.getByTestId('citation-marker').first()).toBeVisible({
    timeout: 30000,
  });
});
