import { test, expect } from '@playwright/test';
import { LoginPage } from '../../src/pages/LoginPage';
import { config } from '../../src/utils/config';

test.describe('Salesforce valid login', () => {
  test('user can login successfully with valid credentials', async ({ page }) => {
    const loginPage = new LoginPage(page);

    await page.goto(config.baseUrl);
    await loginPage.login(config.validUsername, config.validPassword);

    await expect(page).toHaveURL(/.*(home|lightning|one.app)/i);
  });
});
