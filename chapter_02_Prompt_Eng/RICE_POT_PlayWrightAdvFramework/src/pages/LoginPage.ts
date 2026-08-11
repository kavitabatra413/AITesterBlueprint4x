import { Locator, Page } from '@playwright/test';

export class LoginPage {
  readonly page: Page;
  readonly usernameInput: Locator;
  readonly passwordInput: Locator;
  readonly loginButton: Locator;
  readonly rememberMeCheckbox: Locator;
  readonly errorMessage: Locator;

  constructor(page: Page) {
    this.page = page;
    this.usernameInput = page.locator("//input[@type='email' or @name='username' or @id='username']");
    this.passwordInput = page.locator("//input[@type='password' or @name='pw' or @id='password']");
    this.loginButton = page.locator("//input[@type='submit' or @name='Login' or contains(@value,'Log In')] | //button[contains(.,'Log In')]");
    this.rememberMeCheckbox = page.locator("//label[contains(.,'Remember me')] | //input[@type='checkbox']");
    this.errorMessage = page.locator("//div[contains(@class,'error') or contains(@class,'alert') or contains(@class,'message')]");
  }

  async goto() {
    await this.page.goto('/');
  }

  async enterUsername(username: string) {
    await this.usernameInput.waitFor({ state: 'visible' });
    await this.usernameInput.fill(username);
  }

  async enterPassword(password: string) {
    await this.passwordInput.waitFor({ state: 'visible' });
    await this.passwordInput.fill(password);
  }

  async clickLogin() {
    await this.loginButton.waitFor({ state: 'visible' });
    await this.loginButton.click();
  }

  async login(username: string, password: string) {
    await this.enterUsername(username);
    await this.enterPassword(password);
    await this.clickLogin();
  }

  async getErrorMessageText() {
    await this.errorMessage.waitFor({ state: 'visible' });
    return (await this.errorMessage.textContent())?.trim() ?? '';
  }

  async isErrorMessageVisible() {
    return await this.errorMessage.isVisible();
  }

  async isRememberMeChecked() {
    const checkbox = this.page.locator("//input[@type='checkbox']");
    return await checkbox.isChecked();
  }
}
