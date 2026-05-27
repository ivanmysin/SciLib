import { test, expect } from '@playwright/test';

test.describe('Library', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.getByPlaceholder('Email').fill('test@example.com');
    await page.getByPlaceholder('Password').fill('password');
    await page.getByRole('button', { name: /sign in/i }).click();
    await page.waitForURL(/\/library/);
  });

  test('displays library page', async ({ page }) => {
    await expect(page.getByText('Library')).toBeVisible();
    await expect(page.getByText(/collections/i)).toBeVisible();
  });

  test('can navigate to search', async ({ page }) => {
    await page.getByText('Search').click();
    await expect(page).toHaveURL(/\/search/);
  });

  test('can navigate to groups', async ({ page }) => {
    await page.getByText('Groups').click();
    await expect(page).toHaveURL(/\/groups/);
  });
});
