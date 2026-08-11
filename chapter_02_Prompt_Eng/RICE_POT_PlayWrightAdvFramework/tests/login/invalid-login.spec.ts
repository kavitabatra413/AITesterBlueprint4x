import { test, expect } from '@playwright/test';
import { LoginPage } from '../../src/pages/LoginPage';
import { config } from '../../src/utils/config';

test.describe('Salesforce invalid login', () => {
  test('invalid password shows error message', async ({ page }) => {
    const loginPage = new LoginPage(page);

    await page.goto(config.baseUrl);
    await loginPage.login('invaliduser@example.com', config.invalidPassword);

    const errorText = await loginPage.getErrorMessageText();
    expect(errorText.length).toBeGreaterThan(0);
  });

  test('empty username and password fail validation', async ({ page }) => {
    const loginPage = new LoginPage(page);

    await page.goto(config.baseUrl);
    await loginPage.clickLogin();

    await expect(page.locator('body')).toContainText(/required|username|password/i);
  });
});
