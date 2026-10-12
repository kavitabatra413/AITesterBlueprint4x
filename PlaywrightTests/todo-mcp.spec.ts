import { test, expect } from '@playwright/test';

test('can add and complete a todo item', async ({ page }) => {
  await page.goto('https://demo.playwright.dev/todomvc/');

  const todoText = `Learn Playwright automation ${Date.now()}`;
  const newTodo = page.getByRole('textbox', { name: 'What needs to be done?' });

  await newTodo.fill(todoText);
  await newTodo.press('Enter');

  const todoItem = page.getByRole('listitem').filter({ hasText: todoText });
  await expect(todoItem).toBeVisible();

  const todoCheckbox = todoItem.getByRole('checkbox');
  await todoCheckbox.check();
  await expect(todoCheckbox).toBeChecked();
});
