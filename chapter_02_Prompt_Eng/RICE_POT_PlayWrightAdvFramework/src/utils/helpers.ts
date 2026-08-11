import { expect, Page } from '@playwright/test';

export async function waitForPageLoad(page: Page) {
  await page.waitForLoadState('domcontentloaded');
  await page.waitForLoadState('networkidle');
}

export async function assertLoginErrorVisible(page: Page, message?: string) {
  const error = page.locator("//div[contains(@class,'error') or contains(@class,'alert') or contains(@class,'message')]");
  await expect(error).toBeVisible();

  if (message) {
    await expect(error).toContainText(message);
  }
}
